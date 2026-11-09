# Skills

`handmade/SKILL.md` is an agent skill. A skill is a set of instructions an AI agent loads when a task matches its description. This one loads for any UI work.

## Install for Claude Code

```bash
mkdir -p ~/.claude/skills && cp -r skills/handmade ~/.claude/skills/
```

To use it in one project only, copy it to `.claude/skills/` inside that project instead.

## What it makes the agent do

1. Ask what the product is, who uses it and which mood fits.
2. Run `handmade prompt` and save `handmade.system.json`.
3. Write a short design brief, then build from the system.
4. Run `handmade check`, fix what fails and repeat until PASS.

It forbids passing the gate by editing the system file, adding `--ignore` or lowering `--min-score` without the user's agreement.

If the `handmade` command is not installed, the skill falls back to a written checklist, so it still helps.
