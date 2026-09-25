# Incremental load protocol

**Issue:** [#779](https://github.com/jepegit/cellpy/issues/779)
**Status:** decided with the #779 plan.

## Context

Epic L needs an optional way for a loader to return rows since a marker.
Core `update_data` already trims overlap. The marker must not become a
cellpycore type.

## Decision

- Host `SupportsIncrementalLoad`, `LoadMarker`, and `IncrementalChunk` in
  cellpy `readers/instruments/contract.py`.
- `IncrementalChunk.new_raw` is a polars `DataFrame`, the same type as
  `LoaderResult.raw` and `update_data`'s `new_raw`.
- The protocol is methods-only, so `issubclass` works. It is not part of
  `InstrumentLoader`. Loaders that omit `load_since` stay valid.
- cellpycore is unchanged. Overlap trimming stays in `update_data`.

## Alternatives

- Put the protocol in cellpycore so `update_data` could take a marker.
  Rejected: the issue and the live-incremental design keep the contract
  between loaders and a future `CellpyCell.update()`.
- Use pandas for `new_raw` because some cellpy frames are still pandas.
  Rejected: the core merge primitive and the loader result are polars.

## Loaders that implement it (#780)

`arbin_res`, `arbin_sql`, `neware_txt`, `maccor_txt`. Every other shipped
loader stays full-read and does **not** match the protocol (`TxtLoader`
itself has the shared `_load_since_rows`, but only those two text loaders
expose `load_since`).

- `new_raw` is the frame `harmonize(parse())` yields for the rows read, so
  it has the same columns as `data.raw` on the harmonized load path and can
  go straight into `update_core_data`. `test_id` is stamped 0 by
  `harmonize`; the caller (`update()`, #164) re-stamps `active_test_id`.
- **Rewind to a cycle start.** `harmonize.normalize_reset_granularity`
  re-accumulates per-step capacity and rebases each cycle to start at 0
  using the *first row of the cycle*. A chunk that begins mid-cycle would be
  rebased against the wrong row without raising. So the marker a loader
  returns points at the first row of the last cycle it read, and the next
  call re-reads that cycle whole. The overlap is allowed by the contract and
  `update_data` keeps the new rows for it (`kept_raw = raw < r2_start`).
  Helper: `cellpy/readers/instruments/incremental.py::last_cycle_start`.
- **Marker field per source:** text loaders set `row_count` (file data rows
  before the re-read position; header lines are not counted); arbin sets
  `last_source_datapoint_num` (rows with a larger `Data_Point` are returned,
  via the existing `data_points` filter for `.res` and one extra `WHERE`
  clause for SQL Server). `byte_offset` is unused. `complete` is always
  `False`; none of these sources can tell a test has ended.
- `marker=None` or an all-`None` marker reads everything. A marker past
  the end gives an empty `new_raw` and the marker back unchanged (empty
  `new_raw` is a no-op for `update_core_data`).
- `load_since` clears the loader's parse cache (`_parsed_frame` /
  `_parsed_data`) so a later `loader()` never reuses a partial frame.
- A caller-made marker mid-cycle still reads the right rows, but the
  cycle-local rebase may differ from a full load. Only loader-made markers
  carry the equality guarantee.

## Link

Design §3 in `cellpy-design-and-development/active/cellpy2-live-incremental-design.md`.
`CellpyCell.update()` is #164. Tests: `tests/test_load_since.py`.
