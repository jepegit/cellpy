# Issue #668 — Status

- [x] Done

## What's done

- Core tracking: [cellpy/cellpy-core#142](https://github.com/cellpy/cellpy-core/issues/142) (noted on #668).
- **Fix A** (`batch_plotters.py`): name unnamed summary index to `cycle_index` before `reset_index`; guard `canvas.show()` when `canvas is None`.
- **Fix B**:
  - `unwrap_meta_value` in `cellpy/readers/cellpy_file/meta.py`
  - unwrap `cycle_mode` after list-shaped meta load in `read.py` + `legacy_read.py`
  - recursive unwrap (+ write-back) in `CellpyCell.cycle_mode` getter/setter
  - touch `self.cycle_mode` at start of `_make_summary` so the core bridge sees a scalar
- Tests: `tests/test_issue668_batch_bugs.py` (essential).
- `uv run pytest -m essential` green on close.
- HISTORY.md Unreleased bullet added.

## Remaining work

- None for this issue. Follow-up: cellpy-core#142 (optional pin bump later).
