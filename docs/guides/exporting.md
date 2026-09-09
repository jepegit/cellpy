# Get your data out

Sooner or later you want the numbers somewhere else — in Excel, in Origin, in
a colleague's hands, or in a data repository. cellpy has a different answer for
each of those.

## Which one do you want?

| You want to… | Use |
| --- | --- |
| come back to this cell in cellpy later | `c.save("cell.cellpy")` |
| open it in Excel | `c.to_excel("cell.xlsx")` |
| open it in Origin, MATLAB, or anything else | `c.to_csv("out_folder")` |
| do your own analysis in Python | the frames on `c.data` |
| share or archive it in a standard format | `c.to_bdf("cell.bdf.csv")` |
| get the whole batch's cycle summaries | `b.summaries` |
| hand a colleague a working batch | `b.export_project("bundle")` |
| save a figure | see [Plot one cell](plotting.md#saving-a-figure) |

## A cellpy file — the one that keeps everything

```python
c.save("my_run.cellpy")
```

This is the only format that round-trips: frames, metadata, units, step table
and summary all come back with `cellpy.get("my_run.cellpy")`. It is a zip of
parquet tables plus a `meta.json`, so it is compact and fast to reopen — much
faster than re-reading the tester's raw file.

Writing is atomic: an interrupted save leaves the existing file intact rather
than truncating it.

To write the legacy HDF5 layout instead (only if a collaborator is still on
cellpy 1.x):

```python
c.save("my_run.h5")                                # suffix decides
c.save("out.cellpy", cellpy_file_format="hdf5")    # or say so explicitly
```

That path needs `pip install "cellpy[legacy-files]"`. See
[File formats](../fundamentals/file_formats.md).

## Excel

```python
c.to_excel("my_run.xlsx")
```

One workbook, several sheets:

```text
meta_common          cell metadata, plus cellpy_units and raw_units
meta_test_dependent  per-test metadata
summary              the per-cycle summary
steps                the step table
```

Add the voltage–capacity curves as one sheet per cycle:

```python
c.to_excel("my_run.xlsx", cycles=[1, 2, 5, 10])
```

```text
meta_common  meta_test_dependent  summary  steps  cycle_001  cycle_002  cycle_005  cycle_010
```

| Argument | Meaning |
| --- | --- |
| `filename` | the `.xlsx` file to write. Leave it out and cellpy names it `<timestamp>_cellpy.xlsx` |
| `cycles` | `None` (no curve sheets), `True`, or a list of cycle numbers |
| `raw` | add the raw frame too (default `False`) |
| `steps` | include the step table (default `True`) |
| `nice` | formatting (default `True`) |
| `get_cap_kwargs` | passed to `get_cap` — how the curves are built |
| `to_excel_kwargs` | passed to pandas' `DataFrame.to_excel` |

!!! warning "`to_excel` takes a file name, not a folder"
    `c.to_excel("out_folder")` fails. It is `c.to_csv` that takes a directory.

Excel tops out at 1 048 576 rows, so a large raw frame is skipped rather than
truncated (with a warning in the log). For raw data, use CSV.

## CSV

```python
c.to_csv("out_folder")
```

Writes several files, named after the file the cell was loaded from:

```text
20160805_test001_45_cc_01_normal.csv   the raw frame
20160805_test001_45_cc_01_steps.csv    the step table
20160805_test001_45_cc_01_stats.csv    the per-cycle summary
```

| Argument | Meaning |
| --- | --- |
| `datadir` | folder to write into (current folder if omitted) |
| `sep` | column separator (defaults to the configured `sep`) |
| `raw` | write the raw and step files (default `True`) |
| `summary` | write the summary file (default `True`) |
| `cycles` | also write a voltage–capacity file (default `False`) |
| `method` | how the curves are laid out: `"back-and-forth"`, `"forth"`, `"forth-and-forth"` |
| `shifted`, `shift` | cumulate the shift between cycles, starting at `shift` |
| `last_cycle` | stop after this cycle |

If your locale expects a semicolon separator and a comma decimal mark, set
`sep=";"` here (and check `[reader] sep` in your configuration for the
default).

## Straight to pandas

The per-cell frames *are* pandas DataFrames, so you never have to go through
cellpy's exporters:

```python
c.data.summary.to_csv("summary.csv")
c.data.raw.to_excel("raw.xlsx")
c.data.steps.head()
```

Use `c.schema` for the column names, as in
[the data structure](../fundamentals/data_structure.md).

## Battery Data Format (BDF) — for sharing and archiving

[BDF](https://github.com/battery-data-alliance/battery-data-format) is a
community format for battery cycling data, with spelled-out column names and
units in the header. It is the right choice when the data is leaving your group
— a supplementary file for a paper, or a deposit in a repository.

```python
c.to_bdf("my_run.bdf.csv")
```

```text
Test Time / s,Voltage / V,Current / A,Unix Time / s,Cycle Count / 1,Step Index / 1,
Charging Capacity / Ah,Discharging Capacity / Ah,Charging Energy / Wh,...
```

| Argument | Meaning |
| --- | --- |
| `filename` | output path; a missing suffix becomes `<cell_name>.bdf.<format>` |
| `format` | `"csv"` (default) or `"parquet"` |
| `cycles` / `last_cycle` | export a subset |
| `header_style` | `"preferred"` (BDF spec, `"Test Time / s"`) or `"machine"` (`test_time_second`) |
| `extras` | append raw columns that BDF does not define. The file is then no longer strictly BDF-compliant |
| `bdf_units` | write in units other than the BDF defaults (also breaks strict compliance) |
| `preprocess_fn` | a function applied to the raw frame before export |

cellpy can also *read* BDF files — see
[BatMo BDF files](../examples/08_batmo_bdf.md).

## A whole batch

### The combined summaries

```python
from cellpy.utils import batch

b = batch.load(name="paper01", project="cool_project")

b.summaries          # every cell's per-cycle summary, stacked
```

!!! warning "Batch frames are polars, not pandas"
    `c.data.summary` on a single cell is a **pandas** DataFrame, but
    `b.summaries`, `b.journal.pages` and `b.tests` are **polars** DataFrames.
    They look similar and behave differently — `.to_csv()` does not exist on a
    polars frame.

    ```python
    b.summaries.write_csv("summaries.csv")           # polars
    b.summaries.to_pandas().to_excel("summaries.xlsx")   # via pandas
    ```

    `write_excel()` exists on polars too, but needs `pip install xlsxwriter`.
    Going through `to_pandas()` uses the openpyxl that cellpy already has.

### A shareable bundle

```python
journal = b.export_project("bundle")
```

Writes one `<label>.cellpy` per cell into `bundle/`, rewrites the journal so it
points at those files, and saves the journal JSON. A colleague can then
`batch.load(...)` the journal without access to your raw files or your database.

Every cell has to be loaded first — `export_project` raises `ValueError` and
names the unloaded cells otherwise. It does **not** copy the raw files.

To write only the journal:

```python
b.save()                   # cellpy_batch_<name>.json
b.export_journal(path)     # the same thing, to a chosen path
```

## What survives which format

| | frames | metadata | units | step table | reopens in cellpy |
| --- | --- | --- | --- | --- | --- |
| `.cellpy` | ✅ | ✅ | ✅ | ✅ | ✅ |
| Excel | summary + steps (+ raw, curves) | ✅ (own sheets) | ✅ (own sheet) | ✅ | ❌ |
| CSV | ✅ | ❌ | ❌ | ✅ | ❌ |
| BDF | raw only | header only | ✅ (in headers) | ❌ | ✅ (as raw) |

Keep the `.cellpy` file as your working copy and treat the rest as output. If
you only ever export CSV, you will be re-reading raw tester files — and
re-entering masses — forever.

## See also

- [File formats](../fundamentals/file_formats.md) — what a cellpy file contains
- [Plot one cell](plotting.md#saving-a-figure) — saving figures
- [Set up the cellpy database](batch_database.md) — where batch cells come from
- [Command line](../reference/cli.md#cellpy-convert) — `cellpy convert` for old
  files
