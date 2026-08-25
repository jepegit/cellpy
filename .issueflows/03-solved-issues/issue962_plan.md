# Issue #962 plan

## Goal

`batch.load` must make it obvious when filefinder found no raw files. Today
`cellpy.get()` with no paths returns an empty `CellpyCell` and the cell is
marked `LOADED`.

## Constraints

- Do not change filefinder search rules or OtherPath resolution.
- Keep `accept_errors=True` default (errors stay on `BatchResult`).
- Do not raise the whole batch by default.

### Prior art

- `cellpy.get` (`filename is None` and no `cellpy_file`) returns empty cell.
- `runner._get_kwargs` sets `source=None` when both paths are missing.
- `_dbengine.find_files` stores `None` and continues.
- `BatchResult.failed` / `raise_if_failed` already exist.

## Approach

1. `load_cell`: if `source is None`, `FAILED` + `FileNotFoundError` (re-raise
   when `accept_errors=False`).
2. `find_files`: `UserWarning` listing cells with no raw match.
3. `_finalize`: after `update()`, `UserWarning` if any cell failed, pointing
   at `batch.result.report()`.

## Files to touch

- `cellpy/batch/runner.py`
- `cellpy/batch/_dbengine.py`
- `cellpy/batch/facade.py`
- `tests/test_batch_v3_runner.py`, `tests/test_batch.py`
- `test-registry.md`

## Test strategy

`uv run pytest -m essential`. New tests for the empty-source fail and the
find_files warning.

## Open questions

None — yolo-fit.
