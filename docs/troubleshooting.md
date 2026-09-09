---
icon: material/lifebuoy
---

# Troubleshooting

Things that commonly go wrong, and what to do about them. Find your symptom in
the list below — most entries are one or two lines of code away from a fix.

If your problem is not here, jump to [Reporting a problem](#reporting-a-problem)
at the end.

---

## First: make cellpy tell you what happened

By default cellpy is quiet. Two switches make it talk.

**Turn on messages while loading:**

```python
import cellpy

c = cellpy.get("my_cell.res", mass=0.85, logging_mode="INFO")
```

Use `logging_mode="DEBUG"` for the full firehose (much more output, but it
usually names the exact point where loading gave up).

**Find the log files.** cellpy also writes `cellpy_info.log`,
`cellpy_debug.log` and `cellpy_errors.log`. They land in the `filelogdir`
folder from your configuration, and in the current working directory if that
folder does not exist:

```console
cellpy info --config
```

Look for the `filelogdir` entry in the output. See
[Setup and configuration](getting_started/configuration.md) if you want to move
it somewhere more convenient, and the
[command-line reference](reference/cli.md) for the rest of `cellpy info`.

**Check that the installation itself is healthy:**

```console
cellpy info --check
```

---

## Loading a file

### `AttributeError: 'NoneType' object has no attribute 'data'`

You almost certainly wrote something like this:

```python
c = cellpy.get("my_cell.res")
print(c.data.summary)   # <- AttributeError here
```

`cellpy.get` returns `None` when it could not read the file, so the error you
see is one step *after* the real problem. Look further up in the output —
cellpy printed:

```text
Could not load file: check log!
Returning None
```

Re-run with `logging_mode="INFO"` (see above) to find out *why*. The usual
causes are the next three entries.

### cellpy chose the wrong loader for my file

cellpy guesses the instrument from the file suffix, falling back to the
`instrument` setting in your configuration file. When the guess is wrong, say
so explicitly:

```python
c = cellpy.get("my_cell.txt", instrument="maccor_txt", model="ONE")
```

To see what is available:

```python
import cellpy

cellpy.print_instruments()
```

```text
================================================================================
Implemented instrument loaders
================================================================================
arbin_res
arbin_sql
...
maccor_txt
  models: ZERO, ONE, TWO, THREE, S4000-UBHAM, S4000-KIT, S4000-WMG
...
```

Instruments with a `models:` line need `model=` as well — the same vendor
exports several different text layouts, and cellpy cannot tell them apart from
the suffix. [Other file formats](examples/06_loading_different_formats.md)
shows a worked example per instrument.

!!! note "`.h5` files are ambiguous"
    `.h5` / `.hdf5` is both the old cellpy file format and a raw format for
    some instruments. If you pass `instrument=`, the raw loader wins; leave it
    out to read the file as a cellpy file.

If your cycler is not on the list at all, you can describe its file format
yourself — see [Writing a custom loader](examples/07_custom_loaders.md) — or
package a loader properly as a
[loader plugin](other/writing_a_loader_plugin.md).

### Arbin `.res` files will not open

`.res` files are Microsoft Access databases, so reading them needs a driver
that cellpy does not ship.

- **Windows:** you need an Access / ACE ODBC driver **whose bitness matches
  your Python** (64-bit Python needs the 64-bit driver). A mismatch is the
  single most common cause.
- **Linux / macOS:** you need `mdbtools`. cellpy raises a message that names
  the fix:

    ```text
    Reading Arbin .res on Linux/macOS needs mdbtools (provides `mdb-export`).
    Debian/Ubuntu: apt install mdbtools. macOS: brew install mdbtools.
    ```

Full per-platform instructions are in
[Installation](getting_started/installation.md).

### An old `.h5` cellpy file will not open

```text
... needs the HDF5 stack (PyTables), which is not installed.
```

cellpy 2 writes a zipped-parquet `.cellpy` file and no longer installs the HDF5
machinery by default. To read files written by cellpy 1.x:

```console
python -m pip install "cellpy[legacy-files]"
```

Once installed, `cellpy.get("old_file.h5")` works as before, and
`c.save("new_file.cellpy")` converts it to the current format.

### The file loads but there are no cycles

```python
c = cellpy.get("my_cell.res", mass=0.85)
print(len(c.get_cycle_numbers()))   # 0
```

Usually one of:

- **The run really is one long step** (a rate test that never completed a
  cycle, or a pure OCV recording). Check `c.data.raw` — if the raw table has
  rows, the file was read fine and there is simply nothing to summarise.
- **Only some data sets were loaded.** Arbin `.res` files can hold several
  tests. `cellpy.get(..., dataset_number=1)` picks one; leaving it out merges
  all of them.
- **The summary was skipped.** If you passed `auto_summary=False`, build it
  yourself with `c.make_step_table()` then `c.make_summary()`.

---

## The numbers look wrong

### All my capacities are far too large (or too small)

Check the mass:

```python
print(c.data.mass)   # 1.0  <- the default, in mg
```

If you do not give a mass, cellpy uses **1.0 mg** (or whatever mass was stored
in the file). Every gravimetric capacity is then wrong by the ratio between
1.0 mg and your real mass.

Give the mass when you load:

```python
c = cellpy.get("my_cell.res", mass=0.704)          # mg
c = cellpy.get("my_cell.res", mass="0.704 mg")     # same, explicit unit
```

If the cell is already loaded, set the mass and rebuild the affected columns:

```python
c.mass = 0.704
c.refresh_after("mass")
```

`refresh_after` also takes `"area"`, `"nominal_capacity"` and `"cycle_mode"`.
Changing the metadata alone does **not** update the summary — that is why this
step is needed.

### Charge and discharge look swapped, and the coulombic efficiency is upside down

cellpy's default `cycle_mode` is **`"anode"`** — the half-cell convention,
where the *first* step of a cycle is a discharge (lithiation of the working
electrode). For a full cell or a cathode half-cell, say so:

```python
c = cellpy.get("my_cell.res", mass=0.85, cycle_mode="full_cell")
```

Accepted spellings for the ordinary convention are `"full_cell"`,
`"fullcell"`, `"full cell"`, `"cathode"`, `"standard"` and `"normal"`. Anything
else — `"full-cell"` with a hyphen, for instance — is *not* recognised: cellpy
falls back to the ordinary convention and logs a warning, so check your log if
you are unsure which convention was applied.

To change it on a loaded cell:

```python
c.cycle_mode = "full_cell"
c.refresh_after("cycle_mode")
```

You can also change the default for every load — see `cycle_mode` in the
[configuration reference](getting_started/configuration_reference.md).

### Which capacity column do I actually want?

The summary carries the same quantity in several normalisations:

| Column | Meaning | Unit |
| --- | --- | --- |
| `charge_capacity` | as recorded, not normalised | **the tester's unit** (`c.data.raw_units`) |
| `charge_capacity_absolute` | not normalised | your unit (`c.cellpy_units`), e.g. mAh |
| `charge_capacity_gravimetric` | per active mass | e.g. mAh/g |
| `charge_capacity_areal` | per electrode area | e.g. mAh/cm² |

The bare name is **not** the one in your units. An Arbin `.res` file records
charge in Ah, so `charge_capacity` comes out in Ah while
`charge_capacity_absolute` is in mAh — a factor of 1000 apart. Use
`_absolute` when you want an un-normalised capacity in the unit you configured.

The same split exists for discharge, capacity loss, coulombic difference and
the cumulated variants. `c.schema.summary` gives you the **base** name; add the
postfix yourself:

```python
base = c.schema.summary.charge_capacity          # "charge_capacity"
grav = f"{base}_gravimetric"                     # "charge_capacity_gravimetric"

c.data.summary[grav].head()
```

The areal columns need an electrode area (`area=` on `cellpy.get`, in cm²) to
mean anything. [Units, mass, area and C-rates](guides/units.md) explains the
whole normalisation story, including how to change the units themselves.

### A capacity is missing or too small for some cycles

cellpy works out charge and discharge capacities from the **step table**, so a
step it could not classify contributes nothing. Count the labels:

```python
sc = c.schema.steps
print(c.data.steps[sc.step_type].value_counts())
print((c.data.steps[sc.step_type] == "").sum())   # uncategorized steps
```

An empty `step_type` means no classification rule matched. The fixes —
threshold overrides, per-step overrides, or a full schedule specification — are
in [Understand the step table](guides/step_table.md).

### My capacity used to look twice as large in cellpy 1.x

That is deliberate. Some testers do not reset their cumulative capacity column
between cycles; 1.x passed the column through unchanged, so a forgotten reset
showed up as doubled capacity. cellpy 2 rebases each cycle to start at zero and
warns when it actually changed something:

```text
UserWarning: cellpy rebased vendor capacity/energy so each cycle starts at 0:
charge_capacity (per_test). 1.x kept the tester column as-is (a forgotten
reset then looks like doubled capacity).
```

The cellpy 2 numbers are the correct ones.

---

## Column names

### `KeyError: 'voltage'` (or another column name from cellpy 1.x)

cellpy 2 renamed the frame columns. `voltage` is now `potential`, `data_point`
is `datapoint_num`, and so on. Rather than memorise the new strings, ask the
cell:

```python
v = c.data.raw[c.schema.raw.potential]
q = c.data.summary[c.schema.summary.charge_capacity]
```

Code written this way keeps working across schema changes. The full old → new
table is the [legacy header map](other/header_migration_map.md); the
[migration guide](getting_started/migration_v1_to_v2.md) covers the rest of the
1.x → 2.x differences.

To simply see what a frame contains:

```python
print(list(c.data.summary.columns))
```

---

## Plotting and exporting

### `OptionalDependencyError` when plotting or saving a figure

cellpy keeps the plotting stack optional so a headless install stays small. The
error names the extra to install:

| Message mentions | Install |
| --- | --- |
| matplotlib | `pip install "cellpy[plotting-mpl]"` |
| kaleido (static PNG/SVG/PDF export) | `pip install "cellpy[batch]"` |
| PyTables / HDF5 | `pip install "cellpy[legacy-files]"` |

[Plot one cell](guides/plotting.md) covers what each extra actually buys you.

---

## Batch processing

### I edited my database, but the batch still shows the old cells

`batch.load` reuses an existing `cellpy_batch_<name>.json` journal in the
working directory and does **not** re-read the database when it finds one. It
warns when this happens. To force a rebuild from the database:

```python
from cellpy.utils import batch

b = batch.load(name="my_project", project="my_project", allow_from_journal=False)
```

Deleting the `cellpy_batch_<name>.json` file has the same effect.

### One cell is reported as `FAILED`

The raw file could not be found. cellpy warns and marks the cell rather than
stopping the whole batch. See which ones:

```python
b.result.report()
```

Then check that the file really is where the database says it is, and that your
`rawdatadir` / `cellpydatadir` paths in the configuration point at the right
place.

### `UnderDefined: db_file is not provided`

The batch needs to know which database (Excel sheet) to read. Either pass
`db_file=` explicitly, or set the database path and filename in your
configuration — see [Setup and configuration](getting_started/configuration.md).

### A cell in my spreadsheet never turns up in the batch

Batch selection needs **both** a matching batch name and `exists > 0` on that
row. An empty `exists` column silently drops the cell. See
[Set up the cellpy database](guides/batch_database.md).

---

## Installation and the command line

### `cellpy: command not found` / `'cellpy' is not recognized`

The package is installed but its script folder is not on your `PATH`. If you
installed into a virtual environment or a conda environment, make sure that
environment is activated first. Checking where the package actually landed
usually settles it:

```console
python -c "import cellpy, pathlib; print(pathlib.Path(cellpy.__file__).parent)"
```

If that fails too, cellpy is not installed in the Python you are running — see
[Installation](getting_started/installation.md).

### `cellpy info --check` reports failures

Not every check has to pass. The checks cover optional features — Arbin `.res`
drivers, for instance — so a failure only matters if you need that feature. Fix
the ones that block your workflow and ignore the rest.

---

## Reporting a problem

If none of the above helps, please open an issue at
[github.com/jepegit/cellpy/issues](https://github.com/jepegit/cellpy/issues). A
report that includes the following is usually solved much faster:

1. The output of `cellpy info --version` and `cellpy info --check`.
2. The exact code you ran, and the full error message (all of it, not just the
   last line).
3. The instrument and file type you are loading.
4. The relevant part of `cellpy_debug.log` after re-running with
   `logging_mode="DEBUG"`.

Sharing the data file itself is helpful but rarely necessary — a description of
the layout is often enough.
