# The gate: one PASS or FAIL that combines the AI-default scan and design-system conformance.
#
# Used by `handmade check`, by the MCP tool handmade_check and by the agent skill.
# An AI agent is not done with UI work until this returns PASS.

from __future__ import annotations

from dataclasses import dataclass
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
    "deco.emoji-icons", "deco.blur-blob", "layout.centered-hero",
}


@dataclass
class CheckResult:
    passed: bool
    report: Report
    conformance: Conformance | None
    system_path: str | None
    min_score: int
    rendered: bool = False

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "min_score": self.min_score,
            "score": self.report.score,
            "verdict": self.report.verdict,
            "rendered": self.rendered,
            "system": self.system_path,
            "conformance": self.conformance.to_dict() if self.conformance else None,
            "findings": [f.__dict__ for f in self.report.findings],
        }

    def text(self, max_items: int = 12) -> str:
        tells = by_id()
        lines = [f"handmade check: {'PASS' if self.passed else 'FAIL'}", ""]
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
            lines.append("     Create one with: handmade prompt \"...\" --save-system handmade.system.json")
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
        if self.passed:
            lines.append("Done: no AI defaults above the threshold and everything comes from the design system.")
        else:
            lines.append("NOT DONE. Fix every FAIL above, then run handmade check again.")
        return "\n".join(lines)


def run_check(path: str | Path, system_path: str | Path | None = None, min_score: int = DEFAULT_MIN_SCORE,
              ignore: set[str] | None = None, render: bool = False) -> CheckResult:
    if render:
        from .render import render_scan  # optional dependency (Playwright)
        report = render_scan(path, ignore=ignore)
    else:
        report = scan(path, ignore=ignore)
    sys_file = Path(system_path) if system_path else find_system(path)
    conformance = None
    if sys_file is not None:
        system = load_system(sys_file)
        if render:
            from .render import render_conformance
            conformance = render_conformance(path, system)
        else:
            docs = load_docs(path)
            conformance = check_conformance(docs, build_profile(docs), system)
    hard = [f for f in report.findings if f.tell in HARD_TELLS]
    passed = report.score >= min_score and not hard and (conformance is None or conformance.passed)
    return CheckResult(passed=passed, report=report, conformance=conformance,
                       system_path=str(sys_file) if sys_file else None, min_score=min_score, rendered=render)
