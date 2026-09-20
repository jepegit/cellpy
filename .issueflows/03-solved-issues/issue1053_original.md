# Issue #1053: Deduplicate repeated copy in the MCP getting-started chapter

Source: https://github.com/jepegit/cellpy/issues/1053

## Original issue text

## Problem / context

`docs/getting_started/mcp.md` (“Connect an agent IDE to cellpy”) repeats the same material in several places. Easy to follow the first time; noisy on a re-read, and the copies will drift.

Concrete overlaps:

1. **Identical stdio JSON** under “Cursor (detailed)” and again under “By-hand JSON (any stdio client)” (`mcpServers` → `cellpy` → `command` / `args` / `env.CELLPY_MCP_ROOT`).
2. **VS Code top-level key is `servers`, not `mcpServers`** — client table, a bold paragraph, the by-hand JSON note, and the troubleshoot table.
3. **Fast path (Cursor)** already shows `cellpy mcp install --client cursor [--dry-run]`; “Cursor (detailed)” restates the same install before the extra bits (global vs project `mcp.json`, interpreter path, Settings UI, WSL).

## Spec

Edit `docs/getting_started/mcp.md` only (unless a one-line cross-link in `docs/reference/cli.md` or `docs/how_do_i.md` is needed after a heading change).

- Keep one canonical JSON example; other spots link or say “same block as above”.
- Keep the VS Code `servers` warning once in “Other clients” (or the troubleshoot table); drop the rest.
- Keep Fast path short; Cursor (detailed) should add only what Fast path does not cover.
- Do not drop WSL vs Windows `mcp.json`, the `wsl.exe` example, roots, or the troubleshoot table.

## Acceptance criteria

- [ ] No near-identical JSON or “`servers` not `mcpServers`” paragraph appears twice.
- [ ] Fast path + Cursor (detailed) do not repeat the same install commands as if they were new.
- [ ] A first-time Cursor user can still install, pick the right `mcp.json` (incl. WSL vs Windows), set `CELLPY_MCP_ROOT`, and recover a failed spawn from this page alone.
- [ ] Nav title and inbound links (`agents.md`, `cli.md`, `how_do_i.md`, `checkup.md`) still resolve.

## Out of scope

- New MCP clients or installer backends.
- Duplicating the cellpy-mcp tool/prompt catalog (keep the README link).
- Rewriting `docs/getting_started/agents.md`.
