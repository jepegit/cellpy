# Issue #449 — Plan

## Goal

Complete Stage 1.4 (file plan Steps 6–7): redirect out-of-band HDF5 readers into
`cellpy_file`, replace the bare `Exception("OH MY GOD! …")` with `CorruptCellpyFile`,
narrow `CellpyCell.load()`'s blanket `AttributeError` handler, and add a `cellpy convert`
CLI for v&lt;8 → v8 upgrades — all behavior-preserving on `master`.

## Constraints

- **Stage 1 only** — no user-visible behavior changes except deliberately documented
  exception-type updates (#429 failure-mode tests).
- **Dependencies satisfied** — #448 (read/write in `cellpy_file/`) and #456 (conventions +
  `CorruptCellpyFile` stub) are closed; reuse their modules.
- **Batch link mode** must keep single-table reads (no full `load()`); add a regression
  test that `read_table` does not populate raw/summary.
- **Legacy layouts** — `read_table` / `read_fid_table` must resolve the on-disk version
  via `get_cellpy_file_version` + `get_format()` so v4–v7 key names work (not only v8
  `FORMAT_V8` paths).
- **External paths** — centralize `OtherPath.is_external` temp-copy in `cellpy_file`
  (currently only in `_check_cellpy_file`).
- **PR gate** — `uv run pytest -m essential` green; mark new characterization tests
  `@pytest.mark.essential` where they guard regressions.

### Prior art

| Hit | Module / file | Reuse |
|-----|---------------|--------|
| Out-of-band step read | `batch_helpers.look_up_and_get` | **Migrate** — delegate to `cellpy_file.read_table`; keep function as thin wrapper for call-site stability. |
| Fid freshness check | `cellreader._check_cellpy_file` | **Migrate** — delegate HDF5 open + fid read to `cellpy_file.read_fid_table`; keep `ids` dict assembly + `check_on` logic on `CellpyCell`. |
| Cycle / limits filtering | `cellpy_file.read.hdf5_cycle_filter`, `extract_summary_from_cellpy_file`, `extract_steps_from_cellpy_file` | **Reuse** — `read_table` with `max_cycle` on steps mirrors summary→limits→steps order from the full read path. |
| Key validation | `cellpy_file.keys.check_keys_in_cellpy_file` | **Migrate** — raise `CorruptCellpyFile` instead of bare `Exception`. |
| Exception stub | `cellpy.exceptions.CorruptCellpyFile` | **Use** — already subclasses `IOError` + `CellpyError` (#456). |
| Version + layout | `cellpy_file.meta.get_cellpy_file_version`, `format.get_format` | **Reuse** for path/key resolution. |
| Fid conversion | `cellpy_file.fids.convert2fid_list` | **Reuse** in `read_fid_table` and `_check_cellpy_file`. |
| Failure-mode oracle | `tests/test_cellpy_file_roundtrip.py::test_missing_required_store_key_raises_current_exception` | **Update** — expect `CorruptCellpyFile`, keep message/key-path assertions. |
| CLI patterns | `cellpy/cli.py` (click group), `tests/test_cellpy_cmd.py` (`CliRunner`) | **Mirror** for `convert` command test. |
| Toolbox | `.issueflows/00-tools/` | **None found** (index checked). |
| Graph | `graphify-out/` | **Absent** — grep-only discovery. |

## Approach

### 1. Path resolution helper (`cellpy_file`)

Add a small internal helper (e.g. `_resolve_hdf5_path(path) -> str | Path`) in
`cellpy_file/read.py` (or a tiny `paths.py` if cleaner):

- Accept `str | Path | OtherPath`.
- If `OtherPath.is_external`, `copy()` to a local temp path (same behavior as
  `_check_cellpy_file` today).
- Return a path suitable for `pd.HDFStore`.

Used by `read_table`, `read_fid_table`, and optionally left for a follow-up on
`load()`'s missing external handling (not required for acceptance).

### 2. `read_table(path, table_name, *, max_cycle=None) -> pd.DataFrame`

New public function in `cellpy_file/read.py`, exported from `cellpy_file/__init__.py`.

**Table name contract:** accept the same values callers pass today — prms dir constants
such as `prms._cellpyfile_step` (`/steps`), `prms._cellpyfile_summary`, etc.

**Algorithm:**

1. Resolve path via `_resolve_hdf5_path`.
2. Read `cellpy_file_version`; `fmt = get_format(version)`.
3. Build store key: `f"/{fmt.root}{table_name}"` (table_name already includes leading `/`).
4. Open store with `with pd.HDFStore(...)`.
5. **If `max_cycle` is set and table is the step table:**
   - Read summary slice with `index <= max_cycle` (reuse `extract_summary_from_cellpy_file`
     logic or inline the same `where` + `limit_data_points` computation).
   - Select steps; filter `point_last <= limit_data_points` (same as `extract_steps_from_cellpy_file`).
6. **Else:** `store.select(key)` (no cycle filter).
7. On `KeyError`, raise `WrongFileVersion` (preserves `look_up_and_get` / batch link
   behavior).

**`batch_helpers.look_up_and_get`:** replace body with a call to
`cellpy_file.read_table`, passing through `max_cycle`; ignore deprecated `root` arg
(or warn if `root != fmt.root`).

### 3. `read_fid_table(path) -> tuple[list[FileID], list[int]]`

New public function in `cellpy_file/fids.py` (or `read.py`):

1. Resolve path; detect version + `fmt.fid_dir`.
2. `with HDFStore`: `fid_table = store.select(f"/{fmt.root}{fmt.fid_dir}")`.
3. Return `convert2fid_list(fid_table)`.
4. On missing fid key: return `([], [])` or `None` handling — match current
   `_check_cellpy_file` (warn, return `None` upstream).

**`_check_cellpy_file`:** replace direct `HDFStore` usage with `read_fid_table`;
keep `ids` dict construction and `filestatuschecker` logic unchanged.

### 4. Typed exceptions

**`cellpy_file/keys.py`:** replace `raise Exception("OH MY GOD! …")` with
`raise CorruptCellpyFile(…)` — keep the missing-key path in the message for traceability.

**`cellreader.CellpyCell.load()`:** remove the blanket `except AttributeError` block
that sets `data = None` and logs "file version not supported". The version gate in
`cellpy_file.load()` now runs before extractors; genuine `AttributeError` bugs should
propagate. Preserve existing handling for `data is None` / warning paths for other
failure modes.

### 5. `cellpy convert` CLI

Add `@click.command()` `convert` to `cellpy/cli.py`:

```
cellpy convert <old.h5> [<new.h5>]
```

- **`old.h5`:** required input path.
- **`new.h5`:** optional output; default `{stem}_v8{suffix}` beside input (same
  directory, non-destructive).
- Implementation: `result = cellpy_file.load(old, accept_old=True)` then
  `cellpy_file.save(result.data, new)`.
- Echo paths + resulting `cellpy_file_version` on success; non-zero exit on failure.
- Register: `cli.add_command(convert)`.

### 6. Tests

| Test | File | Purpose |
|------|------|---------|
| `test_missing_required_store_key_raises_corrupt_cellpy_file` | `test_cellpy_file_roundtrip.py` | Update #429 oracle for new exception type. |
| `test_read_table_steps_max_cycle_matches_selector_load` | `test_cellpy_file_roundtrip.py` | `read_table(..., max_cycle=N)` equals full-load steps slice. |
| `test_read_table_does_not_load_raw` | `test_cellpy_file_roundtrip.py` | Assert only requested table is read (no `Data` population / side effects). |
| `test_convert_cli_v4_to_v8` | `test_cellpy_cmd.py` or roundtrip file | CliRunner: convert v4 fixture → tmp v8; reload asserts version 8 + tables present. |
| Existing `test_check_file_ids_matches_res_provenance` | unchanged | Covers `_check_cellpy_file` delegation. |

Mark the corruption + convert + batch-link parity tests `@pytest.mark.essential`.

## Files to touch

| Path | Change |
|------|--------|
| `cellpy/readers/cellpy_file/read.py` | Add `_resolve_hdf5_path`, `read_table`. |
| `cellpy/readers/cellpy_file/fids.py` | Add `read_fid_table`. |
| `cellpy/readers/cellpy_file/keys.py` | `CorruptCellpyFile` instead of bare `Exception`. |
| `cellpy/readers/cellpy_file/__init__.py` | Export `read_table`, `read_fid_table`. |
| `cellpy/utils/batch_tools/batch_helpers.py` | Delegate `look_up_and_get` → `read_table`. |
| `cellpy/readers/cellreader.py` | `_check_cellpy_file` → `read_fid_table`; narrow `load()` `AttributeError`. |
| `cellpy/cli.py` | Add `convert` command + register. |
| `tests/test_cellpy_file_roundtrip.py` | Update failure-mode test; add `read_table` tests. |
| `tests/test_cellpy_cmd.py` | Add `convert` CLI test. |

## Test strategy

```bash
uv run pytest -m essential          # PR merge gate
uv run pytest tests/test_cellpy_file_roundtrip.py tests/test_cellpy_cmd.py -v
```

Manual smoke: `uv run cellpy convert testdata/hdf5/20160805_test001_45_cc_v4.h5 /tmp/out_v8.h5`

## Open questions

1. **Default `convert` output name** — plan proposes `{stem}_v8{suffix}` when
   `new.h5` is omitted. OK, or prefer overwrite-in-place with `--force` flag?
2. **`look_up_and_get` deprecation** — keep as permanent thin wrapper, or add
   `warn_once` pointing at `cellpy_file.read_table`?
3. **`load()` external-path fix** — architecture plan notes `load()` doesn't handle
   `OtherPath.is_external` today. Out of scope for #449 acceptance, or include in this PR?
