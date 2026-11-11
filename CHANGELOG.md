# Changelog

## 0.3.1

**Setup**

- `handmade init` registers the MCP server for VS Code, Cursor or Claude Code in one step. It keeps existing servers and, for VS Code, turns on server autostart.
- If an agent calls `handmade_check` without a brief, the check fails. It tells the agent to get the brief and rebuild. It also adds handmade's instructions to that editor's rules file. Nothing is written up front.

**Photos**

- The brief asks whether the user has their own photos or agrees to free stock photos.
- A new Images section in the brief describes each photo the page needs: subject, place and people.
- Hotlinked stock photos fail the check unless the user agreed to them or they are marked as placeholders. Agreed stock photos need a description in their alt text.

**New checks**

- Browser-default date, time, file and select controls are flagged.
- Images side by side with different heights are flagged in rendered mode.
- A PASS that still has notes now asks the agent to fix them.

**Better questions**

- A "barber shop" is read as a service business, not a retail shop. A "booking page" or "website" is read as a landing page.
- Example answers now fit the trade. A barber is no longer shown a cake order as an example.

**Design**

- Softer corners. Moods that used square corners now use small radii, and the brief asks for them on buttons, inputs, cards and images.

**Docs**

- Install commands now use PyPI: `pipx install handmade` or `pip install handmade`. A PyPI badge was added.
- A uv section covers `uvx`, `uv tool install` and the MCP server through uvx.
- `uvx handmade init` points the editor at uvx instead of a temporary cache path.
- Skill, Cursor rule and AGENTS.md setup commands work without cloning the repo by hand.
- The README no longer says handmade parses syntax trees. It reads source files with pattern matching.

**Project**

- The comma style test was removed. The docstring test stays.

## 0.3.0

**Asks instead of guessing**

- `handmade prompt` reads the product and place from the request and asks only what is missing.
- Questions fit the project. A bakery is asked about best sellers and hours, a clinic about privacy, a SACCO about trust.
- Vague answers such as "everyone" or "modern" get one follow-up. If still vague, they are not used.
- Skipped questions are listed in the brief under "Facts still missing". The AI must ask or leave a marked slot.
- The mood is suggested with a reason and Enter accepts it.
- `--fact key=value` gives any fact from the command line. `--fresh` ignores saved answers.
- Answers are saved in `handmade.system.json`, so the next screen reuses them and the same system.
- MCP: `handmade_design_brief` returns the questions first ("NEEDS INPUT"). The AI asks the user in its own words, then calls again with `answers`.
- A page name in the request wins. "Landing page for my bakery shop" is a landing page, not a shop.

**Finished, not plain**

- A craft standard for every screen type: frame, controls, states, charts and tables.
- New tokens: `raised`, `accent-strong`, `accent-soft`, soft status backgrounds, ten tinted greys and five chart colors.
- Two shadow levels and one depth rule per mood.
- The pilot dashboard and form were rebuilt to this standard. Both pass in source and in the browser.

**Project**

- `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md` and `ROADMAP.md`.
- Issue templates for bugs, false alarms, missed tells and ideas. A pull request template.
- Dependabot keeps the workflow actions up to date.
- Code comments use `#` instead of docstrings. A test keeps it that way.

**Fixed**

- Radius counting now resolves `var()` and shorthands, so two radii in variables no longer count as five.
- Rendered mode no longer reads transparent borders as black.
- `benchmark/bench.py prompts` no longer overwrites pilot folders that hold built results.

## 0.2.0

**New**

- `handmade check`: one PASS or FAIL. It combines the AI-default score with a whitelist of the design system.
- Request screening. AI-style asks and "ignore the rules" in a request are replaced or refused. Keep a real brand choice with `--allow`.
- Rendered mode (`--render`). Checks the page in headless Chrome, including runtime styles, real contrast and fonts that failed to load.
- `--save-system` writes `handmade.system.json`. Prompts also carry it as JSON.
- MCP tool `handmade_check`. The skill, the Cursor rule and `AGENTS.md` make the AI loop until PASS.
- The default mood now follows the product's words, so a bakery gets "warm".
- Benchmark kit in `benchmark/`.
- `TESTING.md` and `docs/how-it-works.md`.

**Better detection**

- Colors are judged by hue in any format: hex, `rgb()`, `hsl()`, `oklch()`, named colors and shadcn tokens.
- Reads React style objects, styled-components, Vue `:style`, Angular `[ngStyle]`, Tailwind config colors, Tailwind v4 `@theme` and `var()` chains.
- Font names match across variants, such as "Inter Variable".

**Fixed**

- One off-system violet button could pass the gate.
- A generated accent could match the error red.
- Muted text could fail contrast on tinted panels.
- Rendered findings repeated once per viewport.
- Soft gray shadows counted as glows.
- A broken `pyproject.toml` stopped `pip install`.
- Windows: files and console output now use UTF-8.

## 0.1.0

First version: the scanner with 40 tells, `prompt`, `fix`, `profile`, the MCP server, the agent skill and the GitHub Action.
