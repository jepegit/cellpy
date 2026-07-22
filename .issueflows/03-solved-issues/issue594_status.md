# Issue #594 — status

- [x] Done

## What's done

- Plan accepted (2026-07-22).
- Removed all five `--ignore=tests/test_plotutils_summary_plot.py` entries from
  `ci-scheduled.yml` (`conda-pytest` ×3, `pip-install` linux/macos).
- Set job-level `MPLBACKEND: Agg` on `conda-pytest` and `pip-install`.
- Updated stale ignore notes in `testing-and-coverage.md` and `AGENTS.md`.
- Local: `MPLBACKEND=Agg uv run pytest tests/test_plotutils_summary_plot.py`
  → **47 passed** (with `--extra batch`).
- Local: `uv run pytest -m essential` → **535 passed** (ignored host
  `test_arbin_variants_two_stage` pyodbc collection error).
- Merged via PR #631 on `master` (2026-07-22).
- `HISTORY.md` Unreleased bullet added; issue group archived to
  `03-solved-issues`.

## Remaining work

- None for #594 code/docs. Optional: dispatch `CI (scheduled)` once and triage
  any platform failures with targeted `skipif` (not a blanket file ignore).
