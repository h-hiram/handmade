# Build a picture of the design choices a project already made.

from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .colors import without_strings
from .extract import Doc

TW_FAMILIES = (
    "slate gray zinc neutral stone red orange amber yellow lime green emerald teal "
    "cyan sky blue indigo violet purple fuchsia pink rose"
).split()
NEUTRALS = {"slate", "gray", "zinc", "neutral", "stone"}
GENERIC_FAMILIES = {
    "sans-serif", "serif", "monospace", "system-ui", "-apple-system", "blinkmacsystemfont",
    "ui-sans-serif", "ui-serif", "ui-monospace", "cursive", "fantasy", "inherit", "initial",
    "segoe ui", "apple color emoji", "segoe ui emoji", "segoe ui symbol", "noto color emoji",
    "var", "unset",
}

VARIANT = re.compile(r"^(?:[^:\[\]]+:)+")
TW_COLOR = re.compile(
    r"^-?(bg|text|border|from|via|to|ring|fill|stroke|shadow|outline|decoration|divide|accent|caret|placeholder)"
    r"-(" + "|".join(TW_FAMILIES) + r")-(\d{2,3})(?:/\d+)?$"
)
HEX = re.compile(r"#(?:[0-9a-fA-F]{3}){1,2}\b")
GOOGLE_FONT = re.compile(r"fonts\.googleapis\.com/css2?\?([^\"'\s)>]+)")
NEXT_FONT = re.compile(r"import\s*\{([^}]+)\}\s*from\s*['\"]next/font/google['\"]")
FONTSOURCE = re.compile(r"@fontsource(?:-variable)?/([\w-]+)")
TW_FONT_ARBITRARY = re.compile(r"^font-\[['\"]?([^\]'\"]+)")
TW_CONFIG_FONT = re.compile(r"(?:sans|serif|mono|display|body|heading)\s*:\s*\[\s*['\"]([^'\"]+)['\"]")
RULE_FONT = re.compile(r"([^{};]+)\{[^{}]*?font-family\s*:\s*([^;}]+)", re.S)
VAR_FONT = re.compile(r"--font-([\w-]+)\s*:\s*([^;}]+)")
BODY_SEL = re.compile(r"(^|[\s,])(html|body|:root|p|main|\.prose)\b")
DISPLAY_SEL = re.compile(r"(^|[\s,])(h[1-3]|\.?(display|heading|headline|title|hero))\b")
BODY_VAR = re.compile(r"^(body|sans|text|base|copy)$")
DISPLAY_VAR = re.compile(r"^(display|heading|headings|serif|title|head)$")


def _first_named(value: str) -> str | None:
    for part in value.split(","):
        name = norm_font(part)
        if is_font_name(name) and name not in GENERIC_FAMILIES:
            return name
    return None


def _font_roles(p: "Profile", text: str) -> None:
    for m in RULE_FONT.finditer(text):
        sel, name = m.group(1).strip().lower(), _first_named(m.group(2))
        if not name:
            continue
        if DISPLAY_SEL.search(sel):
            p.display_fonts[name] += 1
        elif BODY_SEL.search(sel):
            p.body_fonts[name] += 1
    for m in VAR_FONT.finditer(text):
        role, name = m.group(1).lower(), _first_named(m.group(2))
        if not name:
            continue
        if DISPLAY_VAR.match(role):
            p.display_fonts[name] += 1
        elif BODY_VAR.match(role):
            p.body_fonts[name] += 1


TW_COLOR_PROPS = ("bg", "text", "border", "from", "via", "to", "ring", "fill", "stroke", "shadow", "outline",
                  "decoration", "divide", "accent", "caret", "placeholder")
TW_ANY_COLOR = re.compile(r"^-?(" + "|".join(TW_COLOR_PROPS) + r")-(?!\[)([a-z][\w-]*?)(?:-(\d{2,3}))?(?:/\d+)?$")
CONFIG_NESTED = re.compile(r"""['"]?([\w-]+)['"]?\s*:\s*\{([^{}]*)\}""")
CONFIG_FLAT = re.compile(r"""['"]?([\w-]+)['"]?\s*:\s*['"`]([^'"`]+)['"`]""")
CONFIG_FAMILY = re.compile(r"""['"]?([\w-]+)['"]?\s*:\s*colors\.(\w+)""")
THEME_COLOR_VAR = re.compile(r"^--color-([a-z][\w-]*?)(?:-(\d{2,3}))?$")
VAR_REF = re.compile(r"var\(\s*(--[\w-]+)\s*(?:,\s*([^()]*))?\)")


def resolve_vars(value: str, css_vars: dict[str, str], depth: int = 0) -> str:
    # Replace var(--x) with its value, a few levels deep.
    if depth > 4 or "var(" not in value:
        return value
    def sub(m: re.Match) -> str:
        return css_vars.get(m.group(1).lower(), m.group(2) or "")
    return resolve_vars(VAR_REF.sub(sub, value), css_vars, depth + 1)


def _config_colors(p: "Profile", text: str) -> None:
    # Read color names from tailwind.config.* (Tailwind v3 and shadcn style).
    for m in re.finditer(r"\bcolors\s*:\s*\{", text):
        start, depth = m.end() - 1, 0
        for i in range(start, min(len(text), start + 20000)):
            depth += {"{": 1, "}": -1}.get(text[i], 0)
            if depth == 0:
                block = text[start + 1:i]
                break
        else:
            continue
        for nm in CONFIG_NESTED.finditer(block):
            shades = {k if k != "DEFAULT" else "": v for k, v in CONFIG_FLAT.findall(nm.group(2))}
            if shades:
                p.tw_aliases.setdefault(nm.group(1), {}).update(shades)
        flat_block = CONFIG_NESTED.sub("", block)
        for name, value in CONFIG_FLAT.findall(flat_block):
            p.tw_aliases.setdefault(name, {})[""] = value
        for name, family in CONFIG_FAMILY.findall(block):
            p.tw_aliases.setdefault(name, {})["@family"] = family


def _named_gradients(p: "Profile", doc: Doc) -> None:
    for m in re.finditer(r"(?:linear|radial|conic)-gradient\((?:[^()]|\([^()]*\))*\)", doc.text):
        if doc.kind == "config":
            p.named_gradients.append((doc.rel, doc.line(m.start()), m.group(0)))


VAR_BLOCK = re.compile(r"([^{}]*)\{([^{}]*)\}")
VAR_DECL = re.compile(r"(--[\w-]+)\s*:\s*([^;}]+)")
DARK_SCOPE = re.compile(r"\.dark\b|data-theme=['\"]?dark|data-mode=['\"]?dark|\[data-color-scheme=['\"]?dark")


def _collect_vars(p: "Profile", doc: Doc) -> None:
    for m in VAR_BLOCK.finditer(doc.text):
        selector = re.sub(r"/\*.*?\*/", "", m.group(1), flags=re.S).split(";")[-1]
        dark = bool(DARK_SCOPE.search(selector))
        for d in VAR_DECL.finditer(m.group(2)):
            name, value = d.group(1).lower(), d.group(2).strip()
            p.var_sources.append((doc.rel, name, value, dark))
            if not dark:
                p.css_vars[name] = value


FONT_FACE = re.compile(r"@font-face\s*\{[^}]*font-family\s*:\s*['\"]?([^;'\"]+)", re.S)


def base(token: str) -> str:
    # Drop variants like md:, hover:, dark:.
    return VARIANT.sub("", token)


FONT_SUFFIX = re.compile(r"(?:[\s-]*(?:variable|var|vf|fallback|web|webfont))+$")


def norm_font(name: str) -> str:
    # 'Inter Variable', 'InterVariable', 'Inter_Var' and '"Inter"' all become 'inter'.
    n = name.strip().strip("'\"").replace("_", " ").replace("+", " ")
    n = re.sub(r"(?<=[a-z])(?=Variable$|VF$|Var$)", " ", n)
    n = " ".join(n.split()).lower()
    return FONT_SUFFIX.sub("", n).strip() or n


def is_font_name(name: str) -> bool:
    # False for SCSS/Less variables, functions and interpolation.
    return bool(name) and not name.startswith(("$", "@", "var(", "#{", "map.", "theme(")) and "(" not in name and "!" not in name


def norm_hex(value: str) -> str:
    v = value.lower().lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    return "#" + v


@dataclass
class Profile:
    fonts_used: dict[str, list[tuple[str, int]]] = field(default_factory=lambda: defaultdict(list))
    primary_fonts: Counter = field(default_factory=Counter)
    fonts_loaded: set[str] = field(default_factory=set)
    tw_colors: Counter = field(default_factory=Counter)
    hexes: Counter = field(default_factory=Counter)
    css_vars: dict[str, str] = field(default_factory=dict)
    # (file, variable, value, inside a dark-mode selector)
    var_sources: list[tuple[str, str, str, bool]] = field(default_factory=list)
    radii: Counter = field(default_factory=Counter)
    shadows: Counter = field(default_factory=Counter)
    font_sizes: Counter = field(default_factory=Counter)
    # Tailwind color names defined in config or @theme: name -> {shade or "": raw value}
    tw_aliases: dict[str, dict[str, str]] = field(default_factory=dict)
    # gradients defined in Tailwind config or CSS variables: (file, line, raw)
    named_gradients: list[tuple[str, int, str]] = field(default_factory=list)
    body_fonts: Counter = field(default_factory=Counter)
    display_fonts: Counter = field(default_factory=Counter)
    has_dark_class: bool = False
    has_reduced_motion: bool = False
    has_animation: bool = False
    has_focus_visible: bool = False
    files: int = 0

    def resolve(self, value: str) -> str:
        return resolve_vars(value, self.css_vars)

    def token_colors(self, token: str) -> tuple[str | None, list[str]]:
        # For a Tailwind color class, return (palette family or None, resolved hex colors).
        #
        # Works for bg-indigo-600, custom names from tailwind.config (bg-brand-600),
        # Tailwind v4 @theme names (--color-brand-600) and shadcn tokens (bg-primary -> --primary).
        from .colors import colors_in

        m = TW_ANY_COLOR.match(token)
        if not m:
            return None, []
        name, shade = m.group(2), m.group(3) or ""
        if name in TW_FAMILIES:
            return name, []
        alias = self.tw_aliases.get(name, {})
        if "@family" in alias:
            return alias["@family"], []
        raw = alias.get(shade) or alias.get("")
        if raw is None:
            raw = self.css_vars.get(f"--color-{name}-{shade}" if shade else f"--color-{name}")
        if raw is None and not shade:
            raw = self.css_vars.get(f"--{name}")
        if raw is None:
            return None, []
        resolved = self.resolve(raw)
        return None, colors_in(resolved)

    def chromatic_families(self) -> Counter:
        out: Counter = Counter()
        for (family, _shade), n in self.tw_colors.items():
            if family not in NEUTRALS:
                out[family] += n
        return out

    def to_dict(self) -> dict:
        return {
            "files": self.files,
            "fonts": sorted(self.fonts_used),
            "primary_fonts": dict(self.primary_fonts.most_common()),
            "fonts_loaded": sorted(self.fonts_loaded),
            "body_fonts": dict(self.body_fonts.most_common()),
            "heading_fonts": dict(self.display_fonts.most_common()),
            "tailwind_colors": {f"{f}-{s}": n for (f, s), n in self.tw_colors.most_common(20)},
            "hex_colors": dict(self.hexes.most_common(20)),
            "css_variables": dict(list(self.css_vars.items())[:40]),
            "radii": dict(self.radii.most_common()),
            "shadows": dict(self.shadows.most_common()),
            "font_sizes": dict(self.font_sizes.most_common()),
            "reduced_motion_support": self.has_reduced_motion,
        }


LITERAL_SIZE = re.compile(r"^\d+(?:\.\d+)?(?:px|rem|em)$")
LENGTH = re.compile(r"-?\d*\.?\d+(?:px|rem|em)?")


def is_elevation(value: str) -> bool:
    # True when at least one shadow layer has a blur radius above zero.
    if value.strip() in ("none", "0", "inherit", "initial", "unset") or value.lstrip().startswith(("$", "var(")):
        return False
    for layer in re.split(r",(?![^(]*\))", value):
        if "inset" in layer:
            continue
        nums = [n for n in LENGTH.findall(re.sub(r"(rgba?|hsla?)\([^)]*\)|#[0-9a-fA-F]+", "", layer)) if n]
        if len(nums) >= 3 and float(re.sub(r"[a-z]+", "", nums[2]) or 0) > 0:
            return True
    return False


RADIUS = re.compile(r"^rounded(?:-(?:t|r|b|l|s|e|tl|tr|br|bl|ss|se|es|ee))?(?:-(none|xs|sm|md|lg|xl|2xl|3xl|4xl|full|\[[^\]]+\]))?$")
SHADOW = re.compile(r"^shadow(?:-(xs|sm|md|lg|xl|2xl|inner|none|\[[^\]]+\]))?$")
TEXT_SIZE = re.compile(r"^text-(xs|sm|base|lg|xl|[2-9]xl|\[\d+(?:\.\d+)?(?:px|rem|em)\])$")


def build_profile(docs: list[Doc]) -> Profile:
    p = Profile(files=len(docs))
    for doc in docs:
        text = doc.text
        low = text.lower()
        if "prefers-reduced-motion" in low or "motion-safe:" in low or "motion-reduce:" in low or "usereducedmotion" in low:
            p.has_reduced_motion = True
        if re.search(r"@keyframes|\banimate-[a-z]|framer-motion|from ['\"]motion|\bgsap\b|@angular/animations", text):
            p.has_animation = True
        if "focus-visible" in low:
            p.has_focus_visible = True
        if re.search(r"<html[^>]*class(?:Name)?=[\"'{`][^>]*\bdark\b|defaultTheme=[\"']dark", text):
            p.has_dark_class = True
        if doc.kind in ("css", "markup", "script"):
            _font_roles(p, text)

        for m in GOOGLE_FONT.finditer(text):
            for part in m.group(1).split("&"):
                if part.startswith("family="):
                    p.fonts_loaded.add(norm_font(part[7:].split(":")[0]))
        for m in NEXT_FONT.finditer(text):
            for name in m.group(1).split(","):
                name = name.split(" as ")[0].strip()
                if name:
                    p.fonts_loaded.add(norm_font(name))
                    p.fonts_used[norm_font(name)].append((doc.rel, doc.line(m.start())))
        for m in FONTSOURCE.finditer(text):
            p.fonts_loaded.add(norm_font(m.group(1).replace("-", " ")))
        for m in FONT_FACE.finditer(text):
            p.fonts_loaded.add(norm_font(m.group(1)))
        if doc.kind == "config":
            for m in TW_CONFIG_FONT.finditer(text):
                name = norm_font(m.group(1))
                if name not in GENERIC_FAMILIES:
                    p.fonts_used[name].append((doc.rel, doc.line(m.start())))
                    p.primary_fonts[name] += 1

        if doc.kind in ("css", "markup"):
            _collect_vars(p, doc)
        if doc.kind == "config":
            _config_colors(p, text)
            _named_gradients(p, doc)
        for line, prop, val in doc.decls:
            if prop in ("font-family", "font") or (prop.startswith("--font") and "," in val):
                families = [norm_font(f) for f in val.split(",")]
                families = [f for f in families if f and not f.startswith("var(")]
                named = [f for f in families if is_font_name(f) and f not in GENERIC_FAMILIES and not re.match(r"^[\d.]+", f)]
                for f in named:
                    p.fonts_used[f].append((doc.rel, line))
                if named and prop != "font":
                    p.primary_fonts[named[0]] += 1
            for h in HEX.findall(without_strings(val)):
                p.hexes[norm_hex(h)] += 1
            if prop == "border-radius":
                p.radii[val] += 1
            if prop == "box-shadow" and is_elevation(val):
                p.shadows[val] += 1
            if prop == "font-size" and LITERAL_SIZE.match(val):
                p.font_sizes[val] += 1

        for line, tok in doc.tokens:
            b = base(tok)
            m = TW_COLOR.match(b)
            if m:
                p.tw_colors[(m.group(2), m.group(3))] += 1
                continue
            for h in HEX.findall(b):
                p.hexes[norm_hex(h)] += 1
            m = RADIUS.match(b)
            if m:
                p.radii[m.group(1) or "DEFAULT"] += 1
                continue
            m = SHADOW.match(b)
            if m:
                p.shadows[m.group(1) or "DEFAULT"] += 1
                continue
            m = TEXT_SIZE.match(b)
            if m:
                p.font_sizes[m.group(1)] += 1
                continue
            m = TW_FONT_ARBITRARY.match(b)
            if m and is_font_name(norm_font(m.group(1))) and not m.group(1)[0].isdigit():
                name = norm_font(m.group(1))
                p.fonts_used[name].append((doc.rel, line))
                p.primary_fonts[name] += 1
    return p
