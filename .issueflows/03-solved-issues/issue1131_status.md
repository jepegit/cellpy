# Issue #1131 — status

- [x] Done

## What's done

- Captured on branch `1131-nominal-capacity-units` (worktree `cellpy-1131`).
- Plan accepted: lock the Excel contract (unit row ignored; bare number is mAh/g). No rescale.
- `tests/test_dbreader.py::test_excel_unit_row_does_not_rescale_nominal_capacity` passes (`uv run pytest` that node, 1 passed).
- Finding commented on the issue: https://github.com/jepegit/cellpy/issues/1131#issuecomment-5979452832

## Remaining work

- None. Essential suite: 986 passed, 74 skipped.
