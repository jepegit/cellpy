---
icon: material/book-alphabet
---

# Glossary

Battery-lab words as cellpy spells them. Each row is **the term you already
know → the name in cellpy → where the long explanation lives**.

This page does not replace the column lists. When you need every summary
column, go to [Summary columns](../reference/summary_columns.md). When you
need units and mass, go to [Units, mass, area and C-rates](../guides/units.md).

Throughout, `c` is a loaded cell.

```python
from cellpy.utils import example_data

c = example_data.raw_file()
c.schema.summary.coulombic_efficiency   # -> "coulombic_efficiency"
c.schema.raw.cycle_num                  # -> "cycle_num"
```

Prefer `c.schema…` over typing the string, so a rename does not break your
script.

---

## The objects

| You say | cellpy name | Notes |
|---|---|---|
| the cell / the run | `CellpyCell` (`c`) | What `cellpy.get(...)` returns. |
| the data | `c.data` (`Data`) | Frames + metadata for the active test. |
| column names | `c.schema` | `c.schema.raw` / `.steps` / `.summary`. |
| the tester / cycler | `instrument=` | Passed to `cellpy.get`. List: `cellpy.print_instruments()`. |
| a saved cellpy file | `.cellpy` | Native archive (v9). Older files may still be `.h5`. |
| a campaign / many cells | `batch` / journal | `batch.load(...)`. The journal is the JSON that lists the cells. |

→ [The data structure](data_structure.md) ·
[File formats](file_formats.md) ·
[Batch processing](../examples/batch_utility/cellpy_batch_processing.md)

---

## The run

| You say | cellpy name | Notes |
|---|---|---|
| cycle | `cycle_num` | On raw, steps, and summary. Not `cycle_index` (that is a 1.x leftover). |
| step | `step_num` | The tester's step number within the cycle. |
| sub-step | `sub_step_num` | Only on the step table, when the tester splits a step. |
| data point | `datapoint_num` | Row index in the raw frame. |
| charge / discharge / rest | `step_type` | Labels cellpy *assigns*. The built-in classifier emits `charge`, `discharge`, `cv_charge`, `cv_discharge`, `ocvrlx_up`, `ocvrlx_down`, `rest`, `ir`, and `""` (uncategorized). |
| OCV / relaxation | `ocvrlx_up` / `ocvrlx_down`, or `c.get_ocv(...)` | `get_ocv(cycles=5, direction="up")` returns `cycle_num`, `step_num`, `step_time`, `potential`. Summary also has `open_circuit_potential_charge` / `_discharge`. |
| IR pulse / DCIR | `step_type == "ir"` in the step table; `internal_resistance` on raw | Per-cycle columns `ir_charge` / `ir_discharge` (and `ir_start_*` / `ir_end_*`) exist on the schema. They appear in the summary only when the tester recorded IR points. |
| formation | not a column | A cycle you treat as formation. Filter by `cycle_num`; plotting helpers have a formation option. |
| half cell vs full cell | `cycle_mode` | Default `"anode"` (first step is a discharge). Full cell: `cycle_mode="full_cell"`. Wrong setting swaps charge/discharge and inverts coulombic efficiency. |

→ [Understand the step table](../guides/step_table.md) ·
[Troubleshooting](../troubleshooting.md#charge-and-discharge-look-swapped-and-the-coulombic-efficiency-is-upside-down)

---

## The three tables

| You say | cellpy name | Notes |
|---|---|---|
| the time series / the raw file | `c.data.raw` | One row per recorded point. Capacities here are **cumulative**: `cumulative_charge_capacity`, `cumulative_discharge_capacity`. |
| the step list | `c.data.steps` | One row per (cycle, step, sub-step). Built by `make_step_table`. |
| the cycle table / fade table | `c.data.summary` | One row per cycle. Built by `make_summary`. This is where per-cycle capacities and efficiencies live. |

→ [The data structure](data_structure.md)

---

## Capacities, rates, efficiencies

| You say | cellpy name | Notes |
|---|---|---|
| specific capacity / gravimetric | `…_gravimetric` | Per active mass. Needs a real `mass=` (default is 1.0 mg). |
| areal capacity | `…_areal` | Per electrode area. Needs `area=` (cm²). Stored as `c.data.active_electrode_area`. |
| absolute / not normalised | `…_absolute` | In *your* units (`c.cellpy_units`), not divided by mass or area. |
| the bare name (`charge_capacity`) | tester units | `c.data.raw_units` — often Ah on Arbin. Off by 1000 vs mAh if you assume the wrong set. |
| coulombic efficiency | `coulombic_efficiency` | Per cycle, on the summary. Upside-down? Check `cycle_mode`. |
| C-rate | `c_rate` (steps); `charge_c_rate` / `discharge_c_rate` (summary) | Meaningless until you set `nominal_capacity=` (`c.data.nom_cap`). |
| nominal / rated / nameplate capacity | `nominal_capacity=` / `c.data.nom_cap` | Used for C-rates and equivalent full cycles, not for scaling the capacity columns. |
| equivalent full cycles / EFC | `equivalent_full_cycles` | Throughput / (2 × nominal capacity). Also `normalized_cycle_index`. |
| energy efficiency | `energy_efficiency` | On the summary, next to coulombic efficiency. |
| voltage | `potential` | cellpy says potential, not voltage, on the frames. |
| current | `current` | Same word. |

The gravimetric / areal / absolute split is explained, with the factor-of-1000
trap, in [Units, mass, area and C-rates](../guides/units.md). Every summary
column is in [Summary columns](../reference/summary_columns.md).

---

## Mass, area, loading

| You say | cellpy name | Notes |
|---|---|---|
| active-material mass | `mass=` on `cellpy.get`; `c.data.mass` | **mg**. After changing it: `c.refresh_after("mass")`. |
| electrode area | `area=` on `cellpy.get`; `c.data.active_electrode_area` | **cm²**. Then `c.refresh_after("area")`. |
| loading | journal / database column | Used when you set up a batch sheet, not a column on `c.data.summary`. |
| total mass | `c.data.tot_mass` | The whole electrode, if you track it. Not used for specific capacity. |

→ [Units, mass, area and C-rates](../guides/units.md) ·
[Set up the cellpy database](../guides/batch_database.md)

---

## Analysis names

| You say | cellpy name | Notes |
|---|---|---|
| ICA / dQ/dV | `ica.dqdv(c)` | `from cellpy import ica`. |
| DVA / dV/dQ | `ica.dvdq(c)` | Same module. |
| GITT | the GITT tutorial | No dedicated `c.gitt()` helper in 2.x. |
| plot cycle life | `summary_plot(c)` | Or `b.plot()` for a batch. |

→ [Compute ICA / DVA](../guides/ica.md) ·
[Plot one cell](../guides/plotting.md) ·
[GITT](../examples/05_GITT.md)

---

## Words cellpy does not use

| You say | What to do |
|---|---|
| SOC / state of charge | Not a column. Compute from a capacity and a reference (nominal, first cycle, or a voltage cut). |
| DOD / depth of discharge | Same — not a column. |
| CE | Use `coulombic_efficiency`. |
| voltage vs Li | Still `potential`. The reference is in your experiment, not in the column name. |
| `cycle_index` / `Data_Point` / `Voltage` | 1.x or tester names. Translate with the [legacy header map](../other/header_migration_map.md), then prefer `c.schema`. |

---

## See also

- [How do I…?](../how_do_i.md) — task index
- [Your first hour](../getting_started/first_hour.md) — run through a cell
- [Troubleshooting](../troubleshooting.md) — when the numbers look wrong
