# Issue #415 status

- [x] Done

## What's done

- Bumped `pandas` constraint to `>=3.0.3,<4` in `pyproject.toml`; regenerated `uv.lock`
- Fixed `_datetime_to_unix_seconds` in `cellpy/exporters/bdf.py` — epoch delta + `total_seconds()` (pandas 3 default datetime unit is `us`)
- Fixed `Series.view("int64")` → `astype("int64")` in `post_processors.py` (2 sites)
- Fixed `ArrowStringArray.flatten` in `batch_journals.py` — `.dropna().tolist()` (3 sites)
- Added missing `@pytest.mark.skipif(not seaborn_available)` on `TestSummaryPlotBasic`
- Full suite: 477 passed, 61 skipped, 0 failed

## Remaining work

- None
