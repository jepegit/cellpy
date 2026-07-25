# Issue #668 — Status

- [x] Done

## What's done (PR #670 on `v1.x`)

- Core tracking: [cellpy/cellpy-core#142](https://github.com/cellpy/cellpy-core/issues/142).
- **Fix A** (`batch_plotters.py`): name unnamed summary index to `cycle_index` before `reset_index`; guard `canvas.show()` when `canvas is None`.
- **Fix B**: unwrap nested/`list` `cycle_mode` on load + `CellpyCell.cycle_mode`; touch before `_make_summary`.
- Tests: `tests/test_issue668_batch_bugs.py` (essential).
- HISTORY.md Unreleased bullet for #670.

## What's done (re-open / Fix A summary cache)

- Plan v2 accepted (defaults).
- `summary_engine`: soft path reuses non-empty `experiment.summary_frames`; `reset=True` hard-rebuilds from cells.
- `Batch.plot` / `plot_summaries`: `summary_collector.do(reset=bool(reload_data))`.
- Actionable `NullData` when no cells vs empty summary tables.
- Import fix: `NullData` in `batch_helpers.py`.
- Tests: soft-reset reuse, hard-reset rebuild, empty `cell_names` message.
- HISTORY.md Unreleased bullet for the follow-up.
- Essential suite green on close.

## Remaining work

- None for this issue. Follow-up: cellpy-core#142; optional notebook verify after install from PR.
