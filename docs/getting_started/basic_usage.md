# Basic usage

A short path from install to a loaded cell. For plots and longer workflows,
use the [Tutorials](../examples/index.md). Example notebooks and data also live
in the [examples folder on GitHub](https://github.com/jepegit/cellpy/tree/master/examples)
(`cellpy pull` can download them).

## Load a cell

Prefer bundled example data when trying the library for the first time
(needs network on first download):

```python
from cellpy.utils import example_data

c = example_data.raw_file()  # Arbin .res → CellpyCell with steps + summary
```

Or load a path you already have:

```python
import cellpy

c = cellpy.get(
    "path/to/my_cell.res",
    mass=0.982,  # active material mass in mg
    instrument="arbin_res",  # optional; often inferred from the suffix
)
```

`cellpy.get` loads the file, builds the step table, and creates the per-cycle
summary (unless you opt out with keyword arguments).

When you pass `instrument=` for a raw `.h5` / `.hdf5` file, that loader wins
over suffix auto-pick of the native cellpy format. Omit `instrument` (or use a
`.cellpy` / `.cpy` path) when you want the native reader.

## Inspect frames and schema

Measurement tables live on `c.data`. Prefer **`c.schema`** for column names
so code tracks the active schema (native cellpy-core names in 2.x):

```python
print(c.data.summary.head())
print(c.get_cycle_numbers()[:5])

potential = c.data.raw[c.schema.raw.potential]
charge_cap = c.data.summary[c.schema.summary.charge_capacity]
```

Hard-coding 1.x header strings is brittle — see
[Coming from cellpy 1.x](migration_v1_to_v2.md) and the
[legacy header map](../other/header_migration_map.md).

## Save and export

Save a tester-agnostic cellpy file (2.x default is the v9 zip-of-parquet
`.cellpy` format; HDF5 remains readable):

```python
c.save("out/my_cell.cellpy")
```

CSV export:

```python
c.to_csv("out/csv_export")
```

Frames are pandas DataFrames, so you can also use `DataFrame.to_excel` /
`to_csv` on `c.data.raw`, `.steps`, or `.summary` directly. `CellpyCell`
also exposes `to_excel` for a packaged export.

## Cycles and curves

```python
cycles = c.get_cycle_numbers()
print(f"{len(cycles)} cycles")

cap = c.get_cap(5)  # capacity–voltage for cycle 5
ocv = c.get_ocv(ocv_type="ocvrlx_up", cycle_number=44)
```

More extractors (`get_current`, `get_voltage`, `split`, `merge`, …) are on
`CellpyCell` — see the [API reference](../api/cellpy.md) and
[Tutorials](../examples/index.md).

## Next steps

- [Incremental capacity analysis](../examples/04_incremental_capacity_analysis.md)
  and other tutorials for ICA, GITT, and batch work
- [Using cellpy from an agent](agents.md) if you are wiring a GUI or app
- [Check your installation](checkup.md) if something failed to load
