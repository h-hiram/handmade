# Release hygiene: every place that states the version agrees, so a tag never ships mismatched metadata.

import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # run tests without installing

ROOT = Path(__file__).resolve().parents[1]


def pyproject_version() -> str:
    return re.search(r'^version = "([^"]+)"', (ROOT / "pyproject.toml").read_text(encoding="utf-8"), re.M).group(1)


class VersionTests(unittest.TestCase):
    def test_every_version_matches_pyproject(self):
        from handmade import __version__
        version = pyproject_version()
        self.assertEqual(__version__, version, "src/handmade/__init__.py")
        server = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
        self.assertEqual(server["version"], version, "server.json")
        self.assertEqual(server["packages"][0]["version"], version, "server.json packages")

    def test_changelog_has_a_section_for_this_version(self):
        text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(f"\n## {pyproject_version()}\n", text, "add a CHANGELOG section for this version")

    def test_bump_script_touches_every_file(self):
        # The script is the one way to change the version, so it must know every file the test above reads.
        script = (ROOT / "scripts" / "bump_version.py").read_text(encoding="utf-8")
        for name in ("pyproject.toml", "src/handmade/__init__.py", "server.json", "CHANGELOG.md"):
            self.assertIn(name, script)


if __name__ == "__main__":
    unittest.main()
