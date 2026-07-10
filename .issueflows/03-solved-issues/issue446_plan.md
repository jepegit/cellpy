# Issue #446 — plan

## Goal

Extract the cellpy-file layout spec and other non-config `prms.py` constants into
their proper owning modules, with `prms` aliases preserved so behavior stays
identical. This is the shared Step 1 of the file-loading and configuration plans.

## Constraints

- **Behavior-preserving:** no user-visible changes; full suite must stay green.
- **Stage 1 scope only:** create `cellpy_file/format.py` and relocate constants —
  do **not** move `cellreader.py` I/O methods yet (file-loading plan Steps 2–6).
- **Limits-prefix trap (#429):** keep `raw_limit_prefix == ""` verbatim in the v8
  format spec; do not fix the inverted `_create_infotable` loop in this PR.
- **Alias window:** `prms._cellpyfile_*` remain as module-level aliases pointing
  at `format.py` (underscore-private, but `batch_helpers`, tests, and scripts may
  touch them).
- **Version constants:** re-export `CELLPY_FILE_VERSION` / `MINIMUM_CELLPY_FILE_VERSION`
  from `format.py` but keep `internal_settings.py` as the canonical definition site
  (avoids import-cycle with `internal_settings → prms`).
- **Parent issue:** jepegit/cellpy#459 (Stage 1 tracking); prerequisite Stage 0
  (#439) is complete on `master` (v1.0.4a4).

### Prior art

- [`architecture-plan/cellpy-file-loading-refactor-plan.md`](../../architecture-plan/cellpy-file-loading-refactor-plan.md) — Step 1 (§4), `CellpyFileFormat` design (§3.2), limits-prefix trap (Step 0).
- [`architecture-plan/cellpy2-configuration-and-parameters-plan.md`](../../architecture-plan/cellpy2-configuration-and-parameters-plan.md) — Step 1 (§4): purge non-config constants from `prms.py`.
- **Stage 0 oracles:** [`tests/test_cellpy_file_roundtrip.py`](../../tests/test_cellpy_file_roundtrip.py) (round-trip, legacy matrix, limits-prefix trap `test_v8_limits_stored_unprefixed_in_info_table`), [`tests/cellpy_file_support.py`](../../tests/cellpy_file_support.py).
- **Prms characterization:** [`tests/test_prms.py`](../../tests/test_prms.py), [`tests/prms_support.py`](../../tests/prms_support.py) — inventory/parity helpers from #430.
- **Deprecation machinery (#437):** [`cellpy/_deprecation.py`](../../cellpy/_deprecation.py) — available if we want `warn_once` on `prms._cellpyfile_*` access; not required for Step 1 (aliases are silent).
- **Toolbox:** `.issueflows/00-tools/` — no format-spec helper; `scan_hardcoded_headers.py` is for header literals, not file layout.
- **Graph (stale at `6faf87c9`):** Communities around `CellpyCell`, `load_cellpy_file`, `prms` inventory tests — confirms `cellreader.py` + `prms.py` as the hot zone; no existing `cellpy_file` package.

## Approach

### 1. Create `cellpy/readers/cellpy_file/` package (format spec only)

Add:

```
cellpy/readers/cellpy_file/
    __init__.py    # re-export CellpyFileFormat, FORMAT_* constants, get_format()
    format.py      # frozen dataclass + version registry
```

**`CellpyFileFormat`** (frozen dataclass) fields:

| Field | Current source |
|-------|----------------|
| `root` | `prms._cellpyfile_root` (`"CellpyData"`) |
| `raw_dir`, `step_dir`, `summary_dir`, `fid_dir` | prms lines 392–395 |
| `common_meta_dir`, `test_dependent_meta_dir` | prms lines 396–397 |
| `raw_unit_prefix`, `raw_limit_prefix` | prms lines 399–400 |
| `complevel`, `complib` | prms lines 402–403 |
| `raw_format`, `summary_format`, `stepdata_format`, `infotable_format`, `fidtable_format` | prms lines 404–408 |

**Version registry** — one `CellpyFileFormat` per historical layout (plan §3.2):

| Key | Layout | Notes |
|-----|--------|-------|
| `FORMAT_V8` | Modern (`/raw`, `/steps`, …) | Canonical write spec; matches current prms values |
| `FORMAT_V7`, `FORMAT_V6`, `FORMAT_V5` | Same modern paths | Identical to v8 in today's readers |
| `FORMAT_V4` | Legacy (`/dfdata`, `/step_table`, `/dfsummary`, `/fidtable`) | From `_load_old_hdf5_v3_to_v4` (cellreader.py:2073–2078) |

Expose `get_format(version: int) -> CellpyFileFormat` mapping 4→`FORMAT_V4`, 5–8→modern
formats. Re-export version ints from `internal_settings` in `format.py` for convenience.

**Do not** wire `cellreader.py` loaders to `get_format()` in this PR — kwarg defaults
and inline `"CellpyData"` strings stay until file-loading Step 4. Duplication is
expected and locked by existing Stage 0 tests.

### 2. Rewire `prms._cellpyfile_*` as aliases

In `prms.py`, delete the literal assignments (lines 391–408) and replace with aliases
to `FORMAT_V8` fields, e.g.:

```python
from cellpy.readers.cellpy_file.format import FORMAT_V8 as _fmt
_cellpyfile_root = _fmt.root
_cellpyfile_raw = _fmt.raw_dir
# … etc.
```

Zero call-site edits needed (`cellreader.py`, `batch_core.py`, tests keep using
`prms._cellpyfile_*`).

### 3. Move template-registry constants

Move `_github_templates_repo`, `_standard_template_uri`, `_registered_templates` from
`prms.py` to a small owning module — **`cellpy/utils/template_registry.py`** (new,
~15 lines). Update `cli.py` (two call sites) to import from there.

Optional: keep `prms._registered_templates` as a deprecated alias for one release
window. Only `cli.py` uses it today — direct import is enough; skip prms alias unless
you want belt-and-suspenders.

### 4. Move example-data URL constants

Move `_url_example_data`, `_url_example_data_download_with_progressbar`,
`_example_data_in_example_folder_if_available` into **`cellpy/utils/example_data.py`**
(module-level private constants). Update the three internal references in that file;
drop `prms` indirection.

### 5. Delete dead `_globals_*` state

`_globals_status`, `_globals_errors`, `_globals_message` (prms.py:424–426) have **zero**
callers in the repo. Delete all three — no replacement needed (already unused).

### 6. Ordering within the PR

1. Add `format.py` + tests locking values.
2. Switch `prms._cellpyfile_*` to aliases; run essential suite.
3. Move template + example-data constants; update `cli.py` / `example_data.py`.
4. Delete `_globals_*` and moved constant definitions from `prms.py`.
5. Full suite + grep verification.

## Files to touch

| Path | Change |
|------|--------|
| `cellpy/readers/cellpy_file/__init__.py` | **New** — public re-exports |
| `cellpy/readers/cellpy_file/format.py` | **New** — `CellpyFileFormat`, `FORMAT_V4`…`FORMAT_V8`, `get_format()` |
| `cellpy/parameters/prms.py` | Replace `_cellpyfile_*` literals with aliases; remove moved constants + `_globals_*` |
| `cellpy/utils/template_registry.py` | **New** — template registry dict + GitHub URI |
| `cellpy/utils/example_data.py` | Own the example-data URL constants internally |
| `cellpy/cli.py` | Import template registry from new module (2 sites) |
| `tests/test_cellpy_file_format.py` | **New** — format spec parity + limits-prefix + version dispatch smoke |

**Explicitly not touched this PR:** `cellreader.py` (I/O stays), `batch_helpers.py`
(hard-coded `"/CellpyData"` → Stage 1.4 / file-loading Step 6).

## Test strategy

**Commands** (per project convention):

```bash
uv run pytest -m essential
uv run pytest tests/test_cellpy_file_roundtrip.py tests/test_cellpy_file_format.py -v
uv run pytest   # full suite before merge
```

**New tests** (`tests/test_cellpy_file_format.py`):

- `FORMAT_V8` field values match every `prms._cellpyfile_*` alias (parity contract).
- `raw_limit_prefix == ""` on v8 format (limits-prefix trap).
- `get_format(4)` returns legacy dirs; `get_format(8)` returns modern dirs.
- `get_format(5/6/7/8)` all share modern layout paths.

**Existing oracles (must stay green, no edits expected):**

- `tests/test_cellpy_file_roundtrip.py` — round-trip, legacy matrix, selector, limits trap.
- `tests/test_prms.py` — prms inventory/parity (#430).
- `tests/test_cell_readers.py` — uses `prms._cellpyfile_fid` / `_cellpyfile_root`.

**Manual grep check after implementation:**

```bash
rg '_cellpyfile_' cellpy/parameters/prms.py   # aliases only, no literals
rg '"/CellpyData"' cellpy/ --glob '*.py'      # expect batch_helpers only
```

## Open questions

1. **Template registry alias:** Move to `template_registry.py` with direct `cli.py`
   import only (recommended), or also keep `prms._registered_templates` alias?
2. **Issue branch:** Create `446-format-spec` (or `446-stage-1-1-format`) before
   `/iflow-start`? Currently on `master` (clean except untracked `.issueflows/` files).
3. **`CellpyFileFormat.version` field:** Include explicit `version: int` on each
   frozen instance, or keep version mapping only in `get_format()`? (Recommend:
   include `version` for clarity and test assertions.)

---

**Confirm:** Accept / Revise / Abort
