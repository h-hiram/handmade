# Examples

## landing

One page built two ways, for an invented app called Duka Ledger. It tracks stock and sales for small shops in Kenya.

| File | What it is |
|---|---|
| `before.html` | A typical AI landing page. It uses the defaults found most often in real Lovable, v0 and Bolt projects. |
| `prompt.md` | The prompt handmade wrote for the same product. |
| `handmade.system.json` | The design system from that prompt. |
| `after.html` | The page built by following `prompt.md`. |

Try it:

```bash
handmade scan examples/landing/before.html    # score 19
handmade check examples/landing/before.html   # FAIL
handmade check examples/landing/after.html    # PASS
```

Open both HTML files in a browser to compare them. The fonts load from Google Fonts, so you need to be online.

## saas

The most common request AI tools get: a landing page for a software product. Built two ways from one request, `build a landing page for Taskline, a task tracker for small teams`.

| File | What it is |
|---|---|
| `before.html` | What the model does with the request alone: Inter, a purple gradient hero, a pill badge, three feature cards with emoji, invented stats and quotes. |
| `prompt.md` | The brief handmade wrote for the same request, with the facts given on the command line. |
| `handmade.system.json` | The design system from that brief. |
| `after.html` | The page built by following `prompt.md`. Facts nobody gave are left as marked slots. |

```bash
handmade check examples/saas/before.html   # FAIL, score 15
handmade check examples/saas/after.html    # PASS, score 100
```

The README image is rendered from these two files by `python scripts/hero_image.py`, so it always shows what the tool really produces.
