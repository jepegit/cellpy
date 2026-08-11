# Issue #885 status — Iterative fixes: fix-scheduled-ci

Interactive `/iflow-fix` session. Small fixes logged below; landed together via `/iflow-close`.

- [ ] Done

## Iterative fixes log

- 2026-08-11: Dropped `sqlalchemy-access` from `github_actions_environment.yml` (Windows-only / `__win`); install it in `ci-scheduled.yml` on Windows runners only — unblocks conda env solve on Linux/macOS.
- 2026-08-11: Scheduled `pip-install` job now uses `pip install -e ".[legacy-files]"` so Linux has PyTables for HDF5 fixture tests (batch extra still omitted).

