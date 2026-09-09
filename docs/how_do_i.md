---
icon: material/help-circle
---

# How do I…?

An index by question. Find what you are trying to do, get the shortest answer
that works, and follow the link when you need the detail.

Throughout, `c` is a loaded cell (`c = cellpy.get(...)`) and `b` is a loaded
batch (`b = batch.load(...)`).

---

## Get started

**…install cellpy so it can also plot?**

```console
python -m pip install "cellpy[batch]"
```

→ [Installation](getting_started/installation.md#optional-extras)

**…try cellpy without having a data file?**

```python
from cellpy.utils import example_data

c = example_data.raw_file()
```

→ [Your first hour](getting_started/first_hour.md)

**…check that my installation is healthy?**

```console
cellpy info --check
```

→ [Check your installation](getting_started/checkup.md)

**…find my configuration file?**

```console
cellpy info --configloc
cellpy edit config
```

→ [Setup and configuration](getting_started/configuration.md)

---

## Load data

**…load a file from my cycler?**

```python
c = cellpy.get("my_cell.res", instrument="arbin_res", mass=0.85)
```

→ [Basic usage](getting_started/basic_usage.md)

**…see which instruments cellpy supports?**

```python
cellpy.print_instruments()
```

**…load a file format cellpy does not know?**
Describe it in a YAML file and pass `instrument_file=`, or write a loader
plugin.
→ [Writing a custom loader](examples/07_custom_loaders.md) ·
[Loader plugin](other/writing_a_loader_plugin.md)

**…load several raw files as one cell?**

```python
c = cellpy.get(["run_01.res", "run_02.res", "run_03.res"])
```

**…load only some of the data sets in an Arbin file?**

```python
c = cellpy.get("my_cell.res", dataset_number=1)
```

**…load files from a server?**
Use an `scp://` path in `rawdatadir` or in `cellpy.get`.
→ [Work with remote files](getting_started/remote_paths.md)

**…see a cellpy file's metadata without loading the data?**

```python
meta = cellpy.read_meta("my_cell.cellpy")
meta["cell"]["mass"]
```

**…open an old `.h5` file from cellpy 1.x?**

```console
python -m pip install "cellpy[legacy-files]"
cellpy convert old_cell.h5 new_cell.cellpy
```

→ [File formats](fundamentals/file_formats.md)

---

## Set the cell up correctly

**…set the active mass?**

```python
c = cellpy.get("my_cell.res", mass=0.704)   # mg
```

**…change the mass after loading?**

```python
c.mass = 0.704
c.refresh_after("mass")
```

**…tell cellpy this is a full cell, not a half cell?**

```python
c = cellpy.get("my_cell.res", cycle_mode="full_cell")
```

**…set the electrode area, for areal capacities?**

```python
c = cellpy.get("my_cell.res", mass=0.704, area=1.77)   # cm²
```

**…give a nominal capacity, so C-rates mean something?**

```python
c = cellpy.get("my_cell.res", nominal_capacity="3579 mAh/g")
```

→ all four: [Units, mass, area and C-rates](guides/units.md)

---

## Find the numbers

**…get capacity per gram / per cm² / not normalised?**

```python
c.data.summary["charge_capacity_gravimetric"]   # mAh/g
c.data.summary["charge_capacity_areal"]         # mAh/cm²
c.data.summary["charge_capacity_absolute"]      # mAh
```

The name with **no** postfix is in the tester's units, not yours.
→ [Summary columns](reference/summary_columns.md)

**…know what a summary column means?**
→ [Summary columns](reference/summary_columns.md)

**…look up a column name without hard-coding it?**

```python
c.data.raw[c.schema.raw.potential]
c.data.summary[c.schema.summary.coulombic_efficiency]
```

**…translate a column name from cellpy 1.x?**
→ [Legacy header map](other/header_migration_map.md)

**…get a capacity–voltage curve for one cycle?**

```python
curve = c.get_cap(5)                       # potential, capacity
curve = c.get_cap(5, mode="absolute")      # not normalised
```

**…get the OCV relaxation after a cycle?**

```python
ocv = c.get_ocv(cycles=5, direction="up")   # cycle_num, step_num, step_time, potential
```

`direction` is `"up"` or `"down"`.

**…compute dQ/dV or dV/dQ?**

```python
from cellpy import ica

ica_frame = ica.dqdv(c, cycles=[2, 3])
dva_frame = ica.dvdq(c, cycles=2, direction="charge")
```

→ [Compute ICA / DVA](guides/ica.md)

**…pick out only the cycles run at a given C-rate?**

```python
c.get_cycle_numbers(rate=0.061, rate_on="charge", rate_std=0.005)
c.get_cycle_numbers(rate=0.061, rate_on="charge", rate_std=0.005, inverse=True)
```

Needs a `nominal_capacity` to be meaningful.

**…select all the discharge steps?**

```python
c.data.steps.query(f"{c.schema.steps.step_type}=='discharge'")
```

→ [Understand the step table](guides/step_table.md)

---

## Plot

**…plot capacity against cycle number?**

```python
from cellpy.utils.plotutils import summary_plot

fig = summary_plot(c, y="capacities_gravimetric_coulombic_efficiency")
fig.show()
```

**…see what else `summary_plot` can draw?**

```python
from cellpy.plotting import families

for name, description in families():
    print(name, "-", description)
```

**…plot voltage curves for a few cycles?**

```python
from cellpy.utils.plotutils import cycles_plot

cycles_plot(c, cycles=[5, 10, 15])
```

**…check how cellpy labelled the steps in a cycle?**

```python
from cellpy.utils.plotutils import cycle_info_plot

cycle_info_plot(c, cycle=3)
```

**…get the numbers behind a plot?**

```python
fig, data = summary_plot(c, y="capacities_gravimetric", return_data=True)
```

**…save a figure?**

```python
from cellpy.plotting import write_image

open("fig.png", "wb").write(write_image(fig, "png"))   # plotly
fig.write_html("fig.html")                             # interactive
fig.savefig("fig.png", dpi=300)                        # matplotlib
```

→ all six: [Plot one cell](guides/plotting.md)

---

## Get data out

**…save the cell so I can reopen it quickly?**

```python
c.save("my_cell.cellpy")
```

**…get it into Excel?**

```python
c.to_excel("my_cell.xlsx")                 # a file, not a folder
c.to_excel("my_cell.xlsx", cycles=[1, 5])  # plus curve sheets
```

**…get CSV files for Origin or MATLAB?**

```python
c.to_csv("out_folder")                     # a folder, not a file
```

**…export in a standard format for a paper or repository?**

```python
c.to_bdf("my_cell.bdf.csv")
```

**…export a batch's summaries?**

```python
b.summaries.write_csv("summaries.csv")             # polars, not pandas
b.summaries.to_pandas().to_excel("summaries.xlsx")
```

→ all five: [Get your data out](guides/exporting.md)

---

## Work on many cells

**…set up the database the batch utility reads?**
→ [Set up the cellpy database](guides/batch_database.md)

**…load a batch?**

```python
from cellpy.utils import batch

b = batch.load(name="paper01", project="cool_project", batch_col="b01")
```

**…make my spreadsheet edits actually take effect?**

```python
b = batch.load(name="paper01", project="cool_project", allow_from_journal=False)
```

The cached journal is reused otherwise.

**…see which cells failed to load?**

```python
b.result.report()
```

**…get one cell out of a batch?**

```python
c = b.cells["20180418_sf033_2_cc"]
```

**…hand a colleague a working copy of the batch?**

```python
b.export_project("bundle")
```

**…start a project folder with notebooks already wired up?**

```console
cellpy new -p my_project -e paper01
```

→ [Command line](reference/cli.md#cellpy-new) ·
[Batch processing](examples/batch_utility/cellpy_batch_processing.md)

---

## When something is wrong

**…find out why a file will not load?**

```python
c = cellpy.get("my_cell.res", logging_mode="INFO")
```

**…find the log file?**

```console
cellpy info --config     # look for filelogdir
```

**…fix capacities that are off by a factor of hundreds?**
The mass defaults to 1.0 mg. Set it, then `c.refresh_after("mass")`.

**…fix charge and discharge being swapped?**
`cycle_mode` defaults to `"anode"`. Set `cycle_mode="full_cell"`, then
`c.refresh_after("cycle_mode")`.

**…fix a step cellpy classified wrongly?**

```python
c.make_step_table(override_step_types={5: "rest"})
c.make_summary()
```

→ [Understand the step table](guides/step_table.md)

**…anything else that looks wrong?**
→ [Troubleshooting](troubleshooting.md)

---

## Not answered here?

If your question is not on this page and you could not find it in the docs, it
is worth telling us — a question that is hard to look up is a documentation
bug. [Open an issue](https://github.com/jepegit/cellpy/issues).
