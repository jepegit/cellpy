# Status — #878

- [x] Done

## What's done

- `Batch.export_project(destination, *, journal_path=None)`
- `_persist_cells(..., force_rewrite=False)` — export always writes; load persist still skips
- posix path write-back
- essential tests: round-trip, force rewrite, unloaded error
- migration docs + cookiecutter packaging cell
- design note in `batch-load-orchestrator.md`
- HISTORY.md Unreleased bullet
- essential suite: 665 passed (collection of `test_arbin_variants_two_stage.py` ignored locally — missing `libodbc.so.2` / pyodbc; unrelated to this change)

## Remaining work

None.

PR: https://github.com/jepegit/cellpy/pull/894 (#894)
