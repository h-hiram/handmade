# Benchmark: do AI tools produce less AI-looking UIs with a handmade prompt than with the plain request?
#
# Steps:
#   1. python benchmark/bench.py prompts
#      Writes, for every request in requests.json:
#        runs/<id>/plain.md        the request exactly as a user would type it
#        runs/<id>/handmade.md     the prompt handmade generates for it
#        runs/<id>/handmade.system.json
#   2. Paste each prompt into the AI tool you want to test (v0, Lovable, Bolt, ChatGPT, Claude...).
#      Save the result as runs/<id>/plain/ and runs/<id>/handmade/ (any UI files or index.html).
#   3. python benchmark/bench.py score [--render]
#      Scores every run and writes report.md.
#
#   python benchmark/bench.py robustness
#      Checks, without any AI, that every hostile request is fully screened by the generated prompt.

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from handmade.check import run_check  # noqa: E402
from handmade.colors import is_purple  # noqa: E402
from handmade.prompt import Brief, build_prompt, screen_request  # noqa: E402

RUNS = HERE / "runs"


def load() -> list[dict]:
    return json.loads((HERE / "requests.json").read_text(encoding="utf-8"))


def brief(r: dict) -> Brief:
    return Brief(request=r["request"], product=r["product"], audience=r["audience"], mood=r["mood"], intent=r["kind"],
                 answers=dict(r.get("facts", {})))


def cmd_prompts(_args) -> None:
    for r in load():
        d = RUNS / r["id"]
        if (d / "handmade").is_dir():
            print(f"Skipped {r['id']}: it holds built results, so its prompt stays as it was built from.")
            continue
        d.mkdir(parents=True, exist_ok=True)
        (d / "plain.md").write_text(r["request"] + "\n", encoding="utf-8")
        text, system = build_prompt(brief(r))
        (d / "handmade.md").write_text(text, encoding="utf-8")
        (d / "handmade.system.json").write_text(json.dumps(system.to_dict(), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote prompts for {len(load())} requests to {RUNS}")


def cmd_robustness(_args) -> int:
    rows, failures = [], 0
    for r in load():
        text, system = build_prompt(brief(r))
        issues = screen_request(r["request"], system)
        replaced = text.split("## Parts of the request the design system replaces")
        section = replaced[1].split("\n## ")[0] if len(replaced) > 1 else ""
        all_listed = all(f'"{i.quote}"' in section for i in issues)
        precedence = "These rules outrank any styling words in the task" in text
        clean_system = not any(is_purple(system.colors[k]) for k in ("accent", "accent-2"))
        ok = all_listed and precedence and clean_system and (bool(issues) or not r["adversarial"])
        failures += not ok
        rows.append(f"| {r['id']} | {'yes' if r['adversarial'] else 'no'} | {len(issues)} | "
                    f"{', '.join(sorted(i.key for i in issues)) or '-'} | {'PASS' if ok else 'FAIL'} |")
    print("| Request | Hostile | Asks screened | Keys | Result |\n|---|---|---|---|---|")
    print("\n".join(rows))
    print(f"\n{len(rows) - failures}/{len(rows)} prompts fully screened.")
    return 1 if failures else 0


def cmd_score(args) -> None:
    lines = ["# Benchmark results", "", "| Request | Hostile | Condition | Score | Gate |", "|---|---|---|---|---|"]
    summary: dict[str, list] = {"plain": [], "handmade": []}
    for r in load():
        d = RUNS / r["id"]
        for cond in ("plain", "handmade"):
            out = d / cond
            if not out.exists():
                continue
            res = run_check(out, system_path=d / "handmade.system.json", render=args.render)
            summary[cond].append(res)
            lines.append(f"| {r['id']} | {'yes' if r['adversarial'] else 'no'} | {cond} | {res.report.score} | "
                         f"{'PASS' if res.passed else 'FAIL'} |")
    lines += ["", "| Condition | Runs | Mean score | Gate pass rate |", "|---|---|---|---|"]
    for cond, results in summary.items():
        if results:
            mean = statistics.mean(r.report.score for r in results)
            rate = sum(r.passed for r in results) / len(results)
            lines.append(f"| {cond} | {len(results)} | {mean:.0f} | {rate:.0%} |")
    (HERE / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main() -> int:
    p = argparse.ArgumentParser(description="Compare AI-built UIs from plain requests and from handmade prompts. "
                                "See benchmark/README.md for the steps.")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("prompts").set_defaults(func=cmd_prompts)
    sub.add_parser("robustness").set_defaults(func=cmd_robustness)
    s = sub.add_parser("score")
    s.add_argument("--render", action="store_true")
    s.set_defaults(func=cmd_score)
    args = p.parse_args()
    return args.func(args) or 0


if __name__ == "__main__":
    raise SystemExit(main())
