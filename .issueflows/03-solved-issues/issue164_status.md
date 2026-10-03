# Status: #164 `CellpyCell.update()`

- [x] Done

## Done

- `CellpyCell.update()` + helpers (`_raw_sources_changed`,
  `_ensure_loader_for_update`, `_marker_from_raw`, `_update_incremental`,
  `_update_from_raw_rows`, `_summary_has_ir`, `_refresh_fid`,
  `_update_full_reload`) and module helpers `_frame_to_pandas`,
  `_align_dtypes` in `cellpy/readers/cellreader.py`; `_load_marker` attribute
  initialised in `__init__`.
- `tests/incremental_support.incremental_update` now delegates to
  `CellpyCell._update_from_raw_rows` (the #778 oracle covers the shipped engine).
- `tests/test_cell_update.py`: 9 essential tests.
- Docs: `incremental-load-protocol.md` (#164 section), `docs/agents/index.md`,
  root `AGENTS.md`, HISTORY `[Unreleased]`, test-registry.

## Verification

- `uv run pytest tests/test_cell_update.py tests/test_incremental_update.py tests/test_load_since.py` green.
- `uv run pytest -m essential` — see PR.

## Notes

- Branch `164-cell-update` stacked on `780-load-since` (PR #1101); PR base
  is `780-load-since` until #1101 merges.
- Multi-file cells and non-incremental loaders take the full-reload path
  (documented; the smart multi-file merge from the original issue is not
  needed for the live use case, one file per running test).

## Remaining

- None for this issue. Stage 3: #781 (poll loop), #782 (batch live refresh).
