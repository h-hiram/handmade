# Security

## Supported versions

Only the latest release gets fixes.

## What handmade does with your code

- It reads files. It writes only these, and only in the cases named:
  - `handmade.system.json`, when you pass `--save-system` or an agent passes `save_system_to`.
  - `.vscode/mcp.json`, `.vscode/settings.json`, `.cursor/mcp.json` or `.mcp.json`, when you run `handmade init`.
  - `CLAUDE.md`, `.cursor/rules/handmade.mdc` or `.github/copilot-instructions.md`, when an agent calls the MCP tool `handmade_check` on a project with UI files but no design system, and that editor is already set up in the project. It appends a marked section and never creates the editor's folder.
- It sends nothing anywhere. There is no network access in the scanner, the prompt writer or the MCP server.
- Rendered mode (`--render`) opens your pages in a local headless Chrome. Pages you render can load what they normally load, such as fonts.

## Reporting a problem

Please do not open a public issue for a security problem.

Use GitHub's private vulnerability reporting: go to the **Security** tab of the repository and choose **Report a vulnerability**.

Include what you found, how to repeat it and what someone could do with it. You will get a reply within 7 days. Once it is fixed, you will be credited in the release notes, unless you would rather not be.
