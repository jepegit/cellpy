# Plan: #164 `CellpyCell.update()`

Confirmed approach (autonomous run under #783 stage 2; user asked to
"process the issues"). Builds on #778 (`update_core_data`), #779 (protocol),
#780 (`load_since` on four loaders).

## Approach

1. `CellpyCell.update(force=False, **loader_kwargs) -> bool` in
   `cellpy/readers/cellreader.py`, before `merge`.
2. Change detection: fresh `FileID` size/mtime vs stored `raw_data_files`;
   db sources always "changed".
3. Loader recovery from `data._provenance["source_type"]` via
   `set_instrument` (cellpy-file loads carry the default tester).
4. Marker derived from `data.raw` (`_marker_from_raw`: both `row_count` and
   `last_source_datapoint_num`, rewound to the last cycle start). No new
   cellpy-file field.
5. Incremental path (single fid + native schema + harmonized raw + loader
   matches `SupportsIncrementalLoad`): `load_since` → stamp `test_id`, align
   dtypes → `_update_from_raw_rows` (`core.update_core_data` +
   `_add_summary_extras` + `_refresh_scaled_summary_columns`).
6. Fallback full reload (`ValueError`/`LoaderError`, multi-file,
   non-incremental loader): `from_raw` on all sources, restore
   `meta_common` / `cycle_mode` / `cell_name`, `make_step_table`,
   `make_summary(find_ir=...)`.
7. `_refresh_fid`: size/mtimes, `last_data_point`, `raw_data_files_length`.
8. `tests/incremental_support.incremental_update` delegates to the new engine.

## Tests (`tests/test_cell_update.py`, essential)

no-op, growth == full load, two growths (marker), FileID refresh, cellpy-file
round trip, single-cycle fallback keeps meta, force, no source raises,
non-incremental loader routes to full reload.

## Docs

`incremental-load-protocol.md` section for #164, `docs/agents/index.md`,
root `AGENTS.md` quick facts, HISTORY bullet, test-registry rows.

## Out of scope

Poll loop (#781), batch live refresh (#782), multi-file incremental merge
(falls back to full reload).
