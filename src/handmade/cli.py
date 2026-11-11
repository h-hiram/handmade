# handmade: find what makes a UI look AI-generated and get the prompt that fixes it.

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .prompt import Brief, build_fix_prompt, build_prompt
from .scan import CATEGORIES, Report, scan
from .system import MOODS
from .tells import REGISTRY, by_id


def _bar(value: int, width: int = 20) -> str:
    filled = round(value / 100 * width)
    return "#" * filled + "." * (width - filled)


def render_text(report: Report, verbose: bool) -> str:
    tells = by_id()
    out = [
        f"handmade {__version__}  scanned {len(report.files)} file{'' if len(report.files) == 1 else 's'} in {report.root}",
        "",
        f"Score {report.score}/100  {report.verdict}",
        "",
    ]
    for cat, val in report.category_scores().items():
        out.append(f"  {cat:<14} {_bar(val)} {val:>3}")
    if not report.findings:
        out += ["", "No tells found."]
        return "\n".join(out)
    out.append("")
    grouped: dict[str, list] = {}
    for f in report.findings:
        grouped.setdefault(f.tell, []).append(f)
    order = [t for t in REGISTRY if t.id in grouped]
    order.sort(key=lambda t: -t.weight)
    for t in order:
        out.append(f"[-{t.weight}] {t.title}  ({t.id})")
        items = grouped[t.id]
        shown = items if verbose else items[:3]
        for f in shown:
            where = f"{f.file}:{f.line}" if f.line else f.file
            out.append(f"      {where}  {f.detail}")
        if len(items) > len(shown):
            out.append(f"      ... {len(items) - len(shown)} more")
        out.append(f"      fix: {t.fix}")
        out.append("")
    out.append("Next: run `handmade fix` to get a prompt that repairs all of this.")
    _ = tells
    return "\n".join(out)


def render_markdown(report: Report) -> str:
    tells = by_id()
    lines = [f"## handmade report: {report.score}/100, {report.verdict}", "",
             "| Category | Score |", "|---|---|"]
    lines += [f"| {c} | {v} |" for c, v in report.category_scores().items()]
    lines += ["", "| Tell | Where | Detail |", "|---|---|---|"]
    for f in report.findings:
        where = f"`{f.file}:{f.line}`" if f.line else f"`{f.file}`"
        lines.append(f"| {tells[f.tell].title} | {where} | {f.detail.replace('|', '/')} |")
    return "\n".join(lines)


def render_github(report: Report) -> str:
    # GitHub Actions annotations, so tells show up inline on pull requests.
    tells = by_id()
    out = []
    for f in report.findings:
        t = tells[f.tell]
        loc = f"file={f.file},line={max(f.line, 1)}," if f.line else ""
        msg = f"{t.title}: {f.detail}. Fix: {t.fix}".replace("\n", " ")
        out.append(f"::warning {loc}title=handmade {t.id}::{msg}")
    out.append(f"::notice title=handmade score::{report.score}/100 {report.verdict}")
    return "\n".join(out)


def _ignore(args) -> set[str]:
    return {x.strip() for x in (args.ignore or "").split(",") if x.strip()}


def cmd_scan(args) -> int:
    if getattr(args, "render", False):
        from .render import render_scan
        report = render_scan(args.path, ignore=_ignore(args))
    else:
        report = scan(args.path, ignore=_ignore(args))
    if not report.files:
        print(f"No UI files found in {args.path}.", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    elif args.format == "md":
        print(render_markdown(report))
    elif args.format == "github":
        print(render_github(report))
    else:
        print(render_text(report, args.verbose))
    if args.fail_under is not None and report.score < args.fail_under:
        return 1
    return 0


def _saved(args, start: str | None = None) -> tuple[dict | None, Path | None]:
    # The project's saved handmade.system.json, unless --fresh was given.
    from .conform import find_system, load_system
    if getattr(args, "fresh", False):
        return None, None
    where = getattr(args, "project", None) or start or "."
    path = Path(args.save_system) if getattr(args, "save_system", None) and Path(args.save_system).is_file() else find_system(where)
    if path is None:
        return None, None
    try:
        return load_system(path), path
    except (ValueError, OSError):
        return None, None


def _gather(args, request: str, interactive: bool, start: str | None = None) -> tuple[Brief, "Facts", dict | None]:
    # Collect facts: saved answers, then the request's own words, then flags, then questions.
    from .brief import Facts, detect_domain, extract, interview
    from .prompt import detect_intent, mood_with_reason

    saved, saved_path = _saved(args, start)
    facts = Facts.from_dict((saved or {}).get("brief", {}))
    for key, value in extract(request).items():
        facts.values[key] = value
        facts.source[key] = "request"
    for key in ("product", "audience", "reference", "signature"):
        value = getattr(args, key, None)
        if value:
            facts.values[key] = value
            facts.source[key] = "flag"
    for item in getattr(args, "fact", None) or []:
        key, sep, value = item.partition("=")
        if not sep or not key.strip() or not value.strip():
            raise SystemExit(f"handmade: --fact needs KEY=VALUE, got {item!r}")
        facts.values[key.strip()] = value.strip()
        facts.source[key.strip()] = "flag"
        facts.vague.pop(key.strip(), None)
    if getattr(args, "mood", None):
        facts.values["mood"] = args.mood.lower()
        facts.source["mood"] = "flag"
    if saved:
        facts.values["mood"] = saved["mood"]
        facts.source["mood"] = "saved system"

    intent = args.kind or detect_intent(request, facts.get("product"))
    suggested, reason = mood_with_reason(" ".join([request, facts.get("product")]), intent)
    if interactive:
        err = sys.stderr
        known = {k: v for k, v in facts.values.items() if facts.source.get(k) in ("request", "saved", "flag")}
        if known:
            print("Already known:", file=err)
            for k, v in known.items():
                print(f"  {k}: {v}  ({facts.source.get(k)})", file=err)
        if saved_path:
            print(f"Reusing the design system in {saved_path}. Use --fresh to start over.", file=err)
        domain = detect_domain(" ".join([request, facts.get("product")]))
        topic = f" about this {domain.name} project" if domain.name != "general" else ""
        print(f"\nA few questions{topic}. Press Enter to skip any.\n", file=err)

        def ask(text: str) -> str:
            try:
                return input(text)
            except EOFError:
                return ""
        interview(request, facts, intent, suggested, ask, lambda s: print(s, file=err), mood_reason=reason)
        print("", file=err)

    mood = facts.get("mood")
    mood_source = {"flag": "chosen by the user", "answer": "chosen by the user",
                   "suggested, accepted": f"suggested because {reason} and accepted by the user"}.get(
        facts.source.get("mood", ""), "")
    core = {"product", "audience", "mood", "reference", "signature"}
    brief = Brief(request=request, product=facts.get("product"), audience=facts.get("audience"),
                  mood=mood if mood in MOODS else "", reference=facts.get("reference"),
                  signature=facts.get("signature"), intent=args.kind or "",
                  allow=tuple(a.strip().lower() for a in (args.allow or "").split(",") if a.strip()),
                  answers={k: v for k, v in facts.values.items() if k not in core},
                  vague=dict(facts.vague), mood_source=mood_source)
    return brief, facts, saved


def _emit(text: str, out: str | None) -> None:
    if out:
        Path(out).write_text(text, encoding="utf-8")
        print(f"Wrote {out}", file=sys.stderr)
    else:
        print(text)


def cmd_prompt(args) -> int:
    request = " ".join(args.request).strip()
    if not request:
        print("Give the request to rewrite, for example: handmade prompt \"build a booking page for a salon\"", file=sys.stderr)
        return 2
    brief, facts, saved = _gather(args, request, interactive=not args.no_input and sys.stdin.isatty())
    report = scan(args.project) if args.project else None
    text, system = build_prompt(brief, profile=report.profile if report else None, report=report,
                                variant=args.variant, saved_system=saved)
    _emit(text, args.out)
    _save_system(system, args.save_system, facts)
    return 0


def cmd_fix(args) -> int:
    report = scan(args.path, ignore=_ignore(args))
    if not report.files:
        print(f"No UI files found in {args.path}.", file=sys.stderr)
        return 2
    brief, facts, _saved_system = _gather(args, "", interactive=not args.no_input and sys.stdin.isatty(), start=args.path)
    text, system = build_fix_prompt(report, brief, variant=args.variant)
    _emit(text, args.out)
    _save_system(system, args.save_system, facts)
    return 0


def cmd_check(args) -> int:
    from .check import run_check
    result = run_check(args.path, system_path=args.system, min_score=args.min_score, ignore=_ignore(args),
                       render=args.render)
    if not result.report.files and not args.render:
        print(f"No UI files found in {args.path}.", file=sys.stderr)
        return 2
    if args.format == "json":
        print(json.dumps(result.to_dict(), indent=2))
    elif args.format == "github":
        print(render_github(result.report))
        if result.conformance:
            for o in result.conformance.offenders:
                loc = f"file={o.file},line={max(o.line, 1)}," if o.line else ""
                print(f"::warning {loc}title=handmade off-system {o.category}::{o.value} is not in the design system")
        print(f"::{'notice' if result.passed else 'error'} title=handmade check::{'PASS' if result.passed else 'FAIL'}")
    else:
        print(result.text())
    return 0 if result.passed else 1


def _save_system(system, path: str | None, facts=None) -> None:
    # Save the design system and the answers, so the next screen reuses both.
    if path:
        data = system.to_dict()
        if facts is not None:
            data["brief"] = facts.to_dict()
        Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Wrote {path}", file=sys.stderr)


def cmd_tells(args) -> int:
    if args.format == "json":
        print(json.dumps([{"id": t.id, "category": t.category, "weight": t.weight, "title": t.title,
                           "why": t.why, "fix": t.fix} for t in REGISTRY], indent=2))
        return 0
    for cat in CATEGORIES:
        print(cat.upper())
        for t in REGISTRY:
            if t.category == cat:
                print(f"  {t.id:<32} -{t.weight:<3} {t.title}")
        print()
    print(f"{len(REGISTRY)} tells.")
    return 0


def cmd_profile(args) -> int:
    report = scan(args.path)
    print(json.dumps(report.profile.to_dict(), indent=2))
    return 0


def _brief_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--product", help="what the product is, in one line")
    p.add_argument("--audience", help="who uses it and where")
    p.add_argument("--mood", choices=sorted(MOODS), help="overall feel")
    p.add_argument("--reference", help="a site, magazine, place or object you like")
    p.add_argument("--signature", help="the one thing people should remember")
    p.add_argument("--kind", choices=["landing", "dashboard", "form", "ecommerce", "docs", "portfolio", "app"],
                   help="type of screen (detected if not given)")
    p.add_argument("--variant", type=int, default=0, help="pick a different generated system (0, 1, 2...)")
    p.add_argument("--fact", action="append", default=[], metavar="KEY=VALUE",
                   help="any other fact, for example --fact goal='order a cake on WhatsApp' (repeatable)")
    p.add_argument("--allow", default="", help="deliberate brand choices the rules should keep, for example: purple,gradient")
    p.add_argument("--no-input", action="store_true",
                   help="ask nothing; missing facts are listed in the prompt for the AI to ask, never invented")
    p.add_argument("--fresh", action="store_true", help="ignore a saved handmade.system.json and start over")
    p.add_argument("-o", "--out", help="write the prompt to a file")
    p.add_argument("--save-system", metavar="FILE", help="also write the design system as JSON (use handmade.system.json)")


def cmd_init(args) -> int:
    from .editors import init
    editors = None
    if args.editor:
        editors = list(EDITOR_CHOICES[:-1]) if args.editor == "all" else [args.editor]
    for line in init(args.path, editors):
        print(line)
    print("")
    print("Next: open this folder in your editor and ask its AI for a UI.")
    print("The first time, the editor asks if you trust the handmade server. Say yes.")
    print("When the AI first calls a handmade tool, choose the option to always allow it.")
    return 0


EDITOR_CHOICES = ("vscode", "cursor", "claude", "all")


def cmd_mcp(args) -> int:
    from .mcp import main as mcp_main
    return mcp_main()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="handmade", description="Find what makes a UI look AI-generated and get the prompt that fixes it.")
    parser.add_argument("--version", action="version", version=f"handmade {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("scan", help="find AI design tells in a folder or file")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--format", choices=["text", "json", "md", "github"], default="text")
    p.add_argument("--fail-under", type=int, help="exit 1 if the score is below this (for CI)")
    p.add_argument("--ignore", help="comma-separated tell IDs or categories to skip")
    p.add_argument("-v", "--verbose", action="store_true", help="show every location")
    p.add_argument("--render", action="store_true",
                   help="check the rendered page in headless Chrome (path to .html, a folder or a URL)")
    p.set_defaults(func=cmd_scan)

    p = sub.add_parser("prompt", help="rewrite a UI request into a designer-grade prompt")
    p.add_argument("request", nargs="*")
    p.add_argument("--project", help="read fonts and colors from this existing project")
    _brief_args(p)
    p.set_defaults(func=cmd_prompt)

    p = sub.add_parser("fix", help="scan a project and write a prompt that repairs every tell found")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--ignore", help="comma-separated tell IDs or categories to skip")
    _brief_args(p)
    p.set_defaults(func=cmd_fix)

    p = sub.add_parser("check", help="PASS or FAIL: no AI defaults and everything comes from the design system")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--system", help="design system JSON (default: handmade.system.json in the folder or above)")
    p.add_argument("--min-score", type=int, default=85, help="minimum AI-default score to pass (default 85)")
    p.add_argument("--ignore", help="comma-separated tell IDs or categories to skip")
    p.add_argument("--render", action="store_true", help="check the rendered page in headless Chrome")
    p.add_argument("--format", choices=["text", "json", "github"], default="text")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("tells", help="list every tell the scanner knows")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.set_defaults(func=cmd_tells)

    p = sub.add_parser("init", help="connect handmade to VS Code, Cursor or Claude Code in this project")
    p.add_argument("path", nargs="?", default=".")
    p.add_argument("--editor", choices=EDITOR_CHOICES, help="which editor to set up (detected if not given)")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("mcp", help="run the MCP server over stdio (for AI tools)")
    p.set_defaults(func=cmd_mcp)

    p = sub.add_parser("profile", help="show the design tokens found in a project")
    p.add_argument("path", nargs="?", default=".")
    p.set_defaults(func=cmd_profile)
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to a legacy code page
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
