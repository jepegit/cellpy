# Issue #466 — status

- [x] Done

## What's done

- Branch `466-legacy-v4-v5-load-test` created from updated `master`.
- `tests/test_cellpy_file_roundtrip.py`:
  - Extended `LEGACY_SUCCESS` with v4/v5; removed TypeError pin test.
  - Renamed to `test_legacy_v4_v7_load_shapes_and_columns`.
  - v4/v5: `cycle_index` stays a column (index name unset); v6+ keep index-name assert.
- `pytest tests/test_cellpy_file_roundtrip.py` — 10 passed.
