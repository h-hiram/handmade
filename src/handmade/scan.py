# Run every tell over a project and score it.

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .extract import load_docs
from .profile import Profile, build_profile
from .tells import REGISTRY, Context, Finding, Tell

CATEGORIES = ("typography", "color", "decoration", "layout", "spacing", "copy", "accessibility", "motion")


@dataclass
class Report:
    root: str
    profile: Profile
    findings: list[Finding]
    files: list[str]

    @property
    def triggered(self) -> list[Tell]:
        ids = {f.tell for f in self.findings}
        return [t for t in REGISTRY if t.id in ids]

    @property
    def score(self) -> int:
        # 100 means no tells found. Each triggered tell costs its weight once.
        return max(0, 100 - sum(t.weight for t in self.triggered))

    @property
    def verdict(self) -> str:
        s = self.score
        if s >= 85:
            return "Looks designed"
        if s >= 65:
            return "Some AI defaults"
        if s >= 40:
            return "Clearly AI defaults"
        return "Unedited AI output"

    def category_scores(self) -> dict[str, int]:
        out = {}
        for cat in CATEGORIES:
            total = sum(t.weight for t in REGISTRY if t.category == cat)
            hit = sum(t.weight for t in self.triggered if t.category == cat)
            out[cat] = round(100 * (total - hit) / total) if total else 100
        return out

    def to_dict(self) -> dict:
        return {
            "root": self.root,
            "score": self.score,
            "verdict": self.verdict,
            "categories": self.category_scores(),
            "files_scanned": len(self.files),
            "findings": [
                {"tell": f.tell, "file": f.file, "line": f.line, "detail": f.detail}
                for f in self.findings
            ],
            "tells": [
                {"id": t.id, "title": t.title, "category": t.category, "weight": t.weight, "fix": t.fix}
                for t in self.triggered
            ],
            "profile": self.profile.to_dict(),
        }


def scan(path: str | Path, ignore: set[str] | None = None) -> Report:
    docs = load_docs(path)
    profile = build_profile(docs)
    ctx = Context(docs=docs, profile=profile)
    findings: list[Finding] = []
    ignore = ignore or set()
    for t in REGISTRY:
        if t.id in ignore or t.category in ignore:
            continue
        seen = set()
        for f in t.check(ctx):
            key = (f.file, f.line, f.detail)
            if key not in seen:
                seen.add(key)
                findings.append(f)
    findings.sort(key=lambda f: (f.file, f.line, f.tell))
    return Report(root=str(path), profile=profile, findings=findings, files=[d.rel for d in docs])
