# Render the README hero image from the example pages, so it always shows what handmade really produces.
#
#   pip install playwright && playwright install chromium
#   python scripts/hero_image.py
#
# It screenshots examples/landing/before.html and after.html at 2x, puts them in browser frames
# with the request they were built from and the real check results, and writes docs/images/hero.png.

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "landing"
OUT = ROOT / "docs" / "images" / "hero.png"
REQUEST = "build a landing page for Duka Ledger, a stock and sales app for small shops in Kenya"

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Alegreya:wght@700&family=Alegreya+Sans:wght@400;700&family=Red+Hat+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  :root { --ink:#1f191f; --paper:#f8f6f8; --muted:#b9adb6; --line:#3a3039; --ok:#4fbf7a; --bad:#ef6a5e; }
  * { box-sizing:border-box; margin:0; padding:0 }
  body { width:1600px; background:var(--ink); color:var(--paper); font-family:"Alegreya Sans",sans-serif; }
  .wrap { padding:28px 32px 28px; background:
      radial-gradient(900px 420px at 18% 0%, rgba(164,60,125,.16), transparent 70%),
      radial-gradient(900px 420px at 86% 100%, rgba(79,191,122,.10), transparent 70%); }
  header { display:flex; align-items:center; justify-content:space-between; gap:28px; margin-bottom:22px }
  h1 { font-family:Alegreya,serif; font-weight:700; font-size:36px; line-height:1.1; letter-spacing:-.01em; white-space:nowrap }
  h1 em { font-style:normal; color:#e9b7d6 }
  .prompt { font-family:"Red Hat Mono",monospace; font-size:16px; color:#e7dfe5; background:#2a2229; border:1px solid var(--line);
            border-radius:8px; padding:12px 16px; white-space:nowrap }
  .prompt b { color:var(--muted); font-weight:400 }
  .cols { display:grid; grid-template-columns:1fr 1fr; gap:26px }
  .label { display:flex; align-items:baseline; justify-content:space-between; margin-bottom:10px }
  .label h2 { font-size:21px; font-weight:700 }
  .label span { font-size:15px; color:var(--muted) }
  .frame { border-radius:12px; overflow:hidden; border:1px solid #4a3f48; background:#fff;
           box-shadow:0 24px 60px -24px rgba(0,0,0,.8), 0 2px 8px rgba(0,0,0,.4) }
  .bar { height:34px; background:#efe9ee; display:flex; align-items:center; gap:7px; padding:0 12px; border-bottom:1px solid #ded4dc }
  .bar i { width:11px; height:11px; border-radius:50%; background:#d9cdd6; display:block }
  .bar .url { margin-left:10px; flex:1; height:20px; border-radius:5px; background:#fff; color:#6d5f6d; font-size:12px;
              line-height:20px; padding:0 10px; font-family:"Red Hat Mono",monospace }
  .frame img { display:block; width:100%; height:auto }
  .result { margin-top:12px; display:flex; align-items:center; gap:12px; font-family:"Red Hat Mono",monospace; font-size:15px;
            color:#efe7ed; white-space:nowrap }
  .result i { width:12px; height:12px; border-radius:50%; display:block; flex:none }
  .bad i { background:var(--bad); box-shadow:0 0 0 4px rgba(239,106,94,.18) }
  .ok i { background:var(--ok); box-shadow:0 0 0 4px rgba(79,191,122,.18) }
  .result b { font-weight:500 }
  .bad b { color:var(--bad) } .ok b { color:var(--ok) }
  .result span { color:var(--muted) }
</style></head>
<body><div class="wrap">
  <header>
    <h1>Same request, same AI.<br><em>Only one of them was briefed.</em></h1>
    <div class="prompt"><b>$</b> handmade prompt "__REQUEST__"</div>
  </header>
  <div class="cols">
    <section>
      <div class="label"><h2>Plain request</h2><span>what the model does by default</span></div>
      <div class="frame"><div class="bar"><i></i><i></i><i></i><div class="url">localhost:3000/before</div></div><img src="before.png" alt=""></div>
      <div class="result bad"><i></i><b>handmade check: FAIL</b><span>score __BEFORE_SCORE__/100 · __BEFORE_VERDICT__ · __BEFORE_TELLS__ tells</span></div>
    </section>
    <section>
      <div class="label"><h2>Through handmade</h2><span>brief, design system, gate</span></div>
      <div class="frame"><div class="bar"><i></i><i></i><i></i><div class="url">localhost:3000/after</div></div><img src="after.png" alt=""></div>
      <div class="result ok"><i></i><b>handmade check: PASS</b><span>score __AFTER_SCORE__/100 · __AFTER_VERDICT__ · every value from the system</span></div>
    </section>
  </div>
</div></body></html>
"""


def scan(page: Path) -> dict:
    out = subprocess.run([sys.executable, "-m", "handmade", "scan", str(page), "--format", "json"],
                         capture_output=True, text=True, cwd=ROOT, env={**__import__("os").environ, "PYTHONPATH": str(ROOT / "src")})
    return json.loads(out.stdout)


def main() -> int:
    from playwright.sync_api import sync_playwright
    sys.path.insert(0, str(ROOT / "src"))
    from handmade.render import _browser

    before, after = scan(EXAMPLE / "before.html"), scan(EXAMPLE / "after.html")
    work = Path(tempfile.mkdtemp())
    html = (PAGE.replace("__REQUEST__", REQUEST)
            .replace("__BEFORE_SCORE__", str(before["score"])).replace("__BEFORE_VERDICT__", before["verdict"])
            .replace("__BEFORE_TELLS__", str(len(before["tells"])))
            .replace("__AFTER_SCORE__", str(after["score"])).replace("__AFTER_VERDICT__", after["verdict"]))
    (work / "compose.html").write_text(html, encoding="utf-8")
    with sync_playwright() as pw:
        browser = _browser(pw)
        for name in ("before", "after"):
            page = browser.new_page(viewport={"width": 1200, "height": 760}, device_scale_factor=2)
            page.goto((EXAMPLE / f"{name}.html").as_uri(), wait_until="load")
            page.wait_for_timeout(2500)  # web fonts
            page.screenshot(path=str(work / f"{name}.png"))
            page.close()
        page = browser.new_page(viewport={"width": 1600, "height": 800}, device_scale_factor=2)
        page.goto((work / "compose.html").as_uri(), wait_until="load")
        page.wait_for_timeout(2500)
        page.set_viewport_size({"width": 1600, "height": page.evaluate("document.body.scrollHeight")})
        page.screenshot(path=str(OUT), full_page=True)
        browser.close()
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
