# Rendered-page mode. Skipped when Playwright or a Chrome browser is not available.

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # run tests without installing

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "landing"
RUNTIME = ROOT / "tests" / "fixtures" / "runtime"


def _browser_available() -> bool:
    try:
        from handmade.render import collect
        collect(RUNTIME)
        return True
    except Exception:
        return False


AVAILABLE = _browser_available()


@unittest.skipUnless(AVAILABLE, "Playwright with Chrome or Chromium is not available")
class RenderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from handmade.render import collect
        cls.runtime = collect(RUNTIME)
        cls.before = collect(EXAMPLE / "before.html")
        cls.after = collect(EXAMPLE / "after.html")

    def tells(self, data, ignore=()):
        from handmade.render import render_scan
        return {f.tell for f in render_scan("", ignore=set(ignore), data=data).findings}

    def test_runtime_tricks_invisible_to_source_are_caught(self):
        from handmade.scan import scan
        self.assertEqual(scan(RUNTIME).findings, [])
        found = self.tells(self.runtime)
        self.assertTrue({"color.purple-gradient", "color.neon-glow", "type.font-not-loaded"} <= found, found)

    def test_ai_page_renders_its_defaults(self):
        found = self.tells(self.before)
        self.assertTrue({"color.purple-gradient", "type.gradient-text", "deco.glassmorphism", "deco.blur-blob",
                         "layout.centered-hero", "layout.three-cards", "a11y.faint-text", "deco.emoji-icons",
                         "copy.hype"} <= found, found)

    def test_redesigned_page_is_clean(self):
        # Fonts come from Google Fonts; a sandbox without network cannot load them.
        self.assertEqual(self.tells(self.after, ignore=("type.font-not-loaded",)), set())

    def test_rendered_conformance(self):
        from handmade.conform import load_system
        from handmade.render import render_conformance
        system = load_system(EXAMPLE / "handmade.system.json")
        self.assertTrue(render_conformance("", system, data=self.after).passed)
        before = render_conformance("", system, data=self.before)
        self.assertFalse(before.passed)
        self.assertTrue(before.hard_offenders)


if __name__ == "__main__":
    unittest.main()
