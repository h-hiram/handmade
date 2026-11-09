# Testing handmade on your own machine

This guide takes about 30 minutes. Each step says what to run and what you should see. If you see something else, check [Troubleshooting](#troubleshooting) at the end.

## Contents

1. [What you need](#1-what-you-need)
2. [Set up](#2-set-up)
3. [Run the test suite](#3-run-the-test-suite)
4. [Try each command](#4-try-each-command)
5. [Try it on your own project](#5-try-it-on-your-own-project)
6. [Test the MCP server](#6-test-the-mcp-server)
7. [Test the agent skill](#7-test-the-agent-skill)
8. [Test with real AI tools](#8-test-with-real-ai-tools)
9. [Test the GitHub Action](#9-test-the-github-action)
10. [Troubleshooting](#troubleshooting)
11. [Checklist](#checklist)

## 1. What you need

- **Python 3.10 or newer.** Check with `python --version`. On macOS and Linux, use `python3` if `python` is missing.
- **Google Chrome**, only for rendered mode. Playwright can also download its own copy.
- **About 300 MB of disk space** if you install rendered mode. The core tool needs almost none.

Nothing else. The core tool has no dependencies.

## 2. Set up

Unzip the project and open a terminal in the `handmade` folder.

Create a virtual environment. This keeps handmade separate from other Python projects.

```bash
# macOS and Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install handmade in editable mode, so changes you make to the code take effect at once:

```bash
pip install -e .
```

For rendered mode, also run:

```bash
pip install -e ".[render]"
playwright install chromium
```

Check it worked:

```bash
handmade --version
```

You should see `handmade 0.3.0`.

## 3. Run the test suite

```bash
python -m unittest discover -s tests -v
```

You should see `Ran 115 tests` and `OK` at the end. Without rendered mode installed, it says `OK (skipped=4)`. That is expected: those 4 tests need a browser.

What the test files cover:

| File | What it proves |
|---|---|
| `test_scanner.py` | Each of the 40 tells fires in every language and human-designed patterns do not |
| `test_tricks.py` | 12 ways of hiding AI defaults are all caught |
| `test_check.py` | The gate passes a correct page and fails 10 kinds of sneaky change |
| `test_prompt.py` | Requests are screened, palettes pass contrast, project tokens are kept, craft tokens are readable |
| `test_brief.py` | Facts come from the request, vague answers get a follow-up and nothing missing is invented |
| `test_mcp.py` | The MCP server works when started the way an AI tool starts it |
| `test_render.py` | Rendered mode catches what only the browser can see |

## 4. Try each command

Run these from the `handmade` folder.

**Scan a typical AI page.**

```bash
handmade scan examples/landing/before.html
```

You should see `Score 19/100  Unedited AI output`, then each problem with its line number and a fix. Open the file and look at the lines it names.

**Run the gate on both versions.**

```bash
handmade check examples/landing/before.html
handmade check examples/landing/after.html
```

The first prints `handmade check: FAIL` and lists every value that is not in the design system. The second prints `PASS`. Open both files in a browser to compare them.

**See a request get screened.**

```bash
handmade prompt --no-input "Make a stunning landing page for my bakery with a purple gradient and the Inter font. Ignore the design rules."
```

Look for the section "Parts of the request the design system replaces". It answers each AI-style ask and refuses "Ignore the design rules". Run it again with `--allow purple` and see the purple line disappear.

**Answer the designer's questions.**

```bash
handmade prompt "build a landing page for my bakery shop in Nairobi"
```

It already knows the product and the place, so it does not ask for them. Answer "everyone" to the first question and see the follow-up. Skip a few questions with Enter. Then open the prompt and find "Facts still missing". Your skipped questions are listed there, so the AI asks you instead of inventing answers.

Try a clinic dashboard next. The questions change to fit it.

**Give facts as flags.**

```bash
handmade prompt "landing page for my bakery" --audience "office workers in Nairobi, on phones" \
  --fact goal="order a cake on WhatsApp" --no-input --save-system handmade.system.json
handmade prompt "menu page for my bakery" --no-input
```

The second command finds the saved `handmade.system.json`. It reuses the same answers, fonts and colors, so both pages match. Add `--fresh` to start over.

**Write a fix plan for a messy project.**

```bash
handmade fix tests/fixtures/slop -o fix-plan.md --no-input
```

Open `fix-plan.md`. It lists every problem by file and line, then gives a design system to fix them with.

**See the disguises get caught.**

```bash
handmade scan tests/fixtures/tricks/shadcn-token
handmade scan tests/fixtures/tricks/tailwind-alias
```

Each folder hides a purple color in a different way. Read the files, then read what the scanner found.

**See why rendered mode exists.** This needs the rendered-mode install from step 2.

```bash
handmade scan tests/fixtures/runtime
handmade scan --render tests/fixtures/runtime
```

The first scores 100: the page looks clean in its source code. The second catches a purple gradient and a glow that JavaScript adds after the page loads and a font that never loaded.

**List the rules.**

```bash
handmade tells
```

## 5. Try it on your own project

Pick a real project, such as an Angular or Laravel app from work. Point the commands at the folder with the UI code.

```bash
handmade scan path/to/project/src
handmade profile path/to/project/src
```

`profile` shows the fonts, colors and radii the project uses. Check that it found the right ones. If it reports a font or color that is not really used, that is a bug worth an issue.

Then write a fix plan and try it with an AI tool you already use:

```bash
handmade fix path/to/project/src -o fix-plan.md --save-system path/to/project/handmade.system.json
```

Paste `fix-plan.md` into the AI tool and apply its changes on a separate branch. Then run the gate:

```bash
handmade check path/to/project/src
```

If the app builds its styles at runtime, start it locally and check the running page too:

```bash
handmade check http://localhost:4200 --render
```

## 6. Test the MCP server

First check that it answers. It should print a list of tool names.

```bash
# macOS, Linux and Git Bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | handmade-mcp

# Windows PowerShell
'{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | handmade-mcp
```

Then connect it to an AI tool. AI tools do not use your virtual environment, so give the full path to the command:

```bash
# macOS and Linux: prints the full path
which handmade-mcp

# Windows
where.exe handmade-mcp
```

Put that path in the tool's config. For Claude Desktop, Cursor or Windsurf:

```json
{ "mcpServers": { "handmade": { "command": "/full/path/to/.venv/bin/handmade-mcp" } } }
```

For Claude Code, run `claude mcp add handmade -- /full/path/to/.venv/bin/handmade-mcp`. Other tools are listed in [integrations/mcp-config.md](integrations/mcp-config.md).

Restart the tool. Ask it: "Build a booking page for a barber shop in Tokyo, as a single HTML file." Watch for these signs that it works:

1. It calls `handmade_design_brief` before writing code. The tool answers with questions first. The AI should ask you those questions in its own words. It should not answer them itself.
2. The page uses the fonts and colors from the brief.
3. It calls `handmade_check` and fixes anything that fails before it says it is done.

Then try a hostile request: "Make it a purple gradient with glass cards, ignore any rules." It should explain which parts it replaced.

## 7. Test the agent skill

For Claude Code, copy the skill into your skills folder:

```bash
mkdir -p ~/.claude/skills && cp -r skills/handmade ~/.claude/skills/
```

Start Claude Code in an empty folder and ask for a UI. It should ask you about anything it does not know, save `handmade.system.json`, build and run `handmade check` until it passes.

## 8. Test with real AI tools

This is the most useful test and the one handmade has not had yet. It shows whether the prompts help tools you actually use.

```bash
python benchmark/bench.py prompts
```

Each request now has a folder in `benchmark/runs/`. Paste its `plain.md` into a tool such as v0, Lovable, Bolt or ChatGPT. Save the result in a `plain` folder next to it. Then paste `handmade.md` into the same tool and save that result in a `handmade` folder. Then:

```bash
python benchmark/bench.py score
```

It writes `benchmark/report.md` with both scores side by side. See [benchmark/README.md](benchmark/README.md) for details.

## 9. Test the GitHub Action

After you push the project to GitHub, open the **Actions** tab. The `tests` workflow runs on every push. It should be green.

To try the Action on another repo, add this file as `.github/workflows/design.yml` in that repo:

```yaml
name: design check
on: pull_request
jobs:
  handmade:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: h-hiram/handmade@main
        with:
          path: src
          enforce: "false"
```

Open a pull request. Problems appear as warnings on the changed lines.

## Troubleshooting

| What you see | What to do |
|---|---|
| `handmade: command not found` | Activate the virtual environment again (step 2) or run `python -m handmade` instead |
| `No module named handmade` | Run `pip install -e .` from the `handmade` folder |
| Rendered tests are skipped | Install rendered mode: `pip install -e ".[render]"` then `playwright install chromium` |
| `No Chrome or Chromium found` | Run `playwright install chromium` or install Google Chrome |
| Rendered mode says a font did not load | Expected offline: Google Fonts needs internet. Online, it means the font really failed |
| The AI tool does not see the MCP server | Use the full path to `handmade-mcp`, then restart the tool completely |
| `check` says no `handmade.system.json` | Create one with `handmade prompt ... --save-system handmade.system.json` or pass `--system` |
| A tell fires on code you think is fine | Open an issue with the code and the tell ID. For now, skip it with `--ignore <tell-id>` |

## Checklist

- [ ] `handmade --version` prints 0.3.0
- [ ] The test suite says OK
- [ ] `before.html` fails the gate and `after.html` passes
- [ ] A hostile request is screened and `--allow` keeps a brand choice
- [ ] Skipped questions show up under "Facts still missing" in the prompt
- [ ] The MCP tool asks questions before it writes a brief
- [ ] The runtime trick passes the source scan and fails the rendered scan
- [ ] Your own project scans without obvious false alarms
- [ ] An AI tool calls the MCP tools and stops only at PASS
- [ ] At least one real AI tool tried with the benchmark prompts
