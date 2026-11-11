# Set the version in every file that states it, in one step.
#
#   python scripts/bump_version.py 0.3.2
#
# Then review the diff, finish the CHANGELOG section, commit, and push the tag v0.3.2.
# The release workflow refuses a tag that does not match pyproject.toml, so this stays the one source of truth.

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def current() -> str:
    return re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M).group(1)


def set_version(new: str) -> list[str]:
    if not re.fullmatch(r"\d+\.\d+\.\d+", new):
        raise SystemExit(f"bump_version: {new!r} is not MAJOR.MINOR.PATCH")
    old = current()
    done = []

    def edit(rel: str, pattern: str, repl: str, count: int = 1) -> None:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        text, n = re.subn(pattern, repl, text, count=count, flags=re.M)
        if n == 0:
            raise SystemExit(f"bump_version: nothing to change in {rel}")
        path.write_text(text, encoding="utf-8")
        done.append(rel)

    edit("pyproject.toml", r'^version = "[^"]+"', f'version = "{new}"')
    edit("src/handmade/__init__.py", r'^__version__ = "[^"]+"', f'__version__ = "{new}"')
    server_path = ROOT / "server.json"
    server = json.loads(server_path.read_text(encoding="utf-8"))
    server["version"] = new
    for package in server.get("packages", []):
        package["version"] = new
    server_path.write_text(json.dumps(server, indent=2) + "\n", encoding="utf-8")
    done.append("server.json")
    changelog = ROOT / "CHANGELOG.md"
    text = changelog.read_text(encoding="utf-8")
    if f"\n## {new}\n" not in text:
        # Everything under "Unreleased" becomes this version. The heading stays for the next changes.
        text = text.replace("## Unreleased\n", f"## Unreleased\n\n## {new}\n", 1)
        changelog.write_text(text, encoding="utf-8")
        done.append("CHANGELOG.md")
    for rel in ("TESTING.md", "README.md"):
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        updated = text.replace(f"handmade {old}", f"handmade {new}").replace(f"prints {old}", f"prints {new}")
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            done.append(rel)
    return done


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: python scripts/bump_version.py NEW_VERSION   (current: {current()})")
        return 2
    for rel in set_version(argv[1]):
        print(f"updated {rel}")
    print(f"Now finish the CHANGELOG section, run the tests, commit, then: git tag v{argv[1]} && git push origin v{argv[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
