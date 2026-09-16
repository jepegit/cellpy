# Issue #1028 — status

- [x] Done

## What's done

- Flipped packaged default `file_names.cellpy_file_extension` `h5` → `cellpy`
  in `FileNamesConfig`, `FileNamesClass`, and `.cellpy_prms_default.conf`.
- Docs: configuration reference default column.
- Tests: inventory expected value; constructed-name asserts in
  `test_filefinder` / `test_search_for_files` now expect `.cellpy`;
  `default_file_names` docstring updated.
- Targeted: 33 passed. `pytest -m essential`: 860 passed, 70 skipped.
- HISTORY Unreleased bullet.

## Remaining work

- None.

## Essential review

- Changed tests (`test_filefinder` name asserts, `test_search_for_files`)
  stay unmarked (name-construction only). Inventory already essential via
  `tests/test_prms.py`. No new tests.
