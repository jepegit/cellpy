---
icon: material/card-text
---

# Cheat sheet

The calls you'll use most, one block each. New to cellpy? Start with
[Your first hour](first_hour.md), which explains what each of these does. For
anything not listed here, see [How do I…?](../how_do_i.md).

## Load

```python
import cellpy

c = cellpy.get("my_cell.res", instrument="arbin_res", mass=0.85)  # mass in mg
c = cellpy.get(["run_01.res", "run_02.res"], mass=0.85)          # continued runs
c = cellpy.get("my_cell.cellpy")                                   # a saved cell

from cellpy.utils import example_data
c = example_data.raw_file()                                        # bundled data
```

`cellpy.get` reads the file, builds the step table and makes the per-cycle
summary. `cellpy.print_instruments()` lists the `instrument=` names.

## Set the cell up

```python
c = cellpy.get("my_cell.res", mass=0.704, area=1.77)               # mg, cm²
c = cellpy.get("my_cell.res", nominal_capacity="3579 mAh/g")       # for C-rates
c = cellpy.get("my_cell.res", cycle_mode="full_cell")              # not a half cell

c.mass = 0.704            # changed your mind after loading?
c.refresh_after("mass")   # …then recompute what depends on it
```

→ [Units, mass, area and C-rates](../guides/units.md)

## Look at the tables

```python
c.data.raw        # every data point the tester wrote
c.data.steps      # one row per step: charge, discharge, rest, …
c.data.summary    # one row per cycle

c.get_cycle_numbers()
```

All three are pandas DataFrames. What each column means:
[Summary columns](../reference/summary_columns.md) ·
[The step table](../guides/step_table.md).

## Get the numbers

```python
c.data.summary["charge_capacity_gravimetric"]   # mAh/g
c.data.summary["charge_capacity_areal"]         # mAh/cm²
c.data.summary["charge_capacity_absolute"]      # mAh
c.data.summary[c.schema.summary.coulombic_efficiency]
```

!!! warning
    The bare `charge_capacity` column is in the **tester's** units, not yours.
    For an Arbin file that means Ah, a factor of 1000 off from mAh.

## Curves for one cycle

```python
curve = c.get_cap(5)                           # capacity vs potential
ocv = c.get_ocv(cycles=5, direction="up")      # relaxation after the cycle

from cellpy import ica
ica_frame = ica.dqdv(c, cycles=[2, 3])         # dQ/dV
dva_frame = ica.dvdq(c, cycles=2, direction="charge")   # dV/dQ
```

## Plot

```python
from cellpy.utils.plotutils import summary_plot, cycles_plot

fig = summary_plot(c, y="capacities_gravimetric_coulombic_efficiency")
fig.show()                        # summary_plot returns the figure…
cycles_plot(c, cycles=[5, 10, 15])   # …cycles_plot shows it itself
```

Plotting needs the `batch` extra (`pip install "cellpy[batch]"`).
→ [Plot one cell](../guides/plotting.md)

## Save and export

```python
c.save("my_cell.cellpy")          # everything, reloadable with cellpy.get
c.to_excel("my_cell.xlsx")        # summary, steps and metadata as sheets
c.to_csv("out_folder")            # one CSV per table (the folder must exist)
```

→ [Get your data out](../guides/exporting.md)

## Many cells

```python
from cellpy.utils import batch

b = batch.load(name="paper01", project="cool_project", batch_col="b01")
# every row in the cellpy database sheet whose "b01" column says "paper01"
```

→ [Batch processing](../examples/batch_utility/cellpy_batch_processing.md) ·
[Set up the cellpy database](../guides/batch_database.md)
