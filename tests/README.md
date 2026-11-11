# Tests

Run them all from the project folder:

```bash
python -m unittest discover -s tests -v
```

The tests run without installing handmade. The 4 rendered-mode tests are skipped when Playwright and a browser are missing.

## Test files

| File | What it checks |
|---|---|
| `test_scanner.py` | Tells fire in every language. Known human-designed patterns do not trigger false alarms. |
| `test_tricks.py` | Every disguise in `fixtures/tricks/` is caught. |
| `test_check.py` | The gate passes a correct page and fails each of 10 small tampers. |
| `test_prompt.py` | Request screening, mood choice, contrast of every generated palette, craft tokens and reuse of project tokens. |
| `test_brief.py` | Facts read from the request, domain questions, vague answers and missing facts listed instead of invented. |
| `test_mcp.py` | The MCP server, started as a separate process the way AI tools start it, including the ask-first flow. |
| `test_editors.py` | `handmade init` and the fallback that adds instructions when an AI skips the brief. |
| `test_style.py` | House style: `#` comments instead of docstrings. |
| `test_render.py` | Rendered mode in headless Chrome. |

## Fixtures

| Folder | What it holds |
|---|---|
| `fixtures/slop/` | Typical AI output in HTML, CSS, Blade, Angular, Vue, Svelte and TSX. Should score low. |
| `fixtures/clean/` | A hand-designed page. Must score 100. |
| `fixtures/tricks/` | 12 folders, each hiding AI defaults a different way. |
| `fixtures/runtime/` | A page that adds its AI defaults with JavaScript. Clean in source, caught when rendered. |

## Adding a test

- **A new tell:** add an example to a file in `fixtures/slop/` and an assertion in `test_scanner.py`.
- **A new disguise:** add a folder to `fixtures/tricks/` and its expected tells to `EXPECTED` in `test_tricks.py`.
- **A false alarm you fixed:** add the snippet as a test in `test_scanner.py`, so it cannot come back.
