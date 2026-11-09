# Red-team tests: AI defaults hidden in ways a naive scanner misses must still be caught.

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))  # run tests without installing

from handmade.scan import scan  # noqa: E402

TRICKS = Path(__file__).resolve().parent / "fixtures" / "tricks"

EXPECTED = {
    "jsx-style": {"color.purple-gradient", "type.gradient-text"},
    "styled-components": {"color.purple-gradient", "deco.glassmorphism", "color.neon-glow"},
    "hsl-oklch": {"color.purple-gradient", "color.indigo-accent"},
    "var-indirection": {"color.purple-gradient"},
    "tailwind-alias": {"color.purple-gradient", "color.indigo-accent"},
    "tailwind-v4-theme": {"color.indigo-accent"},
    "shadcn-token": {"color.indigo-accent"},
    "vue-style": {"color.indigo-accent", "type.trend-font"},
    "angular-ngstyle": {"color.neon-glow", "color.purple-gradient"},
    "font-variants": {"type.generic-font"},
    "named-and-upper": {"color.indigo-accent"},
    "blade-class-directive": {"color.indigo-accent", "color.purple-gradient"},
}


class TrickTests(unittest.TestCase):
    def test_every_trick_is_caught(self):
        failures = []
        for name, expected in EXPECTED.items():
            found = {f.tell for f in scan(TRICKS / name).findings}
            missing = expected - found
            if missing:
                failures.append(f"{name}: missed {sorted(missing)}, found {sorted(found)}")
        self.assertFalse(failures, "\n" + "\n".join(failures))

    def test_corpus_has_no_untested_folders(self):
        self.assertEqual({p.name for p in TRICKS.iterdir() if p.is_dir()}, set(EXPECTED))


if __name__ == "__main__":
    unittest.main()
