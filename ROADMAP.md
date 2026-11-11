# Roadmap

This is what comes next. Open an issue if you think something is missing or in the wrong order.

## Now: 0.3

- [x] Ask before writing. Missing facts are asked for or left as marked slots, never guessed.
- [x] Questions that fit the project: a bakery gets asked about best sellers, a clinic about privacy.
- [x] The MCP server hands its questions to your AI tool, which asks you in its own words.
- [x] A craft standard: states, real controls, chart colors, soft status colors, one depth rule per mood.
- [x] Rebuilt pilot dashboard and form to that standard.
- [x] `handmade init` connects the MCP server to VS Code, Cursor or Claude Code in one step. (0.3.1)
- [x] Listed in the official MCP Registry as `io.github.h-hiram/handmade`. (0.3.1)
- [x] Rendered checks cover several pages of a running app in one run, with `--page`. (0.3.2)

## Next: 0.4

- [ ] **Web playground.** Paste code, get the score and the fix prompt. Runs in the browser with Pyodide, so code never leaves your machine.
- [ ] **More moods.** For example "industrial" and "children".
- [ ] **Dark theme screenshots** in the docs and examples.
- [ ] **Swahili and French question sets** for the brief.
- [ ] **A `handmade export` command** that writes the design system into CSS variables or a Tailwind theme for you.

## Later

- [ ] VS Code extension that underlines tells and copies the fix prompt.
- [ ] A Claude Code plugin that installs the skill and the MCP server together.
- [ ] Figma tokens export from the design system.

## Good first issues

Small, clear tasks for a first pull request. Each one should take an evening or less.

- Add a tell for "every button has the same icon on the left".
- Add a tell for `animate-bounce` on call to action buttons.
- Add Svelte `class:` directive support to the extractor, with a test.
- Add questions for a "nonprofit" domain in `brief.py`.
- Add `--format md` to `handmade check`, for pasting into pull requests.
- Translate the README introduction into Swahili.
- Add a `tests/fixtures/tricks/` case you found in a real AI-built page.

## How releases work

A release goes out when a few fixes or one feature are ready. Every false alarm fixed counts. The changelog lists every change.
