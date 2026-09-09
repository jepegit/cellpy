# Set up the cellpy database

To work on many cells at once, cellpy needs a small **database**: an Excel
sheet with one row per cell. The shipped example has 67 columns, which is
intimidating — but you only have to fill in about ten of them.

This page is about the sheet itself. For what to *do* with a loaded batch, see
the [Batch processing tutorial](../examples/batch_utility/cellpy_batch_processing.md).

## What the sheet looks like

Three kinds of row:

| Row | Contents |
| --- | --- |
| row 1 | column **names** (`id`, `cell`, `mass_active_material`, …) |
| row 2 | column **types** (`int`, `str`, `float`, `bol`, `categorical`, `list`) |
| row 3 onwards | one **cell** per row |

A ready-made file is in the repository at
[`examples/batch_utility/cellpy_db.xlsx`](https://github.com/jepegit/cellpy/tree/master/examples/batch_utility).
Start from that rather than building one from scratch — the extra columns cost
you nothing, and you can leave them empty.

Tell cellpy where it is:

```python
import cellpy.config as config

config.paths.db_path = "."                    # folder holding the sheet
config.paths.db_filename = "cellpy_db.xlsx"   # its name
config.paths.rawdatadir = "data/raw"          # where the tester files live
config.paths.cellpydatadir = "data/cellpyfiles"
```

or set the same four in your `cellpy.toml` so you never think about it again
(see [Setup and configuration](../getting_started/configuration.md)).

## The columns that actually matter

| Column in the sheet | What it does | Leave empty? |
| --- | --- | --- |
| `id` | row key — a **unique integer** per row | no |
| `exists` | row is only used when this is **> 0** | no — set it to `1` |
| `b01` … `b07` | batch selectors; you name one when you load | no — fill the one you use |
| `cell` | the cell's name, and its label in the batch | no |
| `file_name_indicator` | what cellpy globs for when finding raw files | falls back to `cell` |
| `instrument` | which loader to use (`arbin_res`, `maccor_txt`, …) | no |
| `cell_type` | becomes the cell's **`cycle_mode`** — `anode` or `full_cell` | no |
| `mass_active_material` | active mass in mg | only if you never look at gravimetric capacity |
| `area` | electrode area in cm² | only if you never look at areal capacity |
| `nominal_capacity` | for C-rates and equivalent full cycles | yes, if you do not need those |
| `nominal_capacity_specifics` | `gravimetric` (default) / `areal` / `absolute` | usually |
| `group` | groups cells for plotting and legends | yes |
| `label` | display name in plots, instead of the file name | yes |
| `loading_active_material`, `mass_total` | carried into the journal | yes |
| `comment_general`, `comment_cell`, `comment_slurry` | your notes | yes |
| `argument` | per-cell loader keywords (see below) | yes |

Every other column in the example file is either bookkeeping for the authors'
own lab or reserved for later. Leaving them blank is fine.

!!! warning "`exists` is not optional"
    Batch selection is `batch column matches` **and** `exists > 0`. A row with
    an empty `exists` is silently skipped, which looks exactly like a broken
    file path. If a cell you expected is missing from the batch, check this
    column first.

!!! tip "`cell_type` is really `cycle_mode`"
    The value in `cell_type` is used as the cell's `cycle_mode`, which decides
    whether the first step of a cycle counts as a discharge. Put `anode` there
    for half cells and `full_cell` for full cells — not a material name. See
    [Units, mass, area and C-rates](units.md) for what it changes.

## Batch columns — how cells are grouped into a batch

`b01` through `b07` are seven independent selectors, so the same cell can
belong to several batches at once. Put a batch name in one of them:

| `id` | `cell` | `b01` | `b02` |
| --- | --- | --- | --- |
| 1070 | `20180418_sf033_2_cc` | `paper01` | |
| 1071 | `20180418_sf033_3_cc` | `paper01` | `rate_study` |
| 1072 | `20180420_sf036_2_cc` | `paper01` | `rate_study` |

Then load by naming both the batch and the column:

```python
from cellpy.utils import batch

b = batch.load(name="paper01", project="cool_project", batch_col="b01")
```

`batch_col` defaults to `"b01"`, so you can leave it out if that is the column
you used. Matching is **case-sensitive**.

`project` is the campaign the batch belongs to; it decides where the journal
file is written and, if you turn on `config.batch.auto_use_file_list`, it must
match the folder name under `rawdatadir` exactly.

## How cellpy finds the raw files

You do not put file paths in the sheet. cellpy builds them:

- **raw files** — globs `<file_name_indicator>*.<raw_extension>` under
  `paths.rawdatadir`, including sub-folders. With
  `file_name_indicator = "20180418_sf033_2_cc"` and the default
  `raw_extension = "res"`, that matches
  `20180418_sf033_2_cc_01.res`, `..._02.res`, and so on — several files for one
  cell are merged automatically.
- **cellpy files** — looks for `<file_name_indicator>.<cellpy_file_extension>`
  in `paths.cellpydatadir`, and reuses it instead of re-reading the raw file
  when it is there.

So the naming convention is doing real work: the indicator has to be a prefix
of the tester's file names.

If a cell's raw file is not found, cellpy warns, marks the cell, and carries
on with the rest of the batch:

```text
UserWarning: filefinder found no raw files for 1 cell(s): 20180418_sf033_9_cc.
Check paths.rawdatadir (and OtherPath hosts) plus the filename indicators in
the database.
```

`b.result.report()` lists which cells failed.

## Per-cell loader arguments

The `argument` column takes loader keywords for that one cell, as
`key=value` pairs separated by semicolons:

```text
model=ONE;dataset_number=1
```

These are merged on top of the values from the other columns, so it is the
place for the one Maccor file in an otherwise Arbin batch, or the one cell
where you need to skip a data set.

## Loading and checking the result

```python
from cellpy.utils import batch

b = batch.load(name="paper01", project="cool_project", batch_col="b01")

print(list(b.cells.keys()))
b.journal.pages          # one row per cell — what cellpy resolved
b.summaries              # all the per-cycle summaries, stacked
```

The journal is where you check that the sheet was read the way you meant:

```python
b.journal.pages.select(
    ["filename", "mass", "cell_type", "instrument", "group", "label"]
)
```

```text
{'filename': '20180418_sf033_2_cc', 'mass': 0.337, 'cell_type': 'anode',
 'instrument': 'arbin_res', 'group': 1, 'label': 'sf033_2'}
```

The journal columns come from the sheet like this:

| Journal column | Comes from |
| --- | --- |
| `filename` | `cell` |
| `mass` | `mass_active_material` |
| `total_mass` | `mass_total` |
| `file_name_indicator` | `file_name_indicator` (or `cell`) |
| `nom_cap` / `nom_cap_specifics` | `nominal_capacity` / `nominal_capacity_specifics` |
| `cell_type` | `cell_type` — and becomes `cycle_mode` |
| `experiment` | `experiment_type` |
| `group` / `group_label` | `group` |
| `raw_file_names` / `cellpy_file_name` | filled in by the file search |

## The journal file, and why your edits sometimes do nothing

The first successful load writes `cellpy_batch_<name>.json` into
`journal_dir` — by default the directory you started the kernel in, so usually
next to your notebook. (`save_cellpy=False` skips that write, along with the
`.cellpy` files.) On the **next** load cellpy finds that file and reuses it: it
does not re-read the Excel sheet, and it warns about that if you passed
database arguments.

That is a feature (fast reloads, and a record of exactly what a figure was made
from), but it is also the single most confusing thing about the batch utility:
you edit a mass in the spreadsheet, re-run, and nothing changes.

To rebuild from the database:

```python
b = batch.load(
    name="paper01",
    project="cool_project",
    allow_from_journal=False,     # ignore the cached journal
)
```

Deleting the `cellpy_batch_<name>.json` file has the same effect.

If you only changed metadata that affects derived numbers (mass, nominal
capacity, cycle mode), add `force_recalc=True` so the summaries are rebuilt
too.

## Common problems

| Symptom | Likely cause |
| --- | --- |
| a cell is missing from the batch | `exists` is empty or 0, or the batch name does not match exactly (case-sensitive) |
| every cell is `FAILED` | `paths.rawdatadir` is wrong, or `file_name_indicator` does not prefix the real file names |
| capacities are absurd | `mass_active_material` empty → the 1.0 mg default |
| charge and discharge swapped | `cell_type` is not `anode` / `full_cell` |
| edits to the sheet have no effect | the cached journal — use `allow_from_journal=False` |
| `UnderDefined: db_file is not provided` | `paths.db_path` / `db_filename` not set |

## Using a different database

The Excel sheet is only the default. `batch.load` takes `db_reader=` /
`reader=` to select another reader, and `reader_path=` to point at its file —
a JSON-backed database, for instance. The column names cellpy looks for in the
Excel sheet are themselves configurable, under `[db_cols]` in `cellpy.toml`;
see the [configuration reference](../getting_started/configuration_reference.md#db_cols).
A configured column that is missing from your sheet warns once and comes back
empty rather than failing the load.

## See also

- [Batch processing tutorial](../examples/batch_utility/cellpy_batch_processing.md)
  — the full worked notebook
- [Units, mass, area and C-rates](units.md) — what `mass`, `area` and
  `nominal_capacity` change
- [Troubleshooting](../troubleshooting.md) — batch failures and journal reuse
