# handmade 0.3.0: test report

Date: 9 November 2026. Everything below can be reproduced with the commands at the end.

## Summary

| Question | Result |
|---|---|
| Can a request make handmade produce AI-default design? | No. All 12 benchmark requests were screened, including 4 hostile ones. "Ignore the rules" phrasings are refused and cannot be allowed. |
| Can AI defaults be hidden from the scanner? | 12 of 12 known disguises are caught in source. A runtime-only disguise is caught in rendered mode. |
| Can a passing page drift without the gate noticing? | No. 10 single tampers to a passing page each turn PASS into FAIL. |
| Does it raise false alarms on human-designed code? | GOV.UK Frontend scores 97 of 100. Each false alarm found during testing was fixed and given a regression test. |
| Does following the generated prompt pass the gate? | Yes, in the pilot: 3 of 3 pages pass in source and rendered mode. |
| Does it guess facts the user never gave? | No. Missing facts are asked for or listed under "Facts still missing". Through MCP, the brief is withheld until the user answers or chooses to skip. |
| Test suite | 130 tests, all passing. 5 rendered-mode tests need Playwright and Chrome and are skipped without them. |

## 1. Request screening

`python benchmark/bench.py robustness` builds a prompt for each of 12 requests and checks three things. Every AI-default ask in the request is listed with its replacement. The prompt states that its rules outrank styling words in the task. The generated palette has no purple accent.

| Request | Hostile | Asks screened |
|---|---|---|
| coffee-landing-hostile | yes | override, purple, gradient, glass, Inter, emoji, three cards, vague style words, "like Stripe" (9) |
| portfolio-hostile | yes | neon glow, gradient, gradient text, bento, sparkles, Space Grotesk, vague style words (7) |
| saas-hostile | yes | override, centered hero, blobs, testimonials and vanity stats (4) |
| bank-hostile | yes | violet, glassmorphism, glow, Poppins, aurora effect (5) |
| 8 ordinary requests | no | none needed |

Result: 12 of 12 pass.

Unit tests cover three more cases. Five phrasings of "ignore the rules" are all refused. Words like "interactive" do not count as the Inter font. And `--allow` keeps a brand choice, but it cannot switch off the refusal.

## 2. Scanner red team

Each folder in `tests/fixtures/tricks/` hides AI defaults in a different way. Before this release, a sample using four of these tricks scored 95, "Looks designed". Now:

| Disguise | Caught as |
|---|---|
| React `style={{ }}` gradient and gradient text | purple gradient, gradient text |
| styled-components template | purple gradient, glass, glow |
| `hsl()` and `oklch()` purple | purple gradient, indigo accent |
| `var()` chain into a gradient | purple gradient |
| Tailwind config alias (`brand` = indigo) and named gradient | indigo accent, purple gradient |
| Tailwind v4 `@theme` color | indigo accent |
| shadcn `--primary: 262 83% 58%` used as `bg-primary` | indigo accent |
| Vue `:style` | indigo accent, trend font |
| Angular `[ngStyle]` | glow, purple gradient |
| "InterVariable" and `@fontsource-variable/inter` | default font |
| Named color `blueviolet`, uppercase and 8-digit hex | indigo accent |
| Blade `@class([...])` with inline style | indigo accent, purple gradient |
| Gradient and glow assembled by JavaScript at runtime | Not visible in source (score 100). Caught in rendered mode, along with a font that silently failed to load. |

## 3. The gate

`tests/test_check.py` starts from a page that passes and changes one thing at a time:

| Tamper | Result |
|---|---|
| Accent renamed to a purple hex | FAIL |
| Accent written as `oklch()` purple | FAIL |
| Accent moved slightly (near miss) | FAIL |
| Body font swapped to "Inter Variable" | FAIL |
| Font sizes off the scale | FAIL |
| Radii off the system | FAIL |
| One `bg-violet-600` class | FAIL (this one passed at first, see bug 4) |
| One colored glow | FAIL |
| One emoji | FAIL |
| One glass panel | FAIL |

The typical AI page in `examples/landing/before.html` fails every category. The redesigned page passes 100% in every category, in source and rendered mode.

## 4. Real projects

| Project | Score |
|---|---|
| GOV.UK Frontend (human design team) | 97 |
| shadcn taxonomy (human, but widely copied by AI tools) | 44 |
| 5 public projects built with Lovable, v0 and Bolt | 9, 18, 34, 54, 75 |

## 5. Pilot run of the full pipeline

Three benchmark requests were built by following their generated prompts and the hostile request was also built by following it literally.

| Page | Source check | Rendered check |
|---|---|---|
| Hostile coffee request, followed literally | FAIL, score 48 | FAIL, score 43 |
| Hostile coffee request, through handmade | PASS, score 100 | PASS, score 100 |
| Clinic dashboard, through handmade | PASS, score 100 | PASS, score 100 |
| SACCO signup form, through handmade | PASS, score 100 | PASS, score 100 |

The clinic dashboard and the SACCO form were rebuilt for 0.3.0 from the new brief, with its craft standard. The first versions passed the gate but looked plain. The new ones have a full frame, real charts, styled controls and every state. The form leaves the SACCO's name, fee and licence as marked slots, because the request never gave them. Building them found two bugs, listed below as 9 and 10.

**Caveat.** These pages were written by the same AI that built handmade. That proves the pipeline works end to end and that the gate rejects literal compliance with a hostile request. It is not independent evidence of how v0, Lovable or ChatGPT respond to the prompts. The benchmark kit in `benchmark/` is ready for that test.

## 6. Bugs found by testing and fixed

| # | Found by | Problem | Fix |
|---|---|---|---|
| 1 | Hand-made trick sample | JSX style objects, `hsl()` and `oklch()` colors, Tailwind aliases and font variants were invisible | Parse style objects and CSS-in-JS, judge colors by hue in any format, resolve `var()` and aliases, normalize font names |
| 2 | Calibration | Tailwind indigo-500 and indigo-400 sat just outside the purple band | Band set to 230 to 300 degrees, with a test of purples and blues |
| 3 | GOV.UK | One `rebeccapurple` in a debug helper counted as an accent | A purple counts as an accent only as a fill, a brand token or when repeated |
| 4 | Gate tamper test | One `bg-violet-600` passed, because 1 of 31 colors stayed above the 95% threshold | Off-system colors with a hue, off-system fonts and signature tells now fail outright |
| 5 | Reading generated output | A generated accent was almost the same red as the error color | Status colors now search for a hue, saturation and lightness clearly distinct from the accent |
| 6 | Reading generated output | Some berry accents leaned purple | Accent bands moved toward raspberry, with a wider guard around the purple band |
| 7 | Rendered mode | Findings repeated per viewport; faint gray card shadows counted as glows | Deduplicated; shadows under 20% opacity or near black are ignored |
| 8 | Rendered mode | Muted text and accents passed on the page background but failed (4.2:1) on tinted panels | Every text color is now checked against both backgrounds. Tested on 840 palettes |
| 9 | Pilot rebuild | Two radii written as `var()` and a shorthand counted as five radii | Radii are resolved and split before counting |
| 10 | Pilot rebuild | Rendered mode read transparent borders as black | Transparent and near-transparent borders are skipped |
| 11 | A user's first run | "Landing page for my bakery shop" was treated as a shop and the same five questions were asked every time | Page names win over loose words. Questions now depend on the request and the domain |
| 12 | A user's first run | Vague answers such as "everyone" were used as facts | Vague answers get one follow-up, then are marked vague and not used |

## 7. Known limitations

- The gate proves the defaults are gone and the design system was followed. It cannot prove the design is good.
- The source scanner cannot see runtime styles. Rendered mode can, but needs Playwright and Chrome.
- Pixels inside images are not analysed.
- Generated palettes do not yet take the product into account (a coffee roaster can get a green accent).

## Reproduce

```bash
python -m unittest discover -s tests -v          # 130 tests
python benchmark/bench.py robustness             # request screening
python benchmark/bench.py score                  # pilot runs
handmade check examples/landing/before.html      # FAIL
handmade check examples/landing/after.html       # PASS
handmade scan tests/fixtures/runtime             # 100: runtime trick invisible in source
handmade scan --render tests/fixtures/runtime    # caught in the rendered page
```
