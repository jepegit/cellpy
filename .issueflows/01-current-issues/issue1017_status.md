# Issue #1017 status

`journal_from_db(skip_file_search=True)` crashes with the Excel reader.

- [ ] Done

PR: https://github.com/jepegit/cellpy/pull/1020 (#1020, draft)
Branch: `cursor/1017-journal-from-db-skip-file-search-3975`

## What's done

- Issue captured, plan confirmed (`issue1017_plan.md`).
- `_dbengine.find_files`: the `skip_file_search=True` branch pads missing or
  empty `raw_file_names` / `cellpy_file_name` with `[None] * n_cells`
  (pre-filled JSON paths untouched). Docstring updated.
- `batch.db.journal_from_db` docstring: flag valid for any reader; unset file
  columns are `None`, `update()` marks those cells `FAILED`.
- Tests: `tests/test_dbreader.py::test_simple_db_engine_skip_file_search_excel_reader`
  (essential; reproduced `ValueError: All arrays must be of the same length`
  before the fix) and
  `tests/test_batch.py::test_find_files_skip_file_search_pads_missing_columns`.
- `uv run pytest tests/test_dbreader.py tests/test_batch.py`: 71 passed.
- `uv run pytest -m essential`: 829 passed, 64 skipped
  (`tests/test_arbin_variants_two_stage.py` ignored locally — `pyodbc` needs
  `libodbc.so.2`, missing on this VM; unrelated to the change).

## Remaining work

- `HISTORY.md` `[Unreleased]` bullet (at `/iflow-close`).
