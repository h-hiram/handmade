import json
import tempfile
import unittest
from pathlib import Path

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # run tests without installing

from handmade.cli import main
from handmade.scan import scan
from handmade.tells import REGISTRY

FIX = Path(__file__).resolve().parent / "fixtures"
SLOP = FIX / "slop"
CLEAN = FIX / "clean"


def tells_in(path: Path) -> set[str]:
    return {f.tell for f in scan(path).findings}


class PerLanguageTests(unittest.TestCase):
    # Each language fixture must trigger the tells written into it.

    def check(self, name: str, expected: set[str]) -> None:
        found = tells_in(SLOP / name)
        missing = expected - found
        self.assertFalse(missing, f"{name} missed {sorted(missing)}; found {sorted(found)}")

    def test_html(self):
        self.check("index.html", {
            "color.purple-gradient", "type.gradient-text", "deco.blur-blob", "deco.pill-above-headline",
            "layout.centered-hero", "deco.emoji-icons", "deco.icon-tile", "copy.hype", "copy.placeholder",
            "copy.vanity-stats", "a11y.img-no-alt", "a11y.focus-removed", "color.neon-glow", "deco.hover-scale",
        })

    def test_css(self):
        self.check("styles.css", {
            "color.purple-gradient", "type.gradient-text", "deco.glassmorphism", "color.neon-glow",
            "space.off-grid", "a11y.focus-removed", "type.generic-font", "motion.no-reduced-motion",
            "motion.transition-all",
        } - {"motion.transition-all"})

    def test_blade(self):
        self.check("welcome.blade.php", {
            "color.purple-gradient", "layout.centered-hero", "deco.glassmorphism", "copy.generic-headline",
            "copy.hype", "deco.emoji-icons",
        })

    def test_angular_inline_component(self):
        self.check("dashboard.component.ts", {
            "layout.three-cards", "deco.rounded-shadow-everywhere", "color.indigo-accent", "a11y.focus-removed",
            "type.trend-font", "type.font-not-loaded", "space.off-grid", "deco.emoji-icons",
        } - {"deco.rounded-shadow-everywhere"})

    def test_vue(self):
        self.check("Pricing.vue", {
            "type.arbitrary-size", "layout.three-cards", "color.indigo-accent", "copy.hype", "copy.generic-headline",
        })

    def test_svelte(self):
        self.check("Hero.svelte", {
            "deco.grid-background", "layout.centered-hero", "color.indigo-accent", "color.one-off",
            "type.arbitrary-size", "copy.generic-headline",
        })

    def test_tsx(self):
        self.check("Features.tsx", {
            "deco.sparkle", "deco.stock-effects", "layout.bento", "copy.hype", "deco.glassmorphism",
            "space.arbitrary", "type.arbitrary-size", "color.indigo-accent",
        })


class ScoreTests(unittest.TestCase):
    def test_slop_project_scores_low(self):
        report = scan(SLOP)
        self.assertLess(report.score, 40)
        self.assertEqual(len(report.files), 7)

    def test_clean_project_has_no_tells(self):
        report = scan(CLEAN)
        self.assertEqual(report.findings, [], [f"{f.tell} {f.file}:{f.line}" for f in report.findings])
        self.assertEqual(report.score, 100)

    def test_every_tell_fires_somewhere_in_slop(self):
        found = tells_in(SLOP)
        never = {t.id for t in REGISTRY} - found - {"color.tasteful-default", "color.palette-sprawl", "layout.same-section-padding",
                                                    "layout.center-everything"}
        self.assertFalse(never, f"tells with no slop coverage: {sorted(never)}")

    def test_ignore_skips_a_category(self):
        report = scan(SLOP, ignore={"copy"})
        self.assertFalse(any(f.tell.startswith("copy.") for f in report.findings))

    def test_line_numbers_point_at_the_tell(self):
        report = scan(SLOP / "index.html")
        hit = next(f for f in report.findings if f.tell == "deco.blur-blob")
        line = (SLOP / "index.html").read_text(encoding="utf-8").splitlines()[hit.line - 1]
        self.assertIn("blur-3xl", line)


class EdgeCaseTests(unittest.TestCase):
    def write(self, name: str, text: str) -> Path:
        folder = Path(tempfile.mkdtemp())
        (folder / name).write_text(text, encoding="utf-8")
        return folder

    def test_cream_terracotta_palette(self):
        folder = self.write("a.css", ":root{--bg:#f5f0e8;--accent:#c2410c;} body{font-family:'Newsreader',serif}")
        self.assertIn("color.tasteful-default", tells_in(folder))

    def test_deliberate_focus_style_is_not_flagged(self):
        folder = self.write("a.html", '<button class="outline-none focus-visible:ring-2 focus-visible:ring-teal-700">Pay</button>')
        self.assertNotIn("a11y.focus-removed", tells_in(folder))

    def test_skips_node_modules(self):
        folder = self.write("ok.html", "<p>hi</p>")
        (folder / "node_modules").mkdir()
        (folder / "node_modules" / "x.html").write_text('<div class="from-purple-500 to-blue-500"></div>', encoding="utf-8")
        self.assertNotIn("color.purple-gradient", tells_in(folder))

    def test_plain_js_without_ui_is_ignored(self):
        folder = self.write("util.js", "export const add = (a, b) => a + b; // unlock seamless")
        self.assertEqual(scan(folder).files, [])

    def test_font_loaded_with_next_font_counts_as_loaded(self):
        folder = self.write("layout.tsx", "import { Literata } from 'next/font/google';\n"
                                          "export default () => <p className=\"font-['Literata']\">Hi</p>")
        self.assertNotIn("type.font-not-loaded", tells_in(folder))


class FalseAlarmTests(unittest.TestCase):
    # Patterns from GOV.UK Frontend, a human-designed system, must not be flagged.

    def write(self, name: str, text: str) -> Path:
        folder = Path(tempfile.mkdtemp())
        (folder / name).write_text(text, encoding="utf-8")
        return folder

    def test_scss_variables_are_not_fonts(self):
        folder = self.write("_t.scss", "@font-face { font-family: 'GDS Transport'; src: url(t.woff2); }\n"
                                       "$font-family: 'GDS Transport', arial;\n.a { font-family: $font-family; font-size: $size; }")
        report = scan(folder)
        self.assertFalse(any("$" in f.detail for f in report.findings), [f.detail for f in report.findings])
        self.assertNotIn("type.font-not-loaded", {f.tell for f in report.findings})
        self.assertNotIn("type.scale-sprawl", {f.tell for f in report.findings})

    def test_focus_ring_box_shadows_are_not_elevation(self):
        rules = "".join(f".f{i}:focus {{ box-shadow: 0 -2px #ffdd00, 0 {i}px #0b0c0c; }}\n" for i in range(1, 8))
        self.assertNotIn("space.shadow-sprawl", tells_in(self.write("a.css", rules)))

    def test_outline_zero_with_own_focus_style_is_fine(self):
        css = ".btn:focus { outline: 0; box-shadow: 0 0 0 3px #ffdd00; }"
        self.assertNotIn("a11y.focus-removed", tells_in(self.write("a.css", css)))

    def test_five_px_grid_is_a_grid(self):
        css = ".a{padding:5px 10px;margin:15px;gap:20px} .b{padding:25px;margin:30px 10px}"
        self.assertNotIn("space.off-grid", tells_in(self.write("a.css", css)))

    def test_single_debug_purple_is_not_an_accent(self):
        css = "body::before { content: 'debug'; color: rebeccapurple; } .btn { background: #0b6e4f; }"
        self.assertNotIn("color.indigo-accent", tells_in(self.write("a.css", css)))

    def test_small_centered_auth_heading_is_not_a_hero(self):
        html = ('<div class="text-center"><h1 class="text-2xl">Sign in</h1>'
                '<a href="/forgot">Forgot password</a><a href="/register">Create account</a></div>')
        self.assertNotIn("layout.centered-hero", tells_in(self.write("login.html", html)))

    def test_aria_selected_counts_as_focus_style(self):
        html = '<div class="outline-none aria-selected:bg-accent">Item</div>'
        self.assertNotIn("a11y.focus-removed", tells_in(self.write("a.html", html)))


class RealProjectLessonsTests(unittest.TestCase):
    # False alarms found by scanning real Lovable, v0 and Bolt projects.

    def write(self, name: str, text: str) -> Path:
        folder = Path(tempfile.mkdtemp())
        (folder / name).write_text(text, encoding="utf-8")
        return folder

    def test_amber_warning_badge_is_not_a_cream_palette(self):
        html = ('<div class="bg-amber-50 text-amber-700">Pending</div>'
                '<button class="bg-teal-700">Save</button><a class="text-teal-700">Docs</a>')
        self.assertNotIn("color.tasteful-default", tells_in(self.write("a.html", html)))

    def test_real_cream_terracotta_page_is_flagged(self):
        html = "".join('<section class="bg-stone-50"><a class="text-orange-700 border-orange-700">Go</a></section>' for _ in range(3))
        self.assertIn("color.tasteful-default", tells_in(self.write("a.html", html)))

    def test_radix_overlay_container_is_not_a_focus_problem(self):
        html = '<div class="z-50 rounded-md border p-4 outline-none data-[state=open]:animate-in">Menu</div>'
        self.assertNotIn("a11y.focus-removed", tells_in(self.write("popover.tsx", "export const P = () => (" + html + ")")))


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> tuple[int, str]:
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = main(list(args))
        return code, buf.getvalue()

    def test_json_output(self):
        code, out = self.run_cli("scan", str(SLOP), "--format", "json")
        data = json.loads(out)
        self.assertEqual(code, 0)
        self.assertIn("findings", data)
        self.assertEqual(data["score"], scan(SLOP).score)

    def test_fail_under_returns_1(self):
        code, _ = self.run_cli("scan", str(SLOP), "--fail-under", "80")
        self.assertEqual(code, 1)

    def test_github_annotations(self):
        _, out = self.run_cli("scan", str(SLOP), "--format", "github")
        self.assertIn("::warning file=index.html,line=", out)

    def test_tells_lists_registry(self):
        _, out = self.run_cli("tells")
        self.assertIn(f"{len(REGISTRY)} tells.", out)


if __name__ == "__main__":
    unittest.main()
