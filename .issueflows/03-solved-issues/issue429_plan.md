# Issue #429 — Plan

## Goal

Add characterization tests that lock current cellpy-file (HDF5 v8) load/save behavior and
legacy version handling **before** the cellpy-file extraction refactor (Step 0 in
[`cellpy-file-loading-refactor-plan.md`](../../architecture-plan/cellpy-file-loading-refactor-plan.md)).

## Constraints

- **Behavior-preserving only** — assert today's outputs and exceptions; no production refactors.
- **Fixtures stay in `testdata/hdf5/`** — committed `.h5` files; no golden parquet for this issue
  (cellpy-file *is* the oracle; differs from Stage 0.1 pipeline goldens).
- **Fast PR gate** — mark a small subset `@pytest.mark.essential`; keep Tier 1 under ~2 min.
- **Plan doc paths** — issue text says `code-reviews/`; read
  [`architecture-plan/cellpy-file-loading-refactor-plan.md`](../../architecture-plan/cellpy-file-loading-refactor-plan.md)
  instead.
- **Do not fix `tests/fdv.py` legacy naming** (e.g. `cellpy_file_path_v4` → `*_v0.h5`) in this
  issue — add **new, correctly named** constants for the characterization suite only.

### Prior art

| Hit | Module / file | Reuse |
|-----|---------------|--------|
| Weak round-trip (no assertions) | `tests/test_cell_readers.py::test_cellpyfile_roundtrip` | **Coexist** — new file supersedes intent; leave old test untouched this issue. |
| Legacy load smoke | `test_cellpy_version_4/5`, `test_v6`, `test_load_cellpyfile` | **Coexist** — shallow; new suite adds shapes/meta/selector coverage. |
| `check_file_ids` | `tests/test_cell_readers.py`, `tests/test_cellpycell_internals.py` | **Coexist** — one thin test in new file calls `check_file_ids` to cover `_check_cellpy_file` in §1.1 traceability. |
| Frame compare helpers | `tests/golden_support.py` | **Mirror** — extract `cellpy_file_support.py` with `assert_frames_equal_cellpy_file()` reusing `date_time` approx tolerance where applicable. |
| HDF5 fixtures + paths | `tests/fdv.py`, `testdata/hdf5/` | **Extend** — add explicit `*_v5/_v7/_v8` path constants. |
| Step 0 spec | `architecture-plan/cellpy-file-loading-refactor-plan.md` § Step 0, §1.1 | **Authoritative** acceptance checklist. |
| Graph | `CellpyCell.load()` community in `cellreader.py` | Confirms load/save/check_file_ids as the public surface. |
| Toolbox | `.issueflows/00-tools/` | Empty — no helpers to reuse. |

## Approach

### 1. Shared compare helpers — `tests/cellpy_file_support.py`

Small module (not a golden suite):

- `load_cellpy_file(path, **kwargs) -> CellpyCell` — thin wrapper for consistency.
- `assert_data_frames_equal(actual, expected)` — `pandas.testing.assert_frame_equal` with
  sorted columns; for `date_time` columns reuse `golden_support.date_time_as_epoch_ns` +
  `pytest.approx(abs=1000)` (same cross-platform rule as Stage 0.1).
- `assert_meta_equal(actual_common, actual_test_dep, expected_common, expected_test_dep)` —
  compare `meta_common` / `meta_test_dependent` dataclass fields (ignore volatile timestamps if
  any appear on save — pin fields listed in plan Step 0: mass, nom_cap, cell_name, version, etc.).
- `assert_raw_limits_and_units_equal(cell_a, cell_b)` — dict equality on `raw_limits` /
  `raw_units`.
- `assert_fid_lists_equal(cell_a, cell_b)` — compare fid table contents (populated fixture below).

### 2. Main test module — `tests/test_cellpy_file_roundtrip.py`

Structure by concern (one file, as issue acceptance specifies):

#### A. v8 round-trip (`@pytest.mark.essential`)

1. Load `testdata/hdf5/20160805_test001_45_cc_v8_with_fids.h5` (see §4 — fid-populated v8).
2. Snapshot in-memory state: `raw`, `steps`, `summary`, meta dicts, `raw_limits`, `raw_units`.
3. `save()` to `tmp_path`, fresh `CellpyCell`, `load()` reload.
4. Assert frame equality (all three tables), meta fields, limits/units, **and fid list**.
5. Optionally assert HDFStore keys unchanged (`/CellpyData/{raw,steps,summary,fid,info,...}`).

Covers write path: `save`, `_save_to_hdf5`, `_create_infotable`, `_convert2fid_table`,
`_fix_dtype_step_table` (normal path), and read path through `_load_hdf5_current_version` +
extractors.

#### B. Limits-prefix trap (`@pytest.mark.essential`)

After save to `tmp_path`, open with `pd.HDFStore` and assert:

- `prms._cellpyfile_raw_limit_pre_id == ""`.
- Every key in `data.raw_limits` appears as a **top-level column** in `/CellpyData/info`
  (unprefixed — e.g. `current_hard`, not `limit_current_hard`).
- Unit columns remain prefixed (`raw_unit_*`).

Documents the inverted loop at `cellreader.py:2452–2455`.

#### C. Selector — `max_cycle` (`@pytest.mark.essential`)

Parametrize `max_cycle=3` (known good from probe: 18→3 cycles, `limit_data_points=3119`):

- `load(..., selector={"max_cycle": N})` sets `limit_data_points` and `limit_loaded_cycles`.
- Summary row count == N; raw/steps row counts match truncated data (compare against full load
  sliced consistently).
- Covers `_unpack_selector`, `_extract_summary/raw/steps_from_cellpy_file`,
  `_hdf5_locate_data_points_from_max_cycle_number`, `_hdf5_cycle_filter`.

#### D. Legacy version matrix (full suite only)

Parametrize committed fixtures (correct filenames):

| File | Version | Expect |
|------|---------|--------|
| `*_v4.h5` | 4 | Load with `accept_old=True`; assert raw/summary shapes, renamed columns present |
| `*_v5.h5` | 5 | Same |
| `*_v6.h5` | 6 | Same |
| `*_v7.h5` | 7 | Same + legacy meta path |
| `*_v0.h5` | n/a | `WrongFileVersion` ("VERY old") |

Per-version: assert `data.raw.shape`, `data.summary.shape`, a small set of canonical column
names post-rename (from `HeadersNormal` / `HeadersSummary`), and `cellpy_file_version` meta when
available. Keeps tests fast (shape + spot columns, not full frame diff on legacy).

#### E. Failure mode — missing store key (full suite)

Copy v8 fixture to `tmp_path`, open with `pd.HDFStore`, remove `/CellpyData/summary` (or `/raw`),
close, then `load()` and assert:

- Raises `Exception` (current type — do **not** change to `CorruptCellpyFile` yet).
- Message contains `"OH MY GOD"` and the missing key path.

Covers `_check_keys_in_cellpy_file`.

#### F. Freshness helper smoke (full suite)

One test: `check_file_ids(rawfiles=..., cellpyfile=v8_path)` returns expected structure when
raw file matches fixture provenance (reuse paths from existing `test_check_file_ids` pattern).
Covers `_check_cellpy_file` / `_check_HDFStore_available` indirectly.

### 3. §1.1 method coverage traceability

All listed methods are **private** except `load`, `save`, `check_file_ids`. Tests exercise them
through the public API except where noted:

| Method | Exercised by |
|--------|----------------|
| `load`, `_load_hdf5`, `_get_cellpy_file_version` | All load tests |
| `_load_hdf5_current_version`, `_extract_*` (v8) | A |
| `_load_hdf5_v5/v6/v7`, `_load_old_hdf5`, `_load_old_hdf5_v3_to_v4` | D |
| `_create_initial_data_set_from_cellpy_file` | A, D |
| `_check_keys_in_cellpy_file` | E |
| `_hdf5_locate_*`, `_hdf5_cycle_filter`, `_unpack_selector` | C |
| `_extract_meta_from_old_*`, `_extract_from_meta_dictionary` | D, A (meta asserts) |
| `_convert2fid_list`, `_convert2fid_table` | A (round-trip with fid-populated fixture) |
| `save`, `_save_to_hdf5`, `_create_infotable`, `_fix_dtype_step_table` | A, B |
| `check_file_ids`, `_check_cellpy_file`, `_check_HDFStore_available` | F |

**Note:** `_fix_dtype_step_table`'s `TypeError` retry branch is only hit on exotic dtypes; normal
v8 round-trip covers the happy path. A synthetic dtype-break test is **out of scope** unless we
find a natural fixture trigger during implementation.

### 4. Fixtures — `testdata/hdf5/` + `tests/fdv.py`

**Fid-populated v8 oracle (confirmed):** generate once from the canonical Arbin
`testdata/data/20160805_test001_45_cc_01.res`, commit as
`testdata/hdf5/20160805_test001_45_cc_v8_with_fids.h5`:

```text
from_raw → mass=1.0 → make_step_table → make_summary → save (v8)
```

Verify after save: load without *no fid_table* warning; `data.raw_files` / fid table non-empty.
Add a one-line note in `tests/data/goldens/README.md` or `tests/README.md` that this file is a
**committed characterization fixture** (not a golden parquet suite) — regenerate only when
cellpy-file v8 write semantics intentionally change.

**Existing v8** (`*_v8.h5`, no fids) stays for legacy-matrix adjacency; round-trip oracle uses
`*_v8_with_fids.h5`.

Add path constants in `fdv.py` (do not rename existing symbols):

```python
cellpy_file_path_v5 = .../20160805_test001_45_cc_v5.h5
cellpy_file_path_v7 = .../20160805_test001_45_cc_v7.h5
cellpy_file_path_v8 = .../20160805_test001_45_cc_v8.h5
cellpy_file_path_v8_with_fids = .../20160805_test001_45_cc_v8_with_fids.h5
```

Primary oracle for tests A/B/C/F: `cellpy_file_path_v8_with_fids`.

### 5. Documentation

Add a short **Cellpy-file characterization** subsection to `tests/README.md` pointing at
`test_cellpy_file_roundtrip.py`, essential vs full markers, and `testdata/hdf5/` layout.

## Files to touch

| Path | Change |
|------|--------|
| `tests/test_cellpy_file_roundtrip.py` | **New** — all characterization tests |
| `tests/cellpy_file_support.py` | **New** — compare helpers |
| `tests/fdv.py` | Add v5/v7/v8 + `v8_with_fids` path constants |
| `testdata/hdf5/20160805_test001_45_cc_v8_with_fids.h5` | **New** — committed fid-populated v8 oracle |
| `tests/README.md` | Document new suite + essential subset + fixture regen note |
| `tests/test_cell_readers.py` | One-line comment on `test_cellpyfile_roundtrip` → new module |

No changes to `cellpy/readers/cellreader.py` or workflows.

## Test strategy

```bash
# During development (inner loop)
uv run pytest tests/test_cellpy_file_roundtrip.py -v

# PR gate subset (after marking essential)
uv run pytest -m essential --ignore=tests/test_plotutils_summary_plot.py

# Before merge
uv run pytest tests/test_cellpy_file_roundtrip.py
uv run pytest   # full suite — ensure legacy tests still pass
```

**Essential budget:** target **3–4** new essential tests (A + B + C; optionally v0 failure if
still fast). Legacy matrix + corrupt-file tests stay unmarked.

Expected essential count after merge: ~21–22 (was 18 after #428).

## Confirmed decisions (2026-07-09)

1. **Full frame equality** on v8 round-trip (raw/steps/summary) in essential — try as-is; split
   only if CI essential job exceeds ~30s for this test.
2. **Build fid-populated fixture** from `.res` → `*_v8_with_fids.h5`; round-trip asserts fid list.
3. **Leave** `test_cellpyfile_roundtrip`; add one-line pointer comment to `test_cellpy_file_roundtrip.py`.

## Branch

Suggest `429-cellpy-file-characterization-tests` off current `master` before `/iflow-start`.
