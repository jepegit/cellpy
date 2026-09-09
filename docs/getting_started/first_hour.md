---
icon: material/clock-fast
---

# Your first hour with cellpy

A guided run-through, start to finish, using data that ships with cellpy — so
nothing depends on your files or your configuration being right yet. Copy each
block, run it, and look at what comes back.

By the end you will have loaded a cell, read its per-cycle numbers, plotted its
capacity fade, exported it, and then done the same with a file of your own.

You do not need to know much Python. Where something is a Python idiom rather
than a cellpy idea, it is called out.

---

## Before you start

```console
python -m pip install "cellpy[batch]"
```

The `[batch]` part pulls in the plotting stack. Plain `pip install cellpy` works
too, but then step 5 will not draw anything. Conda users:
`conda install -c conda-forge cellpy`. Full details:
[Installation](installation.md).

Then, once:

```console
cellpy setup
```

That creates a `cellpy_data` folder and a configuration file. You do not need to
change anything in it yet.

Check that it worked:

```console
cellpy info --check
```

Not every line has to say ✓ — the checks cover optional features. If it printed
a version and found a configuration file, you are fine.

---

## 1. Open a Python session

Anything that runs Python will do: a Jupyter notebook, an IDE, or the plain
interpreter. If you want Jupyter and installed `cellpy[batch]`:

```console
cellpy serve --lab
```

---

## 2. Load a cell

```python
from cellpy.utils import example_data

c = example_data.raw_file()
```

That downloads a small Arbin `.res` file the first time (so you need network
once), reads it, and builds everything derived from it.

`c` is now a **cell object**. Almost everything you do goes through it. The name
`c` is just a variable — call it whatever you like.

How many cycles did we get?

```python
print(len(c.get_cycle_numbers()))
```

```text
18
```

---

## 3. Look at the per-cycle numbers

The per-cycle results live in `c.data.summary`, one row per cycle:

```python
c.data.summary[[
    "cycle_num",
    "charge_capacity_gravimetric",
    "discharge_capacity_gravimetric",
    "coulombic_efficiency",
]].head()
```

```text
 cycle_num  charge_capacity_gravimetric  discharge_capacity_gravimetric  coulombic_efficiency
         1                       2308.8                          2493.0                  92.6
         2                       2414.2                          2226.5                 108.4
         3                       2459.5                          2252.4                 109.2
         4                       2238.6                          2155.3                 103.9
         5                       2180.8                          2089.8                 104.4
```

An anode half cell, capacities in mAh/g. The efficiency above 100% from cycle 2
is the anode convention at work — see step 8.

Three things worth knowing right away:

- **`_gravimetric` means per gram of active material.** There are also
  `_areal` (per cm²) and `_absolute` (not normalised) versions of every
  capacity column. The version with *no* postfix is in the tester's own units,
  not yours — see [Summary columns](../reference/summary_columns.md).
- **The capacity depends on the mass you gave.** This example already has one.
  Yours will not (step 8).
- There are 58 columns in total. `print(c.data.summary.columns)` lists them.

---

## 4. The three tables

```python
c.data.raw       # every measured point
c.data.steps     # one row per step, with what kind of step it is
c.data.summary   # one row per cycle
```

They are [pandas](https://pandas.pydata.org/) DataFrames, so anything you
already know about pandas works here.

Column names change between cellpy versions, so ask the cell rather than typing
strings:

```python
potential = c.data.raw[c.schema.raw.potential]
current = c.data.raw[c.schema.raw.current]
```

More: [The data structure](../fundamentals/data_structure.md).

---

## 5. Draw a picture

```python
from cellpy.utils.plotutils import summary_plot

fig = summary_plot(c, y="capacities_gravimetric_coulombic_efficiency")
fig.show()
```

Capacity against cycle number, with coulombic efficiency in its own panel. In a
notebook, the figure appears in the cell; in a script, `fig.show()` opens it in
your browser.

Voltage curves for a few cycles:

```python
from cellpy.utils.plotutils import cycles_plot

cycles_plot(c, cycles=[5, 10, 15])
```

!!! note
    `summary_plot` **returns** a figure for you to show; `cycles_plot` shows it
    itself. That inconsistency is real — [Plot one cell](../guides/plotting.md)
    explains it and covers the rest of the plotting options.

---

## 6. Get one cycle's curve as numbers

```python
curve = c.get_cap(5)
curve.head()
```

```text
      potential      capacity
3635   0.792888  2.173295e-07
3636   0.787038  3.806380e-02
3637   0.781495  1.403270e-01
```

Potential in V, capacity in mAh/g. Plot it, fit it, or write it out — it is an
ordinary DataFrame.

---

## 7. Save your work

Save the cell in cellpy's own format so you never have to re-read the raw file:

```python
c.save("my_first_cell.cellpy")
```

Reopening it is fast, and everything comes back — data, metadata, units:

```python
import cellpy

c = cellpy.get("my_first_cell.cellpy")
```

For Excel:

```python
c.to_excel("my_first_cell.xlsx")
```

One workbook with the metadata, the summary and the step table on separate
sheets. Other formats — CSV, and the Battery Data Format for sharing — are in
[Get your data out](../guides/exporting.md).

---

## 8. Now your own file

Three things the example gave you for free, and you have to supply:

```python
import cellpy

c = cellpy.get(
    "path/to/my_cell.res",
    instrument="arbin_res",   # which tester wrote it
    mass=0.85,                # mg of active material
    cycle_mode="full_cell",   # or "anode" for a half cell
)
```

**`instrument`** — cellpy usually guesses from the file suffix, but say it
explicitly when the guess is wrong. `cellpy.print_instruments()` lists what is
available; some need a `model=` as well.

**`mass`** — in **milligrams**. If you leave it out, cellpy uses **1.0 mg** and
every gravimetric capacity is wrong by that ratio. This is the single most
common mistake.

**`cycle_mode`** — `"anode"` (the default) means the cycle starts on discharge,
the half-cell convention. For a full cell or a cathode half cell use
`"full_cell"`, or charge and discharge come out swapped and the coulombic
efficiency is upside down.

Then check it landed:

```python
print(c.data.mass, c.cycle_mode)
```

If you got `None` back from `cellpy.get` instead of a cell, see
[Troubleshooting](../troubleshooting.md#attributeerror-nonetype-object-has-no-attribute-data)
— that one has a specific cause and a specific fix.

---

## Where to go next

Depending on what you are actually trying to do:

| You want to… | Go to |
| --- | --- |
| understand the numbers you just saw | [Summary columns](../reference/summary_columns.md) |
| get capacities per area, or change units | [Units, mass, area and C-rates](../guides/units.md) |
| make better figures | [Plot one cell](../guides/plotting.md) |
| do dQ/dV | [Compute ICA / DVA](../guides/ica.md) |
| work on many cells at once | [Set up the cellpy database](../guides/batch_database.md) |
| get data into Excel or a repository | [Get your data out](../guides/exporting.md) |
| find out why a number looks wrong | [Troubleshooting](../troubleshooting.md) |

Longer worked examples, with real analysis rather than a tour, are in
[Tutorials](../examples/index.md). For a shorter answer to a specific question,
[How do I…?](../how_do_i.md) is indexed by exactly that.
