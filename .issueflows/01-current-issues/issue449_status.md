# Issue #449 — status

- [ ] Done

## What's done

- Added `cellpy_file.read_table`, `read_fid_table`, and `resolve_hdf5_path`.
- `CorruptCellpyFile` replaces bare `Exception` in key validation.
- `batch_helpers.look_up_and_get` and `_check_cellpy_file` delegate to `cellpy_file`.
- Removed blanket `AttributeError` swallow in `CellpyCell.load()`.
- Added `cellpy convert` CLI (v4→v8 upgrade path).
- Tests: updated failure-mode oracle, `read_table` parity, convert CLI.
- Essential suite: 86 passed.

## Remaining work

- PR review and merge via `/iflow-close`.
