# Contributing to handmade

Thanks for helping. Small fixes are as welcome as big features.

## The fastest way to help

**Report a false alarm.** If handmade flags something a designer chose on purpose, that is a bug. Open a "False alarm" issue with the smallest snippet that shows it. Each false alarm becomes a test, so it never comes back.

**Report a miss.** If an AI-built page scores well but still looks generated, show us. Name the tell you see. A screenshot helps.

**Share a benchmark run.** Build the same request with and without handmade in your AI tool. Add both results under `benchmark/runs/<id>/`. Independent runs are the best evidence we can get.

## Set up

You need Python 3.10 or newer. There are no other dependencies.

```bash
git clone https://github.com/h-hiram/handmade
cd handmade
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e .
python -m unittest discover -s tests
```

Rendered mode needs Playwright. Install it only if you work on `render.py`:

```bash
pip install -e ".[render]" && playwright install chromium
```

## How the code is laid out

| File | What it does |
|---|---|
| `extract.py` | Reads files of every supported language and pulls out classes, CSS and text |
| `profile.py` | Builds a picture of the project: fonts, colors, variables, radii, shadows |
| `tells.py` | The registry of AI design tells. One function per tell |
| `scan.py` | Runs the tells and scores the project |
| `system.py` | Generates the design system: palette, fonts, scale, craft tokens |
| `brief.py` | Works out what is known and what to ask, so nothing gets guessed |
| `prompt.py` | Writes the design brief and the fix prompt |
| `conform.py` | Checks that a UI uses only values from the design system |
| `check.py` | The pass or fail gate |
| `render.py` | The same checks on a real page in headless Chrome |
| `mcp.py` | The MCP server |
| `cli.py` | The command line |

[docs/how-it-works.md](docs/how-it-works.md) explains the ideas behind each part.

## Adding a tell

1. Add a function in `tells.py` with the `@tell(...)` decorator. Give it an ID, a category, a weight, a short name, why it matters and how to fix it.
2. Add a failing example to `tests/fixtures/slop/` or a new folder in `tests/fixtures/tricks/`.
3. Add a clean example that must not trigger it. This matters more than the failing one.
4. Run the full test suite.

Keep weights honest. A tell that only some AI pages have should weigh less than one almost all of them have.

## Rules for pull requests

- One change per pull request.
- Every bug fix comes with a test that failed before the fix.
- No new runtime dependencies. handmade must run on plain Python.
- Write code comments with `#`. Do not use docstrings.
- Write docs in plain, short sentences. The project checks its own docs this way.
- Run `python -m unittest discover -s tests` before you push. CI runs it on Linux with Python 3.10, 3.12 and 3.13, plus the rendered-mode tests in a real browser.

## Releasing

1. Run `python scripts/bump_version.py X.Y.Z`. It sets the version in `pyproject.toml`, `src/handmade/__init__.py`, `server.json` and turns the "Unreleased" changelog entries into that version. A test fails if any of them disagree.
2. Finish the changelog section, run the tests and commit.
3. Push the tag: `git tag vX.Y.Z && git push origin vX.Y.Z`. The release workflow refuses a tag that does not match `pyproject.toml`. It publishes to PyPI, attaches `handmade.pyz` to the GitHub release, lists the MCP server in the registry and moves the `v0` tag.

## Good first issues

Look for the `good first issue` label. These are small and well described. Comment on the issue before you start, so two people do not do the same work.

## Questions

Open a discussion or an issue. 

By taking part, you agree to follow the [Code of Conduct](CODE_OF_CONDUCT.md).
