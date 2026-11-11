# Render the README image from the example pages, so it always shows what handmade really produces.
#
#   pip install playwright && playwright install chromium
#   python scripts/hero_image.py
#
# The image holds only the two pages, side by side on white: the plain AI result of a request and
# the result of the same request through handmade. Scores and reasons live in the README text, not here.

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "saas"
OUT = ROOT / "docs" / "images" / "hero.png"
PAGE_WIDTH, PAGE_HEIGHT, GAP, SCALE = 1200, 860, 24, 1.5

PAGE = """<!doctype html><html><head><meta charset="utf-8"><style>
  * { margin:0; padding:0; box-sizing:border-box }
  body { background:#ffffff; width:__W__px; display:flex; gap:__GAP__px; align-items:flex-start }
  img { display:block; width:__PW__px; height:auto; outline:1px solid #d1d6db }
</style></head><body><img src="before.png" alt=""><img src="after.png" alt=""></body></html>"""


def main() -> int:
    from playwright.sync_api import sync_playwright
    sys.path.insert(0, str(ROOT / "src"))
    from handmade.render import _browser

    work = Path(tempfile.mkdtemp())
    width = PAGE_WIDTH * 2 + GAP
    (work / "compose.html").write_text(PAGE.replace("__W__", str(width)).replace("__GAP__", str(GAP))
                                       .replace("__PW__", str(PAGE_WIDTH)), encoding="utf-8")
    with sync_playwright() as pw:
        browser = _browser(pw)
        for name in ("before", "after"):
            page = browser.new_page(viewport={"width": PAGE_WIDTH, "height": PAGE_HEIGHT}, device_scale_factor=2)
            page.goto((EXAMPLE / f"{name}.html").as_uri(), wait_until="load")
            page.wait_for_timeout(2500)  # web fonts
            page.screenshot(path=str(work / f"{name}.png"))
            page.close()
        page = browser.new_page(viewport={"width": width, "height": PAGE_HEIGHT}, device_scale_factor=SCALE)
        page.goto((work / "compose.html").as_uri(), wait_until="load")
        page.wait_for_timeout(500)
        page.screenshot(path=str(OUT), full_page=True)
        browser.close()
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
