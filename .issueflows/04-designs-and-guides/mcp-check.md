# `cellpy mcp check` — proving an MCP install from the terminal

## Context

The MCP server lives in the separate `cellpy-mcp` distribution; cellpy ships
the shim (`cellpy mcp serve | install | status`, #840, #992, #1051). "Install
cellpy MCP and test it" still had no terminal answer for the *test* half:
`status` says whether the package imports, but only a restarted editor showed
whether the registered `command` could actually be spawned and answered MCP.
Meanwhile `cellpy-mcp` 0.1.0 on PyPI knows only Claude Desktop, so
`cellpy mcp install --client cursor` fails on the released package with
`Unknown client 'cursor'` (Cursor / VS Code support is on GitHub `main`,
unreleased).

## Decision

- **`cellpy mcp check`** is implemented in cellpy (`cli_api.mcp_check`,
  `_mcp_probe`), not delegated to `cellpy_mcp`: it acts as the *client*, so a
  server cannot vouch for itself, and a few lines of stdlib JSON-RPC over
  stdio need no MCP SDK and work against any `cellpy-mcp` build.
- Default: spawn `sys.executable -m cellpy_mcp`. With `--client <name>`: read
  that client's own config (path and key via `cellpy_mcp.clients`, never a
  hardcoded table) and spawn the exact `command` + `args` + `env` in it — the
  thing that fails most often is that this differs from the current env.
- Probe = `initialize` → `notifications/initialized` → `tools/list` →
  `tools/call list_instruments` (cheap, file-free). Reader threads give a
  portable timeout and keep the server from blocking on a full stderr pipe.
- Failure is a message plus exit 1: missing interpreter path, non-JSON on
  stdout ("banner on the protocol channel"), early exit (last stderr line),
  or timeout. `status` keeps exiting 0 — different question.
- `install` adds an upgrade hint when the package raises `Unknown client`.
- Docs: `docs/getting_started/mcp.md` gained an *Ask your agent to do it*
  checklist (prompt to paste + numbered commands with checkable outcomes,
  including the 0.1.0 fallback via a GitHub install). `AGENTS.md` points at it.

## Alternatives considered

- Put `check()` in `cellpy-mcp` and delegate: needs a release first, and a
  server-side self-check does not test the client's spawn path.
- Import the MCP SDK client in cellpy: adds the dependency the shim exists to
  avoid.

## Follow-ups

- Release `cellpy-mcp` ≥ 0.2 with Cursor / VS Code clients so the GitHub
  fallback in the docs can be dropped.
- #1053 (dedupe the MCP chapter) and #1054 (`llms.txt`) remain open.
