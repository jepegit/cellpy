# Status — #878

- [ ] Done

## What's done

- `Batch.export_project(destination, *, journal_path=None)`
- `_persist_cells(..., force_rewrite=False)` — export always writes; load persist still skips
- posix path write-back
- essential tests: round-trip, force rewrite, unloaded error
- migration docs + cookiecutter packaging cell
- design note in `batch-load-orchestrator.md`

## Remaining work

- Run essential tests
- HISTORY.md on close
- `/iflow-close`

PR: https://github.com/jepegit/cellpy/pull/894 (#894, draft)
