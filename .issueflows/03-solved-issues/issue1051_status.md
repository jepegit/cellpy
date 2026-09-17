# Issue #1051 — status

- [x] Done

## What's done

- Recipe page `docs/getting_started/mcp.md` (Cursor walkthrough, WSL vs Windows
  `mcp.json`, other harnesses, roots, troubleshoot).
- Findability: nav, `index.md`, `how_do_i.md`, `cli.md`, `agents.md`,
  `checkup.md`, one pointer in unmanaged `AGENTS.md`. README skipped.
- `cellpy mcp install --list-clients` through the shim (`list_clients()` or
  `cellpy_mcp.clients`; never calls `install()`).
- Essential tests in `tests/test_cli_mcp.py`; CLI surface snapshot unchanged.
- `uv run pytest -m essential`: 866 passed, 70 skipped.
- `HISTORY.md` Unreleased bullet.

## Remaining work

- None.
