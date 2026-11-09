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
