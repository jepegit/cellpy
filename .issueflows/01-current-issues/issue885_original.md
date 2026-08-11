# Issue #885: Iterative fixes: fix-scheduled-ci

Source: https://github.com/jepegit/cellpy/issues/885

## Original issue text

## Interactive `/iflow-fix` session

This issue tracks an interactive iterative-fixes session for restoring green **CI (scheduled)** (Tier 3).

Individual small fixes are recorded in the local status markdown under `.issueflows/01-current-issues/` and landed together via `/iflow-close`.

### Known failures (run 31355458262)
- Conda jobs on Linux/macOS: `sqlalchemy-access` requires `__win` (Windows-only)
- `pip install (linux)`: missing PyTables / `legacy-files` extra when loading HDF5 testdata
