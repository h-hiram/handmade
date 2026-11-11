# Generate a starting design system a designer would sign off on.
#
# Choices come from a mood and a seed. The seed is derived from the product
# description, so different products get different systems and no single
# 'handmade default' appears. Every color pair is checked for WCAG contrast.

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field

from .colors import contrast, hex_hsl, hsl_hex, is_cream, is_purple, is_terracotta, luminance, parse_color  # noqa: F401
from .profile import Profile
from .tells import AI_PURPLES, CREAMS, GENERIC_FONTS, TERRACOTTAS, TREND_FONTS


@dataclass(frozen=True)
class Mood:
    name: str
    summary: str
    pairs: tuple[tuple[str, str], ...]  # (display or heading face, body face)
    mono: tuple[str, ...]
    ratio: float
    radius: tuple[int, int]  # (controls, containers) in px
    hues: tuple[tuple[int, int], ...]  # allowed accent hue bands
    saturation: tuple[int, int]
    details: tuple[str, ...]
    depth: str = "borders"  # one way to show depth: borders, shadows, tonal or rules


# One depth strategy per mood. Mixing them is what makes a UI look unplanned.
DEPTH_RULES = {
    "borders": "Depth comes from 1px `line` borders and the `surface` tint. Cards sit flat. "
               "Only menus, popovers and dialogs float, with the `overlay` shadow.",
    "shadows": "Cards are `raised` on `paper` with the soft `raised` shadow and no border or a border and no shadow. "
               "Never both. Menus and dialogs use the `overlay` shadow.",
    "tonal": "Depth comes from stepping background tones: `paper`, then `surface`, then `raised`. "
             "No borders on cards and no shadows except the `overlay` shadow on dialogs.",
    "rules": "Thin horizontal rules in `line` separate sections. No boxes around content. "
             "Only menus and dialogs float, with the `overlay` shadow.",
}

MOODS: dict[str, Mood] = {m.name: m for m in (
    Mood("editorial", "Calm, typographic, reads like a good publication",
         (("Newsreader", "Public Sans"), ("Source Serif 4", "Source Sans 3"), ("Literata", "Karla"),
          ("Spectral", "Work Sans"), ("Libre Caslon Text", "Libre Franklin")),
         ("IBM Plex Mono", "Source Code Pro"), 1.333, (4, 8), ((195, 222), (140, 175), (322, 342), (40, 55)), (45, 65),
         ("Thin horizontal rules separate sections instead of cards.",
          "Body text column of 60 to 75 characters.",
          "Small caps or letter-spaced labels for metadata."), depth="rules"),
    Mood("utilitarian", "Dense, fast to scan, built for daily work",
         (("IBM Plex Sans", "IBM Plex Sans"), ("Public Sans", "Public Sans"), ("Source Sans 3", "Source Sans 3"),
          ("Atkinson Hyperlegible", "Atkinson Hyperlegible"), ("Archivo", "Archivo")),
         ("IBM Plex Mono", "JetBrains Mono", "Source Code Pro", "Red Hat Mono"), 1.2, (4, 6),
         ((200, 232), (160, 190), (90, 140), (40, 55)), (50, 70),
         ("Tabular numerals for every figure.",
          "1px borders and background tints define regions. No floating cards.",
          "Compact rows: 32 to 40px tall in tables."), depth="borders"),
    Mood("warm", "Friendly and human, feels local and trusted",
         (("Alegreya", "Alegreya Sans"), ("Bitter", "Hanken Grotesk"), ("Zilla Slab", "Commissioner"),
          ("Young Serif", "Familjen Grotesk"), ("Gelasio", "Rubik")),
         ("Red Hat Mono",), 1.25, (8, 12), ((40, 60), (90, 130), (322, 345), (170, 195)), (45, 65),
         ("Photography of real people and places from the product's market.",
          "Slightly larger body text (17 to 18px) and relaxed line height.",
          "One illustrated or photographic element per section at most."), depth="shadows"),
    Mood("playful", "Bold, energetic, a little loud on purpose",
         (("Anybody", "Lexend"), ("Epilogue", "Lexend"), ("Big Shoulders Display", "Rubik"),
          ("Chivo", "Lexend"), ("Archivo", "Rubik")),
         ("Martian Mono",), 1.333, (12, 20), ((322, 345), (55, 75), (160, 190), (25, 38)), (65, 85),
         ("Large type with tight leading for headlines.",
          "Solid blocks of color for sections, not gradients.",
          "One playful interaction that serves the task, not decoration."), depth="tonal"),
    Mood("technical", "Precise and engineered, for builders",
         (("Red Hat Display", "Red Hat Text"), ("Chivo", "Chivo"), ("Archivo", "Archivo"),
          ("Schibsted Grotesk", "Schibsted Grotesk"), ("Overpass", "Overpass")),
         ("Red Hat Mono", "Chivo Mono", "Martian Mono", "JetBrains Mono", "Overpass Mono"), 1.25, (6, 8),
         ((160, 200), (60, 90), (25, 38), (200, 222)), (55, 75),
         ("Show real code, real output or a real diagram near the top.",
          "Monospace for labels, values and keyboard shortcuts.",
          "Hairline borders and a visible grid instead of shadows."), depth="borders"),
    Mood("luxury", "Quiet, slow, expensive",
         (("Cormorant Garamond", "Jost"), ("Bodoni Moda", "Mulish"), ("Marcellus", "Karla"),
          ("EB Garamond", "Work Sans"), ("Gloock", "Hanken Grotesk")),
         ("IBM Plex Mono",), 1.414, (4, 8), ((325, 345), (150, 170), (200, 220), (40, 50)), (25, 45),
         ("A lot of empty space. Few elements per screen.",
          "Large photography, cropped with intent.",
          "Thin type, wide letter spacing on small labels."), depth="tonal"),
    Mood("civic", "Plain, trustworthy, accessible to everyone",
         (("Public Sans", "Public Sans"), ("Libre Franklin", "Libre Baskerville"), ("Source Sans 3", "Source Serif 4"),
          ("Atkinson Hyperlegible", "Atkinson Hyperlegible"), ("Merriweather Sans", "Merriweather")),
         ("Source Code Pro",), 1.2, (6, 8), ((200, 222), (170, 190), (40, 50)), (50, 70),
         ("Plain language at a reading age most citizens can follow.",
          "Clear headings that say what the section does.",
          "Meet WCAG 2.2 AA everywhere, AAA for body text where possible."), depth="borders"),
)}


def _darken_until(h: float, s: float, l: float, against: str, target: float) -> str:
    color = hsl_hex(h, s, l)
    while contrast(color, against) < target and l > 5:
        l -= 2
        color = hsl_hex(h, s, l)
    return color


def _avoid_default_hues(h: float) -> float:
    # Move a hue out of the purple band the scanner flags (230 to 300 degrees), with a margin.
    h %= 360
    if 226 <= h <= 314:
        return 222 if h < 265 else 320
    return h


@dataclass
class DesignSystem:
    mood: Mood
    display_font: str
    body_font: str
    mono_font: str
    colors: dict[str, str]
    type_scale: list[int]
    spacing: list[int]
    radius: tuple[int, int]
    kept: list[str] = field(default_factory=list)
    replaced: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "DesignSystem":
        # Rebuild a saved system, so later screens of a project use exactly the same values.
        return cls(
            mood=MOODS[data["mood"]],
            display_font=data["fonts"]["display"],
            body_font=data["fonts"]["body"],
            mono_font=data["fonts"]["mono"],
            colors=add_craft(dict(data["colors"]), luminance(data["colors"]["paper"]) < 0.18),
            type_scale=list(data["type_scale_px"]),
            spacing=list(data["spacing_px"]),
            radius=(data["radius_px"]["controls"], data["radius_px"]["containers"]),
            kept=["the saved design system (handmade.system.json)"],
        )

    def to_dict(self) -> dict:
        return {
            "handmade_system": 1,
            "mood": self.mood.name,
            "theme": "dark" if self.dark else "light",
            "fonts": {"display": self.display_font, "body": self.body_font, "mono": self.mono_font},
            "colors": dict(self.colors),
            "type_scale_px": list(self.type_scale),
            "spacing_px": list(self.spacing),
            "radius_px": {"controls": self.radius[0], "containers": self.radius[1]},
            "shadows": self.shadows,
            "depth": self.mood.depth,
        }

    @property
    def shadows(self) -> dict[str, str]:
        return shadows_for(self.colors, self.dark)

    @property
    def dark(self) -> bool:
        return luminance(self.colors["paper"]) < 0.18

    def contrast_report(self) -> dict[str, float]:
        c = self.colors
        return {
            "ink on paper": round(contrast(c["ink"], c["paper"]), 1),
            "muted on paper": round(contrast(c["muted"], c["paper"]), 1),
            "accent on paper": round(contrast(c["accent"], c["paper"]), 1),
            "text on accent": round(contrast(c["on-accent"], c["accent"]), 1),
        }


def seed_from(*parts: str) -> int:
    joined = "|".join(p.strip().lower() for p in parts if p)
    return int(hashlib.sha256(joined.encode()).hexdigest()[:12], 16)


def _lighten_until(h: float, s: float, l: float, against: str, target: float) -> str:
    color = hsl_hex(h, s, l)
    while contrast(color, against) < target and l < 95:
        l += 2
        color = hsl_hex(h, s, l)
    return color


def _fit(h: float, s: float, l: float, against: str, target: float, dark: bool) -> str:
    return _lighten_until(h, s, l, against, target) if dark else _darken_until(h, s, l, against, target)


def _palette(mood: Mood, rng: random.Random, accent_hex: str | None, dark: bool = False) -> dict[str, str]:
    if accent_hex:
        h, s, _l = hex_hsl(accent_hex)
    else:
        lo, hi = rng.choice(mood.hues)
        h = _avoid_default_hues(rng.uniform(lo, hi))
        s = rng.uniform(*mood.saturation)
    # Text colors are checked against the harder of the two backgrounds they sit on (paper and surface),
    # so muted text in a table header or a tinted panel still passes WCAG.
    if dark:
        paper = hsl_hex(h, rng.uniform(10, 18), 7)
        surface = hsl_hex(h, 12, 11)
        colors = {"paper": paper, "surface": surface, "line": hsl_hex(h, 10, 22),
                  "ink": hsl_hex(h, 12, 93), "muted": _lighten_until(h, 10, 60, surface, 4.5)}
        accent = accent_hex if accent_hex and contrast(accent_hex, surface) >= 4.5 else _lighten_until(h, s, 56, surface, 4.5)
    else:
        paper = hsl_hex(h, rng.uniform(8, 16), 97)
        surface = hsl_hex(h, 14, 93)
        colors = {"paper": paper, "surface": surface, "line": hsl_hex(h, 12, 84),
                  "ink": hsl_hex(h, 28, 11), "muted": _darken_until(h, 12, 44, surface, 4.5)}
        accent = accent_hex if accent_hex and contrast(accent_hex, surface) >= 4.5 else _darken_until(h, s, 44, surface, 4.5)
    colors["accent"] = accent
    colors["on-accent"] = max(("#ffffff", colors["ink"], paper), key=lambda c: contrast(c, accent))
    h2 = _avoid_default_hues(h + rng.choice((150, 165, 180, 195, 210)))
    colors["accent-2"] = _fit(h2, s * 0.8, 60 if dark else 46, surface, 3.0, dark)
    # Status colors must never be mistaken for the accent: try nearby hues and saturations until distinct.
    from .colors import distance
    status_plan = {
        "danger": ((4, 352, 12, 345), 70, 58 if dark else 44),
        "success": ((145, 160, 128, 170), 55, 50 if dark else 34),
        "warning": ((36, 28, 44, 22), 90, 50 if dark else 36),
    }
    taken = [colors["accent"]]
    for name, (hues, sat, light) in status_plan.items():
        choice = None
        candidates = [(hue, s, light + dl) for dl in (0, -10, 10, -18) for hue in hues for s in (sat, sat - 20, sat + 10)]
        for hue, s, l in candidates:
            cand = _fit(hue, s, l, surface, 4.5, dark)
            if all(distance(cand, other) > 0.1 for other in taken):
                choice = cand
                break
        colors[name] = choice or _fit(hues[0], sat, light, surface, 4.5, dark)
        taken.append(colors[name])
    return colors


NEUTRAL_STEPS = (50, 100, 200, 300, 400, 500, 600, 700, 800, 900)
_LIGHTNESS = (97, 94, 88, 79, 66, 52, 40, 29, 19, 11)


def _rgba(hex_value: str, alpha: float) -> str:
    r, g, b = (int(hex_value[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r}, {g}, {b}, {alpha:g})"


def add_craft(colors: dict[str, str], dark: bool) -> dict[str, str]:
    # Derive the extra tokens a finished UI needs from the base palette. Fills only missing keys.
    #
    # No randomness here, so a saved system always gets the same craft tokens back.
    from .colors import distance
    out = dict(colors)
    h, s, _l = hex_hsl(colors["accent"])
    ph, ps, _pl = hex_hsl(colors["paper"])
    surface = colors["surface"]
    craft: dict[str, str] = {}
    if dark:
        craft["raised"] = hsl_hex(ph, max(ps, 10), 15)
        craft["accent-soft"] = hsl_hex(h, min(s, 45), 18)
        al = hex_hsl(colors["accent"])[2]
        craft["accent-strong"] = hsl_hex(h, s, min(al + 8, 90))
    else:
        craft["raised"] = hsl_hex(ph, min(ps, 30), 99.5)
        craft["accent-soft"] = hsl_hex(h, min(s, 60), 94)
        craft["accent-strong"] = _darken_until(h, s, max(hex_hsl(colors["accent"])[2] - 8, 8), surface, 6.0)
    for status in ("success", "warning", "danger"):
        if status in colors:
            sh, ss, _sl = hex_hsl(colors[status])
            soft_s, soft_l = (min(ss, 45), 16) if dark else (min(ss, 70), 95)
            soft = hsl_hex(sh, soft_s, soft_l)
            while contrast(colors[status], soft) < 4.5 and 6 < soft_l < 99:
                soft_l += -1 if dark else 0.5
                soft_s *= 0.9
                soft = hsl_hex(sh, soft_s, soft_l)
            craft[f"{status}-soft"] = soft
    lights = _LIGHTNESS[::-1] if dark else _LIGHTNESS
    for step, light in zip(NEUTRAL_STEPS, lights):
        craft[f"neutral-{step}"] = hsl_hex(ph, 6 + 6 * (abs(light - 50) / 50), light)
    # Chart series: start at the accent, walk the wheel, skip purple, keep every series distinct and readable.
    series = [colors["accent"]]
    avoid = [colors[k] for k in ("danger", "success", "warning") if k in colors]
    offsets = [k * 137.5 for k in range(1, 40)]
    for off in offsets:
        if len(series) >= 5:
            break
        hue = _avoid_default_hues((h + off) % 360)
        found = None
        for sat in (s, 60, 45, 75):
            for light in ((62, 70, 54) if dark else (46, 38, 54)):
                cand = _fit(hue, sat, light, colors["paper"], 3.0, dark)
                if all(distance(cand, c) > 0.11 for c in series) and all(distance(cand, c) > 0.06 for c in avoid) \
                        and not is_purple(cand):
                    found = cand
                    break
            if found:
                break
        if found:
            series.append(found)
    for i, col in enumerate(series, 1):
        craft[f"chart-{i}"] = col
    for key, value in craft.items():
        out.setdefault(key, value)
    return out


def shadows_for(colors: dict[str, str], dark: bool) -> dict[str, str]:
    # Two elevation levels, layered and soft, tinted with the ink color instead of pure black.
    base = "#000000" if dark else colors["ink"]
    if dark:
        return {"raised": f"0 1px 0 {_rgba('#ffffff', 0.04)} inset, 0 1px 2px {_rgba(base, 0.4)}",
                "overlay": f"0 16px 40px -12px {_rgba(base, 0.6)}, 0 4px 12px -4px {_rgba(base, 0.4)}"}
    return {"raised": f"0 1px 2px {_rgba(base, 0.06)}, 0 2px 8px -2px {_rgba(base, 0.06)}",
            "overlay": f"0 16px 40px -12px {_rgba(base, 0.22)}, 0 4px 12px -4px {_rgba(base, 0.08)}"}


def _scale(base_px: int, ratio: float) -> list[int]:
    # Modular scale, rounded the way designers round: even numbers above 14px.
    out = set()
    for n in range(-1, 6):
        size = base_px * ratio ** n
        out.add(round(size) if size <= 14 else 2 * round(size / 2))
    return sorted(out)


def _is_ai_color(hex_value: str) -> bool:
    return is_purple(hex_value) or is_cream(hex_value) or is_terracotta(hex_value)


ACCENT_VARS = ("--primary", "--brand", "--color-primary", "--color-brand", "--brand-color", "--accent", "--color-accent")
BG_VARS = ("--background", "--color-background", "--bg", "--color-bg", "--paper", "--page-bg")


def _accent_source(profile: Profile | None) -> tuple[str | None, str | None, str | None]:
    # Return (hex, note, file) for the project's own brand color, if it has one that is not an AI default.
    #
    # Default-scope values are checked before dark-mode ones. A neutral value is never a brand,
    # so leftover template files (shadcn's black --primary) are skipped automatically.
    if profile is None:
        return None, None, None
    for dark_pass in (False, True):
        for name in ACCENT_VARS:
            for rel, var, value, dark in profile.var_sources:
                if var != name or dark != dark_pass:
                    continue
                val = parse_color(value)
                if val:
                    _h, s, l = hex_hsl(val)
                    if s > 25 and 15 < l < 85 and not _is_ai_color(val):
                        return val, f"brand accent {val} (from {name} in {rel})", rel
    for hex_value, _n in profile.hexes.most_common():
        h, s, l = hex_hsl(hex_value)
        if s > 35 and 20 < l < 60 and not _is_ai_color(hex_value):
            return hex_value, f"accent {hex_value} (most used saturated color)", None
    return None, None, None


def _existing_accent(profile: Profile | None) -> tuple[str | None, str | None]:
    val, note, _rel = _accent_source(profile)
    return val, note


def is_dark_theme(profile: Profile | None) -> bool:
    # True when the project's default (not .dark) background is dark.
    if profile is None:
        return False
    _val, _note, accent_file = _accent_source(profile)
    candidates = [(rel, value) for rel, var, value, dark in profile.var_sources if var in BG_VARS and not dark]
    if accent_file:
        same_file = [c for c in candidates if c[0] == accent_file]
        candidates = same_file or candidates
    for _rel, value in candidates:
        val = parse_color(value)
        if val:
            return luminance(val) < 0.18
    return profile.has_dark_class


def build_system(mood_name: str, seed: int, profile: Profile | None = None, dense: bool = False,
                 dark: bool | None = None) -> DesignSystem:
    mood = MOODS[mood_name]
    rng = random.Random(seed)
    display, body = rng.choice(mood.pairs)
    rng_pair_body = body
    mono = rng.choice(mood.mono)
    kept: list[str] = []
    replaced: list[str] = []

    if profile is not None:
        own = [f for f, _n in profile.primary_fonts.most_common() if f not in GENERIC_FONTS and f not in TREND_FONTS]
        for f in profile.primary_fonts:
            swap = mono if "mono" in f else body
            if f in GENERIC_FONTS:
                replaced.append(f"{f.title()} (a default face) with {swap}")
            elif f in TREND_FONTS:
                replaced.append(f"{f.title()} (a common AI pick) with {swap}, unless it is your brand font")
        if own:
            ok = set(own)
            body_pick = next((f for f, _n in profile.body_fonts.most_common() if f in ok), None)
            display_pick = next((f for f, _n in profile.display_fonts.most_common() if f in ok and f != body_pick), None)
            if body_pick is None:
                body_pick = next((f for f in own if f != display_pick), own[0])
            if display_pick is None:
                display_pick = next((f for f in own if f != body_pick), None)
            body = body_pick.title()
            kept.append(f"body font {body}")
            if display_pick:
                display = display_pick.title()
                kept.append(f"heading font {display}")
            elif display == rng_pair_body:
                display = body  # the mood uses one face, so keep it to the project's face

    accent, note = _existing_accent(profile)
    if note:
        kept.append(note)
    elif profile is not None and any(_is_ai_color(h) for h in profile.hexes):
        replaced.append("purple or cream-terracotta colors with the palette below")

    theme_dark = is_dark_theme(profile) if dark is None else dark
    base_px = 14 if dense else 16
    spacing = [4, 8, 12, 16, 24, 32, 48, 64] if dense or mood.ratio <= 1.2 else [8, 16, 24, 32, 48, 64, 96, 128]
    return DesignSystem(
        mood=mood,
        display_font=display,
        body_font=body,
        mono_font=mono,
        colors=add_craft(_palette(mood, rng, accent, dark=theme_dark), theme_dark),
        type_scale=_scale(base_px, mood.ratio),
        spacing=spacing,
        radius=mood.radius,
        kept=kept,
        replaced=replaced,
    )
