# Issue #761 — status

- [x] Done

## What's done

- Plan accepted: raise `LoaderError` from custom `DataLoader.validate` for
  declared-but-absent columns; rewrite the bad-fixture tests.
- `DataLoader.validate` on the custom loader: after rename, every key in
  `normal_headers_renaming_dict` must exist as a cellpy header; miss raises
  `LoaderError` naming the vendor column(s).
- Replaced silent-omit pin + xfail with
  `test_missing_column_raises_loader_error` (`@pytest.mark.essential`).
- `uv run pytest tests/test_bad_fixtures.py` — 5 passed.
- `uv run pytest -m essential` — 861 passed, 70 skipped.
- HISTORY `[Unreleased]` bullet; test-registry row.

## Remaining work

- None.
