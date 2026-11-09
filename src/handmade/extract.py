# Find UI files and pull out what the scanner needs from them.
#
# The scanner reads source code, not a rendered page. It supports:
# HTML, CSS, SCSS, Sass, Less, Tailwind classes, JSX, TSX, Vue, Svelte,
# Astro, MDX, Laravel Blade, Angular templates and Angular inline components.

from __future__ import annotations

import re
from bisect import bisect_right
from dataclasses import dataclass, field
from pathlib import Path

MARKUP_SUFFIXES = (".html", ".htm", ".vue", ".svelte", ".astro", ".jsx", ".tsx", ".mdx")
CSS_SUFFIXES = (".css", ".scss", ".sass", ".less", ".pcss")
SCRIPT_SUFFIXES = (".js", ".ts", ".mjs", ".cjs")
SKIP_DIRS = {
    "node_modules", ".git", "dist", "build", ".next", ".nuxt", "vendor", "storage",
    "coverage", ".svelte-kit", "out", "__pycache__", ".venv", "venv", ".angular",
    ".turbo", ".cache", ".output",
}
MAX_BYTES = 1_000_000

# Hints that a .js or .ts file holds UI code worth scanning.
SCRIPT_UI_HINTS = ("@Component(", "className", "class=", "styled.", "css`", "fontFamily", "tailwind")

CLASS_ATTR = re.compile(
    r"""(?<![\w:-])(?:className|class|:class|v-bind:class|\[ngClass\]|\[class\]|ngClass|class:list)"""
    r"""\s*=\s*\{?\s*(?P<q>["'`])(?P<v>.*?)(?P=q)""",
    re.S,
)
CLASS_CALL = re.compile(r"(?:\b(?:cn|clsx|cva|twMerge|twJoin|classnames|classNames|cx|tv)|@class)\s*\(")
APPLY = re.compile(r"@apply\s+([^;}]+)")
STRING_LIT = re.compile(r"""(["'`])((?:\\.|(?!\1).)*?)\1""", re.S)
DECL = re.compile(
    r"(?<![\w-])(?P<prop>-{0,2}[a-zA-Z][\w-]*)\s*:\s*(?P<val>[^;{}<>]+?)\s*(?:;|(?=\}))"
)
STYLE_BLOCK = re.compile(r"<style\b[^>]*>(.*?)</style>", re.S | re.I)
STYLE_ATTR = re.compile(r"""(?<![:\[\w-])style\s*=\s*(["'])(.*?)\1""", re.S)
SCRIPT_BLOCK = re.compile(r"<script\b[^>]*>.*?</script>", re.S | re.I)
TEXT_NODE = re.compile(r">([^<>]+)<")
TEMPLATE_LIT = re.compile(r"`([^`]*)`", re.S)
STYLE_OBJECT = re.compile(
    r"""(?:\bstyle\s*=\s*\{\{(?P<jsx>.*?)\}\}|(?::style|v-bind:style|\[ngStyle\]|\[style\])\s*=\s*"\s*\{(?P<obj>.*?)\}\s*")""",
    re.S,
)
STYLE_PAIR = re.compile(r"""['"]?([A-Za-z][\w-]*)['"]?\s*:\s*(["'`])(.*?)\2""", re.S)
JS_STYLE_FILES = (".jsx", ".tsx", ".vue", ".svelte", ".astro", ".mdx", ".js", ".ts")


def _kebab(name: str) -> str:
    out = re.sub(r"([A-Z])", lambda m: "-" + m.group(1).lower(), name)
    return "-" + out if out.startswith(("webkit-", "moz-", "ms-")) else out
STRIP_CHARS = "{}'\"`,;()"


@dataclass
class Doc:
    path: Path
    rel: str
    text: str
    kind: str  # markup, css, script or config
    _starts: list[int] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._starts = [0] + [m.end() for m in re.finditer("\n", self.text)]
        self.elements = _elements(self)
        self.decls = _decls(self)
        self.texts = _texts(self)

    def line(self, index: int) -> int:
        return bisect_right(self._starts, index)

    @property
    def tokens(self) -> list[tuple[int, str]]:
        return [(line, tok) for line, toks in self.elements for tok in toks]


def _clean_tokens(value: str) -> list[str]:
    out = []
    for raw in value.split():
        tok = raw.strip(STRIP_CHARS)
        if tok and not tok.startswith(("$", "{{", "@")) and len(tok) < 120:
            out.append(tok)
    return out


def _matching_paren(text: str, open_index: int) -> int:
    depth = 0
    for i in range(open_index, min(len(text), open_index + 5000)):
        ch = text[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i
    return min(len(text), open_index + 5000)


def _elements(doc: Doc) -> list[tuple[int, frozenset[str]]]:
    # Each element is one set of classes that land on the same node.
    found: list[tuple[int, frozenset[str]]] = []
    if doc.kind in ("markup", "script"):
        for m in CLASS_ATTR.finditer(doc.text):
            toks = _clean_tokens(m.group("v"))
            if toks:
                found.append((doc.line(m.start("v")), frozenset(toks)))
        for m in CLASS_CALL.finditer(doc.text):
            start = m.end() - 1
            end = _matching_paren(doc.text, start)
            toks: list[str] = []
            for lit in STRING_LIT.finditer(doc.text, start, end):
                toks.extend(_clean_tokens(lit.group(2)))
            if toks:
                found.append((doc.line(m.start()), frozenset(toks)))
    for m in APPLY.finditer(doc.text):
        toks = _clean_tokens(m.group(1))
        if toks:
            found.append((doc.line(m.start()), frozenset(toks)))
    return found


def _decls(doc: Doc) -> list[tuple[int, str, str]]:
    # CSS declarations as (line, property, value).
    regions: list[tuple[int, str]] = []
    if doc.kind == "css":
        regions.append((0, doc.text))
    else:
        for m in STYLE_BLOCK.finditer(doc.text):
            regions.append((m.start(1), m.group(1)))
        for m in STYLE_ATTR.finditer(doc.text):
            regions.append((m.start(2), m.group(2) + ";"))
        for m in STYLE_OBJECT.finditer(doc.text):
            body = m.group("jsx") if m.group("jsx") is not None else m.group("obj")
            start = m.start("jsx") if m.group("jsx") is not None else m.start("obj")
            for pair in STYLE_PAIR.finditer(body):
                regions.append((start + pair.start(), f"{_kebab(pair.group(1))}: {pair.group(3)};"))
        if doc.kind == "script" or doc.path.suffix.lower() in JS_STYLE_FILES:
            for m in TEMPLATE_LIT.finditer(doc.text):
                body = m.group(1)
                if ":" in body and ";" in body:
                    regions.append((m.start(1), body))
    out = []
    for offset, body in regions:
        for d in DECL.finditer(body):
            prop = d.group("prop").lower()
            out.append((doc.line(offset + d.start()), prop, d.group("val").strip()))
    return out


def _texts(doc: Doc) -> list[tuple[int, str]]:
    # Human-visible text: text between tags, plus sentence-like string literals.
    if doc.kind not in ("markup", "script"):
        return []
    blanked = SCRIPT_BLOCK.sub(lambda m: " " * len(m.group(0)), doc.text) if doc.kind == "markup" else doc.text
    blanked = STYLE_BLOCK.sub(lambda m: " " * len(m.group(0)), blanked)
    out = []
    for m in TEXT_NODE.finditer(blanked):
        chunk = " ".join(m.group(1).split())
        if chunk and any(c.isalpha() or ord(c) > 0x2000 for c in chunk):
            out.append((doc.line(m.start(1)), chunk))
    # String literals are read from the full text, so copy in <script> data (Vue, Svelte) counts.
    no_style = STYLE_BLOCK.sub(lambda m: " " * len(m.group(0)), doc.text)
    for m in STRING_LIT.finditer(no_style):
        value = " ".join(m.group(2).split())
        words = value.split()
        if len(value) < 12 or len(words) < 2:
            continue
        # Skip class lists and code-like strings.
        if sum(1 for w in words if "-" in w or ":" in w or "/" in w) > len(words) / 3:
            continue
        out.append((doc.line(m.start(2)), value))
    return out


def _kind(path: Path, text: str) -> str | None:
    name = path.name.lower()
    if name.endswith(".blade.php") or path.suffix.lower() in MARKUP_SUFFIXES:
        return "markup"
    if path.suffix.lower() in CSS_SUFFIXES:
        return "css"
    if name.startswith("tailwind.config."):
        return "config"
    if path.suffix.lower() in SCRIPT_SUFFIXES and any(h in text for h in SCRIPT_UI_HINTS):
        return "script"
    return None


def load_docs(root: str | Path) -> list[Doc]:
    root = Path(root)
    paths = [root] if root.is_file() else sorted(
        p for p in root.rglob("*")
        if p.is_file() and not any(part in SKIP_DIRS for part in p.relative_to(root).parts)
    )
    docs = []
    for path in paths:
        try:
            if path.stat().st_size > MAX_BYTES:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        kind = _kind(path, text)
        if kind is None:
            continue
        rel = path.name if root.is_file() else path.relative_to(root).as_posix()
        docs.append(Doc(path=path, rel=rel, text=text, kind=kind))
    return docs
