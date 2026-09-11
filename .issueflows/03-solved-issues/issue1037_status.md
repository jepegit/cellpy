# Issue #1037 — status

- [x] Done

## What's done

- Non-interactive `cellpy setup` with an existing config now creates
  missing configured local folders (including `raw/`).
- `_join_under_home` keeps remote `OtherPath`s off the local mkdir path.
- `config.paths.instrumentsdir` → `instrumentdir`.
- Essential tests + registry rows.
- Docs: `configuration.md`, `agents.md`, root `AGENTS.md`.
- `uv run pytest -m essential`: 858 passed, 70 skipped.

## Remaining work

- None.
