# Issue #1131 — Plan: nominal capacity Ah/g vs mAh/g

## Goal

Rule out a current-cellpy bug that would store a nominal capacity whose magnitude is in Ah/g while callers (including cellpy-simple-gui) treat that magnitude as mAh/g. If the Excel journal path is doing that, fix it. If it is not, lock the contract with a test and record the finding on the issue.

## Constraints

- Stored `nominal_capacity` is a bare float in `cellpy_units.nominal_capacity`. Default is `mAh/g` (`CellpyUnits` in cellpycore, mirrored in `cellpy.config.models`).
- A bare number on the setter is kept as-is. A quantity string is parsed by `_dump_cellpy_unit`, which stores the magnitude and **replaces** `cellpy_units.nominal_capacity` with the parsed unit. It does not convert into the previous unit.
- cellpy-simple-gui labels gravimetric nominal capacity `mAh/g` in `nomCapUnit` and does not read `cellpy_units`. That label is out of this repo.
- Do not rescale existing Excel databases in this issue. A silent ×1000 would rewrite every sheet whose numbers are already mAh/g.

### Prior art

- `Reader.get_nom_cap` in `src/cellpy/readers/dbreader.py` — returns the sheet cell. No unit conversion.
- `Reader._find_out_what_rows_to_skip` — `skiprows.union((self.db_unit_row,))` discards the new set, so the unit row is not added by that line. With the defaults (header 0, unit row 1, data start 2) the unit row is still skipped because it sits before the data start. The unit strings are never applied.
- `JsonReader._convert_nominal_capacity_unit` in `src/cellpy/readers/json_dbreader.py` — when the Unit field matches `[unit]`, converts into `cellpy_units["nominal_capacity"]` (mAh/g). Excel does not do this.
- `batch._dbengine._create_pages_dict` — copies `get_nom_cap` onto journal pages unchanged.
- `CellpyCell.nominal_capacity` setter — `_dump_cellpy_unit` in `src/cellpy/readers/cellreader.py`.
- Instrument `raw_units["nominal_capacity"] = "Ah/g"` on Arbin SQL h5 and Neware loaders is the tester charge unit declaration, not a journal value.
- Toolbox: no helper for this. Graph: units live around `nominal_capacity_as_absolute` (cellpycore). No extra journal-unit node to follow.

## Approach

1. Confirm with one Excel fixture: header row, unit row `Ah/g` on the nominal-capacity column, data value `3.5`. `get_nom_cap` must return `3.5`, not `3500`. Journal pages must carry `3.5`. That is the current contract: the sheet number is already in mAh/g; the unit row is documentation cellpy does not read.
2. Confirm the setter: `nominal_capacity = 3.5` leaves the value at `3.5` and leaves `cellpy_units.nominal_capacity` at `mAh/g`. A quantity string is recorded as a finding, not changed here.
3. No production change when step 1 matches the code as read. Comment on GitHub #1131 with the three paths (Excel: number kept; JSON: `[Ah/g]` converted to mAh/g; GUI: hardcoded mAh/g label).
4. Do not touch cellpy-simple-gui, BatBase JSON conversion, or instrument `raw_units`.

## Files to touch

- `tests/test_dbreader.py` — tiny xlsx (or openpyxl workbook in tmp) whose unit row says `Ah/g` and whose nominal capacity is `3.5`. Assert `get_nom_cap` returns `3.5`.
- No change to `src/cellpy/readers/dbreader.py` unless the test shows the value is rescaled.

## Test strategy

`uv run pytest tests/test_dbreader.py -q` from the worktree. No full suite for this lock-in test.

## Open questions

- Honor the Excel unit row and convert `Ah/g` → `mAh/g`? Recommended: no. The unit row has never been applied, and converting now would rescale sheets that already store mAh/g. If a real sheet's unit row says `Ah/g` and the numbers are in that unit, the sheet should be rewritten to mAh/g (or a later, explicit converter).
- Fix `_dump_cellpy_unit` so `"3.5 Ah/g"` becomes `3500` mAh/g instead of storing `3.5` and relabeling the unit? Recommended: no in this issue. The reported path is the journal/Excel loader, which passes a bare number.
