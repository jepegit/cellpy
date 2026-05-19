# Status for issue #356: Export bdf for dsToolbox

- [x] Done

## Summary

Added Battery Data Format (BDF) export for cellpy raw time-series, with
optional cycle filtering, for use by UiA's `dsToolbox` and any other
BDF-aware tool.

## What shipped

- New `CellpyCell.to_bdf(filename, *, cycles=None, last_cycle=None,
  header_style="preferred", format="csv") -> Path` in
  `cellpy/readers/cellreader.py`. Same function exposed at module level
  as `cellpy.exporters.to_bdf`.
- New `cellpy/exporters/` package (first inhabitant: `bdf.py`).
- New `cellpy/filters/` package with reusable
  `filter_cycles(df, cycles, last_cycle, column) -> df` in `cycles.py`.
- Unit conversion delegated to `cellpy.readers.core.Q` (pint), the same
  helper `CellpyCell` already uses for capacity / mass arithmetic. No
  hand-rolled factor table; non-default `cellpy_units` (e.g.
  `current="mA"`, `energy="kWh"`) work automatically.
- Default header row uses BDF "Preferred Labels" (`Test Time / s`,
  `Voltage / V`, ...); `header_style="machine"` switches to
  `test_time_second`-style names.
- Default extension is `.bdf.csv` when no suffix is given; explicit
  suffix is honoured.
- Required BDF columns missing from `data.raw` raise `ValueError`;
  recommended/optional missing columns are warn-and-skipped.

## Architectural rule established

`cellpy/readers/cellreader.py` (and the `CellpyCell` class) imports
export logic from `cellpy.exporters` and filter logic from
`cellpy.filters`, never from `cellpy.utils`. Recorded in
`.issueflows/04-designs-and-guides/bdf-export.md` so future exporters
follow it.

## Tests

- `tests/test_filters_cycles.py` - generic filter behaviour.
- `tests/test_exporters_bdf.py` - BDF column/unit map, header style,
  cycle filter passthrough, parquet round-trip, missing-column policy,
  pint-driven conversion with non-default `cellpy_units`, and an
  import-graph guard that fails if `cellpy.exporters.bdf` ever picks
  up a `cellpy.utils` import.

## Out of scope (clean follow-ups)

- Batch-utility integration (`cellpy.utils.batch*`).
- BDF metadata sidecar (`.json` / `.jsonld`).
- Aligning `cellpy/libs/local_fastnda/formats.py` with the BDF FAQ
  (preferred-label headers there too).
- `every_nth_cycle` cycle-filter knob.

## Linked PR / commits

- Branch: `356-export-bdf-for-dstoolbox`.
- Initial commit on branch (already pushed): `02f45f47` *Update Python
  version requirement and add BDF export functionality*.
- Final commit (this round): pint-driven unit conversion + test fix.
- PR: opened via `/issue-close`.
