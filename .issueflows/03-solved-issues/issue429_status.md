# Issue #429 — Status

- [x] Done

## What's done

- Branch `429-cellpy-file-characterization-tests` created from `master`
- Committed fixture `testdata/hdf5/20160805_test001_45_cc_v8_with_fids.h5` (from canonical `.res`, fid-populated)
- `tests/cellpy_file_support.py` — frame/meta/fid compare helpers (HDF meta list normalization)
- `tests/test_cellpy_file_roundtrip.py` — 10 tests (3 essential: v8 round-trip, limits-prefix, selector)
- `tests/fdv.py` — v5/v7/v8/v8_with_fids path constants
- `tests/README.md` — Cellpy-file characterization section
- Pointer comment on `test_cellpyfile_roundtrip` in `test_cell_readers.py`
- All 10 roundtrip tests green; essential suite 21 passed (~12s locally)
- `HISTORY.md` updated

## Remaining work

- None
