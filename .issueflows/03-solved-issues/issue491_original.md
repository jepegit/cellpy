# Issue #491: Iterative fixes: full-suite test failures

Source: https://github.com/jepegit/cellpy/issues/491

## Original issue text

Interactive `/iflow-fix` session addressing failures from `uv run pytest`:

- `test_extract_fids_from_cellpy_file` â€” AttributeError: `_extract_fids_from_cellpy_file` moved to module function
- `test_check_file_ids_external_not_accessible` â€” TimeoutError from live SCP connection attempt
- `test_curve_extraction_matches_golden[curve_get_dcap_null_cycle]` â€” ODBC/Access error in full suite (passes in isolation)

Individual fixes are recorded in the status markdown; landed together via `/iflow-close`.
