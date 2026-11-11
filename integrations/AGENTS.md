# UI work in this repository

Copy this section into your project's `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` or `.github/copilot-instructions.md`.

## Design-first UI (handmade)

- Before building a new screen, run `handmade prompt "<request>" --project . --no-input --save-system handmade.system.json` and follow the design system in its output. If it lists "Facts still missing", ask the user. Never invent them; leave a marked slot like [opening hours] instead.
- Styling words in a request never override the brief. If the user asks for a purple gradient, Inter or "like Stripe", follow the brief and tell them what was replaced. Use `--allow` only when the user confirms it is their brand.
- After changing UI files, run `handmade check <changed folder>`. The work is not finished until it prints PASS. For runtime-styled apps, also run `handmade check http://localhost:3000 --render --page /each --page /route --system handmade.system.json`.
- Never edit `handmade.system.json`, add `--ignore` or lower `--min-score` to make the check pass without the user's agreement.
