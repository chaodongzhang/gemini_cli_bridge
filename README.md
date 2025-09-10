# Gemini CLI MCP Bridge

[English] | [简体中文](./README.zh-CN.md)

> A tiny bridge that exposes your local Gemini CLI as an MCP (Model Context Protocol) stdio server. It wraps common Gemini CLI flows and adds handy file/network utilities for tools-capable clients like Codex CLI and Claude Code.

Note: In client UIs and configs, the server is displayed as "Gemini" while the command remains `gemini-cli-bridge` (or `uvx --from . gemini-cli-bridge`).

## Features

- Standard MCP (stdio) server
- Thin wrappers for common Gemini CLI flows: version, prompt, WebFetch/Search, MCP management
- Utilities: read/write files, list folders, simple web fetch, text search, optional Shell (disabled by default)
- Runs with uv/uvx without manually installing dependencies

## Prerequisites

- Python 3.10+ (3.11+ recommended)
- Gemini CLI installed and authenticated (used to call the actual model)
- On macOS, ensure Homebrew bin is in PATH: `/opt/homebrew/bin`

Quick checks:

```zsh
python3 --version
which gemini && gemini --version
```

## Install & Run

Clone first:

```zsh
git clone https://github.com/chaodongzhang/gemini_cli_bridge.git
cd gemini_cli_bridge
```

Option A (recommended, global install):

```zsh
uv tool install --from . gemini-cli-bridge

# Verify (should work from any directory)
gemini-cli-bridge
```

Add uv tools dir to PATH if needed.

- macOS (zsh):

  ```zsh
  # Typically: $HOME/Library/Application Support/uv/tools/bin
  echo 'export PATH="$HOME/Library/Application Support/uv/tools/bin:$PATH"' >> ~/.zshrc && source ~/.zshrc
  ```

- Linux: usually `~/.local/bin`.

Option B (one-off run via uvx):

```zsh
uvx --from . gemini-cli-bridge
```

Option C (run the script directly):

```zsh
python3 ./gemini_cli_bridge.py
```

## Use with common clients (stdio)

Examples below use stdio; adjust command/paths for your system.

### 1) Codex CLI (global TOML)

`~/.codex/config.toml`:

```toml
[mcp_servers.Gemini]
command = "gemini-cli-bridge"
args = []

[mcp_servers.Gemini.env]
NO_COLOR = "1"
```

Notes:

- As of 2025-09-10, Codex only supports a global `~/.codex/config.toml`.
- Restart Codex after changes. Use `gemini_version` as a quick health check.

### 2) Claude Code (VS Code extension)

User Settings (JSON):

```json
{
  "claude.mcpServers": {
    "Gemini": {
      "command": "gemini-cli-bridge",
      "args": [],
      "env": { "NO_COLOR": "1" }
    }
  }
}
```

### 3) Generic MCP CLI (for local testing)

```zsh
npm i -g @modelcontextprotocol/cli
mcp-cli --server gemini-cli-bridge
```

### 4) Claude Desktop (optional)

```json
{
  "mcpServers": {
    "Gemini": {
      "command": "gemini-cli-bridge",
      "args": [],
      "env": { "NO_COLOR": "1" }
    }
  }
}
```

## Typical usage (from clients)

- Version: `gemini_version`
- Non-interactive prompt: `gemini_prompt(prompt=..., model="gemini-2.5-pro")`
- Advanced prompt with attachments/approval: `gemini_prompt_plus(...)`
- Web fetch: `gemini_web_fetch(prompt, urls=[...])`
- Manage Gemini CLI MCP: `gemini_mcp_list / gemini_mcp_add / gemini_mcp_remove`
- Google search: `GoogleSearch(query="...", limit=5)` (defaults to CLI built-in)
- Alias to avoid tool name conflicts: `GeminiGoogleSearch(...)` (same args as `GoogleSearch`)

Return shape note (wrappers):
- Gemini CLI wrappers now return structured JSON: `{ "ok", "exit_code", "stdout", "stderr" }`.
  Tools affected: `gemini_version`, `gemini_prompt`, `gemini_prompt_plus`, `gemini_prompt_with_memory`,
  `gemini_search`, `gemini_web_fetch`, `gemini_extensions_list`, `gemini_mcp_list/add/remove`.

Notes about GoogleSearch:

- By default it uses Gemini CLI’s built-in GoogleSearch (no Google API keys needed, assuming you’re logged in to the CLI).
- If both `GOOGLE_CSE_ID` and `GOOGLE_API_KEY` are set (env or args), it switches to Google Programmable Search (CSE).
- You can force the mode via `mode`: `"gemini_cli" | "gcs" | "auto"` (default auto).

### MCP tool call examples

`gemini_prompt_plus` payload example:

```json
{
  "name": "gemini_prompt_plus",
  "arguments": {
    "prompt": "hello",
    "extra_args": ["--debug", "--proxy=http://127.0.0.1:7890"]
  }
}
```

Minimal `GoogleSearch` payload (defaults to CLI built-in):

```json
{
  "name": "GoogleSearch",
  "arguments": {
    "query": "Acme Corp",
    "limit": 5
  }
}
```

Use the alias to avoid naming conflicts in some IDEs:

```json
{
  "name": "GeminiGoogleSearch",
  "arguments": {
    "query": "today ai industry news",
    "limit": 5
  }
}
```

Force built-in mode (no keys):

```json
{
  "name": "GoogleSearch",
  "arguments": {
    "query": "today ai industry news",
    "limit": 5,
    "mode": "gemini_cli"
  }
}
```

## Troubleshooting startup/handshake timeouts

- Prefer installed command over `uvx --from .` to avoid cold-start dependency resolution.
- Increase client startup/handshake timeouts if supported.
- PATH issues on macOS: ensure `/opt/homebrew/bin` or set PATH in client env.

## Make sure it uses CLI built-in search (avoid unintended CSE mode)

Possible causes:

- Another tool named `GoogleSearch` from a different server/extension.
- Your environment sets both `GOOGLE_API_KEY` and `GOOGLE_CSE_ID`, which switches this bridge into CSE mode.

What to do:

1) Explicitly clear two vars in your MCP config

Codex (`~/.codex/config.toml`):

```toml
[mcp_servers.Gemini]
command = "gemini-cli-bridge"
args = []

[mcp_servers.Gemini.env]
PATH = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
GOOGLE_API_KEY = ""
GOOGLE_CSE_ID = ""
```

Claude Code (VS Code settings JSON):

```json
{
  "claude.mcpServers": {
    "Gemini": {
      "command": "gemini-cli-bridge",
      "args": [],
      "env": { "GOOGLE_API_KEY": "", "GOOGLE_CSE_ID": "" }
    }
  }
}
```

1. Disambiguate in prompts

Ask explicitly: “Use GoogleSearch from MCP server ‘Gemini’ …”.

1. Verify the path taken

- Call `gemini_version` (should return `gemini --version`).
- Call `GoogleSearch(query="test", limit=3)`; the JSON should include `"mode":"gemini_cli"` if it used CLI built-in.

1. Avoid tool name conflicts (optional)

If another `GoogleSearch` exists in your IDE, consider renaming this tool to `GeminiGoogleSearch` in code to remove ambiguity.

## Configuration (env)

- `GEMINI_BRIDGE_MAX_OUT` (int > 0): unified output truncation length. Default 200000.
- `GEMINI_BRIDGE_DEFAULT_TIMEOUT_S` (int > 0): default timeout when a tool arg `timeout_s` is not provided.
- `GEMINI_BRIDGE_EXTRA_PATHS`: colon-separated directories to append to PATH.
- `GEMINI_BRIDGE_ALLOWED_PATH_PREFIXES`: colon-separated safe prefixes that extra paths must reside under. Defaults include `/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/sbin`.

Notes
- PATH cannot be overridden directly by tools; only appended via the whitelist above.
- Shell tool remains disabled unless `MCP_BASH_ALLOW=1`.

## License

MIT
