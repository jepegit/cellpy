# BDF export design notes

Durable design notes for the Battery Data Format (BDF) export path.
Keep this file in sync with the code; it is the long-lived counterpart
to the per-issue plans (issue [#356](https://github.com/jepegit/cellpy/issues/356)
introduced this code).

## Layering rule

> **The cellpy class layer (`cellpy/readers/cellreader.py`, primarily
> `CellpyCell`) must not import from `cellpy.utils`. Reusable export
> logic lives under `cellpy/exporters/`; reusable data-shaping logic
> lives under `cellpy/filters/`.**

Rationale: `cellpy.utils` has accreted a wide grab-bag of helpers,
including some that import other heavy parts of cellpy. Keeping the
class layer free of `utils` imports lets us evolve the utility surface
without risking circular imports or surprising side effects on
`CellpyCell`.

The dependency arrow goes one way only:

```
cellpy.readers.cellreader.CellpyCell
   |
   v
cellpy.exporters.*
   |
   v
cellpy.filters.*
   |
   v
cellpy.parameters.internal_settings (HeadersNormal, CellpyUnits)
```

The forbidden edge is `cellpy.readers.cellreader -> cellpy.utils.*`. A
small import-graph guard lives in `tests/test_exporters_bdf.py` and
greps the BDF exporter source for `cellpy.utils` imports; future
exporters should add a similar guard.

## What BDF is

[Battery Data Format](https://github.com/battery-data-alliance/battery-data-format)
(BDF) is the Battery Data Alliance's open schema for cycler time-series.
Defining points relevant to cellpy:

- One file = one cell. (Multiple files per cell are allowed.)
- Required columns: `Test Time / s`, `Voltage / V`, `Current / A`.
- Recommended: `Unix Time / s`, `Cycle Count / 1`, `Step Count / 1`,
  `Ambient Temperature / degC`.
- Optional: step / cumulative / charging / discharging capacity (Ah),
  energy (Wh), power (W), internal resistance (Ohm), temperatures, ...
- Two parallel naming conventions: a "Preferred Label" (e.g.
  `Test Time / s`) and a machine-readable name (`test_time_second`).
  The spec recommends preferred labels for column headers.
- Default extension: `.bdf`, or `<name>.bdf.<ext>` for non-text
  serialisations (e.g. `.bdf.parquet`).

## Locked decisions

| ID | Decision | Knob | Default |
|---|---|---|---|
| Q1 | Header style | `header_style` | `"preferred"` (BDF spec); opt-out `"machine"` |
| Q2 | Cycle filter API | `cycles`, `last_cycle` | mirrors `CellpyCell.to_csv`; `every_nth_cycle` deferred |
| Q3 | Default extension | inferred from `filename` and `format` | `.bdf.csv` when no suffix is given |
| Q4 | Scope | n/a | raw time-series only; steps/summary/metadata/batch deferred |
| Q5 | Missing columns | n/a | hard-fail on missing *required*, warn-and-skip recommended/optional |
| Q6 | Non-BDF columns | `extras` | `False` (strict BDF). `True` appends all unmapped raw columns verbatim; iterable/str selects a subset. No unit conversion or renaming on extras; the resulting file is not strictly BDF-compliant. |
| Q7 | Target unit override (issue [#365](https://github.com/jepegit/cellpy/issues/365)) | `bdf_units` | `None` (strict BDF spec: `A`, `V`, `Ah`, `Wh`, `s`, `W`, `ohm`). A `CellpyUnits` overrides per `unit_kind`; column labels (`"Charging Capacity / mAh"`) and machine names (`"charging_capacity_mah"`) are rebuilt and values scaled via pint. Incompatible units raise `ValueError`. Any non-default override means the file is no longer strictly BDF-compliant (logged once at INFO). |

## Unit conversion

All non-datetime unit conversions go through
[`cellpy.readers.core.Q`](../../cellpy/readers/core.py) (the project-wide
`pint` wrapper, also used by `CellpyCell` itself for capacity / mass /
nominal-capacity arithmetic). The exporter does not maintain its own
factor table - it just declares each column's BDF target unit
(`"A"`, `"Ah"`, `"V"`, `"s"`, `"Wh"`, `"W"`, `"ohm"`) and lets pint
compute the multiplier from the cell's current `CellpyUnits`. As a
result, users who customise units (e.g. `cellpy_units.current = "mA"`,
`cellpy_units.energy = "kWh"`) get the right numbers automatically.

The `date_time` column is the one exception: pint does not handle wall
clocks, so cellpy's pandas timestamps are converted to UTC Unix seconds
explicitly.

### Overriding target units (`bdf_units=`)

Issue [#365](https://github.com/jepegit/cellpy/issues/365) added a
`bdf_units` keyword to both `cellpy.exporters.bdf.to_bdf` and
`CellpyCell.to_bdf`. It accepts a
[`CellpyUnits`](../../cellpy/parameters/internal_settings.py) object
whose attributes control the **units written into the BDF file** (not
the source side — `cell.data.raw` is still assumed to be in
`cell.cellpy_units`).

Semantics:

- `bdf_units=None` (default) → strict BDF spec output, byte-for-byte
  identical to the pre-#365 behaviour.
- `bdf_units=CellpyUnits(charge="mAh", current="mA")` → emits
  `Charging Capacity / mAh` (machine: `charging_capacity_mah`) and
  `Current / mA` (machine: `current_ma`), with values scaled via pint.
- Per-kind precedence: attributes on the supplied object that are
  **pint-equivalent** to the BDF spec default (`"sec" ≡ "s"`,
  `"V" ≡ "volt"`, etc.) keep the canonical BDF label and machine name.
  Only non-equivalent kinds flip labels.
- A unit pint cannot convert from the cell's source unit (e.g.
  `charge="kg"` while `cell.cellpy_units.charge == "mAh"`) raises
  `ValueError`. No silent factor-1.0 fallback under an explicit
  override.
- The exporter logs one `INFO` line listing the non-default unit kinds,
  mirroring how `extras=True` declares the file is no longer strictly
  BDF-compliant.

Label synthesis lives in `_resolve_column_name` in
[cellpy/exporters/bdf.py](../../cellpy/exporters/bdf.py); the
unit-kind → target-unit lookup lives in `_resolve_target_units`. Each
`_BdfColumn` row carries both the canonical BDF spec spellings
(`preferred` / `machine`) and unitless bases (`base_preferred` /
`base_machine`) so the override path never has to monkey with the
BDF-spec defaults.

## Column / unit map

Source of truth: `_COLUMN_MAP` in
[cellpy/exporters/bdf.py](../../cellpy/exporters/bdf.py).

| cellpy `HeadersNormal` field | Preferred label | Machine name | Tier | Cellpy default unit | BDF unit | Factor |
|---|---|---|---|---|---|---|
| `test_time_txt` | `Test Time / s` | `test_time_second` | required | `sec` | `s` | 1 |
| `voltage_txt` | `Voltage / V` | `voltage_volt` | required | `V` | `V` | 1 |
| `current_txt` | `Current / A` | `current_ampere` | required | `A` | `A` | 1 (or 1e-3 if cellpy `current="mA"`) |
| `datetime_txt` | `Unix Time / s` | `unix_time_second` | recommended | `datetime64` | `s` (Unix) | UTC seconds |
| `cycle_index_txt` | `Cycle Count / 1` | `cycle_count` | recommended | int | dimensionless | 1 |
| `step_index_txt` | `Step Index / 1` | `step_index` | optional | int | dimensionless | 1 |
| `charge_capacity_txt` | `Charging Capacity / Ah` | `charging_capacity_ah` | optional | `mAh` | `Ah` | 1e-3 |
| `discharge_capacity_txt` | `Discharging Capacity / Ah` | `discharging_capacity_ah` | optional | `mAh` | `Ah` | 1e-3 |
| `charge_energy_txt` | `Charging Energy / Wh` | `charging_energy_wh` | optional | `Wh` | `Wh` | 1 |
| `discharge_energy_txt` | `Discharging Energy / Wh` | `discharging_energy_wh` | optional | `Wh` | `Wh` | 1 |
| `power_txt` | `Power / W` | `power_watt` | optional | `W` | `W` | 1 |
| `internal_resistance_txt` | `Internal Resistance / Ohm` | `internal_resistance_ohm` | optional | `ohm` | `Ohm` | 1 |

`step_count` (BDF recommended, monotonic across program) is *not*
present in cellpy's `HeadersNormal`. It is currently warn-and-skipped.
When/if a monotonic step counter is added to cellpy's raw schema, wire
it into `_COLUMN_MAP` rather than computing on the fly here.

## Why we do not reuse `cellpy/libs/local_fastnda/formats.py:to_bdf`

`cellpy/libs/local_fastnda/formats.py` already has a `to_bdf` function
that converts a polars DataFrame produced by the Neware nda/ndax
backend into BDF column names. We deliberately keep that path separate:

- It operates on polars, not pandas.
- It only handles the columns the nda backend produces; it does not
  speak `HeadersNormal` or `CellpyUnits`.
- It currently emits *machine-readable* names (`voltage_volt`...) as
  column headers; the cellpy exporter defaults to *preferred labels*
  per the BDF FAQ.
- It runs at the file-level conversion stage, before a `CellpyCell`
  exists. Our exporter runs the other way around: cell -> file.

If/when the two paths converge (e.g. local_fastnda goes through a
`CellpyCell`), revisit this decision.

## Out of scope (clean follow-ups)

- BDF metadata sidecar (`.json` / `.jsonld`). The Battery Data
  Alliance's parallel metadata format is still next-step work upstream.
- Batch-utility integration (`cellpy/utils/batch*`). A `to_bdf` on a
  batch journal is a clean extension once the per-cell method is
  stable.
- Aligning the local_fastnda `to_bdf` to also default to preferred
  labels.
- Adding `every_nth_cycle` (downsample by N) to the cycle filter.
- Surface temperatures and pressure columns (BDF optional). Wire them
  in once cellpy's `HeadersNormal` exposes them.

## Tests / guards

- `tests/test_filters_cycles.py` covers the generic filter.
- `tests/test_exporters_bdf.py` covers the column/unit map, header
  style, cycle filter passthrough, parquet round-trip, missing-column
  policy, and the *no-`cellpy.utils`-imports* import-graph guard.
