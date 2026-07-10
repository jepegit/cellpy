# Plan: issue #466 — fix legacy v4/v5 cellpy-file roundtrip test

## Goal

Restore green scheduled CI by aligning the v4/v5 characterization test with actual loader
behavior: legacy v4/v5 files load successfully with `accept_old=True` (same contract as v6/v7).

## Constraints

- **Test-only fix** — do not change `cellpy/readers/cellreader.py`; v4/v5 paths already call
  `upgrade_from_to=(4|5, CELLPY_FILE_VERSION)` on extract steps and meta.
- **Stage 0.2 intent** — issue #429 plan §D always expected v4/v5 *successful* load with shape/column
  asserts; the `TypeError` test was a temporary pin of a bug, noted as stale in #432 status.
- **Scope** — one test module change; no fixture regen.

### Prior art

| Hit | Relevance |
|-----|-----------|
| `tests/test_cellpy_file_roundtrip.py` | `LEGACY_SUCCESS` + `test_legacy_v6_v7_load_shapes_and_columns` — mirror for v4/v5 |
| `tests/cellpy_file_support.py::load_cellpy_file` | Shared load helper used by v6/v7 test |
| `cellpy/readers/cellreader.py` `_load_hdf5_v5` / `_load_old_hdf5_v3_to_v4` | v4/v5 loaders with `upgrade_from_to` — explains why load now succeeds |
| `.issueflows/03-solved-issues/issue429_plan.md` §D | Original matrix: v4/v5 expect successful load + shapes/columns |
| `.issueflows/03-solved-issues/issue432_status.md` | Documents this test as pre-existing stale failure |

## Approach

**Option 1 (recommended): update the test to match successful load.**

1. Extend `LEGACY_SUCCESS` to include v4 and v5:

   ```python
   LEGACY_SUCCESS = [
       ("v4", "20160805_test001_45_cc_v4.h5", 4),
       ("v5", "20160805_test001_45_cc_v5.h5", 5),
       ("v6", "20160805_test001_45_cc_v6.h5", 6),
       ("v7", "20160805_test001_45_cc_v7.h5", 7),
   ]
   ```

2. Remove `LEGACY_TYPE_ERROR` and delete `test_legacy_v4_v5_currently_raise_typeerror_on_meta_extract`.

3. Rename parametrized test to `test_legacy_v4_v7_load_shapes_and_columns` (docstring: legacy
   v4–v7 load succeeds with expected shapes, renamed columns, and `cellpy_file_version` meta).

4. Keep markers unchanged — v4–v7 stay **outside** `@pytest.mark.essential` (same as current v6/v7).

**Rejected: Option 2 (re-raise TypeError in loader).** Would undo working v4/v5 support and
contradict #429 §D and existing `_load_hdf5_v5` / `_load_old_hdf5_v3_to_v4` implementation.

## Files to touch

| Path | Change |
|------|--------|
| `tests/test_cellpy_file_roundtrip.py` | Merge v4/v5 into `LEGACY_SUCCESS`; remove TypeError test; rename v6/v7 test |

## Test strategy

```bash
conda activate cellpy_dev_313   # or uv run
pytest tests/test_cellpy_file_roundtrip.py -v
pytest tests/test_cellpy_file_roundtrip.py::test_legacy_v4_v7_load_shapes_and_columns -v
```

Optional sanity: `pytest -m essential` (unrelated pre-existing failures may remain).

## Open questions

None — Option 1 is the clear fix unless you want v4/v5 promoted to `@pytest.mark.essential`
(not recommended; keeps essential budget unchanged).
