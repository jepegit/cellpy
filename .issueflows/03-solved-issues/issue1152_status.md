# Issue #1152 — status

- [x] Done

## What's done

- `_collect_derivative` skips a cell with no cycle curve, warns once, and records `cells_included` / `cells_skipped`. Same path for ICA and DVA.
- Docstrings on `ica_collector`, `dva_collector`, `collect_ica`, and `collect_dva`.
- Agent notes in `docs/agents/index.md` and `AGENTS.md`.
- Essential tests for the skip, the quiet path, and a schema error that still aborts.
- `uv run pytest -m essential`: 993 passed, 74 skipped.

## Remaining work

- None.
