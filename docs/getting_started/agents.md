# Using cellpy from an agent

This page is for **coding agents** (and humans directing them) that need to
**call cellpy as a library** — for example a researcher building a small
desktop GUI, web app, or notebook pipeline around cell cycling data.

For contributing to the cellpy *codebase*, start at
[AGENTS.md](https://github.com/jepegit/cellpy/blob/master/AGENTS.md) in the
repo root and the [developers guide](../contributing/developers_guide/index.md).

!!! tip "Findability"
    Root `AGENTS.md` points here. Prefer this chapter for usage recipes; keep
    `AGENTS.md` short (commands + link).

## What cellpy is (and is not)

| Is | Is not |
| --- | --- |
| A Python library that loads battery-tester files into a consistent shape | A GUI or web server product |
| Builds **step** and **summary** tables from raw time-series | A plotting-first dashboard (helpers exist; bring your own UI) |
| Ships a `cellpy` CLI (`setup`, `info`, `serve` → Jupyter) | Long-running app hosting — `serve` only launches Jupyter |

Primary object: **`CellpyCell`**. Measurement frames live on **`c.data`**
(`raw`, `steps`, `summary`). Column names for the active schema are on
**`c.schema`** — prefer that over legacy `headers_*` attributes.

## Install and smoke-check

Consumer install:

```bash
pip install cellpy
# or: conda install -c conda-forge cellpy
```

From a clone of this repo (dev):

```bash
uv sync
uv run cellpy setup --silent
uv run cellpy info --check
uv run pytest -m essential
```

Always run Python through the project environment (`uv run …` in this repo,
or the user's activated venv/conda env). Do not call bare `python` unless the
user already activated an env that has `cellpy` installed.

## Minimal load → inspect → export

Use bundled example data when the agent has network access (first call may
download small fixtures from GitHub):

```python
from cellpy.utils import example_data

c = example_data.raw_file()  # Arbin .res → CellpyCell with steps + summary

# Prefer schema-resolved column names (v2 native headers)
potential = c.data.raw[c.schema.raw.potential]
charge_cap = c.data.summary[c.schema.summary.charge_capacity]

print(c.data.summary.head())
print(c.get_cycle_numbers()[:5])
```

Load a path the user provides:

```python
import cellpy

c = cellpy.get(
    r"C:\data\my_cell_01.res",
    mass=0.85,  # active material mass in mg (instrument-dependent context)
    instrument="arbin_res",  # omit to use config default / extension guess
    # For raw .h5/.hdf5, a set instrument= wins over native suffix auto-pick.
)
c.save("out/my_cell.cellpy")  # cellpy file — fast reload later
c.to_csv("out/csv_export")
```

`save` is atomic: it writes a staged file next to the destination and replaces it
only once complete, so an interrupted save leaves any previous file intact and
never produces a half-written archive. No app-side staging needed for a single
file.

Peek metadata only (no raw/steps/summary — good for file browsers):

```python
meta = cellpy.read_meta("out/my_cell.cellpy")
mass = meta["cell"]["mass"]  # also under tests["0"]["cell"] on v9 archives
```

Build an ingestion form for a picked instrument (shared `cellpy.get` meta knobs today):

```python
schema = cellpy.instrument_meta_schema("maccor_txt")
for field in schema["fields"]:
    print(field["name"], field["required"], field.get("unit"))
```

Reload a `.cellpy` file the same way:

```python
c = cellpy.get("out/my_cell.cellpy")
```

## Core mental model for app code

```text
cellpy.get(path, ...)  →  CellpyCell
                            ├─ .data.raw      # time-series (pandas DataFrame)
                            ├─ .data.steps    # per-step stats / types
                            ├─ .data.summary  # per-cycle summary
                            └─ .schema        # stable names → actual columns
```

Useful methods on `CellpyCell` (non-exhaustive):

- `get_cycle_numbers()` — list of cycle indices
- `get_cap(...)` / capacity–voltage style extracts (see API / examples)
- ICA / DVA — `from cellpy import ica` then `ica.dqdv(c)` / `ica.dvdq(c)`
  (see [Compute ICA / DVA](../guides/ica.md))
- `make_step_table()` / `make_summary()` — usually already run by `get`
- `refresh_after(("mass",))` — after editing mass / area / `nominal_capacity` /
  `cycle_mode` on a cell that already has a summary, rebuild only the
  meta-dependent columns (cheaper than a full `make_summary()`). See
  `cellpy.readers.cellreader.SUMMARY_META_DEPENDENCIES` for the map GUIs
  can use for messaging.
- `save` / `to_csv` / Excel helpers — persist for the user's workflow

Deeper shape docs: [Data structure](../fundamentals/data_structure.md).
Human tutorial path: [Basic usage](basic_usage.md),
[Examples](../examples/index.md).

## Recipe: researcher GUI / app around cellpy

Typical agent task: “build a small app that loads my tester files and shows
capacities.” Keep **cellpy in the data layer**; keep UI (Streamlit, Qt,
Panel, FastAPI, …) thin.

Suggested layering:

1. **Load** — `cellpy.get(path, mass=..., instrument=...)` in a worker thread
   or async job so the UI stays responsive on large files.
2. **Resolve columns** — always via `c.schema.*`, never hard-coded legacy
   strings, so v1→v2 and instrument differences hurt less.
3. **Present** — pass pandas frames or simple dicts to the UI
   (`summary` for cycle tables; slices of `raw` for plots).
4. **Export** — offer `.cellpy` (canonical) plus CSV/Excel for the user.
   For a Plotly download response from a collected figure:

   ```python
   from cellpy.plotting import image_media_type

   png = collection.to_image("png")  # needs cellpy[batch] (plotly + kaleido)
   # FastAPI: Response(content=png, media_type=image_media_type("png"))
   # Or: cellpy.plotting.write_image(collection.plot(...), "svg")
   ```

!!! tip "DataFrame types & quiet startup (building GUIs)"

    - **polars vs pandas — know the boundary.** A cell's frames
      (`c.data.raw` / `.steps` / `.summary`) are **pandas**; a
      `cellpy.collect.Collection.data` is **polars**, and `Collection.plot()`
      converts to pandas internally. Convert explicitly at the seam
      (`collection.data.to_pandas()` / `pl.from_pandas(df)`) rather than mixing
      the two in UI code.
    - **Summary facet y-scales.** Collected summary plots default to
      independent y-axes (`share_y=False`). For Capacity+CE, pin CE with
      `collection.plot(y_ranges={"coulombic_efficiency": [0, 110]})`
      (Plotly). `share_y=True` / `match_axes=True` restores a shared scale.
      Default y-axis titles include units (`Charge Capacity (mAh/g)`). Facet
      rows follow the collected `columns=` order top → bottom.
    - **Instrument picker for free.** `cellpy.list_instruments()` returns
      `[{"id", "label", "models", "suffixes"}, ...]` and is quiet by contract
      (probe/discovery skips stay at DEBUG — no `WARNING` spam on the root
      logger), ready to drive an import form.
    - **Keep the console quiet.** cellpy logs through the `cellpy` logger; raise
      its level in an app you want silent:
      `logging.getLogger("cellpy").setLevel(logging.ERROR)`. Suppress one-off
      deprecation notices (e.g. `get_summary()` → `c.data.summary`) with
      `warnings.filterwarnings("ignore", category=DeprecationWarning, module="cellpy")`.

Skeleton (UI-agnostic):

```python
from dataclasses import dataclass
from pathlib import Path

import cellpy


@dataclass
class LoadRequest:
    path: Path
    mass_mg: float
    instrument: str | None = None


def load_cell(req: LoadRequest):
    kwargs = {"filename": str(req.path), "mass": req.mass_mg}
    if req.instrument:
        kwargs["instrument"] = req.instrument
    return cellpy.get(**kwargs)


def cycle_table(c):
    s = c.schema.summary
    df = c.data.summary
    cols = [s.charge_capacity, s.discharge_capacity]
    cols = [col for col in cols if col in df.columns]
    return df[cols].copy()
```

Instrument strings and formats: see
[Loading different formats](../examples/06_loading_different_formats.md) and
the instruments API. Coming from cellpy 1.x:
[migration guide](migration_v1_to_v2.md).

## Recipe: incremental capacity and differential voltage

Prefer `from cellpy import ica`. `cellpy.utils.ica` is a re-export of the same
objects. Do not use the removed 1.x helpers (`Converter`, `dqdv_cycle`,
`dqdv_cycles`, `dqdv_np`) or the old `dq` column.

```python
from cellpy import ica
from cellpy.utils.plotutils import ica_plot, dva_plot

frame = ica.dqdv(c, cycles=[1, 2])           # cycle, direction, voltage, capacity, dqdv
dva = ica.dvdq(c, cycles=1, direction="charge")  # cycle, direction, capacity, voltage, dvdq
charge = frame[frame.direction == "charge"]  # cell-centric labels

# reusable recipe (frozen — tweak with replace() or stack a keyword)
opts = ica.IcaOptions(voltage_resolution=0.005, voltage_fwhm=0.015)
frame = ica.dqdv(c, cycles=[1, 2], options=opts)
frame = ica.dqdv(c, cycles=[1, 2], options=opts.replace(pre_smoothing=True))
fig = ica_plot(c, cycles=[1, 2], options=opts)
```

`cellpy.ica.IcaOptions` is the transform recipe. `cellpy.collect.IcaOptions`
is a different dataclass (cycles + resolution knobs only) for
`collect_ica` / `collect_dva`. Do not mix them. How-to:
[Compute ICA / DVA](../guides/ica.md).

Multi-cell: `cellpy.collect.collect_ica(batch)` / `collect_dva(batch)`.
Worked notebook: [Incremental capacity analysis](../examples/04_incremental_capacity_analysis.md).
API: [ICA and DVA](../api/ica.md).

## Recipe: loading many cells (batch) and its speed knobs

```python
from cellpy import batch

b = batch.load(name="my_experiment", project="my_project")
summaries = b.summaries          # polars frame across cells
c = b.cells["my_cell_01"]        # a CellpyCell
fig = b.plot()                   # summary plot
# If filefinder found no raw files, those cells are FAILED (not empty
# LOADED). Check b.result.report() / the UserWarning from load.
```

Dropping cells:

- `b.mark_as_bad("my_cell_01")` only writes `journal.session["bad_cells"]`.
  The cell stays in `pages`, the store, and plots until you drop it. A name
  that is not in `b.cell_names` raises `ValueError` (it could never drop
  anything); `b.drop` warns instead of doing nothing quietly.
- `b.drop("my_cell_01")` (or `b.drop_cells_marked_bad()`) removes it now.
  `b.plot()` / `b.summaries` / `b.report()` then use the remaining cells —
  no `update()` required. Call `b.save()` to persist the thinner journal.
- Next `batch.load(...)` (default `drop_bad_cells=True`) drops
  `session["bad_cells"]` **before** it loads, so a saved mark is enough if
  you reload instead of dropping in the same session.

Building a batch from cells you already hold (a GUI, a notebook, a file
picker) goes through `from_cells`, which takes cells — not paths:

```python
from cellpy.collect import from_cells

b = from_cells({"cell_01": cellpy.get(path_1), "cell_02": cellpy.get(path_2)})
```

- A value that is not a cell raises `ValueError` naming every offending key
  and the type that arrived. Watch the `example_data` asymmetry:
  `cellpy_file()` hands back a cell, `rate_file()` hands back a **path**.
- `collect_summaries` warns (`UserWarning`) and names any cell that
  contributed no rows, so a collection that is thinner than your cell list
  says why. `collection.meta.cells_included` is the authoritative list.

`batch.load` (and `Batch.update` / `Batch.load` under it) takes an `executor`
and a `progress` knob:

```python
b = batch.load(name="my_experiment", project="my_project", executor="threads")
b = batch.load(name="my_experiment", project="my_project", progress=False)
```

`progress=None` (default) shows tqdm on a TTY or in JupyterLab. `False` turns
bars off. `True` forces them on. A callable receives progress events
(`journal` / `search` / `copy` / `parse` / `save` / `cell_done`). The older
`on_progress(i, n, result)` callback still fires on each finished cell.
`executor="threads"` draws one child bar per in-flight cell; `processes`
keeps the overall bar only.

| `executor` | When it helps |
| --- | --- |
| `"serial"` (default) | Always correct; the only mode that never adds overhead |
| `"threads"` | **Reopening** cells from local `.cellpy` files — measured 25 warm cells 5.2 s → 2.0 s |
| `"processes"` | Rarely; Windows process spawn usually eats the gain |

The **first** load of remote raw files stays effectively serial on the wire —
SFTP transfers do not overlap, so `executor="threads"` buys ~nothing there
(measured 38.5 s serial vs 37.1 s threads for 3 remote `.h5`). Use threads for
the reopen path, not the download path.

Other measured knobs for a slow first batch load:

- **File search.** Creating a journal from the database searches for each
  cell's raw files, and on a shared remote `rawdatadir` that walks the tree
  once per cell. `config.batch.auto_use_file_list` (default `false`) is the
  switch for dumping the directory **once** and matching every cell against
  that list instead (project-scoped when the batch has a `project`). Wiring it
  into the v3 journal path is tracked in
  [#900](https://github.com/jepegit/cellpy/issues/900); either way, pointing
  `rawdatadir` at the project folder is the cheapest fix. See
  [Remote paths](remote_paths.md#behaviour-notes).
- **Saving `.cellpy` files.** First load writes one file per cell. Pass
  `save_cellpy=False` if the app only needs the frames in memory.
- **`pyarrow` installed twice.** A pip `pyarrow` on top of a conda
  `pyarrow-core` (or the reverse) breaks `.cellpy` reads with a DLL error at
  load time. Keep one installer's copy — see the environment notes in
  [CONTRIBUTING.md](https://github.com/jepegit/cellpy/blob/master/CONTRIBUTING.md).
- **A cold first reopen is not a decode bug.** On Windows the first read of a
  large `.cellpy` can be slower than parsing the raw file, because of page
  cache / antivirus, not the v9 format.

## Pitfalls agents hit

- **Hard-coded column names** — use `c.schema.raw.potential` (etc.), not
  remembered 1.x header strings.
- **Blocking the UI thread** — `get` on large `.res` / SQL dumps can take
  seconds; load off the main thread.
- **Missing mass / instrument** — wrong capacities or wrong loader; surface
  these as required inputs in the GUI.
- **Writing into the install tree** — treat user data dirs as read/write;
  never assume repo `testdata/` exists for end users.
- **Committing secrets / local config** — `cellpy setup` writes
  `.env_cellpy` and a user `cellpy.toml` (legacy installs may still have
  `~/.cellpy_prms_*.conf`); do not commit those.
- **Plot backends in headless CI** — set `MPLBACKEND=Agg` when running tests
  or batch plot export without a display.

## Where to read next

| Need | Page |
| --- | --- |
| Install / config / CLI checkup | [Installation](installation.md), [Configuration](configuration.md), [Checkup](checkup.md) |
| Frames and `schema` | [Data structure](../fundamentals/data_structure.md) |
| Tutorials | [Examples](../examples/index.md) |
| ICA / DVA | [How-to](../guides/ica.md), [API](../api/ica.md) |
| API signatures | [API reference](../api/index.md) |
| Contribute to cellpy itself | [Developers guide](../contributing/developers_guide/index.md) |

## Maintaining this page

When you change the public `cellpy.get` / `CellpyCell` / `schema` / CLI
surface, update **this file** and the short pointer section in root
`AGENTS.md` in the same PR. That rule is also recorded in
`.issueflows/04-designs-and-guides/this-project.md`.
