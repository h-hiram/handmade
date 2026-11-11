# The gate: one PASS or FAIL that combines the AI-default scan and design-system conformance.
#
# Used by `handmade check`, by the MCP tool handmade_check and by the agent skill.
# An AI agent is not done with UI work until this returns PASS.

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .conform import PASS_THRESHOLDS, Conformance, check_conformance, find_system, load_system
from .extract import load_docs
from .profile import build_profile
from .scan import Report, scan
from .tells import by_id

DEFAULT_MIN_SCORE = 85
# Signature AI defaults: any one of these fails the gate, whatever the score.
HARD_TELLS = {
    "color.purple-gradient", "color.indigo-accent", "color.neon-glow", "color.tasteful-default",
    "type.gradient-text", "type.generic-font", "type.trend-font", "deco.glassmorphism", "deco.stock-effects",
    "deco.emoji-icons", "deco.blur-blob", "layout.centered-hero", "copy.stock-photos",
}


@dataclass
class CheckResult:
    passed: bool
    report: Report
    conformance: Conformance | None
    system_path: str | None
    min_score: int
    rendered: bool = False
    pages: list[str] = field(default_factory=list)  # every page that was checked (rendered mode)

    @property
    def is_url(self) -> bool:
        return str(self.report.root).startswith(("http://", "https://"))

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "min_score": self.min_score,
            "score": self.report.score,
            "verdict": self.report.verdict,
            "rendered": self.rendered,
            "pages": list(self.pages),
            "system": self.system_path,
            "conformance": self.conformance.to_dict() if self.conformance else None,
            "findings": [f.__dict__ for f in self.report.findings],
        }

    def text(self, max_items: int = 12) -> str:
        tells = by_id()
        lines = [f"handmade check: {'PASS' if self.passed else 'FAIL'}", ""]
        if len(self.pages) > 1:
            lines.append(f"Checked {len(self.pages)} pages: " + ", ".join(self.pages))
            lines.append("")
        hard = sorted({tells[f.tell].title for f in self.report.findings if f.tell in HARD_TELLS})
        mark = "ok  " if self.report.score >= self.min_score and not hard else "FAIL"
        lines.append(f"{mark} AI defaults: score {self.report.score}/100 ({self.report.verdict}), "
                     f"needs {self.min_score} and no signature defaults")
        if hard:
            lines.append(f"     Signature AI defaults found (each one fails the check): {', '.join(hard)}")
        shown = 0
        for f in sorted(self.report.findings, key=lambda f: -tells[f.tell].weight):
            if shown >= max_items:
                lines.append(f"     ... {len(self.report.findings) - shown} more, run `handmade scan -v`")
                break
            where = f"{f.file}:{f.line}" if f.line else f.file
            lines.append(f"     - {tells[f.tell].title}: {where} {f.detail}. Fix: {tells[f.tell].fix}")
            shown += 1
        lines.append("")
        if self.conformance is None:
            lines.append("skip Design system: no handmade.system.json found, so only AI defaults were checked.")
            if self.is_url:
                lines.append("     For a URL, run the check from the project folder or pass --system handmade.system.json.")
            else:
                lines.append("     Create one with: handmade prompt \"...\" --save-system handmade.system.json")
                lines.append("     Built by an AI tool? Run `handmade init` in the project so the AI gets a brief first.")
        else:
            lines.append(f"Design system: {self.system_path}")
            for cat, need in PASS_THRESHOLDS.items():
                pct = self.conformance.percent(cat)
                seen = self.conformance.seen.get(cat, 0)
                mark = "ok  " if pct >= need else "FAIL"
                hard_here = [o for o in self.conformance.hard_offenders if o.category == cat]
                mark = "ok  " if pct >= need and not hard_here else "FAIL"
                extra = " (any off-system color with a hue or any off-system font, fails)" if hard_here else ""
                lines.append(f"{mark} {cat:<11} {pct:>3}% from the system ({seen} values), needs {need}%{extra}")
                offs = [o for o in self.conformance.offenders if o.category == cat]
                for o in offs[:5]:
                    times = f" x{o.count}" if o.count > 1 else ""
                    lines.append(f"     - {o.value}{times} at {o.file}:{o.line}")
                if len(offs) > 5:
                    lines.append(f"     ... {len(offs) - 5} more off-system values")
        lines.append("")
        if self.passed and self.conformance is None:
            lines.append("Done: no AI defaults above the threshold. The design system was not checked.")
        elif self.passed:
            lines.append("Done: no AI defaults above the threshold and everything comes from the design system.")
        if self.passed:
            if self.report.findings:
                lines.append("Notes are listed above. They do not block a PASS, but fix them if you can.")
        else:
            lines.append("NOT DONE. Fix every FAIL above, then run handmade check again.")
        return "\n".join(lines)


def system_for(path: str | Path, system_path: str | Path | None = None) -> Path | None:
    # The design system to check against. A URL has no folder, so the working directory stands in for it.
    if system_path:
        return Path(system_path)
    is_url = str(path).startswith(("http://", "https://"))
    return find_system(Path.cwd()) if is_url else find_system(path)


def run_check(path: str | Path, system_path: str | Path | None = None, min_score: int = DEFAULT_MIN_SCORE,
              ignore: set[str] | None = None, render: bool = False, pages: list[str] | None = None) -> CheckResult:
    # Raises ValueError for a bad system file or bad arguments, OSError for a missing one,
    # RuntimeError when rendered mode has no browser.
    pages = [p for p in (pages or []) if str(p).strip()]
    if pages and not render:
        raise ValueError("--page needs --render: extra pages are opened in the browser")
    sys_file = system_for(path, system_path)
    system = load_system(sys_file) if sys_file is not None else None
    allow_stock = bool(system) and system.get("brief", {}).get("answers", {}).get("photos") == "stock"
    if render:
        from .render import collect_many, page_urls, render_scan  # optional dependency (Playwright)
        urls = page_urls(path, pages)
        data = collect_many(urls)  # one browser session for every page and both checks
        report = render_scan(path, ignore=ignore, allow_stock=allow_stock, data=data)
    else:
        urls = []
        report = scan(path, ignore=ignore, allow_stock=allow_stock)
    conformance = None
    if system is not None:
        if render:
            from .render import render_conformance
            conformance = render_conformance(path, system, data=data)
        else:
            docs = load_docs(path)
            conformance = check_conformance(docs, build_profile(docs), system)
    hard = [f for f in report.findings if f.tell in HARD_TELLS]
    passed = report.score >= min_score and not hard and (conformance is None or conformance.passed)
    return CheckResult(passed=passed, report=report, conformance=conformance,
                       system_path=str(sys_file) if sys_file else None, min_score=min_score, rendered=render,
                       pages=urls)
