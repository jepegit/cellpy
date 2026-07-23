# Issue #654 — status

- [x] Done

## What's done

- Plan accepted (2026-07-24).
- Shared `_cv_partition_summary_frames` in `cellpy/utils/helpers.py`:
  non-CV via `exclude_step_types=["cv_"]`, with-CV = `full − non_cv` (clip ≥ 0);
  warns when step table has no `cv_*` types.
- Wired `partition_summary_cv_steps`, `_partition_summary_based_on_cv_steps`, and
  `_prepare_fullcell_standard_data` off dead `selector_type`.
- Tests: `tests/test_cv_partition.py` (rate cell identity + melt/wide; CC-only ≈ 0).
- `uv run pytest -m essential`: 590 passed, 13 skipped.
- HISTORY.md Unreleased bullet; closed via `/iflow-close yolo` (2026-07-24).

## Remaining work

- None.
