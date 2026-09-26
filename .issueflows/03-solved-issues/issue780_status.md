# Issue #780 status

- [x] Done

## What's done

- `cellpy/readers/instruments/incremental.py`: `last_cycle_start`,
  `vendor_column` (shared rewind-to-cycle-start policy, documented there).
- `TxtLoader.query_file(name, skiprows=None)` + `TxtLoader._load_since_rows`;
  `neware_txt` and `maccor_txt` `DataLoader.load_since` delegate to it.
  `TxtLoader` itself does not advertise the protocol.
- `arbin_res.DataLoader.load_since` via `parse(..., data_points=(N+1, None))`.
- `arbin_sql._query_sql(name, since_data_point=None)` adds a `Data_Point >`
  clause on the fully qualified table; `parse(since_data_point=)`;
  `DataLoader.load_since`.
- Both arbin loaders clear their parse cache; text path clears
  `_parsed_frame`.
- `tests/test_load_since.py` (11 essential tests, incl. the #778 oracle
  driven by a real chunk; arbin_res skips without mdbtools).
- `incremental-load-protocol.md` extended; registry rows; HISTORY bullet.

## Remaining work

- None in this issue. `CellpyCell.update()` consuming these chunks is #164.
