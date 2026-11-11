# The registry of tells: patterns that make a UI look like an unedited AI default.
#
# Each tell has an ID, a category, a weight, a reason and a concrete fix.
# A tell is a signal, not proof. Every one can be a fine choice when it is deliberate.

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass

from .extract import Doc
from .colors import colors_in, is_ai_gradient_stop, is_cream, is_neutral, is_purple, is_terracotta
from .profile import NEUTRALS, Profile, base

MAX_PER_FILE = 3


@dataclass(frozen=True)
class Finding:
    tell: str
    file: str
    line: int
    detail: str


@dataclass(frozen=True)
class Tell:
    id: str
    category: str
    weight: int
    title: str
    why: str
    fix: str
    check: Callable[["Context"], list[Finding]]


@dataclass
class Context:
    docs: list[Doc]
    profile: Profile
    allow_stock: bool = False  # the user agreed to stock photos in the brief


REGISTRY: list[Tell] = []


def tell(id: str, category: str, weight: int, title: str, why: str, fix: str):
    def wrap(fn: Callable[[Context], list[Finding]]):
        REGISTRY.append(Tell(id, category, weight, title, why, fix, fn))
        return fn
    return wrap


# ---------- helpers ----------

def _token_hits(ctx: Context, tid: str, pattern: re.Pattern, label: str | None = None) -> list[Finding]:
    out = []
    for doc in ctx.docs:
        n = 0
        for line, tok in doc.tokens:
            if pattern.search(base(tok)):
                out.append(Finding(tid, doc.rel, line, label or tok))
                n += 1
                if n >= MAX_PER_FILE:
                    break
    return out


def _element_hits(ctx: Context, tid: str, test: Callable[[set[str]], bool], label: str) -> list[Finding]:
    out = []
    for doc in ctx.docs:
        n = 0
        for line, toks in doc.elements:
            bases = {base(t) for t in toks}
            if test(bases):
                out.append(Finding(tid, doc.rel, line, label))
                n += 1
                if n >= MAX_PER_FILE:
                    break
    return out


def _text_hits(ctx: Context, tid: str, pattern: re.Pattern, kinds=("markup", "script", "css")) -> list[Finding]:
    out = []
    for doc in ctx.docs:
        if doc.kind not in kinds:
            continue
        n = 0
        for m in pattern.finditer(doc.text):
            out.append(Finding(tid, doc.rel, doc.line(m.start()), m.group(0).strip()[:60]))
            n += 1
            if n >= MAX_PER_FILE:
                break
    return out


def _copy_hits(ctx: Context, tid: str, pattern: re.Pattern) -> list[Finding]:
    out = []
    for doc in ctx.docs:
        n = 0
        seen: set[int] = set()
        for line, text in doc.texts:
            m = pattern.search(text)
            if m and line not in seen:
                seen.add(line)
                out.append(Finding(tid, doc.rel, line, f'"{m.group(0)}" in "{text[:70]}"'))
                n += 1
                if n >= MAX_PER_FILE:
                    break
    return out


def _decl_hits(ctx: Context, tid: str, test: Callable[[str, str], bool], label: Callable[[str, str], str]) -> list[Finding]:
    out = []
    for doc in ctx.docs:
        n = 0
        for line, prop, val in doc.decls:
            if test(prop, val):
                out.append(Finding(tid, doc.rel, line, label(prop, val)))
                n += 1
                if n >= MAX_PER_FILE:
                    break
    return out


def _any(bases: Iterable[str], pattern: str) -> bool:
    rx = re.compile(pattern)
    return any(rx.search(b) for b in bases)


def _first_location(p: Profile, name: str) -> tuple[str, int]:
    locs = p.fonts_used.get(name) or [("(project)", 0)]
    return locs[0]


# ---------- typography ----------

GENERIC_FONTS = {"inter", "inter tight", "inter display", "roboto", "roboto flex", "arial", "helvetica",
                 "helvetica neue", "open sans", "lato", "noto sans"}
TREND_FONTS = {
    "space grotesk", "geist", "geist sans", "geist mono", "instrument serif", "fraunces", "poppins",
    "montserrat", "dm sans", "dm serif display", "plus jakarta sans", "outfit", "manrope",
    "playfair display", "satoshi", "cabinet grotesk", "clash display", "general sans", "sora",
}


@tell("type.generic-font", "typography", 8, "Default sans as the only voice",
      "Inter, Roboto, Arial and friends are what a model picks when nobody chose a typeface.",
      "Pick a typeface for this product's tone, load it and pair it with a second face for headings or numbers.")
def _generic_font(ctx: Context) -> list[Finding]:
    p = ctx.profile
    out = []
    for name in p.primary_fonts:
        if name in GENERIC_FONTS:
            rel, line = _first_location(p, name)
            out.append(Finding("type.generic-font", rel, line, f"primary font is {name.title()}"))
    has_markup = any(d.kind == "markup" for d in ctx.docs)
    loaded_generic = sorted(f for f in p.fonts_loaded if f in GENERIC_FONTS)
    if not p.primary_fonts and loaded_generic:
        out.append(Finding("type.generic-font", "(project)", 0, f"loads {', '.join(f.title() for f in loaded_generic)}"))
    elif not p.primary_fonts and has_markup and not p.fonts_loaded:
        out.append(Finding("type.generic-font", "(project)", 0, "no typeface chosen anywhere; browser or Tailwind default stack"))
    return out


@tell("type.trend-font", "typography", 4, "The new 'tasteful' AI font",
      "Space Grotesk, Geist, Instrument Serif, Fraunces and similar became the second wave of model defaults.",
      "Keep it only if you chose it on purpose. Otherwise pick a face nobody else in your niche uses.")
def _trend_font(ctx: Context) -> list[Finding]:
    p = ctx.profile
    out = []
    for name in p.fonts_used:
        if name in TREND_FONTS:
            rel, line = _first_location(p, name)
            out.append(Finding("type.trend-font", rel, line, name.title()))
    return out


@tell("type.font-not-loaded", "typography", 5, "Font named but never loaded",
      "A font-family the browser cannot find falls back silently, so the page shows a default face.",
      "Load the font with a <link>, @font-face, next/font or @fontsource or remove it from the stack.")
def _font_not_loaded(ctx: Context) -> list[Finding]:
    p = ctx.profile
    out = []
    local_ok = {"georgia", "times new roman", "courier new", "verdana", "tahoma", "trebuchet ms",
                "menlo", "monaco", "consolas", "sf mono", "sf pro", "sf pro text", "sf pro display",
                "helvetica", "helvetica neue", "arial"}
    for name in p.primary_fonts:
        if name in p.fonts_loaded or name in local_ok or name.startswith("var("):
            continue
        rel, line = _first_location(p, name)
        out.append(Finding("type.font-not-loaded", rel, line, name.title()))
    return out


@tell("type.scale-sprawl", "typography", 4, "No type scale",
      "More than seven font sizes means sizes were picked one by one, not from a scale.",
      "Define a scale with a fixed ratio (for example 1.2 or 1.25) and use only those sizes.")
def _scale_sprawl(ctx: Context) -> list[Finding]:
    sizes = ctx.profile.font_sizes
    if len(sizes) > 7:
        return [Finding("type.scale-sprawl", "(project)", 0, f"{len(sizes)} sizes: {', '.join(list(sizes)[:10])}")]
    return []


@tell("type.gradient-text", "typography", 6, "Gradient-filled headline text",
      "Clipped gradient text on a headline is one of the most recognised model flourishes.",
      "Use solid ink. Create emphasis with weight, size, a second typeface or one accent word.")
def _gradient_text(ctx: Context) -> list[Finding]:
    out = _element_hits(ctx, "type.gradient-text",
                        lambda b: "bg-clip-text" in b and "text-transparent" in b,
                        "bg-clip-text + text-transparent")
    out += _decl_hits(ctx, "type.gradient-text",
                      lambda prop, val: prop in ("-webkit-background-clip", "background-clip") and val.startswith("text"),
                      lambda prop, val: f"{prop}: {val}")
    return out


@tell("type.arbitrary-size", "typography", 3, "One-off font sizes",
      "Sizes like text-[22px] bypass the type scale.",
      "Map each one to the nearest step in your type scale.")
def _arbitrary_type(ctx: Context) -> list[Finding]:
    return _token_hits(ctx, "type.arbitrary-size", re.compile(r"^(?:text|leading|tracking)-\[\d"))


# ---------- color ----------
# Colors are judged by hue, in any format, after resolving var() and Tailwind aliases.

AI_PURPLES = {
    "#6366f1", "#4f46e5", "#4338ca", "#8b5cf6", "#7c3aed", "#6d28d9", "#a855f7", "#9333ea",
    "#7e22ce", "#c084fc", "#a78bfa", "#818cf8", "#667eea", "#764ba2", "#d946ef", "#ec4899",
}  # kept for reference and for the generator; detection uses is_purple()
CREAMS = {"#faf7f2", "#f5f0e8", "#fdf8f3", "#f7f3ee", "#fbf8f3", "#f8f5f0", "#faf9f6", "#f5f1ea", "#fdfbf7", "#f4efe6"}
TERRACOTTAS = {"#c2410c", "#e07a5f", "#d97757", "#b45309", "#c65d3b", "#cc5833", "#d4643b", "#bc5a3c", "#9a3412", "#ea580c"}
PURPLE_FAM = "purple|violet|indigo|fuchsia"
PURPLE_FAMILIES = {"purple", "violet", "indigo", "fuchsia"}
GRADIENT_FAMILIES = PURPLE_FAMILIES | {"blue", "pink", "cyan", "sky", "rose"}
COLOR_PROPS = ("color", "background", "background-color", "border-color", "fill", "stroke", "outline-color",
               "border", "border-top-color", "border-bottom-color", "text-decoration-color", "caret-color")
BRAND_VARS = re.compile(r"^--(?:color-)?(?:primary|accent|brand|main|theme)(?:-\d+)?$")
GRADIENT = re.compile(r"(?:repeating-)?(?:linear|radial|conic)-gradient\((?:[^()]|\([^()]*\))*\)", re.I)


def _token_purple(p: Profile, b: str) -> tuple[bool, bool]:
    # (is a gradient-family stop, is purple) for one Tailwind color class.
    family, hexes = p.token_colors(b)
    if family:
        return family in GRADIENT_FAMILIES, family in PURPLE_FAMILIES
    return any(is_ai_gradient_stop(h) for h in hexes), any(is_purple(h) for h in hexes)


def _gradient_is_ai(value: str) -> bool:
    stops = colors_in(value)
    return any(is_purple(c) for c in stops) and sum(1 for c in stops if is_ai_gradient_stop(c)) >= 2 or (
        len(stops) == 1 and is_purple(stops[0]))


@tell("color.purple-gradient", "color", 10, "Purple to blue or pink gradient",
      "The purple gradient is the single best-known sign of an AI-made page.",
      "Drop the gradient. Use one flat brand color chosen for the product and a tinted neutral background.")
def _purple_gradient(ctx: Context) -> list[Finding]:
    p = ctx.profile
    out = []
    for doc in ctx.docs:
        n = 0
        for line, toks in doc.elements:
            stops = [base(t) for t in toks if re.match(r"^(from|via|to)-", base(t))]
            if len(stops) < 2:
                continue
            judged = [_token_purple(p, s) for s in stops]
            if any(purple for _g, purple in judged) and sum(1 for g, _p in judged if g) >= 2:
                out.append(Finding("color.purple-gradient", doc.rel, line, "Tailwind gradient through purple"))
                n += 1
                if n >= MAX_PER_FILE:
                    break
        for line, tok in doc.tokens:
            b = base(tok)
            if b.startswith("bg-[") and "gradient" in b and _gradient_is_ai(b.replace("_", " ")):
                out.append(Finding("color.purple-gradient", doc.rel, line, b[:50]))
    def css_test(prop: str, val: str) -> bool:
        resolved = p.resolve(val)
        return any(_gradient_is_ai(g) for g in GRADIENT.findall(resolved))
    out += _decl_hits(ctx, "color.purple-gradient", css_test, lambda prop, val: f"{prop}: {val[:50]}")
    for rel, line, raw in p.named_gradients:
        if _gradient_is_ai(raw):
            out.append(Finding("color.purple-gradient", rel, line, f"named gradient {raw[:40]}"))
    return out


@tell("color.indigo-accent", "color", 6, "Indigo or violet primary color",
      "Indigo-600 is Tailwind's demo color and the default accent of countless generated apps.",
      "Choose an accent hue from the brand or the product's world. Avoid the 230 to 300 degree hue range unless it is the brand.")
def _indigo_accent(ctx: Context) -> list[Finding]:
    p = ctx.profile
    out = []
    for doc in ctx.docs:
        n = 0
        for line, tok in doc.tokens:
            b = base(tok)
            m = re.match(r"^(bg|text|border|ring|outline|fill|stroke|accent|decoration)-", b)
            if not m:
                continue
            family, hexes = p.token_colors(b)
            shade = re.search(r"-(\d{3})(?:/\d+)?$", b)
            purple = (family in PURPLE_FAMILIES and (shade is None or 400 <= int(shade.group(1)) <= 800)) or any(
                is_purple(h) for h in hexes)
            if not purple and b.startswith(("bg-[", "text-[", "border-[", "ring-[")):
                purple = any(is_purple(h) for h in colors_in(b[b.index("[") + 1:-1].replace("_", " ")))
            if purple:
                out.append(Finding("color.indigo-accent", doc.rel, line, tok))
                n += 1
                if n >= MAX_PER_FILE:
                    break
    def css_test(prop: str, val: str) -> bool:
        if not (prop in COLOR_PROPS or BRAND_VARS.match(prop)):
            return False
        resolved = p.resolve(val)
        if GRADIENT.search(resolved):
            return False
        return any(is_purple(c) for c in colors_in(resolved))
    css_hits = _decl_hits(ctx, "color.indigo-accent", css_test, lambda prop, val: f"{prop}: {val[:40]}")
    brand = [f for f in css_hits if f.detail.startswith("--")]
    # One stray purple declaration (a debug helper, a chart series) is not an accent.
    fills = [f for f in css_hits if f.detail.startswith(("background", "fill"))]
    if brand or fills or len(css_hits) + len(out) >= 2:
        out += css_hits
    return out


@tell("color.tasteful-default", "color", 5, "Cream and terracotta palette",
      "After the purple backlash, models moved to cream backgrounds with a terracotta accent. It is now a default too.",
      "Derive the palette from the product. Try a cool or saturated paper tint or an unexpected accent hue.")
def _tasteful(ctx: Context) -> list[Finding]:
    # Cream must be a page-level background and terracotta a main accent, not a badge.
    p = ctx.profile
    cream_bg = terra_uses = 0
    chroma: dict[str, int] = {}
    for doc in ctx.docs:
        for _line, prop, val in doc.decls:
            cols = colors_in(p.resolve(val))
            is_bg = prop in ("background", "background-color") or any(k in prop for k in ("bg", "background", "paper", "surface", "canvas"))
            if is_bg and any(is_cream(c) for c in cols):
                cream_bg += 3
            if any(is_terracotta(c) for c in cols):
                # A terracotta accent or brand token is the palette's main color, so it weighs more.
                terra_uses += 3 if any(k in prop for k in ("accent", "primary", "brand")) else 1
        for _line, tok in doc.tokens:
            b = base(tok)
            family, hexes = p.token_colors(b)
            if b.startswith("bg-") and (re.match(r"^bg-(stone|amber|orange)-50(/\d+)?$", b) or any(is_cream(h) for h in hexes)
                                       or (b.startswith("bg-[") and any(is_cream(h) for h in colors_in(b[4:-1])))):
                cream_bg += 1
            if family and family not in NEUTRALS:
                chroma[family] = chroma.get(family, 0) + 1
                if family in ("orange", "amber") and re.search(r"-(600|700|800)", b):
                    terra_uses += 1
            elif any(is_terracotta(h) for h in hexes):
                terra_uses += 1
                chroma["orange"] = chroma.get("orange", 0) + 1
    total = sum(chroma.values()) or 1
    warm_share = (chroma.get("orange", 0) + chroma.get("amber", 0)) / total
    if cream_bg >= 3 and terra_uses >= 3 and (not chroma or warm_share >= 0.3 or terra_uses >= 6):
        return [Finding("color.tasteful-default", "(project)", 0, "cream background with terracotta accent")]
    return []


@tell("color.palette-sprawl", "color", 4, "Too many hues",
      "Using many unrelated color families means no palette was designed.",
      "Pick one accent, one optional secondary, tinted neutrals and status colors. Remove the rest.")
def _palette_sprawl(ctx: Context) -> list[Finding]:
    fams = ctx.profile.chromatic_families()
    if len(fams) > 5:
        return [Finding("color.palette-sprawl", "(project)", 0, f"{len(fams)} hue families: {', '.join(fams)}")]
    return []


@tell("color.one-off", "color", 3, "Hard-coded one-off colors",
      "Colors like bg-[#1a1a1a] sit outside any token system and drift over time.",
      "Move each color into a named token (CSS variable or Tailwind theme) and use the token.")
def _one_off_color(ctx: Context) -> list[Finding]:
    return _token_hits(ctx, "color.one-off", re.compile(r"^(?:bg|text|border|from|to|via|fill|stroke|ring)-\[(?:#|rgb|hsl|oklch)"))


GLOW = re.compile(
    r"(?<![\w.-])-?\d{1,2}(?:px)?[ _]+-?\d{1,2}(?:px)?[ _]+(\d{2,})px(?:[ _]+-?\d+px)?[ _]+"
    r"(rgba?\([^)]*\)|hsla?\([^)]*\)|oklch\([^)]*\)|#[0-9a-fA-F]{3,8}|var\(--[\w-]+\))"
)


def _is_colored(color: str, p: Profile | None = None) -> bool:
    # True for a chromatic color, False for black, white and grays.
    value = p.resolve(color) if p is not None else color
    hexes = colors_in(value)
    return any(not is_neutral(h) for h in hexes)


@tell("color.neon-glow", "color", 5, "Colored glow shadows",
      "Colored glows around cards and buttons are a stock 'futuristic' effect.",
      "Remove the glow. If depth is needed, use a neutral shadow on overlays only.")
def _neon_glow(ctx: Context) -> list[Finding]:
    p = ctx.profile
    out = _token_hits(ctx, "color.neon-glow",
                      re.compile(rf"^(?:shadow|drop-shadow)-({PURPLE_FAM}|blue|cyan|pink|sky|emerald|teal)-\d|^animate-(?:glow|neon|pulse-glow)"))
    for doc in ctx.docs:
        if doc.kind not in ("markup", "script", "css"):
            continue
        n = 0
        for m in GLOW.finditer(doc.text):
            if int(m.group(1)) >= 16 and _is_colored(m.group(2), p):
                out.append(Finding("color.neon-glow", doc.rel, doc.line(m.start()), f"glow {m.group(0)[:40]}"))
                n += 1
                if n >= MAX_PER_FILE:
                    break
    return out


# ---------- decoration ----------

@tell("deco.rounded-shadow-everywhere", "decoration", 6, "Big radius and big shadow on everything",
      "rounded-2xl with shadow-lg on every card makes the page look like a template.",
      "Use borders and spacing for structure. Keep shadows for things that float, like menus and dialogs.")
def _rounded_shadow(ctx: Context) -> list[Finding]:
    hits = _element_hits(ctx, "deco.rounded-shadow-everywhere",
                         lambda b: _any(b, r"^rounded(?:-[a-z]{1,2})?-(xl|2xl|3xl)$") and _any(b, r"^shadow-(md|lg|xl|2xl)$"),
                         "rounded-xl+ with shadow-md+")
    total = sum(1 for d in ctx.docs for _l, toks in d.elements
                if _any({base(t) for t in toks}, r"^rounded(?:-[a-z]{1,2})?-(xl|2xl|3xl)$") and _any({base(t) for t in toks}, r"^shadow-(md|lg|xl|2xl)$"))
    return hits if total >= 3 else []


@tell("deco.glassmorphism", "decoration", 5, "Frosted glass panels",
      "Backdrop blur over translucent white is a reflexive model choice and often hurts contrast.",
      "Use a solid surface color. Keep blur for overlays that sit above real content, if at all.")
def _glass(ctx: Context) -> list[Finding]:
    out = _element_hits(ctx, "deco.glassmorphism",
                        lambda b: _any(b, r"^backdrop-blur") and _any(b, r"^bg-(white|black|slate-\d+|gray-\d+|zinc-\d+)/\d+$"),
                        "backdrop-blur on translucent background")
    out += _decl_hits(ctx, "deco.glassmorphism", lambda prop, val: prop in ("backdrop-filter", "-webkit-backdrop-filter") and "blur" in val,
                      lambda prop, val: f"{prop}: {val}")
    return out


@tell("deco.icon-tile", "decoration", 5, "Icon in a pastel rounded square",
      "A small icon inside a tinted rounded tile above each feature is the most common generated card.",
      "Drop the tile. Use a plain icon at text size, a number, a real screenshot crop or no icon.")
def _icon_tile(ctx: Context) -> list[Finding]:
    def test(b: set[str]) -> bool:
        return (_any(b, r"^rounded-(md|lg|xl|2xl|full)$")
                and _any(b, r"^bg-[a-z]+-(50|100)$|^bg-[a-z]+-\d{3}/(5|10|15|20)$")
                and _any(b, r"^(w|h|size)-(8|9|10|11|12|14)$")
                and _any(b, r"^items-center$|^place-items-center$"))
    hits = _element_hits(ctx, "deco.icon-tile", test, "icon tile")
    return hits if len(hits) >= 2 else []


EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿⭐⬆↔-↪]")


@tell("deco.emoji-icons", "decoration", 6, "Emoji used as icons",
      "Emoji in headings, buttons and feature lists are a quick filler models reach for.",
      "Use one consistent icon set or none. Keep emoji for user content only.")
def _emoji(ctx: Context) -> list[Finding]:
    out = []
    for doc in ctx.docs:
        n = 0
        for line, text in doc.texts:
            m = EMOJI.search(text)
            if m:
                out.append(Finding("deco.emoji-icons", doc.rel, line, f"{m.group(0)} in \"{text[:50]}\""))
                n += 1
                if n >= MAX_PER_FILE:
                    break
    return out


@tell("deco.sparkle", "decoration", 4, "Sparkle motif",
      "The sparkle icon has become shorthand for 'AI feature' and signals a generated design.",
      "Name the feature plainly and show what it does instead of decorating it.")
def _sparkle(ctx: Context) -> list[Finding]:
    return _text_hits(ctx, "deco.sparkle", re.compile(r"\bSparkles?(?:Icon)?\b|✨|\bsparkles\b"), kinds=("markup", "script"))


@tell("deco.blur-blob", "decoration", 5, "Blurred color blobs in the background",
      "Huge blurred circles behind the hero add color without meaning.",
      "Remove them. Let real content or one deliberate image carry the visual weight.")
def _blob(ctx: Context) -> list[Finding]:
    out = _element_hits(ctx, "deco.blur-blob",
                        lambda b: _any(b, r"^blur-(2xl|3xl|\[\d{2,}px\])$") and _any(b, r"^rounded-full$") and _any(b, r"^bg-"),
                        "blurred rounded-full background shape")
    out += _decl_hits(ctx, "deco.blur-blob",
                      lambda prop, val: prop == "filter" and bool(re.search(r"blur\(\s*([4-9]\d|\d{3})px", val)),
                      lambda prop, val: f"{prop}: {val}")
    return out


@tell("deco.hover-scale", "decoration", 3, "Everything grows on hover",
      "hover:scale-105 on many cards is a stock interaction that adds motion without feedback value.",
      "Give hover a purposeful change: underline, border color or background shift on the clickable part only.")
def _hover_scale(ctx: Context) -> list[Finding]:
    hits = _token_hits(ctx, "deco.hover-scale", re.compile(r"^scale-1\d\d$"), None)
    hits = [h for h in hits if "hover" in h.detail or "group-hover" in h.detail]
    return hits if len(hits) >= 3 else []


STOCK_EFFECTS = (
    "BackgroundBeams", "Spotlight", "Meteors", "SparklesCore", "BentoGrid", "ShimmerButton",
    "AnimatedGradientText", "BorderBeam", "MagicCard", "WobbleCard", "TextGenerateEffect",
    "LampContainer", "AuroraBackground", "RetroGrid", "DotPattern", "GridPattern", "Particles",
    "AnimatedBeam", "OrbitingCircles", "HeroHighlight", "TypewriterEffect", "InfiniteMovingCards",
)


@tell("deco.stock-effects", "decoration", 5, "Stock effect components",
      "Copy-paste effects from Aceternity UI or Magic UI are recognised across thousands of sites.",
      "Remove them or rebuild one effect so it is specific to your product.")
def _stock(ctx: Context) -> list[Finding]:
    rx = re.compile(r"<(?:" + "|".join(STOCK_EFFECTS) + r")\b|from ['\"][^'\"]*(?:magicui|aceternity)[^'\"]*['\"]")
    return _text_hits(ctx, "deco.stock-effects", rx, kinds=("markup", "script"))


@tell("deco.grid-background", "decoration", 3, "Grid or dot pattern background",
      "A faint grid or dot field behind the hero is a common filler texture.",
      "Use a plain tinted surface or a texture taken from the product's world.")
def _grid_bg(ctx: Context) -> list[Finding]:
    out = _token_hits(ctx, "deco.grid-background",
                      re.compile(r"^bg-(grid|dot)(-|$)|^bg-\[(?:linear-gradient\(to_right|radial-gradient\(.*?1px)"))
    out += _decl_hits(ctx, "deco.grid-background",
                      lambda prop, val: prop == "background-image" and "radial-gradient" in val and "1px" in val,
                      lambda prop, val: f"{prop}: {val[:40]}")
    return out


@tell("deco.pill-above-headline", "decoration", 4, "Badge pill above the headline",
      "A small rounded 'New' or 'Introducing' pill sitting on top of the H1 is a template signature.",
      "Remove it. If news matters, put it in the navigation or as a plain line of text.")
def _pill(ctx: Context) -> list[Finding]:
    out = []
    pill_cls = re.compile(r"rounded-full[^\"'`]*?(?:px-[23]|py-1)|(?:px-[23]|py-1)[^\"'`]*?rounded-full")
    for doc in ctx.docs:
        if doc.kind != "markup" and doc.kind != "script":
            continue
        for m in re.finditer(r"<h1\b", doc.text, re.I):
            before = doc.text[max(0, m.start() - 500):m.start()]
            if pill_cls.search(before) and re.search(r"text-(xs|sm)", before):
                out.append(Finding("deco.pill-above-headline", doc.rel, doc.line(m.start()), "pill badge before <h1>"))
    return out


# ---------- layout ----------

@tell("layout.three-cards", "layout", 4, "Three equal feature cards",
      "A row of three identical cards is the default way models fill a features section.",
      "Vary the format: a list with real detail, a comparison, a screenshot with callouts or two unequal columns.")
def _three(ctx: Context) -> list[Finding]:
    out = _token_hits(ctx, "layout.three-cards", re.compile(r"^grid-cols-3$"))
    out += _decl_hits(ctx, "layout.three-cards",
                      lambda prop, val: prop == "grid-template-columns" and bool(re.match(r"repeat\(\s*3\s*,\s*(1fr|minmax)", val)),
                      lambda prop, val: f"{prop}: {val}")
    return out


@tell("layout.centered-hero", "layout", 5, "Centered hero with two buttons",
      "Big centered headline, a subline, then a primary and a secondary button. Every generator makes this.",
      "Lead with the product itself: a working demo, real data or a screenshot, with a left-aligned headline.")
def _centered_hero(ctx: Context) -> list[Finding]:
    out = []
    cta = re.compile(r"<(?:button|Button|Link|a|router-link)\b|routerLink|href=", re.I)
    for doc in ctx.docs:
        if doc.kind not in ("markup", "script"):
            continue
        for m in re.finditer(r"<h1\b", doc.text, re.I):
            before = doc.text[max(0, m.start() - 700):m.start()]
            after = doc.text[m.start():m.start() + 1500]
            head = doc.text[m.start():m.start() + 300]
            big = re.search(r"text-([4-9]xl|\[\d{2,}px\])|clamp\(|display|hero", head + before[-300:], re.I)
            if big and re.search(r"text-center|text-align:\s*center", before) and len(cta.findall(after)) >= 2:
                out.append(Finding("layout.centered-hero", doc.rel, doc.line(m.start()), "centered <h1> followed by two calls to action"))
    return out


@tell("layout.bento", "layout", 3, "Bento grid",
      "Mixed-size bento tiles became the default 'modern' feature layout.",
      "Use it only if the content really has different sizes of importance. Otherwise use a simple list.")
def _bento(ctx: Context) -> list[Finding]:
    hits = _element_hits(ctx, "layout.bento", lambda b: _any(b, r"^(?:col|row)-span-2$"), "span-2 tile")
    words = _text_hits(ctx, "layout.bento", re.compile(r"\bbento\b", re.I), kinds=("markup", "script", "css"))
    return (hits if len(hits) >= 2 else []) + words


@tell("layout.center-everything", "layout", 3, "Everything centered",
      "Centering every block removes the reading line and makes long pages feel like slides.",
      "Left-align body text and most sections. Center only short, isolated moments.")
def _center_all(ctx: Context) -> list[Finding]:
    out = []
    for doc in ctx.docs:
        n = sum(1 for _l, t in doc.tokens if base(t) == "text-center")
        n += sum(1 for _l, p, v in doc.decls if p == "text-align" and v == "center")
        if n >= 6:
            out.append(Finding("layout.center-everything", doc.rel, 0, f"{n} centered blocks"))
    return out


@tell("layout.same-section-padding", "layout", 2, "Every section has the same padding",
      "Identical py-24 on every section gives the page no rhythm or hierarchy.",
      "Vary section spacing by importance. Tighter for related content, larger before a new topic.")
def _same_padding(ctx: Context) -> list[Finding]:
    out = []
    for doc in ctx.docs:
        counts: dict[str, int] = {}
        for _l, t in doc.tokens:
            b = base(t)
            if re.match(r"^py-(16|20|24|28|32)$", b):
                counts[b] = counts.get(b, 0) + 1
        for value, n in counts.items():
            if n >= 4:
                out.append(Finding("layout.same-section-padding", doc.rel, 0, f"{value} used {n} times"))
    return out


# ---------- spacing and consistency ----------

@tell("space.arbitrary", "spacing", 3, "One-off spacing values",
      "Values like p-[13px] fall off the spacing scale.",
      "Snap to your scale (4 or 8 px steps).")
def _arb_space(ctx: Context) -> list[Finding]:
    return _token_hits(ctx, "space.arbitrary", re.compile(r"^-?(?:p|px|py|pt|pr|pb|pl|ps|pe|m|mx|my|mt|mr|mb|ml|gap|gap-x|gap-y|space-x|space-y)-\[\d"))


@tell("space.off-grid", "spacing", 3, "CSS spacing off the grid",
      "Padding, margin and gap values that fit no common base unit suggest guessed spacing.",
      "Pick a base unit (4px or 8px is common) and use only multiples of it.")
def _off_grid(ctx: Context) -> list[Finding]:
    values: list[tuple[str, int, str, int]] = []
    for doc in ctx.docs:
        for line, prop, val in doc.decls:
            if prop.split("-")[0] in ("padding", "margin", "gap") or prop in ("row-gap", "column-gap"):
                for num in re.findall(r"(?<![\d.])(\d+)px", val):
                    if int(num) > 4:  # 1 to 4px tweaks are usually optical or border offsets
                        values.append((doc.rel, line, f"{prop}: {val}", int(num)))
    if len(values) < 5:
        return []
    grid = max((4, 5, 6, 8), key=lambda g: sum(1 for v in values if v[3] % g == 0))
    off = [v for v in values if v[3] % grid]
    if len(off) / len(values) <= 0.25:
        return []
    out = []
    per_file: dict[str, int] = {}
    for rel, line, detail, _n in off:
        if per_file.get(rel, 0) < MAX_PER_FILE:
            per_file[rel] = per_file.get(rel, 0) + 1
            out.append(Finding("space.off-grid", rel, line, f"{detail} (project grid looks like {grid}px)"))
    return out


@tell("space.radius-sprawl", "spacing", 3, "Too many corner radii",
      "More than four different radii means corners were styled one at a time.",
      "Pick two radii: one for controls, one for containers.")
def _radius_sprawl(ctx: Context) -> list[Finding]:
    radii: list[str] = []
    for raw in ctx.profile.radii:
        # Resolve var() and split shorthands, so var(--r-card) and "0 0 6px 6px" count as the radii they really are.
        for part in ctx.profile.resolve(raw).split():
            m = re.fullmatch(r"(-?[\d.]+)(px|rem|em)?", part)
            if m and (float(m.group(1)) == 0 or float(m.group(1)) * (16 if m.group(2) in ("rem", "em") else 1) >= 999):
                continue
            if part in ("none", "full", "0", "50%", "9999px", "/") or part in radii:
                continue
            radii.append(part)
    if len(radii) > 4:
        return [Finding("space.radius-sprawl", "(project)", 0, f"{len(radii)} radii: {', '.join(radii[:8])}")]
    return []


@tell("space.shadow-sprawl", "spacing", 2, "Too many shadow styles",
      "Several different shadows means elevation has no system.",
      "Define at most two elevation levels and use them only for floating layers.")
def _shadow_sprawl(ctx: Context) -> list[Finding]:
    shadows = [s for s in ctx.profile.shadows if s != "none"]
    if len(shadows) > 3:
        return [Finding("space.shadow-sprawl", "(project)", 0, f"{len(shadows)} shadow styles")]
    return []


# ---------- copy ----------

HYPE = re.compile(
    r"\b(unlock(?:s|ing)?|supercharge[sd]?|revolutioni[sz]e[sd]?|seamless(?:ly)?|elevate[sd]?|"
    r"next[- ]gen(?:eration)?|game[- ]chang(?:er|ing)|effortless(?:ly)?|cutting[- ]edge|"
    r"harness the power|unleash(?:es)?|empower(?:s|ing)?|transform your|streamline[sd]?|"
    r"take (?:it|your \w+) to the next level|lightning[- ]fast|blazing(?:ly)? fast|world[- ]class|"
    r"state[- ]of[- ]the[- ]art|all[- ]in[- ]one|reimagine[sd]?)\b",
    re.I,
)
PLACEHOLDER = re.compile(r"\b(lorem ipsum|dolor sit amet|john doe|jane doe|acme(?: inc| corp)?|your company|"
                         r"company name|example@|user@example\.com|\(555\)|123 main st)\b", re.I)
VANITY = re.compile(r"\b\d{1,3}(?:,\d{3})*(?:\.\d)?[kKmM]?\+\s*(?:happy\s+|active\s+)?(?:users|customers|developers|teams|companies|businesses)\b|\b99\.9+%|\b10x\b", re.I)
GENERIC_HEAD = re.compile(r"\b(welcome to|the future of|built for the modern|everything you need|"
                          r"your all-in-one|made simple|like never before|at your fingertips|"
                          r"bienvenidos? a|bienvenue (?:à|sur|chez)|willkommen (?:bei|in|auf)|bem-vindos? (?:a|ao)|"
                          r"karibu (?:kwenye|katika))\b", re.I)


@tell("copy.hype", "copy", 5, "Hype words",
      "Unlock, seamless, supercharge, elevate. These words carry no information and mark generated copy.",
      "Say what the product does, for whom, with a number or a concrete example.")
def _hype(ctx: Context) -> list[Finding]:
    return _copy_hits(ctx, "copy.hype", HYPE)


@tell("copy.placeholder", "copy", 4, "Placeholder content",
      "Lorem ipsum, John Doe and Acme Inc show that nobody wrote real content.",
      "Write real copy and use realistic names and data from the product's market.")
def _placeholder(ctx: Context) -> list[Finding]:
    return _copy_hits(ctx, "copy.placeholder", PLACEHOLDER)


@tell("copy.vanity-stats", "copy", 3, "Invented vanity numbers",
      "'10,000+ happy users' and '99.9% uptime' are filled in by models when no real number exists.",
      "Use real figures with a source or remove the stat.")
def _vanity(ctx: Context) -> list[Finding]:
    return _copy_hits(ctx, "copy.vanity-stats", VANITY)


@tell("copy.generic-headline", "copy", 3, "Generic headline",
      "'Welcome to', 'The future of' and 'Everything you need' could head any product page.",
      "Write a headline only this product could use.")
def _generic_head(ctx: Context) -> list[Finding]:
    return _copy_hits(ctx, "copy.generic-headline", GENERIC_HEAD)


# ---------- accessibility and motion ----------

@tell("a11y.focus-removed", "accessibility", 5, "Focus outline removed",
      "outline-none without a replacement hides keyboard focus. Designers always design the focus state.",
      "Add a visible focus style, for example focus-visible:ring-2 with an accent color and offset.")
def _focus(ctx: Context) -> list[Finding]:
    def no_replacement(raw: set[str], b: set[str]) -> bool:
        if any(x.startswith(("data-[state", "data-[side")) for x in raw):
            return False  # Radix overlay containers (popover, hover card) are not tab stops
        replaced = any(re.search(r"(^|:)(focus|focus-visible|focus-within|group-focus|peer-focus|aria-selected|data-\[(selected|highlighted|focus))", x) and not x.endswith("outline-none") for x in raw)
        return _any(b, r"^outline-none$") and not replaced and not _any(b, r"^ring-\d|^outline-(\d|solid|dashed|dotted)")
    out = []
    for doc in ctx.docs:
        n = 0
        for line, toks in doc.elements:
            if no_replacement(set(toks), {base(t) for t in toks}):
                out.append(Finding("a11y.focus-removed", doc.rel, line, "outline-none with no focus replacement"))
                n += 1
                if n >= MAX_PER_FILE:
                    break
    focus_style = re.compile(r"focus[^{;]*\{[^}]*(box-shadow|background|border|text-decoration|outline\s*:(?!\s*(?:none|0)))|@include\s+[\w-]*focus", re.S)
    for doc in ctx.docs:
        if any(p == "outline" and v.startswith(("none", "0")) for _l, p, v in doc.decls) and "focus-visible" not in doc.text and not focus_style.search(doc.text):
            line = next(l for l, p, v in doc.decls if p == "outline" and v.startswith(("none", "0")))
            out.append(Finding("a11y.focus-removed", doc.rel, line, "outline: none"))
    return out


@tell("a11y.faint-text", "accessibility", 3, "Faint gray body text",
      "Light gray text on white (gray-400 and lighter) usually fails WCAG contrast.",
      "Use at least gray-600 on white for body text and check contrast at 4.5:1.")
def _faint(ctx: Context) -> list[Finding]:
    hits = _element_hits(ctx, "a11y.faint-text",
                         lambda b: _any(b, rf"^text-({'|'.join(NEUTRALS)})-(300|400)$") and not any(x.startswith("dark:") for x in b),
                         "text-*-300/400")
    return hits if len(hits) >= 2 else []


@tell("a11y.img-no-alt", "accessibility", 3, "Images without alt text",
      "Missing alt text is a quality gap that generated markup often leaves.",
      "Add alt text that describes the image or alt=\"\" for decoration.")
def _img_alt(ctx: Context) -> list[Finding]:
    out = []
    for doc in ctx.docs:
        if doc.kind not in ("markup", "script"):
            continue
        n = 0
        for m in re.finditer(r"<(?:img|Image|NuxtImg)\b[^>]*>", doc.text):
            if not re.search(r"\b(?:alt|:alt|\[alt\])\s*=", m.group(0)):
                out.append(Finding("a11y.img-no-alt", doc.rel, doc.line(m.start()), m.group(0)[:50]))
                n += 1
                if n >= MAX_PER_FILE:
                    break
    return out


@tell("motion.no-reduced-motion", "motion", 3, "Animation without a reduced-motion option",
      "Animations that ignore prefers-reduced-motion can make some users ill.",
      "Wrap animations in @media (prefers-reduced-motion: no-preference) or use motion-safe: in Tailwind.")
def _reduced(ctx: Context) -> list[Finding]:
    p = ctx.profile
    if p.has_animation and not p.has_reduced_motion:
        return [Finding("motion.no-reduced-motion", "(project)", 0, "animations found, no reduced-motion handling")]
    return []


@tell("motion.transition-all", "motion", 2, "transition-all everywhere",
      "Animating every property is a lazy default. It can also animate layout and hurt performance.",
      "Transition only the properties that change, such as color, background-color or transform.")
def _transition_all(ctx: Context) -> list[Finding]:
    hits = _token_hits(ctx, "motion.transition-all", re.compile(r"^transition-all$"))
    hits += _decl_hits(ctx, "motion.transition-all", lambda p, v: p == "transition" and v.startswith("all"), lambda p, v: f"{p}: {v}")
    return hits if len(hits) >= 3 else []


# ---------- content and craft ----------

# Free stock photo hosts. A hotlinked photo from these is almost never the business's own.
STOCK_HOSTS = re.compile(
    r"(?:images|plus|source)\.unsplash\.com|unsplash\.com/photos|images\.pexels\.com|cdn\.pixabay\.com|pixabay\.com/get"
    r"|picsum\.photos|loremflickr\.com|randomuser\.me|i\.pravatar\.cc|placehold\.co|via\.placeholder\.com"
    r"|dummyimage\.com|placekitten\.com|images\.generated\.photos|thispersondoesnotexist\.com", re.I)
# Words that show a photo is knowingly a stand-in for the real one.
MARKED_PLACEHOLDER = re.compile(r"placeholder|replace|stand-in|sample photo|\[photo|data-slot", re.I)
STOCK_USE = re.compile(r"<(?:img|Image|NuxtImg|source)\b[^>]*>|url\(\s*['\"]?[^)'\"]+['\"]?\s*\)|\bsrc\s*[:=]\s*['\"`][^'\"`]+['\"`]",
                       re.I)


def described(tag: str) -> bool:
    # A stock photo the user agreed to must say what it shows, in alt text of at least four words.
    m = re.search(r"\balt\s*=\s*['\"]([^'\"]*)['\"]", tag)
    return bool(m) and len(re.findall(r"[^\W\d_]+", m.group(1))) >= 4


@tell("copy.stock-photos", "copy", 6, "Hotlinked stock photos",
      "Photos pulled from Unsplash or Pexels rarely show the product's real people or place. "
      "They are an invented fact, like a made-up price.",
      "Use the business's own photos. If there are none yet, mark each image as a placeholder in its alt text, "
      "for example alt=\"[photo of the shop front]\". If the user agreed to stock photos in the brief, "
      "describe each photo in its alt text.")
def _stock_photos(ctx: Context) -> list[Finding]:
    out = []
    for doc in ctx.docs:
        n = 0
        for m in STOCK_USE.finditer(doc.text):
            chunk = m.group(0)
            host = STOCK_HOSTS.search(chunk)
            if not host:
                continue
            if ctx.allow_stock and described(chunk):
                continue
            before = doc.text[max(0, m.start() - 160):m.start()]
            if MARKED_PLACEHOLDER.search(chunk) or re.search(r"(?:<!--|/\*|//)[^\n]*(?:placeholder|replace)", before, re.I):
                continue
            out.append(Finding("copy.stock-photos", doc.rel, doc.line(m.start()), host.group(0)))
            n += 1
            if n >= MAX_PER_FILE:
                break
    return out


NATIVE_INPUT = re.compile(r"<input\b[^>]*\btype\s*=\s*['\"]?(date|time|datetime-local|month|week|color|file)\b[^>]*>", re.I)
NATIVE_SELECT = re.compile(r"<select\b", re.I)


@tell("layout.native-controls", "layout", 4, "Browser-default form controls",
      "Unstyled date, time, file and select controls look different in every browser and break the design.",
      "Style them from the design system: set appearance: none, add your own arrow or calendar icon, "
      "and keep the native input underneath for accessibility.")
def _native_controls(ctx: Context) -> list[Finding]:
    styled = False
    for doc in ctx.docs:
        if re.search(r"appearance\s*:\s*none|::-webkit-calendar-picker-indicator|::file-selector-button|::-webkit-file-upload-button",
                     doc.text, re.I) or any(base(tok) == "appearance-none" for _l, tok in doc.tokens):
            styled = True
            break
    if styled:
        return []
    out = []
    for doc in ctx.docs:
        if doc.kind not in ("markup", "script"):
            continue
        hits = [(m.start(), f"<input type=\"{m.group(1)}\">") for m in NATIVE_INPUT.finditer(doc.text)]
        hits += [(m.start(), "<select>") for m in NATIVE_SELECT.finditer(doc.text)]
        for pos, label in sorted(hits)[:MAX_PER_FILE]:
            out.append(Finding("layout.native-controls", doc.rel, doc.line(pos), label))
    return out


@tell("layout.uneven-images", "layout", 4, "Uneven images in a row",
      "Images side by side with different heights make names and captions under them misalign.",
      "Give images in a row one aspect ratio with aspect-ratio and object-fit: cover.")
def _uneven_images(ctx: Context) -> list[Finding]:
    return []  # needs real sizes, so only rendered mode can see it


def by_id() -> dict[str, Tell]:
    return {t.id: t for t in REGISTRY}
