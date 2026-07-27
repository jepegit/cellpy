# Migrating from cellpy 2.0 to 2.1

cellpy **2.1** completes "Stage 4": it **removes the 2.0 deprecation shims**
(breaking) and finishes the batch / collect redesign. Every 2.0 shim that
warned *"removed in 2.1"* is now gone.

**If you heeded the 2.0 `DeprecationWarning`s, you are already migrated.** This
guide maps each removed surface to its replacement. What still warns (now with a
2.2 removal date) is listed in
[`DEPRECATIONS.md`](../reference/deprecations.md).

## At a glance

| Area | Removed in 2.1 | Use instead |
|---|---|---|
| Column names | `c.headers_normal` / `c.headers_summary` / `c.headers_step_table` | `c.schema.raw` / `c.schema.summary` / `c.schema.steps` |
| Empty cell | `make_new_cell()` | `CellpyCell.vacant()` |
| ICA | `ica.Converter`, `dqdv_cycle` / `dqdv_cycles` / `dqdv_np`, the duplicate `dq` column | `ica.dqdv(...)` |
| Plotting | `interactive=`, `xlim=` / `ylim=`, `summary_plot_legacy` | `backend=` + the returned figure |
| Plot backends | `backend="seaborn"`, `backend="bokeh"` | `"plotly"` (default) or `"matplotlib"` |
| Batch package | `cellpy.utils.batch_tools.*` | `cellpy.batch` / `cellpy.collect` |
| Config | `prms.Paths` / `prms.Reader` / … global-mutation shim | `cellpy.config` (or `cellpy.config.override(...)`) |

`cellpy.utils.batch` and `cellpy.utils.collectors` remain as **permanent
one-line re-export shims**, so the top-level import paths keep working.

## Column headers: `c.headers_*` → `c.schema.*`

The per-cell `headers_normal` / `headers_summary` / `headers_step_table`
attributes were a 2.0 shim that mapped legacy `*_txt` names to the native
cellpy-core column names. They are removed. `c.schema` is the replacement — and
its contract is stronger: **whatever `c.schema.<frame>.<column>` returns is a
valid key into `c.data.<frame>`** on both the native and legacy runtimes.

| Legacy attribute | Replacement |
|---|---|
| `c.headers_normal` | `c.schema.raw` |
| `c.headers_step_table` | `c.schema.steps` |
| `c.headers_summary` | `c.schema.summary` |

The column *names* changed too (native cellpy-core spelling). The most common:

| Frame | Legacy `*_txt` / name | Native (`c.schema.*`) |
|---|---|---|
| raw | `voltage_txt` | `potential` |
| raw | `current_txt` | `current` |
| raw | `cycle_index_txt` | `cycle_num` |
| raw | `step_index_txt` | `step_num` |
| raw | `data_point_txt` | `datapoint_num` |
| raw | `test_time_txt` | `test_time` |
| raw | `charge_capacity_txt` | `cumulative_charge_capacity` |
| raw | `discharge_capacity_txt` | `cumulative_discharge_capacity` |
| steps | `type` | `step_type` |
| steps | `cycle` | `cycle_num` |
| steps | `step` | `step_num` |
| steps | `rate_avr` | `c_rate` |
| summary | `cycle_index` | `cycle_num` |
| summary | `data_point` | `datapoint_num_last` |
| summary | `test_time` | `last_test_time` |
| summary | `end_voltage_charge` / `end_voltage_discharge` | `potential_end_charge` / `potential_end_discharge` |

```python
# 2.0
hdr = c.headers_normal
v = c.data.raw[hdr.voltage_txt]

# 2.1
v = c.data.raw[c.schema.raw.potential]
```

`make_new_cell()` is gone — use the classmethod `CellpyCell.vacant()`.

## Incremental capacity analysis (ICA)

The 1.x ICA compatibility layer is removed.

| Removed | Use instead |
|---|---|
| `ica.Converter` | `ica.dqdv(...)` |
| `ica.dqdv_cycle(...)` / `dqdv_cycles(...)` / `dqdv_np(...)` | `ica.dqdv(...)` |
| `dqdv(..., split=…, tidy=…, cycle=…, label_direction=…)` | the current `dqdv` signature |
| the duplicate `dq` output column | the single canonical dQ/dV column |

For **multi-cell** ICA collection, prefer `cellpy.collect.collect_ica(batch)`
(see the batch section below).

## Plotting

Legacy `summary_plot` knobs are removed:

| Removed | Use instead |
|---|---|
| `interactive=True/False` | pick the engine with `backend=` |
| `xlim=` / `ylim=` | `x_range=` / `y_range=` |
| `summary_plot_legacy` | `summary_plot` |

### Backends dropped: seaborn and bokeh

Only **plotly** (default) and **matplotlib** remain. `backend="seaborn"` and
`backend="bokeh"` now raise `ValueError`:

```python
from cellpy.utils.plotutils import summary_plot

# 2.0: summary_plot(c, interactive=True, backend="seaborn")
# 2.1:
fig = summary_plot(c, backend="plotly")      # or backend="matplotlib"
```

## Batch and collectors

The `cellpy.utils.batch_tools` "farm/barn" machinery is **removed**. The batch
subsystem now lives in `cellpy.batch`, and the collectors in `cellpy.collect`.
`cellpy.utils.batch` and `cellpy.utils.collectors` stay as thin re-exports.

### Symbol map

| 2.0 (`utils/batch_tools`) | 2.1 |
|---|---|
| `utils.batch.init(...)` | `cellpy.batch.load(...)` (or `cellpy.utils.batch.init`, shim) |
| `batch_journals.LabJournal` + `from_db()` | `cellpy.batch.Batch.from_db(...)` |
| `batch_journals.LabJournal().from_file(...)` | `cellpy.batch.from_journal(...)` |
| `engines.simple_db_engine(...)` | internal — `cellpy.batch.Batch.from_db(...)` |
| `BatchSummaryCollector` / `summary_collector(...)` | `cellpy.collect.collect_summaries(batch)` |
| `BatchCyclesCollector` / `cycles_collector(...)` | `cellpy.collect.collect_cycles(batch)` |
| `BatchICACollector` / `ica_collector(...)` | `cellpy.collect.collect_ica(batch)` |
| `batch_exporters` / `dumpers` | `cellpy.batch` outputs (`Batch.combine_summaries()`, `to_bdf`, …) |

### `iterate_batches` / `process_batch` are recipes now

Instead of the removed helpers, loop over `cellpy.batch.load`:

```python
# process_batch(...) equivalent
from cellpy import batch

b = batch.load("my_batch", "my_project")
b.update()
summaries = b.combine_summaries()
```

```python
# iterate_batches(...) equivalent
for name in ("batch_a", "batch_b"):
    b = batch.load(name, "my_project")
    b.update()
    ...
```

### Bug fix: cross-cell cycle narrowing

The legacy `cycles_collector` / `ica_collector` reassigned the **shared**
`cycles` list inside their per-cell loop. If the first cell lacked a requested
cycle, that cycle was silently dropped for **every cell after it**.

`cellpy.collect` computes the cycle selection **per cell from the originally
requested cycles**, so one cell missing a cycle never narrows the request for
the others.

```text
Request: cycles [1, 2, 3, 4, 5] across cells A, B, C
  cell A has [1, 2, 3]  (missing 4, 5)

2.0 (buggy): shared `cycles` narrows to [1, 2, 3] after A
             → B and C also lose 4, 5
2.1 (fixed): A returns [1, 2, 3]; B and C still return [1, 2, 3, 4, 5]
```

This is a **behavior change**: multi-cell curve/ICA collections now include
cycles that were previously dropped. If you relied on the narrowed output, pass
an explicit cycle list.

## Configuration: `prms.*` → `cellpy.config`

The `prms.Paths` / `prms.Reader` / `prms.Batch` / … capitalized-section shim
(which forwarded reads and global mutation to `cellpy.config` with a
`DeprecationWarning`) is removed. Use `cellpy.config` directly.

| 2.0 | 2.1 |
|---|---|
| `prms.Paths.rawdatadir = ...` | `config.paths.rawdatadir = ...` |
| `prms.FileNames.raw_extension` | `config.file_names.raw_extension` |
| `prms.Reader.cycle_mode` | `config.reader.cycle_mode` |
| `prms.Db` / `prms.DbCols` | `config.db` / `config.db_cols` |
| `prms.Batch.auto_use_file_list` | `config.batch.auto_use_file_list` |
| `prms.Instruments.tester` | `config.instruments.tester` |
| `prms.CellInfo.*` | `config.defaults.cell_info.*` |
| `prms.Materials.*` | `config.defaults.materials.*` |

```python
from cellpy import config

# direct mutation (global, as before)
config.paths.rawdatadir = "/data/raw"
config.reader.cycle_mode = "cathode"

# or scoped, auto-restoring:
with config.override(reader={"cycle_mode": "cathode"}):
    ...
```

**Kept past 2.1:** the `CellpyCell.mass`, `.nom_cap`, and `.nom_cap_specifics`
property facades are *not* deprecated — `c.mass = 0.86` keeps working.

## Deprecations remaining

Only future-dated (2.2) deprecations still warn. See
[`DEPRECATIONS.md`](../reference/deprecations.md) (generated from
`cellpy._deprecation`; regenerate with `uv run python -m cellpy._deprecation`).

| Name | Replacement | Removal |
|---|---|---|
| `MultiCycleOcvFit.data` | `MultiCycleOcvFit.cell` | 2.2 |
| `MultiCycleOcvFit.set_data` | `MultiCycleOcvFit.set_cell` | 2.2 |
