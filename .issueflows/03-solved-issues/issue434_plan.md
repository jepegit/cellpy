# Plan for issue #434: Value-parity comparator

## Goal

`tests/parity.py::assert_value_parity(legacy, native, family, *, exceptions=...)` — the
Phase-3 oracle harness comparing legacy-named pandas frames to native-named frames through
`cellpycore.legacy.mapping`.

## Approach

1. **`tests/parity.py`**
   - Build mapped column pairs per family (`raw`, `steps`, `summary`) from
     `cellpycore.legacy.mapping`, including summary `{col}_{mode}` specific variants
     (`gravimetric`, `areal`, `absolute`) via `CycleCols.specific_columns`.
   - Align rows on declared key columns; compare values dtype-tolerantly
     (`pandas.testing.assert_series_equal`, `check_dtype=False`).
   - `exceptions`: `frozenset` of legacy or native column names; unlisted mismatches fail.

2. **`tests/parity_support.py`**
   - `run_legacy_pipeline(cell)` — canonical Arbin `.res` load → steps → summary.
   - `build_native_frames(cell)` — mirror `OldCellpyCellCore` native engine path
     (polars `make_step_table` / `make_summary` + scaled columns) without legacy rename.

3. **`tests/test_value_parity.py`**
   - `@pytest.mark.essential` trivial-pass tests for raw / steps / summary on the canonical
     `.res` cell (skip when testdata missing).

4. **`tests/README.md`** — short section on the value-parity oracle.

## Test strategy

```bash
uv run pytest tests/test_value_parity.py -m essential
```

## Files

- `tests/parity.py` (new)
- `tests/parity_support.py` (new)
- `tests/test_value_parity.py` (new)
- `tests/README.md`
