# Conformance: does the UI use only the design system it was given?
#
# The scanner looks for known AI defaults (a blacklist). This module is a whitelist:
# every font, color, font size, corner radius and spacing value must come from
# handmade.system.json. Renaming a color or hiding it in a variable does not help,
# because anything that is not in the system fails.

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .colors import colors_in, distance, is_neutral
from .extract import Doc
from .profile import GENERIC_FAMILIES, NEUTRALS as NEUTRAL_FAMILIES, Profile, base, norm_font

SYSTEM_FILE = "handmade.system.json"
COLOR_TOLERANCE = 0.025  # OKLab distance; about the smallest step people notice
ALWAYS_OK_COLORS = ("transparent", "currentcolor", "inherit", "initial", "unset", "none")
PASS_THRESHOLDS = {"fonts": 100, "colors": 95, "font sizes": 90, "radii": 90, "spacing": 85}

TW_SIZES = {"xs": 12, "sm": 14, "base": 16, "lg": 18, "xl": 20, "2xl": 24, "3xl": 30, "4xl": 36,
            "5xl": 48, "6xl": 60, "7xl": 72, "8xl": 96, "9xl": 128}
TW_RADII_V3 = {"none": 0, "sm": 2, "DEFAULT": 4, "md": 6, "lg": 8, "xl": 12, "2xl": 16, "3xl": 24}
TW_RADII_V4 = {"none": 0, "xs": 2, "sm": 4, "DEFAULT": 4, "md": 6, "lg": 8, "xl": 12, "2xl": 16, "3xl": 24, "4xl": 32}
SPACING_PROPS = re.compile(r"^(?:padding|margin|gap|row-gap|column-gap)(?:-(?:top|right|bottom|left|inline|block)(?:-start|-end)?)?$")
TW_SPACE = re.compile(r"^-?(?:p|px|py|pt|pr|pb|pl|ps|pe|m|mx|my|mt|mr|mb|ml|ms|me|gap|gap-x|gap-y|space-x|space-y)-(?:(\d+(?:\.\d+)?)|\[([^\]]+)\])$")
TW_TEXT = re.compile(r"^text-(?:(xs|sm|base|lg|xl|[2-9]xl)|\[(\d+(?:\.\d+)?(?:px|rem|em))\])$")
TW_RADIUS = re.compile(r"^rounded(?:-(?:t|r|b|l|s|e|tl|tr|br|bl|ss|se|es|ee))?(?:-(none|xs|sm|md|lg|xl|2xl|3xl|4xl|full|\[[^\]]+\]))?$")
LENGTH = re.compile(r"(-?\d*\.?\d+)(px|rem|em)\b")


@dataclass
class Offender:
    category: str
    value: str
    file: str
    line: int
    count: int = 1
    hard: bool = False  # chromatic colors and fonts: one is enough to fail


@dataclass
class Conformance:
    system: dict
    seen: dict[str, int] = field(default_factory=dict)
    offenders: list[Offender] = field(default_factory=list)

    def off_count(self, category: str) -> int:
        return sum(o.count for o in self.offenders if o.category == category)

    def percent(self, category: str) -> int:
        total = self.seen.get(category, 0)
        if total == 0:
            return 100
        return round(100 * (total - self.off_count(category)) / total)

    @property
    def scores(self) -> dict[str, int]:
        return {c: self.percent(c) for c in PASS_THRESHOLDS}

    @property
    def hard_offenders(self) -> list[Offender]:
        return [o for o in self.offenders if o.hard]

    @property
    def passed(self) -> bool:
        return not self.hard_offenders and all(self.percent(c) >= t for c, t in PASS_THRESHOLDS.items())

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "scores": self.scores,
            "thresholds": PASS_THRESHOLDS,
            "values_checked": self.seen,
            "off_system": [o.__dict__ for o in self.offenders],
        }


def load_system(path: str | Path) -> dict:
    # Read handmade.system.json or the JSON block inside a prompt written by handmade.
    text = Path(path).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
        if not m:
            raise ValueError(f"no design system found in {path}")
        data = json.loads(m.group(1))
    if data.get("handmade_system") != 1:
        raise ValueError(f"{path} is not a handmade design system")
    return data


def find_system(root: str | Path) -> Path | None:
    start = Path(root).resolve()
    folder = start if start.is_dir() else start.parent
    for candidate in (folder, *folder.parents[:3]):
        f = candidate / SYSTEM_FILE
        if f.is_file():
            return f
    return None


def _px(number: str, unit: str) -> float:
    return float(number) * (16 if unit in ("rem", "em") else 1)


class _Collector:
    def __init__(self, conf: Conformance) -> None:
        self.conf = conf
        self._index: dict[tuple[str, str], Offender] = {}

    def seen(self, category: str) -> None:
        self.conf.seen[category] = self.conf.seen.get(category, 0) + 1

    def off(self, category: str, value: str, file: str, line: int, hard: bool = False) -> None:
        key = (category, value)
        if key in self._index:
            self._index[key].count += 1
            return
        o = Offender(category, value, file, line, hard=hard)
        self._index[key] = o
        self.conf.offenders.append(o)


def check_conformance(docs: list[Doc], profile: Profile, system: dict) -> Conformance:
    conf = Conformance(system=system)
    col = _Collector(conf)

    fonts_ok = {norm_font(f) for f in system["fonts"].values()} | GENERIC_FAMILIES
    colors_ok = [c.lower() for c in system["colors"].values()]
    sizes_ok = [float(s) for s in system["type_scale_px"]]
    space_ok = [float(s) for s in system["spacing_px"]]
    radius_ok = [0.0, float(system["radius_px"]["controls"]), float(system["radius_px"]["containers"])]
    v4 = any('@import "tailwindcss"' in d.text or "@import 'tailwindcss'" in d.text or "@theme" in d.text for d in docs)
    tw_radii = TW_RADII_V4 if v4 else TW_RADII_V3

    def color_ok(hex_value: str) -> bool:
        return any(distance(hex_value, ok) <= COLOR_TOLERANCE for ok in colors_ok)

    def near(value: float, allowed: list[float], tol: float = 0.5) -> bool:
        return any(abs(value - a) <= tol for a in allowed)

    # Fonts
    for name, locations in profile.fonts_used.items():
        if not name or name.startswith("var"):
            continue
        for rel, line in locations:
            col.seen("fonts")
            if name not in fonts_ok:
                col.off("fonts", name, rel, line, hard=True)

    for doc in docs:
        # CSS declarations, after resolving var()
        for line, prop, val in doc.decls:
            low = val.strip().lower()
            if low in ALWAYS_OK_COLORS:
                continue
            if prop.startswith("--") and not re.search(r"color|bg|background|paper|ink|accent|primary|brand|surface|line|border|text|fg", prop):
                pass  # non-color variables are checked where they are used
            else:
                for c in colors_in(profile.resolve(val)):
                    col.seen("colors")
                    if not color_ok(c):
                        col.off("colors", c, doc.rel, line, hard=not is_neutral(c))
            if prop == "font-size":
                for num, unit in LENGTH.findall(profile.resolve(val)):
                    col.seen("font sizes")
                    if not near(_px(num, unit), sizes_ok):
                        col.off("font sizes", f"{num}{unit}", doc.rel, line)
            if prop.startswith("border") and prop.endswith("radius"):
                for num, unit in LENGTH.findall(profile.resolve(val)):
                    px = _px(num, unit)
                    if px >= 999:
                        continue
                    col.seen("radii")
                    if not near(px, radius_ok):
                        col.off("radii", f"{num}{unit}", doc.rel, line)
            if SPACING_PROPS.match(prop):
                for num, unit in LENGTH.findall(profile.resolve(val)):
                    px = abs(_px(num, unit))
                    if px <= 4:
                        continue
                    col.seen("spacing")
                    if not near(px, space_ok):
                        col.off("spacing", f"{num}{unit}", doc.rel, line)

        # Tailwind classes
        for line, tok in doc.tokens:
            b = base(tok)
            family, hexes = profile.token_colors(b)
            if family and family not in ("white", "black", "transparent", "current", "inherit"):
                col.seen("colors")
                col.off("colors", b, doc.rel, line, hard=family not in NEUTRAL_FAMILIES)
            elif hexes:
                for c in hexes:
                    col.seen("colors")
                    if not color_ok(c):
                        col.off("colors", f"{b} ({c})", doc.rel, line, hard=not is_neutral(c))
            elif re.match(r"^(?:bg|text|border|from|via|to|ring|fill|stroke|outline|decoration)-\[", b):
                for c in colors_in(b[b.index("[") + 1:-1].replace("_", " ")):
                    col.seen("colors")
                    if not color_ok(c):
                        col.off("colors", b, doc.rel, line, hard=not is_neutral(c))
            m = TW_TEXT.match(b)
            if m:
                px = TW_SIZES[m.group(1)] if m.group(1) else _px(*LENGTH.findall(m.group(2))[0])
                col.seen("font sizes")
                if not near(px, sizes_ok):
                    col.off("font sizes", b, doc.rel, line)
            m = TW_RADIUS.match(b)
            if m:
                key = m.group(1) or "DEFAULT"
                if key == "full":
                    continue
                px = tw_radii.get(key)
                if px is None and key.startswith("["):
                    lens = LENGTH.findall(key)
                    px = _px(*lens[0]) if lens else None
                if px is not None:
                    col.seen("radii")
                    if not near(px, radius_ok):
                        col.off("radii", b, doc.rel, line)
            m = TW_SPACE.match(b)
            if m:
                if m.group(1) is not None:
                    px = float(m.group(1)) * 4
                else:
                    lens = LENGTH.findall(m.group(2))
                    px = _px(*lens[0]) if lens else None
                if px is not None and abs(px) > 4:
                    col.seen("spacing")
                    if not near(abs(px), space_ok):
                        col.off("spacing", b, doc.rel, line)
    return conf
