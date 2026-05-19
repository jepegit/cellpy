# Plan for issue #356: Export bdf for dsToolbox

## Goal

Let cellpy users export `CellpyCell.data.raw` as a
[Battery Data Format](https://github.com/battery-data-alliance/battery-data-format)
(BDF) compliant file (CSV first, Parquet second) with optional cycle
filtering, so the result drops straight into the UiA `dsToolbox` script
and any other BDF-aware tool.

## Locked decisions (Q1 - Q5)

- **Header style**: preferred labels by default (`Test Time / s`,
  `Voltage / V`, `Current / A`); `header_style="machine"` opt-out for
  `test_time_second`-style names.
- **Cycle filter**: `cycles + last_cycle` only (mirrors
  `CellpyCell.to_csv`); `every_nth_cycle` deferred.
- **Default extension**: `.bdf.csv` when caller passes no suffix; an
  explicit suffix is honoured as-is.
- **Scope**: raw time-series only. Steps, summary, metadata sidecar, and
  batch integration are explicit follow-ups.
- **Missing columns**: hard-fail only on missing BDF *required* columns
  (`test_time`, `voltage`, `current`); warn-and-skip recommended/optional.

## Architectural rule (project invariant established here)

> The cellpy class layer (`cellpy/readers/cellreader.py`, primarily
> `CellpyCell`) must not import from `cellpy.utils`. Reusable export logic
> lives under `cellpy/exporters/`; reusable data-shaping logic lives under
> `cellpy/filters/`.

This issue is the first inhabitant of the new `cellpy/exporters/` and
`cellpy/filters/` packages and sets the precedent. The invariant is
recorded in the durable design note so future exporters/filters follow
it.

## Public API

Added on `CellpyCell` in
[cellpy/readers/cellreader.py](../../cellpy/readers/cellreader.py)
next to `to_csv` / `to_excel`:

```python
def to_bdf(
    self,
    filename: str | Path | None = None,
    *,
    cycles: int | Iterable[int] | None = None,
    last_cycle: int | None = None,
    header_style: Literal["preferred", "machine"] = "preferred",
    format: Literal["csv", "parquet"] = "csv",
) -> Path: ...
```

Same function exposed at module level as
`from cellpy.exporters import to_bdf` (function form takes the cell as
first argument).

The cycle filter is also separately reusable:
`from cellpy.filters import filter_cycles`.

## Code touchpoints

### New files

- [cellpy/exporters/bdf.py](../../cellpy/exporters/bdf.py) - BDF column /
  unit map driven by `HeadersNormal` + `CellpyUnits`, header rendering
  (preferred / machine), CSV + Parquet writer, `.bdf.csv` default
  suffix, warn-and-skip / hard-fail logic.
- [cellpy/filters/cycles.py](../../cellpy/filters/cycles.py) - generic
  `filter_cycles(df, cycles=None, last_cycle=None, column=None) -> df`.
  Default `column` resolves from `HeadersNormal.cycle_index_txt`.
- [tests/test_exporters_bdf.py](../../tests/test_exporters_bdf.py)
- [tests/test_filters_cycles.py](../../tests/test_filters_cycles.py)
- [.issueflows/04-designs-and-guides/bdf-export.md](../04-designs-and-guides/bdf-export.md) -
  design note: column map, defaults, dsToolbox compatibility, and the
  layering rule.

### Modified files

- [cellpy/readers/cellreader.py](../../cellpy/readers/cellreader.py) -
  add `CellpyCell.to_bdf(...)` thin wrapper. Imports
  `from cellpy.exporters import to_bdf` only. No change to `to_csv`,
  `to_excel`, or any other method.
- [cellpy/exporters/__init__.py](../../cellpy/exporters/__init__.py) -
  re-export `to_bdf`.
- [cellpy/filters/__init__.py](../../cellpy/filters/__init__.py) -
  re-export `filter_cycles`.

### Out of scope

- `cellpy/utils/batch.py` and `cellpy/utils/batch_tools/` - batch-level
  BDF export.
- BDF metadata sidecar (`.json` / `.jsonld`).
- Aligning `cellpy/libs/local_fastnda/formats.py` with the BDF FAQ
  (preferred-label headers).

## Column / unit map

| cellpy `HeadersNormal` field | BDF preferred label | BDF machine name | conversion (cellpy default -> BDF) | tier |
|---|---|---|---|---|
| `test_time_txt` | `Test Time / s` | `test_time_second` | `sec -> s` (identity) | required |
| `voltage_txt` | `Voltage / V` | `voltage_volt` | identity | required |
| `current_txt` | `Current / A` | `current_ampere` | `A -> A` (or `mA -> A` x 1e-3) | required |
| `datetime_txt` | `Unix Time / s` | `unix_time_second` | `pd.Timestamp.timestamp()` | recommended |
| `cycle_index_txt` | `Cycle Count / 1` | `cycle_count` | identity | recommended |
| `step_index_txt` | `Step Index / 1` | `step_index` | identity | optional |
| `charge_capacity_txt` | `Charging Capacity / Ah` | `charging_capacity_ah` | `mAh -> Ah` x 1e-3 | optional |
| `discharge_capacity_txt` | `Discharging Capacity / Ah` | `discharging_capacity_ah` | `mAh -> Ah` x 1e-3 | optional |
| `charge_energy_txt` | `Charging Energy / Wh` | `charging_energy_wh` | identity | optional |
| `discharge_energy_txt` | `Discharging Energy / Wh` | `discharging_energy_wh` | identity | optional |
| `power_txt` | `Power / W` | `power_watt` | identity | optional |
| `internal_resistance_txt` | `Internal Resistance / Ohm` | `internal_resistance_ohm` | identity | optional |

`step_count` (BDF recommended, monotonic across program) is not directly
present in cellpy's `HeadersNormal`; if not derivable from existing
columns, it is warn-and-skipped per Q5.

## Test strategy

- New `tests/test_filters_cycles.py`:
  - `cycles=5` (scalar) selects only cycle 5,
  - `cycles=[2, 5]` selects only those cycles,
  - `last_cycle=10` truncates to `cycle <= 10`,
  - `cycles + last_cycle` intersects correctly,
  - default `column` resolves from `HeadersNormal.cycle_index_txt`,
  - missing column raises a clear error.
- New `tests/test_exporters_bdf.py`:
  - required columns hard-fail when absent,
  - `mAh -> Ah` factor applied on capacity columns,
  - preferred-label headers contain `/`, machine headers do not,
  - cycle filter passthrough (delegates to `filter_cycles`),
  - `format="parquet"` writes `out.bdf.parquet` and round-trips,
  - missing recommended column emits a warning, not an error,
  - import-graph guard: `cellpy.exporters.bdf` does not import from
    `cellpy.utils`.
- Regression: `uv run pytest tests/test_cell_readers.py tests/test_cellpy.py`
  to make sure the new `CellpyCell.to_bdf` does not regress existing
  exports.

## Status

- [ ] Done
