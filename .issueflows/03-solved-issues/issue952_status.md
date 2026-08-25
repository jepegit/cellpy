# Status: #952 Batch.drop ghost cell

- [x] Done

## What's done

- Added `CellStore.remove`; `Batch.drop` calls it (`unload` stays cache-only).
- Essential tests: store remove vs unload; loaded two-cell drop → summaries/report/adapter.
- User note in `docs/getting_started/agents.md` and AGENTS.md batch bullet.
- Design note on `batch-load-orchestrator.md`.
- Registry rows for the two new essential tests.
- `uv run pytest -m essential`: 835 passed; one unrelated Windows HDF5 lock flake (`test_v9_files_do_not_need_tables`) passed on retry.

## Remaining work

- None.
