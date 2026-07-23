# Issue #639 — Status

- [ ] Done

## What's done

- Plan accepted (2026-07-23).
- Branch `cursor/639-mpl-backend-4efd`; draft PR #645.
- Added `cellpy/plotting/backends/mpl.py` (`MatplotlibBackend.render`).
- Added `get_backend()`; flipped `summary_plot` to `backend=` with
  `interactive=` as `warn_once` alias (removal 2.1); seeded in
  `_deprecation._seed_known_deprecations` + `DEPRECATIONS.md`.
- Deleted `SeabornPlotBuilder`.
- Migrated oracle/summary tests to `backend=`; added `tests/test_mpl_backend.py`.
- Design notes updated (`plotting-backends.md`, `plotting-prepare.md`).
- Verified green: mpl/prepare/summary_plot/figure_specs + essential gate.

## Remaining work

- `/iflow-close` — HISTORY, archive issue docs, push, mark Done.
