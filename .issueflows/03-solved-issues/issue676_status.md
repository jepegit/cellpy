# Issue #676 — Status

- [x] Done

## What's done

- Plan accepted (A / narrow examples / fix stale migration prose).
- Rewrote `docs/fundamentals/data_structure.md` column headings around `c.schema` + native key-column tables; removed legacy `Headers*` dumps as “current”.
- Updated `docs/getting_started/migration_v1_to_v2.md`: rc1+ native default; notebook/batch recipe with `cumulative_discharge_capacity` gotcha.
- Polished `docs/other/header_migration_map.md` intro + link to recipe.
- Extended `tests/test_cell_schema.py::test_schema_columns_are_keys_into_the_frames` (`step_type`, `cumulative_discharge_capacity`, no `raw.discharge_capacity`).
- Patched instructional source cells:
  - `examples/09_loading_pec_data.ipynb`
  - `examples/08_batmo_bdf.ipynb`
- `uv run pytest -m essential` — 606 passed, 13 skipped.
- HISTORY.md Unreleased bullet added.

## Remaining work

- None (land via PR; `/iflow-cleanup` after merge).
