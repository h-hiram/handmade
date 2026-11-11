# `handmade init` and the fallback that adds instructions when an AI skips the brief.

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # run tests without installing

from handmade.editors import MARKER, init, write_instructions  # noqa: E402
from handmade.mcp import call_tool  # noqa: E402


def project(*folders: str) -> Path:
    root = Path(tempfile.mkdtemp())
    for name in folders:
        (root / name).mkdir(parents=True)
    return root


class InitTests(unittest.TestCase):
    def test_vscode_keeps_other_servers(self):
        root = project(".vscode")
        (root / ".vscode" / "mcp.json").write_text('{"servers": {"other": {"command": "x"}}}', encoding="utf-8")
        init(root, ["vscode"])
        data = json.loads((root / ".vscode" / "mcp.json").read_text(encoding="utf-8"))
        self.assertIn("other", data["servers"])
        self.assertEqual(data["servers"]["handmade"]["type"], "stdio")
        settings = json.loads((root / ".vscode" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(settings["chat.mcp.autostart"], "newAndOutdated")

    def test_settings_with_comments_are_left_alone(self):
        root = project(".vscode")
        original = '{\n  // my settings\n  "editor.fontSize": 14\n}\n'
        (root / ".vscode" / "settings.json").write_text(original, encoding="utf-8")
        done = init(root, ["vscode"])
        self.assertEqual((root / ".vscode" / "settings.json").read_text(encoding="utf-8"), original)
        self.assertTrue(any("skipped" in line for line in done))

    def test_cursor_and_claude(self):
        root = project()
        init(root, ["cursor", "claude"])
        self.assertIn("handmade", json.loads((root / ".cursor" / "mcp.json").read_text(encoding="utf-8"))["mcpServers"])
        self.assertIn("handmade", json.loads((root / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"])

    def test_init_writes_no_instruction_files(self):
        root = project(".vscode")
        init(root, ["vscode"])
        self.assertFalse((root / ".github" / "copilot-instructions.md").exists())


class UvxTests(unittest.TestCase):
    def test_one_off_uvx_run_points_the_editor_at_uvx(self):
        from unittest import mock
        import handmade.editors as editors
        with mock.patch.object(editors.sys, "executable", "/home/a/.cache/uv/archive-v0/abc/bin/python"), \
                mock.patch.object(editors.shutil, "which", return_value="/usr/local/bin/uvx"):
            self.assertEqual(editors.mcp_command(), ("uvx", ["--from", "handmade", "handmade-mcp"]))


class FallbackTests(unittest.TestCase):
    def test_instructions_are_written_once(self):
        root = project(".vscode")
        (root / ".github").mkdir()
        (root / ".github" / "copilot-instructions.md").write_text("# Our rules\n", encoding="utf-8")
        self.assertEqual(len(write_instructions(root)), 1)
        text = (root / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("# Our rules"))
        self.assertIn(MARKER, text)
        self.assertEqual(write_instructions(root), [])

    def test_check_without_a_brief_sends_the_ai_back(self):
        root = project(".vscode")
        (root / "index.html").write_text("<h1>Fades and line-ups</h1>", encoding="utf-8")
        text = call_tool("handmade_check", {"path": str(root)})
        self.assertTrue(text.startswith("handmade check: FAIL"))
        self.assertIn("handmade_design_brief", text)
        self.assertTrue((root / ".github" / "copilot-instructions.md").is_file())


if __name__ == "__main__":
    unittest.main()
