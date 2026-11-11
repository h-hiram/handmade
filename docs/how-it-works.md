# How handmade works

This page explains the ideas behind handmade and where each one lives in the code. Read it before changing anything.

## The problem

A language model writes code one choice at a time. At each step it tends to pick the most common choice it has seen. For interfaces, the most common choices are Inter, an indigo button, a purple gradient and three cards in a row. Every model makes the same picks, so their pages look alike.

A designer works the other way round. They decide on a type scale, a palette, spacing and a layout first. Then they build. Everything on the page traces back to a decision.

handmade makes the model work like the designer and checks that it did.

## The four locks

1. **Ask, never guess.** The brief is built from facts the user gave. Anything missing is asked for or listed so the AI asks. It is never filled in.
2. **Screen the request.** A request can ask for the defaults ("purple gradient, Inter") or try to switch the rules off ("ignore the design rules"). Each such phrase gets a concrete replacement. The refusal of "ignore the rules" cannot be turned off.
3. **Give the model a design system.** Fonts, a type scale, colors, spacing and radii, written into the prompt and saved as `handmade.system.json`.
4. **Gate the result.** `handmade check` fails if the code uses anything outside the system or any signature AI default.

The first three locks make good output likely. The fourth makes bad output visible, so an AI agent cannot call the work done until it is fixed.

## The flow

```text
request ──> ask ──> screen ──> prompt + handmade.system.json ──> AI builds ──> check ──> PASS
                                                              ^           │
                                                              └── fix ────┘ FAIL
```

## The parts

### Reading code: `extract.py`

Finds UI files and pulls out three things from each one:

- **Elements:** the classes on each element. It reads `class`, `className`, `:class`, `[ngClass]`, Blade `@class` and `cn()` or `clsx()` calls.
- **Declarations:** CSS property and value pairs. It reads CSS files, `<style>` blocks, `style=""`, React `style={{ }}`, Vue `:style`, Angular `[ngStyle]` and CSS-in-JS template strings.
- **Text:** what a user would read. It reads text between tags and sentence-like strings in code.

Every item keeps its line number, so findings point to the right place.

### The project's choices: `profile.py`

Builds a summary of what the project already uses: fonts, colors, CSS variables, Tailwind color names and gradients from `tailwind.config` or `@theme`. It also resolves `var(--x)` and Tailwind names like `bg-brand-600` to real colors. This is how a renamed purple gets found.

### Colors: `colors.py`

Reads any CSS color format and turns it into hex: hex, `rgb()`, `hsl()`, `oklch()`, `oklab()`, color names and shadcn's `222 84% 5%` style. It then judges colors by hue and lightness instead of a fixed list. Purple is any hue from 230 to 300 degrees with enough saturation. It also measures contrast the way WCAG defines it.

### The rules: `tells.py`

Each of the 43 tells is a small function with an ID, a category, a weight, a reason and a fix. It returns findings with a file and line. A tell is a signal, not proof.

### Scoring: `scan.py`

Runs every tell. The score starts at 100. Each tell that fires takes off its weight once, however many times it fires.

### Design systems: `system.py`

Builds a design system from a mood and a seed:

- **Mood** sets the font pairings, the type-scale ratio, the radii and the allowed accent hues.
- **Seed** comes from the product description. The same product always gets the same system and different products get different ones. This stops handmade from creating its own new default.

Every text color is adjusted until it passes 4.5:1 contrast on both the page and tinted panels. Status colors are moved until they look different from the accent. With an existing project, its own fonts, brand color and dark or light theme win.

Then `add_craft` derives the tokens a finished screen needs. It uses no randomness, so a saved system always gets the same ones back:

- `raised`, `accent-strong` and `accent-soft` for cards, hover states and selected rows.
- A soft background for each status color, checked so the status text on it passes 4.5:1.
- Ten tinted greys, `neutral-50` to `neutral-900`.
- Five chart colors. They start at the accent, skip purple, stay apart from each other and the status colors and pass 3:1 on the page.

Each mood also has one depth rule: borders, soft shadows, tonal steps or thin rules. Mixing them is what makes a screen look unplanned.

### Facts: `brief.py`

Decides what to ask. It reads the product and the place from the request ("for my bakery shop in Nairobi"). It finds the domain from the words, such as food, health or finance and picks questions that fit it. A bakery gets asked about best sellers and opening hours. A clinic gets asked about privacy on shared screens.

Answers like "everyone", "modern" or "amazing" are too vague to design from. They get one follow-up. If the second answer is still vague, it is recorded as vague, not used.

The same plan serves the terminal and MCP. In the terminal, `interview` asks the questions. Through MCP, `questions_for_ai` hands them to the AI tool, which asks the user in its own words. Answers are saved in `handmade.system.json`, so the next screen does not ask again.

### Prompts: `prompt.py`

Screens the request, picks the screen type and mood and writes the prompt. The mood comes from the product's words when the user names none, so a bakery gets "warm" and a county portal gets "civic".

The prompt always has the same order:

1. The request and the parts of it that get replaced.
2. The context, the facts still missing and the design-first steps.
3. The design system, the layout rules and the craft standard for the screen type.
4. The never-use list, accessibility rules and a self-check.
5. The machine-readable system.

### The whitelist: `conform.py`

Compares every font, color, font size, radius and spacing value in the code with `handmade.system.json`. Small differences in grays are tolerated. Any off-system color with a hue and any off-system font, fails at once.

### The gate: `check.py`

Combines the score and the whitelist into one PASS or FAIL. Twelve signature tells fail the gate on their own, whatever the score. This closes a gap found in testing: one violet button used to slip through.

### Rendered mode: `render.py`

Opens the page in headless Chrome at desktop and phone width and reads the computed styles of every element. It sees styles that JavaScript or a framework adds at runtime. It measures real contrast against the real background and finds fonts that failed to load by measuring text width.

### AI tools: `mcp.py`

An MCP server over standard input and output, with no extra packages. It offers five tools. Its instructions tell the AI to get a brief first and to stop only at PASS.

`handmade_design_brief` asks before it writes. While a required fact is missing, it answers "NEEDS INPUT" with the questions and tells the AI not to answer them itself. The AI asks the user, then calls again with the replies in `answers`. If the user wants to skip, the AI passes `proceed` and the brief lists the gaps as facts still missing.

### The command: `cli.py`

Turns all of the above into the `handmade` command.

## Where to change things

| You want to | Change |
|---|---|
| Add or adjust a rule | `tells.py`, plus a fixture and a test |
| Catch a new way of hiding a color | `extract.py` or `profile.py`, plus a folder in `tests/fixtures/tricks/` |
| Change what a mood looks like | the `MOODS` table in `system.py` |
| Change what the prompt says | `prompt.py` |
| Change what passes the gate | `PASS_THRESHOLDS` in `conform.py` and `HARD_TELLS` in `check.py` |
| Add a phrase that requests get screened for | `REQUEST_RULES` in `prompt.py` |

Run the full test suite after any change.
