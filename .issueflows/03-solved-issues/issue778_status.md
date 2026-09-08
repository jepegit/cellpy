# Issue #778 status — L6 golden equality test

- [x] Done

Branch: `778-l6-golden-equality-update`. Plan: `issue778_plan.md` (accepted 2026-09-08).

## What's done

- `tests/incremental_support.py`: `truncate_text_file`, `tail_rows`,
  `incremental_update` (test-side prototype of L3 `c.update()`: drives
  `update_core_data` with `nom_cap_abs`, current factor, `raw_limits`,
  `find_ir=False`; copies frames back; re-applies `_add_summary_extras` and
  `_refresh_scaled_summary_columns`), `assert_cell_frames_equal`.
- `tests/test_incremental_update.py` (essential, ~6 s): cut points derived
  from the full step table (mid-step / step end / cycle end).
  - overlap re-read (≥1 row) → **full equality** on raw/steps/summary, all
    columns (better than plan's shared-column fallback).
  - gap-append on step/cycle boundary → equal.
  - gap-append mid-step → strict xfail, cellpy/cellpy-core#148 (partial
    trailing step kept → spanning step split, C-rate drift).
  - empty tail → strict xfail, cellpy/cellpy-core#147 (`refresh_derived`
    re-joins C-rate columns → `*_right` duplicates).
- `tests/README.md` subsection.
- `uv run pytest -m essential`: 839 passed, 2 xfailed.

## Findings for L3 (#164)

- `update_core_data` returns a bare cellpycore `Data` (polars frames); cellpy
  must copy frames into its metadata-bearing `Data`, add summary extras
  (`native_core._add_summary_extras` with `core.schema`), then refresh scaled
  columns. `_refresh_scaled_summary_columns` fails on bare core `Data`
  (`no attribute 'tests'`).
- Always re-read from ≥1 already-seen row (ideally start of last step) until
  cellpy-core#148 lands.

## Remaining work

- None here. Drop the two xfail markers when cellpy-core#147 / #148 ship.
