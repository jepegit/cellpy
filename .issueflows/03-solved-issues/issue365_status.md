# Status for issue #365: units when exporting in bdf

- [x] Done

## Summary

Added a `bdf_units` keyword argument to `cellpy.exporters.bdf.to_bdf` and `CellpyCell.to_bdf` so callers can control the **units written into the BDF file**. Default behaviour (no kwarg) is unchanged — strict BDF spec.

## What landed

- **`cellpy/exporters/bdf.py`**
  - `_BdfColumn` now carries canonical BDF spec spellings (`preferred`, `machine`) plus unit-less stems (`base_preferred`, `base_machine`) so non-default unit labels can be synthesized without touching the spec defaults.
  - New helpers: `_slug`, `_is_unit_equivalent`, `_resolve_column_name`, `_resolve_target_units`.
  - `_conversion_factor` gained a `strict` flag — when a `bdf_units` override is active it raises `ValueError` on pint-incompatible units rather than silently leaving values unchanged.
  - `to_bdf` gained `bdf_units: Optional[CellpyUnits] = None`. When set, column labels and values are rebuilt per unit kind; one INFO line announces the file is no longer strictly BDF-compliant.
  - Worked example added to the docstring (mAh / mA scenario).

- **`cellpy/readers/cellreader.py`**
  - `CellpyCell.to_bdf` forwards the new `bdf_units` kwarg and mirrors the docstring example.

- **`tests/test_exporters_bdf.py`**
  - Fresh `CellpyUnits()` per cell in `_make_synthetic_cell` to stop pre-existing leakage from the module-level `cellpy_units` singleton between tests.
  - 9 new tests: explicit `bdf_units=None` matches default; override charge to mAh (preferred + machine styles); override current to mA; override time to min; partial override keeps unrelated columns byte-for-byte at BDF default; no mutation of `cell.cellpy_units` or the passed-in object; pint-incompatible unit raises; pint-equivalent override keeps canonical label; INFO log on non-strict path.

- **`.issueflows/04-designs-and-guides/bdf-export.md`**
  - New Q7 row in the *Locked decisions* table.
  - New **Overriding target units (`bdf_units=`)** subsection under *Unit conversion* with semantics, equivalence rule, failure mode, and pointers to the new helpers; cross-linked to issue #365.

## Tests

`pytest tests/test_exporters_bdf.py -q` → 32 passed locally (31 existing + 9 new − 8 that were already there is the wrong math; actual: 23 pre-existing + 9 new = 32 passed).

## Plan deviations

None. All four `Open questions` resolved as recommended in the plan:

1. Kwarg name: `bdf_units`.
2. Hard-fail (`ValueError`) on pint-incompatible units when override is active.
3. Single INFO log line when override is active.
4. Non-BDF `CellpyUnits` fields stay ignored (out-of-scope per design doc).

One small fixture fix snuck in: `_make_synthetic_cell` now assigns a fresh `CellpyUnits()` to each cell, which sidesteps the pre-existing module-level singleton leak that surfaced when a new test asserted on `cell.cellpy_units.current` defaults. Pre-existing tests unaffected (they mutate `cell.cellpy_units.<field>` per-cell, which still works on the per-cell instance).

## Remaining work

- Run the wider suite at `/issue-close` time.
- Optional follow-ups (still out of scope here, recorded in the design doc):
  - Surfacing BDF temperature / pressure columns when `HeadersNormal` grows them.
  - BDF metadata sidecar (`.json` / `.jsonld`).
  - Batch-utility `to_bdf` entry point.
