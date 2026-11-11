# Rendered-page mode: check what the browser actually draws.
#
# The source scanner reads code. This module opens the page in headless Chrome
# (through Playwright) at desktop and phone width and reads computed styles,
# so styles created at runtime, by JavaScript or by a CSS framework are seen too.
# It also measures real text contrast and detects fonts that silently failed to load.
#
# Needs: pip install playwright, plus a Chrome or Chromium browser
# (`playwright install chromium` or an installed Google Chrome).

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from .colors import colors_in, contrast, distance, is_neutral, is_purple, parse_color
from .conform import PASS_THRESHOLDS, Conformance, _Collector, COLOR_TOLERANCE  # noqa: F401
from .profile import GENERIC_FAMILIES, Profile, norm_font
from .scan import Report
from .tells import (EMOJI, GENERIC_FONTS, GENERIC_HEAD, HYPE, MARKED_PLACEHOLDER, PLACEHOLDER, STOCK_HOSTS, TREND_FONTS, VANITY,
                    Finding, REGISTRY)

VIEWPORTS = {"desktop": (1440, 900), "phone": (390, 844)}

COLLECT_JS = r"""
() => {
  const out = [];
  const els = Array.from(document.querySelectorAll('body *')).slice(0, 4000);
  const canvas = document.createElement('canvas').getContext('2d');
  const probe = 'mmmmmmmmmmlli1WQ@#';
  const fontOk = {};
  function available(family) {
    if (family in fontOk) return fontOk[family];
    let ok = false;
    for (const fallback of ['monospace', 'serif', 'sans-serif']) {
      canvas.font = `40px ${fallback}`; const a = canvas.measureText(probe).width;
      canvas.font = `40px "${family}", ${fallback}`; const b = canvas.measureText(probe).width;
      if (a !== b) { ok = true; break; }
    }
    fontOk[family] = ok; return ok;
  }
  function path(el) {
    let s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    else if (el.classList.length) s += '.' + Array.from(el.classList).slice(0, 2).join('.');
    return s;
  }
  function effectiveBg(el) {
    let node = el;
    while (node && node !== document.documentElement) {
      const cs = getComputedStyle(node);
      const bg = cs.backgroundColor;
      if (bg && bg !== 'transparent' && !/rgba\([^)]*,\s*0\)$/.test(bg)) return bg;
      if (cs.backgroundImage && cs.backgroundImage !== 'none') return 'image:' + cs.backgroundImage;
      node = node.parentElement;
    }
    const root = getComputedStyle(document.documentElement).backgroundColor;
    return (root && !/rgba\([^)]*,\s*0\)$/.test(root)) ? root : 'rgb(255, 255, 255)';
  }
  for (const el of els) {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    if (r.width < 1 || r.height < 1 || cs.visibility === 'hidden' || cs.display === 'none' || +cs.opacity === 0) continue;
    const own = Array.from(el.childNodes).filter(n => n.nodeType === 3).map(n => n.textContent).join(' ').trim();
    const first = cs.fontFamily.split(',')[0].trim().replace(/^["']|["']$/g, '');
    out.push({
      sel: path(el), tag: el.tagName.toLowerCase(), text: own.slice(0, 120),
      role: el.getAttribute('role') || '', href: el.hasAttribute('href'), alt: el.hasAttribute('alt'),
      src: el.tagName === 'IMG' ? (el.currentSrc || el.src || '') : '', altText: (el.getAttribute('alt') || '').slice(0, 120),
      x: r.left, y: r.top + window.scrollY, w: r.width, h: r.height,
      font: first, fontOk: own ? available(first) : true, fontSize: cs.fontSize, fontWeight: cs.fontWeight,
      color: cs.color, bg: cs.backgroundColor, bgImage: cs.backgroundImage, effBg: own ? effectiveBg(el) : '',
      clip: cs.webkitBackgroundClip || cs.backgroundClip, fill: cs.webkitTextFillColor,
      shadow: cs.boxShadow, textShadow: cs.textShadow, filter: cs.filter,
      backdrop: cs.backdropFilter || cs.webkitBackdropFilter || 'none',
      radius: [cs.borderTopLeftRadius, cs.borderTopRightRadius, cs.borderBottomRightRadius, cs.borderBottomLeftRadius],
      border: cs.borderTopWidth + ' ' + cs.borderTopColor,
      padding: [cs.paddingTop, cs.paddingRight, cs.paddingBottom, cs.paddingLeft], gap: cs.rowGap + ' ' + cs.columnGap,
      align: cs.textAlign, parent: el.parentElement ? path(el.parentElement) : '',
      parentIndex: el.parentElement ? Array.from(el.parentElement.children).indexOf(el) : 0,
      siblings: el.parentElement ? el.parentElement.children.length : 0,
    });
  }
  return {title: document.title, text: document.body.innerText.slice(0, 20000), vw: innerWidth, els: out};
}
"""


def _browser(pw):
    try:
        return pw.chromium.launch(args=["--no-sandbox"])
    except Exception:
        for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
            exe = shutil.which(name)
            if exe:
                return pw.chromium.launch(executable_path=exe, args=["--no-sandbox"])
        raise RuntimeError("No Chrome or Chromium found. Run `playwright install chromium` or install Google Chrome.")


def target_url(path: str | Path) -> str:
    s = str(path)
    if re.match(r"^https?://", s):
        return s
    p = Path(s).resolve()
    if p.is_dir():
        pages = [p / "index.html"] if (p / "index.html").is_file() else sorted(p.glob("*.html"))
        if not pages:
            raise ValueError(f"no .html page found in {p}. Pass a URL, for example http://localhost:3000")
        p = pages[0]
    return p.as_uri()


def page_urls(path: str | Path, pages: list[str] | None = None) -> list[str]:
    # The base page plus every extra page, as full URLs. A page can be a route ("/pricing") or a full URL.
    from urllib.parse import urljoin
    base = target_url(path)
    urls = [base]
    for page in pages or []:
        page = str(page).strip()
        if not page:
            continue
        url = page if re.match(r"^(?:https?|file)://", page) else urljoin(base, page)
        if url not in urls:
            urls.append(url)
    return urls


def collect_many(urls: list[str]) -> list[dict]:
    # Load every page at each viewport in one browser and return the raw computed-style data per page.
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("Rendered mode needs Playwright: pip install playwright") from exc
    out = []
    with sync_playwright() as pw:
        browser = _browser(pw)
        try:
            for url in urls:
                data: dict = {}
                for name, (w, h) in VIEWPORTS.items():
                    page = browser.new_page(viewport={"width": w, "height": h})
                    try:
                        page.goto(url, wait_until="load", timeout=30000)
                    except Exception as exc:  # a route that does not answer must not hide the others
                        raise RuntimeError(f"could not open {url}: {str(exc).splitlines()[0]}") from exc
                    page.wait_for_timeout(400)
                    data[name] = page.evaluate(COLLECT_JS)
                    page.close()
                data["url"] = url
                out.append(data)
        finally:
            browser.close()
    return out


def collect(path: str | Path) -> dict[str, dict]:
    # Load one page at each viewport and return the raw computed-style data.
    return collect_many([target_url(path)])[0]


def _as_pages(data) -> list[dict]:
    # Accept one page's data or a list of pages.
    return list(data) if isinstance(data, list) else [data]


# ---------- analysis ----------

def _px(value: str) -> float:
    m = re.match(r"(-?[\d.]+)px", value or "")
    return float(m.group(1)) if m else 0.0


def _blur_colors(value: str) -> list[tuple[float, str]]:
    # (blur, color) for each visible layer of a computed box-shadow or text-shadow.
    #
    # Layers fainter than 20% opacity are ordinary soft shadows, not glows, so they are skipped.
    out = []
    if not value or value == "none":
        return out
    for layer in re.split(r",(?![^(]*\))", value):
        cols = colors_in(layer)
        m = re.search(r"rgba\([^)]*,\s*([\d.]+)\)", layer)
        if m and float(m.group(1)) < 0.2:
            continue
        nums = [float(n) for n in re.findall(r"(-?[\d.]+)px", re.sub(r"rgba?\([^)]*\)", "", layer))]
        if cols and len(nums) >= 3 and "inset" not in layer:
            out.append((nums[2], cols[0]))
    return out


def _alpha(value: str) -> float:
    m = re.match(r"rgba\([^,]+,[^,]+,[^,]+,\s*([\d.]+)\)", value or "")
    return float(m.group(1)) if m else 1.0


def analyze(data: dict, allow_stock: bool = False) -> list[Finding]:
    url = data["url"]
    findings: list[Finding] = []

    def add(tid: str, detail: str) -> None:
        if any(f.tell == tid and f.detail == detail for f in findings):
            return
        if sum(1 for f in findings if f.tell == tid) < 3:
            findings.append(Finding(tid, url, 0, detail))

    desk = data["desktop"]
    for vp_name, vp in (("desktop", data["desktop"]), ("phone", data["phone"])):
        els = vp["els"]
        text_els = [e for e in els if e["text"]]
        # Typography
        fonts = {}
        for e in text_els:
            fonts[norm_font(e["font"])] = fonts.get(norm_font(e["font"]), 0) + len(e["text"])
        if fonts and vp_name == "desktop":
            main = max(fonts, key=fonts.get)
            if main in GENERIC_FONTS or (main in GENERIC_FAMILIES and main != "monospace"):
                add("type.generic-font", f"most text renders in {main}")
            for f in fonts:
                if f in TREND_FONTS:
                    add("type.trend-font", f"text renders in {f.title()}")
            missing = sorted({e["font"] for e in text_els if not e["fontOk"] and norm_font(e["font"]) not in GENERIC_FAMILIES})
            for f in missing:
                add("type.font-not-loaded", f"{f} did not load, the browser fell back to another font")
        for e in els:
            img = e["bgImage"] or ""
            if "gradient" in img:
                stops = colors_in(img)
                if any(is_purple(c) for c in stops) and len(stops) >= 2:
                    add("color.purple-gradient", f"{e['sel']} renders a purple gradient")
                if "text" in (e["clip"] or "") and (e["fill"] or "").endswith(", 0)") or (
                        "text" in (e["clip"] or "") and e["color"].endswith(", 0)")):
                    add("type.gradient-text", f"{e['sel']} has gradient-filled text")
            bg = parse_color(e["bg"]) if e["bg"] and _alpha(e["bg"]) > 0.05 else None
            clickable = e["tag"] in ("button", "a") or e["role"] == "button"
            if bg and is_purple(bg) and (clickable or e["w"] * e["h"] > 20000):
                add("color.indigo-accent", f"{e['sel']} renders with purple background {bg}")
            for blur, col in _blur_colors(e["shadow"]) + _blur_colors(e["textShadow"]):
                if blur >= 16 and not is_neutral(col):
                    add("color.neon-glow", f"{e['sel']} has a colored glow ({col}, {blur:.0f}px blur)")
            if "drop-shadow" in (e["filter"] or ""):
                for c in colors_in(e["filter"]):
                    if not is_neutral(c):
                        add("color.neon-glow", f"{e['sel']} has a colored drop-shadow glow")
            if "blur" in (e["backdrop"] or "") and e["bg"] and 0 < _alpha(e["bg"]) < 1:
                add("deco.glassmorphism", f"{e['sel']} is a frosted glass panel")
            m = re.search(r"blur\(([\d.]+)px\)", e["filter"] or "")
            if m and float(m.group(1)) >= 40:
                add("deco.blur-blob", f"{e['sel']} is a blurred shape ({m.group(1)}px)")
            if e["text"] and EMOJI.search(e["text"]):
                add("deco.emoji-icons", f"{e['sel']} shows emoji: {e['text'][:30]}")
            if e["tag"] == "img" and not e["alt"]:
                add("a11y.img-no-alt", f"{e['sel']} has no alt text")
            alt_words = len(re.findall(r"[^\W\d_]+", e.get("altText", "")))
            if e["tag"] == "img" and STOCK_HOSTS.search(e.get("src", "")) and not MARKED_PLACEHOLDER.search(e.get("altText", "")) \
                    and not (allow_stock and alt_words >= 4):
                add("copy.stock-photos", f"{e['sel']} loads {STOCK_HOSTS.search(e['src']).group(0)}")
        if vp_name == "desktop":
            rs = [e for e in els if max(_px(r) for r in e["radius"]) >= 12 and e["shadow"] not in ("", "none")
                  and max((float(n) for n in re.findall(r"(\d+(?:\.\d+)?)px", re.sub(r"rgba?\([^)]*\)", "", e["shadow"]))[2:3]), default=0) >= 10]
            if len(rs) >= 3:
                add("deco.rounded-shadow-everywhere", f"{len(rs)} elements have large radius and large shadow")
            # Faint text: real contrast against the real background
            faint = []
            for e in text_els:
                fg, bgv = parse_color(e["color"]), e["effBg"]
                if not fg or not bgv or bgv.startswith("image:") or _alpha(e["color"]) < 0.05:
                    continue
                bgc = parse_color(bgv)
                large = _px(e["fontSize"]) >= 24 or (_px(e["fontSize"]) >= 18.66 and int(e["fontWeight"] or 400) >= 700)
                ratio = contrast(fg, bgc) if bgc else 21
                if ratio < (3 if large else 4.5):
                    faint.append(f"{e['sel']} {ratio:.1f}:1")
            if faint:
                add("a11y.faint-text", f"{len(faint)} text elements fail WCAG contrast, e.g. {faint[0]}")
            # Centered hero: first h1 in the first screen, centered, with two or more actions just below
            h1s = [e for e in els if e["tag"] == "h1" and e["y"] < 900]
            if h1s:
                h = h1s[0]
                centered = h["align"] == "center" or abs((h["x"] + h["w"] / 2) - desk["vw"] / 2) < desk["vw"] * 0.03 and h["w"] < desk["vw"] * 0.8
                actions = [e for e in els if (e["tag"] in ("a", "button") or e["role"] == "button") and e["text"]
                           and h["y"] < e["y"] < h["y"] + h["h"] + 400]
                if centered and _px(h["fontSize"]) >= 36 and len(actions) >= 2:
                    add("layout.centered-hero", f"centered {h['fontSize']} headline with {len(actions)} actions below")
            # Images side by side that end up different heights
            rows: dict[int, list] = {}
            for e in els:
                if e["tag"] == "img" and e["w"] >= 120 and e["h"] >= 80:
                    rows.setdefault(round(e["y"] / 8), []).append(e)
            for imgs in rows.values():
                if len(imgs) >= 2:
                    hs = [i["h"] for i in imgs]
                    if max(hs) / min(hs) > 1.12:
                        add("layout.uneven-images",
                            f"{len(imgs)} images in one row range from {min(hs):.0f}px to {max(hs):.0f}px tall")
            # Three equal cards side by side
            groups: dict[str, list] = {}
            for e in els:
                if e["siblings"] == 3 and e["h"] > 80:
                    groups.setdefault(e["parent"] + f"@{round(e['y'])}", []).append(e)
            for key, kids in groups.items():
                if len(kids) == 3 and max(k["w"] for k in kids) - min(k["w"] for k in kids) < 6 and kids[0]["w"] < desk["vw"] / 2.5:
                    add("layout.three-cards", f"three equal boxes in {key.split('@')[0]}")
    body = desk["text"]
    for tid, rx in (("copy.hype", HYPE), ("copy.placeholder", PLACEHOLDER), ("copy.vanity-stats", VANITY),
                    ("copy.generic-headline", GENERIC_HEAD)):
        m = rx.search(body)
        if m:
            add(tid, f'"{m.group(0)}" in the rendered text')
    return findings


def render_scan(path: str | Path, ignore: set[str] | None = None, data: dict | list[dict] | None = None,
                allow_stock: bool = False, pages: list[str] | None = None) -> Report:
    # Scan one page, or the base page plus every page in `pages`. Findings name the page they were seen on.
    pages_data = _as_pages(data) if data else collect_many(page_urls(path, pages))
    ignore = ignore or set()
    cats = {t.id: t.category for t in REGISTRY}
    findings = []
    for page_data in pages_data:
        findings += [f for f in analyze(page_data, allow_stock) if f.tell not in ignore and cats.get(f.tell) not in ignore]
    urls = [d["url"] for d in pages_data]
    return Report(root=urls[0], profile=Profile(), findings=findings, files=urls)


def render_conformance(path: str | Path, system: dict, data: dict | list[dict] | None = None,
                       pages: list[str] | None = None) -> Conformance:
    # Whitelist check on computed styles: fonts, colors, font sizes, radii and padding or gaps.
    # Every page shares one tally, so one off-system value on any page is reported once.
    pages_data = _as_pages(data) if data else collect_many(page_urls(path, pages))
    conf = Conformance(system=system)
    col = _Collector(conf)
    for page_data in pages_data:
        _conform_page(page_data, system, col)
    return conf


def _conform_page(data: dict, system: dict, col: _Collector) -> None:
    url = data["url"]
    fonts_ok = {norm_font(f) for f in system["fonts"].values()} | GENERIC_FAMILIES
    colors_ok = [c.lower() for c in system["colors"].values()]
    sizes_ok = [float(s) for s in system["type_scale_px"]]
    space_ok = [float(s) for s in system["spacing_px"]]
    radius_ok = [0.0, float(system["radius_px"]["controls"]), float(system["radius_px"]["containers"])]

    def near(v: float, allowed: list[float], tol: float = 0.6) -> bool:
        return any(abs(v - a) <= tol for a in allowed)

    def check_color(value: str, where: str) -> None:
        for c in colors_in(value):
            col.seen("colors")
            if not any(distance(c, ok) <= COLOR_TOLERANCE for ok in colors_ok):
                col.off("colors", c, where, 0, hard=not is_neutral(c))

    for vp_name in VIEWPORTS:
        for e in data[vp_name]["els"]:
            where = f"{url} {e['sel']} ({vp_name})"
            if e["text"]:
                f = norm_font(e["font"])
                col.seen("fonts")
                if f not in fonts_ok:
                    col.off("fonts", f, where, 0, hard=True)
                col.seen("font sizes")
                if not near(_px(e["fontSize"]), sizes_ok):
                    col.off("font sizes", e["fontSize"], where, 0)
                if _alpha(e["color"]) > 0.05:
                    check_color(e["color"], where)
            if e["bg"] and _alpha(e["bg"]) > 0.05:
                check_color(e["bg"], where)
            if "gradient" in (e["bgImage"] or ""):
                check_color(e["bgImage"], where)
            bw, _, bcol = (e["border"] or "").partition(" ")
            if _px(bw) > 0 and bcol.strip() != "transparent" and (not bcol.startswith("rgba") or _alpha(bcol) > 0.05):
                check_color(bcol, where)
            for blur, c in _blur_colors(e["shadow"]):
                check_color(c, where) if not is_neutral(c) else None
            for r in e["radius"]:
                v = _px(r)
                if v and v < 999 and not (e["w"] and abs(v - min(e["w"], e["h"]) / 2) < 1):
                    col.seen("radii")
                    if not near(v, radius_ok):
                        col.off("radii", r, where, 0)
            for v in [_px(p) for p in e["padding"]] + [_px(g) for g in (e["gap"] or "").split()]:
                if v > 4:
                    col.seen("spacing")
                    if not near(v, space_ok):
                        col.off("spacing", f"{v:g}px", where, 0)


def dump(path: str | Path) -> str:
    # Raw collected data, for debugging.
    return json.dumps(collect(path), indent=1)[:200000]
