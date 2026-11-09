# Changelog

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
