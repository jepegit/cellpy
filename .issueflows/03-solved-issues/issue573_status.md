# Issue #573 — status

- [x] Done

## What's done

- Plan accepted (freeze default + convert escape + message copy locked).
- Flipped `CellpyCell.load` and `cellpy_file.read.load` default to `accept_old=False`.
- Freeze `WrongFileVersion` message names `cellpy 1.x \`cellpy convert\``.
- Added essential `tests/test_file_format_compat_matrix.py` (read v8/v9, write v9/v8, reject pre-v8, convert escape, v8→v9 parity).
- Fixed pre-v8 test call sites (`test_cellpy_method_integrity`, `test_cell_readers`).
- Synced `docs/getting_started/migration_v1_to_v2.md` and `tests/README.md`.
- `cli_api.convert` still loads with `accept_old=True` (unchanged).
- Verified: matrix + v9 + cli_api (41 passed); `uv run pytest -m essential` (624 passed); matrix re-check on close (10 passed).
- HISTORY.md bullet under `[Unreleased]`.

## Remaining work

- None (close / PR). Follow-up: CI full fixed by `accept_old=True` on `neware_uio.h5` (v7) fixtures.
