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
)
c.save("out/my_cell.cellpy")  # HDF5 cellpy file — fast reload later
c.to_csv("out/csv_export")
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
- `make_step_table()` / `make_summary()` — usually already run by `get`
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
| API signatures | [API reference](../api/index.md) |
| Contribute to cellpy itself | [Developers guide](../contributing/developers_guide/index.md) |

## Maintaining this page

When you change the public `cellpy.get` / `CellpyCell` / `schema` / CLI
surface, update **this file** and the short pointer section in root
`AGENTS.md` in the same PR. That rule is also recorded in
`.issueflows/04-designs-and-guides/this-project.md`.
