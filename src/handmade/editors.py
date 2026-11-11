# Connect handmade to AI editors with one command and repair the setup when an AI skips it.
#
# `handmade init` writes the MCP config for VS Code, Cursor and Claude Code.
# Instruction files are not written up front. They are written only when handmade sees
# that an AI built UI without asking for a brief first (see write_instructions).

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

EDITORS = ("vscode", "cursor", "claude")
ROOT_MARKERS = (".git", ".vscode", ".cursor", ".claude", "package.json", "composer.json", "pyproject.toml",
                "angular.json", "handmade.system.json")
MARKER = "<!-- handmade -->"

INSTRUCTIONS = f"""{MARKER}
## UI work (handmade)

For any UI work, use the handmade MCP tools:

1. Call handmade_design_brief with the user's request before writing any UI code.
   If it answers NEEDS INPUT, ask the user those questions in your own words.
   Then call it again with their replies in `answers`. Never answer the questions yourself.
2. Build exactly what the brief says. Save the design system with save_system_to set to the project folder.
3. Call handmade_check on what you built. Fix every FAIL and check again.
   Do not say the work is done until handmade_check returns PASS.
"""

CURSOR_RULE = f"""---
description: Design-first UI with handmade
alwaysApply: true
---

{INSTRUCTIONS}"""


def mcp_command() -> tuple[str, list[str]]:
    # A one-off `uvx handmade init` runs from uv's cache, which can be cleaned at any time.
    # Point the editor at uvx itself then, so the server is fetched again when needed.
    if "archive-v" in sys.executable.replace("\\", "/") and shutil.which("uvx"):
        return "uvx", ["--from", "handmade", "handmade-mcp"]
    # Otherwise prefer the handmade-mcp that belongs to this Python, so the editor runs this exact install.
    here = Path(sys.executable).parent
    for name in ("handmade-mcp", "handmade-mcp.exe"):
        if (here / name).is_file():
            return str(here / name), []
    found = shutil.which("handmade-mcp")
    if found:
        return str(Path(found).resolve()), []
    return sys.executable, ["-m", "handmade.mcp"]


def project_root(path: str | Path) -> Path:
    start = Path(path).resolve()
    folder = start if start.is_dir() else start.parent
    for candidate in (folder, *folder.parents[:4]):
        if any((candidate / m).exists() for m in ROOT_MARKERS):
            return candidate
    return folder


def detect(root: Path, default: bool = True) -> list[str]:
    # Editors with a footprint in the project. With default=True, an empty result becomes VS Code.
    found = []
    if (root / ".vscode").is_dir() or (root / ".github").is_dir():
        found.append("vscode")
    if (root / ".cursor").is_dir():
        found.append("cursor")
    if (root / ".claude").is_dir() or (root / "CLAUDE.md").is_file() or (root / ".mcp.json").is_file():
        found.append("claude")
    return found or (["vscode"] if default else [])


def _read_json(path: Path) -> dict | None:
    # Returns {} for a missing file and None for a file we must not touch (comments or broken JSON).
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def _write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def init(path: str | Path = ".", editors: list[str] | None = None) -> list[str]:
    # Write the MCP config for each editor. Keeps every other server and setting. Returns what it did.
    root = Path(path).resolve()
    command, args = mcp_command()
    entry = {"command": command, "args": args} if args else {"command": command}
    done = []
    for editor in editors or detect(root):
        if editor == "vscode":
            target = root / ".vscode" / "mcp.json"
            data = _read_json(target)
            if data is None:
                done.append(f"skipped {target}: it is not plain JSON. Add the handmade server by hand.")
            else:
                data.setdefault("servers", {})["handmade"] = {"type": "stdio", **entry}
                _write_json(target, data)
                done.append(f"wrote {target}")
            settings = root / ".vscode" / "settings.json"
            data = _read_json(settings)
            if data is None:
                done.append(f"skipped {settings}: it has comments. Add \"chat.mcp.autostart\": \"newAndOutdated\" by hand.")
            else:
                data["chat.mcp.autostart"] = "newAndOutdated"  # start the server when a chat needs it
                _write_json(settings, data)
                done.append(f"wrote {settings} (the server starts on its own when you chat)")
        elif editor in ("cursor", "claude"):
            target = root / (".cursor/mcp.json" if editor == "cursor" else ".mcp.json")
            data = _read_json(target)
            if data is None:
                done.append(f"skipped {target}: it is not plain JSON. Add the handmade server by hand.")
                continue
            data.setdefault("mcpServers", {})["handmade"] = entry
            _write_json(target, data)
            done.append(f"wrote {target}")
        else:
            raise ValueError(f"unknown editor {editor!r}, use one of: {', '.join(EDITORS)}")
    return done


def write_instructions(path: str | Path) -> list[Path]:
    # Called when an AI checked UI without a brief: tell that editor's AI to use handmade from now on.
    # Only editors that already have a footprint in the project get a file. Nothing is created on a guess.
    root = project_root(path)
    written = []
    targets = []
    for editor in detect(root, default=False):
        if editor == "vscode":
            targets.append((root / ".github" / "copilot-instructions.md", INSTRUCTIONS))
        elif editor == "cursor":
            targets.append((root / ".cursor" / "rules" / "handmade.mdc", CURSOR_RULE))
        elif editor == "claude":
            targets.append((root / "CLAUDE.md", INSTRUCTIONS))
    for target, text in targets:
        current = target.read_text(encoding="utf-8") if target.is_file() else ""
        if MARKER in current:
            continue  # already there, so the AI ignored it; writing it again would not help
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text((current.rstrip() + "\n\n" if current.strip() else "") + text, encoding="utf-8")
        written.append(target)
    return written
