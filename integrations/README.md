# Integrations

Files for connecting handmade to AI coding tools. Pick the one that matches your tool.

| File | Use it with | What to do |
|---|---|---|
| `mcp-config.md` | Claude Desktop, Claude Code, Cursor, VS Code, Windsurf | Add the MCP server to your tool. The page has the exact config for each one. |
| `cursor/handmade.mdc` | Cursor | Copy it to `.cursor/rules/` in your project. |
| `AGENTS.md` | Codex, Copilot, Gemini CLI and others | Paste it into your project's `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` or `.github/copilot-instructions.md`. |

The agent skill lives in `skills/handmade/`.

All of these tell the AI the same three things. Get a design brief before building a new screen. Build only from the design system. Do not finish until `handmade check` passes.
