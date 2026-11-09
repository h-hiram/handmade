# Color parsing and color math shared by the scanner, the generator and the checker.
#
# Colors are judged by hue and lightness, not by matching a list of hex codes,
# so the same purple is caught whether it is written as hex, rgb(), hsl(), oklch()
# or shadcn's bare 'H S% L%' token.

from __future__ import annotations

import colorsys
import math
import re

NAMED = {
    "white": "#ffffff", "black": "#000000", "purple": "#800080", "violet": "#ee82ee",
    "indigo": "#4b0082", "blueviolet": "#8a2be2", "mediumpurple": "#9370db", "rebeccapurple": "#663399",
    "darkviolet": "#9400d3", "darkorchid": "#9932cc", "mediumslateblue": "#7b68ee", "slateblue": "#6a5acd",
    "fuchsia": "#ff00ff", "magenta": "#ff00ff", "orchid": "#da70d6", "plum": "#dda0dd",
}

# A color literal anywhere in a value: hex, functions or a named purple.
COLOR_IN_TEXT = re.compile(
    r"#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3,4}\b"
    r"|(?:rgba?|hsla?|oklch|oklab)\([^()]*\)"
    r"|\b(?:" + "|".join(NAMED) + r")\b",
    re.I,
)


def hsl_hex(h: float, s: float, l: float) -> str:
    r, g, b = colorsys.hls_to_rgb((h % 360) / 360, max(0, min(100, l)) / 100, max(0, min(100, s)) / 100)
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def hex_rgb(value: str) -> tuple[int, int, int]:
    v = value.lstrip("#")
    return int(v[0:2], 16), int(v[2:4], 16), int(v[4:6], 16)


def hex_hsl(value: str) -> tuple[float, float, float]:
    r, g, b = (c / 255 for c in hex_rgb(value))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    return h * 360, s * 100, l * 100


def _oklch_hex(l: float, c: float, h: float) -> str:
    # OKLCH to sRGB hex, using Bjorn Ottosson's OKLab matrices.
    a, b = c * math.cos(math.radians(h)), c * math.sin(math.radians(h))
    return _oklab_hex(l, a, b)


def _oklab_hex(l: float, a: float, b: float) -> str:
    l_ = (l + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (l - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (l - 0.0894841775 * a - 1.2914855480 * b) ** 3
    rgb = (4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_,
           -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_,
           -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_)

    def gamma(x: float) -> int:
        x = max(0.0, min(1.0, x))
        x = 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
        return round(x * 255)
    return "#{:02x}{:02x}{:02x}".format(*(gamma(x) for x in rgb))


def hex_oklab(value: str) -> tuple[float, float, float]:
    def lin(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in hex_rgb(value))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    return (0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s,
            1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s,
            0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s)


def distance(a: str, b: str) -> float:
    # Perceptual distance in OKLab. About 0.02 is barely visible.
    return math.dist(hex_oklab(a), hex_oklab(b))


_NUM = r"(-?[\d.]+)(%|deg)?"


def parse_color(value: str) -> str | None:
    # Read one CSS color as #rrggbb. Alpha is ignored. Returns None if it is not a color.
    v = value.strip().lower().rstrip(";").strip()
    if v in NAMED:
        return NAMED[v]
    m = re.fullmatch(r"#([0-9a-f]{3,4}|[0-9a-f]{6}|[0-9a-f]{8})", v)
    if m:
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(ch * 2 for ch in h[:3])
        return "#" + h[:6]
    nums = re.findall(_NUM, v)
    if v.startswith("oklch(") and len(nums) >= 3:
        l = float(nums[0][0]) / (100 if nums[0][1] == "%" else 1)
        return _oklch_hex(l, float(nums[1][0]), float(nums[2][0]))
    if v.startswith("oklab(") and len(nums) >= 3:
        l = float(nums[0][0]) / (100 if nums[0][1] == "%" else 1)
        return _oklab_hex(l, float(nums[1][0]), float(nums[2][0]))
    if v.startswith("rgb") and len(nums) >= 3:
        vals = [float(n[0]) * (2.55 if n[1] == "%" else 1) for n in nums[:3]]
        return "#" + "".join(f"{max(0, min(255, round(x))):02x}" for x in vals)
    if v.startswith("hsl") and len(nums) >= 3:
        return hsl_hex(float(nums[0][0]), float(nums[1][0]), float(nums[2][0]))
    bare = re.fullmatch(r"(-?[\d.]+)(?:deg)?\s+([\d.]+)%\s+([\d.]+)%(?:\s*/\s*[\d.%]+)?", v)
    if bare:
        return hsl_hex(float(bare.group(1)), float(bare.group(2)), float(bare.group(3)))
    return None


def colors_in(text: str) -> list[str]:
    # Every color literal in a CSS value, as hex.
    out = []
    for m in COLOR_IN_TEXT.finditer(text):
        c = parse_color(m.group(0))
        if c:
            out.append(c)
    bare = parse_color(text)
    if bare and not out:
        out.append(bare)
    return out


def luminance(value: str) -> float:
    def chan(c: float) -> float:
        c /= 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(c) for c in hex_rgb(value))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# ---------- judgments ----------

def is_neutral(value: str) -> bool:
    # Grays, near-black and near-white, including slightly tinted ones like Tailwind's gray-900.
    _h, s, l = hex_hsl(value)
    return s < 12 or l < 15 or l > 97 or (s < 30 and l < 20)


def is_purple(value: str) -> bool:
    # The indigo-to-violet band models default to (Tailwind indigo, violet, purple, fuchsia-ish).
    h, s, l = hex_hsl(value)
    return 230 <= h <= 300 and s >= 30 and 20 <= l <= 85


def is_ai_gradient_stop(value: str) -> bool:
    # Colors that appear in the stock purple-to-blue or purple-to-pink gradients.
    h, s, l = hex_hsl(value)
    return s >= 30 and 20 <= l <= 85 and (200 <= h <= 340)


def is_cream(value: str) -> bool:
    h, s, l = hex_hsl(value)
    return 20 <= h <= 55 and 15 <= s <= 70 and 90 <= l <= 98


def is_terracotta(value: str) -> bool:
    h, s, l = hex_hsl(value)
    return 5 <= h <= 30 and 40 <= s <= 95 and 30 <= l <= 66
