# Issue #594 — status

- [ ] Done

## What's done

- Plan accepted (2026-07-22).

## Remaining work

- Remove `--ignore=tests/test_plotutils_summary_plot.py` from `ci-scheduled.yml` (5 places).
- Set `MPLBACKEND: Agg` on `conda-pytest` and `pip-install` jobs.
- Update stale CI docs that still claim the ignore.
- Local: run summary-plot suite + essential gate.
- Post-merge: dispatch `CI (scheduled)` once and triage any platform failures.
