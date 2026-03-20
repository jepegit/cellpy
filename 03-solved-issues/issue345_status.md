# Issue #345 – Status

**Issue:** batch - read custom json  
**Original:** `issue345_original.md`

## Summary

- Batch utility should support reading info from custom JSON files (not only the currently supported format).
- Allow file searching after reading the JSON file.

## Current status

- [x] Done

## Done

- **Fixture and tests**: Added `tests/fixtures/cellpy_batbase_like.json` and `custom_json_batch_like.json`. Unskipped and hardened `test_reading_json_db` to use fixture and testdata paths. Added `test_batbase_json_reader_pages_dict_shape`, `test_custom_json_reader_pages_dict_and_engine`, and `test_find_files_skip_file_search`.
- **Custom JSON**: Added `CustomJSONReader` in `cellpy/readers/json_dbreader.py` with configurable `column_map` (JSON key → cellpy journal key). Supports arbitrary JSON schemas.
- **File search**: File searching after reading JSON was already in place; added optional `skip_file_search=True` to `batch_helpers.find_files` so existing paths are not overwritten when the JSON already contains them.
- **Engine**: Refactored `simple_db_engine` to use a generic branch for any reader with `pages_dict` (no longer special-casing only `BatBaseJSONReader`).
- **LabJournal**: Registered `custom_json_reader` in `LabJournal` (requires `db_file`, optional `column_map` in kwargs).
- **Docs**: Documented custom JSON readers and file search in `batch.create_journal`; updated this status file.

## Remaining

- (none)

## Notes

- BatBaseJSONReader unchanged; no `from_batch` implementation.
- CustomJSONReader maps JSON columns to journal keys via `column_map`; unmapped columns get None or empty lists. Use `db_reader="custom_json_reader"` with `db_file` and optional `column_map` when creating a batch from arbitrary JSON.

- [x] Done
