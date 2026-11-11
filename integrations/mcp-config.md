# Connect the handmade MCP server

The quickest way is to run `handmade init` in your project. It writes the right file for VS Code, Cursor or Claude Code. The rest of this page shows each file by hand.


Install first: `pipx install handmade` (or `pip install handmade`).
Then add the server to your AI tool. All of them start `handmade-mcp` over stdio.

## Claude Code

```bash
claude mcp add handmade -- handmade-mcp
```

## Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "handmade": { "command": "handmade-mcp" }
  }
}
```

## Cursor

Add to `.cursor/mcp.json` in your project or `~/.cursor/mcp.json` for all projects:

```json
{
  "mcpServers": {
    "handmade": { "command": "handmade-mcp" }
  }
}
```

## Shared project file (VS Code Copilot, Claude Code)

Add `.mcp.json` at the root of your project and commit it, so everyone on the team gets the server:

```json
{
  "mcpServers": {
    "handmade": { "command": "handmade-mcp" }
  }
}
```

## VS Code (older .vscode/mcp.json format)

Add to `.vscode/mcp.json`. Note this format uses `servers`, not `mcpServers`:

```json
{
  "servers": {
    "handmade": { "type": "stdio", "command": "handmade-mcp" }
  }
}
```

## Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "handmade": { "command": "handmade-mcp" }
  }
}
```

## Without installing (uv)

If you use [uv](https://docs.astral.sh/uv/), any client can run it straight from PyPI:

```json
{ "command": "uvx", "args": ["--from", "handmade", "handmade-mcp"] }
```

## Tools

| Tool | What it does |
|---|---|
| `handmade_design_brief` | Turns a UI request into a design system and rules to follow before coding. Screens styling words in the request and can save `handmade.system.json` |
| `handmade_check` | The finish gate. PASS or FAIL against AI defaults and the saved design system. The server tells the AI it is not done until PASS. With `render: true` it takes a URL, `pages` for the app's other routes and `system_path` for the design system |
| `handmade_scan` | Scores a folder and lists every tell with file, line and fix |
| `handmade_fix_plan` | Builds a repair plan for an existing UI from its own tokens |
| `handmade_list_tells` | Lists all tells with reasons and fixes |

For rendered checks (`render: true`), install the extra: `pip install "handmade[render]"` and `playwright install chromium`.

Pass absolute paths. The server's working directory depends on the client.
