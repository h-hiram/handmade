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


class PageListTests(unittest.TestCase):
    # No browser needed: the list of pages to open, and how several pages merge into one result.
    def test_routes_and_urls_resolve_against_the_base(self):
        from handmade.render import page_urls
        urls = page_urls("http://localhost:3000", ["/pricing", "signup", "https://other.test/x", "/pricing", " "])
        self.assertEqual(urls, ["http://localhost:3000", "http://localhost:3000/pricing",
                                "http://localhost:3000/signup", "https://other.test/x"])

    def fake(self, url: str, font: str) -> dict:
        el = {"sel": "p", "tag": "p", "text": "hello world", "role": "", "href": False, "alt": False, "src": "",
              "altText": "", "x": 0, "y": 0, "w": 100, "h": 20, "font": font, "fontOk": True, "fontSize": "16px",
              "fontWeight": "400", "color": "rgb(36, 20, 30)", "bg": "rgba(0, 0, 0, 0)", "bgImage": "none",
              "effBg": "rgb(248, 246, 248)", "clip": "", "fill": "", "shadow": "none", "textShadow": "none",
              "filter": "none", "backdrop": "none", "radius": ["0px"] * 4, "border": "0px rgb(0, 0, 0)",
              "padding": ["0px"] * 4, "gap": "normal normal", "align": "start", "parent": "body",
              "parentIndex": 0, "siblings": 1}
        vp = {"title": "t", "text": "hello world", "vw": 1440, "els": [el]}
        return {"url": url, "desktop": vp, "phone": vp}

    def test_findings_and_conformance_merge_across_pages(self):
        from handmade.conform import load_system
        from handmade.render import render_conformance, render_scan
        pages = [self.fake("http://app/", "Alegreya Sans"), self.fake("http://app/pricing", "Inter")]
        report = render_scan("", data=pages)
        self.assertEqual(report.files, ["http://app/", "http://app/pricing"])
        self.assertEqual({f.file for f in report.findings if f.tell == "type.generic-font"}, {"http://app/pricing"})
        conf = render_conformance("", load_system(EXAMPLE / "handmade.system.json"), data=pages)
        self.assertFalse(conf.passed)
        self.assertEqual([o.value for o in conf.hard_offenders], ["inter"])
        self.assertIn("http://app/pricing", conf.hard_offenders[0].file)


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

    def test_uneven_images_are_caught(self):
        from handmade.render import collect
        data = collect(ROOT / "tests" / "fixtures" / "uneven")
        self.assertIn("layout.uneven-images", self.tells(data))
        self.assertNotIn("layout.uneven-images", self.tells(self.after))

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

    def test_several_pages_in_one_browser_session(self):
        from handmade.check import run_check
        result = run_check(EXAMPLE / "after.html", system_path=EXAMPLE / "handmade.system.json", render=True,
                           pages=["before.html"], ignore={"type.font-not-loaded"})
        self.assertEqual(len(result.pages), 2)
        self.assertFalse(result.passed)  # the AI page is one of the two, so the whole app fails
        self.assertIn("Checked 2 pages", result.text())
        self.assertTrue(any(f.file.endswith("before.html") for f in result.report.findings))
        self.assertFalse(any(f.file.endswith("after.html") for f in result.report.findings))

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
