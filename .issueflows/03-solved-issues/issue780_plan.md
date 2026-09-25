# Issue #780 plan — load_since for arbin_res, arbin_sql, neware_txt, maccor_txt

## Goal

Four shipped loaders advertise `SupportsIncrementalLoad` (#779) and return an
`IncrementalChunk` of harmonized native raw rows read since a `LoadMarker`,
plus the marker for the next call. Every other loader is unchanged and does
not match the protocol.

## Constraints

- Cellpy only. cellpycore unchanged; overlap trimming stays in `update_data`.
- `new_raw` is the same frame `harmonize(parse())` produces for a full load
  (the frame `CellpyCell.from_raw` uses as `data.raw` on the harmonized
  path), so a chunk is directly consumable by `update_core_data`.
- Cycle-local normalisation in `harmonize.normalize_reset_granularity`
  (PER_STEP re-accumulation, PER_TEST/PER_CYCLE rebase to 0 at cycle start)
  needs the whole cycle. A chunk that starts mid-cycle would be rebased
  wrongly. **Policy:** every `load_since` re-reads from the first row of the
  last cycle already seen. The marker therefore points at that cycle start
  ("consumed" = committed complete cycles); the trailing overlap is allowed
  by the contract and `update_data` keeps the new rows for it.
- The marker field is the one the source seeks on: `row_count` for the text
  loaders (data rows before the re-read position), `last_source_datapoint_num`
  for arbin (rows with a larger `Data_Point` are returned). `complete` stays
  `False`; none of these sources can tell that a test has ended.
- `load_since(source, None)` (or an all-`None` marker) returns every row.
  A marker past the end of the file returns an empty `new_raw` and the same
  marker (empty `new_raw` is a no-op for `update_core_data`).
- `load_since` must not leave a partial frame in the loader's parse cache
  (`_parsed_frame` / `_parsed_data`), or a later `loader()` would reuse it.
- Out of scope: `CellpyCell.update()` (#164), marker persistence, poll loop.

### Prior art

- `contract.py` — `LoadMarker`, `IncrementalChunk`, `SupportsIncrementalLoad`
  (#779). Structural; adding a `load_since` method is enough to match.
- `AutoLoader.parse()` / `declarations()` + `harmonize()` — the two-stage
  read every loader here already has. `TxtLoader.query_file` is the single
  `pd.read_csv` call; `parse_loader_parameters` resolves `sep` / `skiprows` /
  `header` (auto-formatter reads only the first 200 lines).
- `arbin_res.parse(source, **kwargs)` forwards `data_points=(d1, d2)` to
  `_loader_win` / `_loader_posix`, which already filter `Data_Point >= d1`.
- `arbin_sql.parse()` → `_query_sql(name)`; the SQL gets one extra
  `AND ... Data_Point > N` clause. No live server in-repo: mock via
  `mock_data_001.xlsx` sheet `arbin_sql` like `tests/test_sql.py`.
- `tests/incremental_support.py` (#778) — `incremental_update` +
  `assert_cell_frames_equal` are the oracle: head cell + real chunk must
  equal a full load.

## Approach

1. New helper module `cellpy/readers/instruments/incremental.py`:
   `last_cycle_start(frame, cycle_column) -> int` (row index of the first
   row of the last cycle; 0 when the column is missing or the frame is
   empty) and `vendor_column(declarations, native_name)` (inverse lookup in
   `column_map`).
2. `TxtLoader`:
   - `query_file(name, skiprows=None)` gains an optional override so a
     partial read reuses the same `pd.read_csv` call.
   - `_load_since_rows(source, marker)`: resolve formatter parameters the
     way `parse()` does, read data rows from `marker.row_count` on with a
     callable `skiprows` that keeps the header, harmonize, compute the
     rewind row on the vendor frame, return
     `IncrementalChunk(new_raw, LoadMarker(row_count=start + rewind))`.
     Clear `_parsed_frame` afterwards.
   - `neware_txt.DataLoader.load_since` and `maccor_txt.DataLoader.load_since`
     delegate to it. `TxtLoader` itself does not get `load_since`, so
     `local_instrument` / `batmo_bdf` / custom stay non-incremental.
3. `arbin_res.DataLoader.load_since`: `parse(source, data_points=(N + 1,
   None))`, harmonize, rewind on the vendor `Cycle_Index` / `Data_Point`
   columns, marker `last_source_datapoint_num = cycle_start_datapoint - 1`.
   Clear `_parsed_data`.
4. `arbin_sql`: `_query_sql(name, since_data_point=None)` adds the clause;
   `parse(source, since_data_point=…)`; `load_since` mirrors arbin_res.
5. Tests (`tests/test_load_since.py`, essential):
   - protocol membership: the four match, `pec_csv` / `biologics_mpr` /
     `local_instrument` do not.
   - neware: `load_since(file, None)` equals the full harmonized frame; a
     head file then the full file returns rows from the head's last cycle
     start; head cell + chunk through `incremental_update` equals
     `cellpy.get` of the whole file (the #778 oracle with a real chunk).
   - maccor: `load_since(file, None)` equals full; marker round-trip.
   - arbin_res (skip if `mdb-export` missing): full equality and the marker
     re-read from a mid-test datapoint.
   - arbin_sql: monkeypatched `_query_sql` records `since_data_point` and
     serves the mock sheet.
   - marker past end → empty `new_raw`, same marker.
6. Docs: extend `incremental-load-protocol.md` with the rewind policy and
   per-loader marker field; registry rows; HISTORY bullet at close.
