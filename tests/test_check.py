# The gate must pass a page built from its system and fail any disguised departure from it.

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # run tests without installing

from handmade.check import run_check  # noqa: E402
from handmade.conform import load_system  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "landing"


class GateTests(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        shutil.copy(EXAMPLE / "after.html", self.dir / "index.html")
        shutil.copy(EXAMPLE / "handmade.system.json", self.dir / "handmade.system.json")
        self.page = (self.dir / "index.html").read_text(encoding="utf-8")

    def tamper(self, old: str, new: str) -> None:
        self.assertIn(old, self.page)
        (self.dir / "index.html").write_text(self.page.replace(old, new, 1), encoding="utf-8")

    def assert_fails(self, category: str | None = None):
        result = run_check(self.dir)
        self.assertFalse(result.passed, result.text())
        if category:
            self.assertLess(result.conformance.percent(category) if result.conformance else 0, 100, result.text())
        return result

    def test_clean_example_passes(self):
        result = run_check(self.dir)
        self.assertTrue(result.passed, result.text())

    def test_renamed_purple_variable_fails(self):
        self.tamper("--accent: #a43c7d;", "--accent: #7c3aed;")
        self.assert_fails("colors")

    def test_purple_hidden_in_oklch_fails(self):
        self.tamper("--accent: #a43c7d;", "--accent: oklch(0.55 0.25 285);")
        self.assert_fails("colors")

    def test_near_miss_color_fails(self):
        self.tamper("--accent: #a43c7d;", "--accent: #b04a8a;")
        self.assert_fails("colors")

    def test_swapped_font_fails_even_as_a_variant(self):
        self.tamper('font-family: "Alegreya Sans", sans-serif;', 'font-family: "Inter Variable", sans-serif;')
        self.assert_fails("fonts")

    def test_off_scale_font_size_fails(self):
        self.page = self.page.replace("h1 { font-size: 48px;", "h1 { font-size: 64px;")
        (self.dir / "index.html").write_text(self.page.replace(".fine { font-size: 16px;", ".fine { font-size: 15px;")
                                             .replace(".how h2 { font-size: 32px;", ".how h2 { font-size: 36px;"), encoding="utf-8")
        self.assert_fails("font sizes")

    def test_off_system_radius_fails(self):
        self.page = self.page.replace("border-radius: 8px", "border-radius: 20px").replace("border-radius: 12px", "border-radius: 20px")
        (self.dir / "index.html").write_text(self.page, encoding="utf-8")
        self.assert_fails("radii")

    def test_tailwind_palette_class_fails(self):
        self.tamper('<a class="primary"', '<a class="primary bg-violet-600"')
        self.assert_fails("colors")

    def test_one_sneaky_glow_fails(self):
        self.tamper('<a class="primary" href="#signup">', '<a class="primary" style="box-shadow: 0 0 24px #a43c7d" href="#signup">')
        self.assert_fails()

    def test_one_emoji_fails(self):
        self.tamper("Start a free month</a>", "Start a free month 🚀</a>")
        self.assert_fails()

    def test_one_glass_panel_fails(self):
        self.tamper(".ledger { background: var(--on-accent);",
                    ".ledger { backdrop-filter: blur(12px); background: rgba(255,255,255,.4);")
        self.assert_fails()

    def test_missing_system_still_checks_defaults(self):
        (self.dir / "handmade.system.json").unlink()
        result = run_check(self.dir)
        self.assertIsNone(result.conformance)
        self.assertTrue(result.passed)
        self.assertIn("no handmade.system.json found", result.text())

    def test_ai_page_fails_on_everything(self):
        shutil.copy(EXAMPLE / "before.html", self.dir / "index.html")
        result = run_check(self.dir)
        self.assertFalse(result.passed)
        for cat in ("fonts", "colors", "font sizes", "radii", "spacing"):
            self.assertLess(result.conformance.percent(cat), 90, cat)

    def test_system_can_be_read_from_a_prompt_file(self):
        data = load_system(EXAMPLE / "prompt.md")
        saved = json.loads((EXAMPLE / "handmade.system.json").read_text(encoding="utf-8"))
        saved.pop("brief", None)  # the user's answers are saved with the system, but are not part of it
        self.assertEqual(data, saved)


class StockPhotoPermissionTests(unittest.TestCase):
    def project(self, alt: str, photos: str | None) -> Path:
        import tempfile
        from handmade.system import build_system
        folder = Path(tempfile.mkdtemp())
        (folder / "index.html").write_text(f'<img src="https://images.unsplash.com/photo-1?w=800" alt="{alt}">',
                                           encoding="utf-8")
        data = build_system("warm", 7).to_dict()
        if photos:
            data["brief"] = {"answers": {"photos": photos}, "vague": {}, "source": {}}
        (folder / "handmade.system.json").write_text(json.dumps(data), encoding="utf-8")
        return folder

    def tells(self, folder: Path) -> set[str]:
        return {f.tell for f in run_check(folder).report.findings}

    def test_agreed_stock_photo_with_a_description_passes(self):
        self.assertNotIn("copy.stock-photos", self.tells(self.project("A barber fading a client's hair", "stock")))

    def test_agreed_stock_photo_without_a_description_fails(self):
        self.assertIn("copy.stock-photos", self.tells(self.project("Barber", "stock")))

    def test_stock_photo_without_agreement_fails(self):
        self.assertIn("copy.stock-photos", self.tells(self.project("A barber fading a client's hair", None)))


class RegistryMetadataTests(unittest.TestCase):
    # The MCP Registry rejects a publish when these drift apart.
    def test_server_json_matches_the_package(self):
        import re
        root = Path(__file__).resolve().parents[1]
        server = json.loads((root / "server.json").read_text(encoding="utf-8"))
        version = re.search(r'^version = "([^"]+)"', (root / "pyproject.toml").read_text(encoding="utf-8"), re.M).group(1)
        self.assertEqual(server["version"], version)
        self.assertEqual(server["packages"][0]["version"], version)
        self.assertLessEqual(len(server["description"]), 100)
        self.assertIn(f"mcp-name: {server['name']}", (root / "README.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
