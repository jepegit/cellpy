# Issue #1017 — plan

## Goal

`journal_from_db(..., skip_file_search=True)` must return a journal for every
reader instead of raising `ValueError: All arrays must be of the same length`.
Cells whose files were not searched get `None` in `raw_file_names` /
`cellpy_file_name` (same shape as a filefinder miss).

## Constraints

- Toolchain: `uv run pytest` (see `this-project.md`); merge gate is `-m essential`.
- No behaviour change for the default `skip_file_search=False` path.
- Do not change the JSON readers' public `pages_dict` contract (they seed the
  two file columns as `[]` too — `BatBaseJSONReader` and `CustomJSONReader`,
  `cellpy/readers/json_dbreader.py`); fix once, at the seam both paths share.
- Keep `_create_pages_dict` seeding as is (tests in `tests/test_dbreader.py`
  and `tests/test_batch.py` read it directly); `find_files` is the only place
  that knows whether the columns will be filled.
- `HISTORY.md` `[Unreleased]` bullet at close (`v2.1.4.post` milestone).

### Prior art

- `find_files` (`cellpy/batch/_dbengine.py`) already seeds `[]` when the
  columns are absent and appends per cell; the `skip_file_search` early return
  is the only branch that returns without normalising lengths → mirror the
  seeding there, padded to the cell count.
- Filefinder miss convention: `raw_files = None`, `cellpyfile = None` per cell
  (`find_files` loop) → reuse `None` as the "not searched" value so
  `policy.py` / `facade.py` (`row.get(...)`, `_clean`, FAILED marking) keep
  working unchanged.
- `tests/test_batch.py::test_find_files_skip_file_search` — existing unit test
  for the skip branch with pre-filled columns; extend alongside it.
- Toolbox (`.issueflows/00-tools/`): nothing applicable. `graphify-out/` absent.

## Approach

1. In `find_files`, replace the bare `if skip_file_search: return info_dict`
   with: compute `n = len(file_name_indicators)` (fallback `filename`), then for
   each of `hdr_journal["raw_file_names"]` / `hdr_journal["cellpy_file_name"]`:
   if the key is missing or its list is empty while `n > 0`, set it to
   `[None] * n`. Pre-filled columns (JSON carrying paths) stay untouched.
2. Docstrings: `find_files` (skip now pads instead of "returned unchanged") and
   `journal_from_db` in `cellpy/batch/db.py` (`skip_file_search=True` also
   valid for the Excel reader; file columns come back `None`, so `b.update()`
   marks those cells `FAILED` until paths are filled or a search is run).
3. No change to `_create_pages_dict` or the JSON readers.

Alternative rejected: raising on `skip_file_search=True` for the Excel reader —
users legitimately want a journal without a (slow/remote) file search and fill
paths afterwards; `None` per cell is the existing "not found" shape.

## Files to touch

- `cellpy/batch/_dbengine.py` — `find_files` skip branch pads the two columns;
  docstring.
- `cellpy/batch/db.py` — `journal_from_db` docstring wording.
- `tests/test_batch.py` — new `test_find_files_skip_file_search_pads_missing_columns`
  (missing + empty columns → `[None] * n`; `n == 0` → `[]`).
- `tests/test_dbreader.py` — `@pytest.mark.essential`
  `test_simple_db_engine_skip_file_search_excel_reader`: `simple_db_engine(reader,
  ids, skip_file_search=True)` on the Excel fixture returns one row per id with
  `None` file columns (reproduces #1017 before the fix).
- `HISTORY.md` — `[Unreleased]` bullet (at `/iflow-close`).

## Test strategy

- `uv run pytest tests/test_dbreader.py tests/test_batch.py -q`
- `uv run pytest -m essential` (merge gate)
- Repro before fix: the new engine test fails with `ValueError: All arrays
  must be of the same length`.

## Open questions

- None. (Optional: also make `journal_from_db` log at INFO that file columns
  are unset when `skip_file_search=True` and the reader is the Excel one —
  skipped for KISS unless wanted.)
