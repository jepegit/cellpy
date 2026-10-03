# PEC CSV data

!!! abstract "In this tutorial"

    You will learn how to:

    - load a PEC CSV export with the `pec_csv` loader
    - merge several PEC tests of the same cell

    **Data:** `pec.csv` and `pec_multiple_tests/` in `examples/data/` (falls back to the bundled example data).

    [:material-github: Open the notebook on GitHub](https://github.com/jepegit/cellpy/blob/master/examples/09_loading_pec_data.ipynb){ .md-button } — or get every notebook and its data with `cellpy pull --examples`.


This notebook shows a minimal PEC workflow with the built-in `pec_csv` loader. It uses the example export that ships with `cellpy`, inspects the raw file header, loads the cycling data, and generates step and summary tables.


```python
from pathlib import Path
import re

import cellpy
```


```python
local_pec_file = Path("data/pec.csv").resolve()
if local_pec_file.is_file():
    pec_file = local_pec_file
    print(f"Using local PEC file: {pec_file}")
else:
    from cellpy.utils import example_data

    pec_file = example_data.pec_file_path()
    print(f"Using example PEC file: {pec_file}")

pec_file
```

## Look at the raw file

Look at the first few lines of the PEC file to understand its structure.



```python
with open(pec_file, encoding="utf-8-sig") as handle:
    for line_number, line in zip(range(1, 13), handle):
        print(f"{line_number:02d}: {line.rstrip()}")

```

## Load the data

Load the PEC data with the built-in `pec_csv` loader. The `mass` value can be adjusted for the dataset.



```python
c = cellpy.get(
    filename=pec_file,
    instrument="pec_csv",
    mass=1.0,
    auto_summary=False,
)
c

```

The raw table is a pandas DataFrame. Prefer `c.schema` so column names track the native 2.1 headers.



```python
raw = c.data.raw
r = c.schema.raw
raw[[r.datapoint_num, r.cycle_num, r.step_num, r.test_time, r.current, r.potential]].head()

```

## Build the step table and summary

Build the step table and summary so cycle and step information is available.



```python
c.make_step_table()
c.make_summary()

print(f"Loaded rows: {len(c.data.raw)}")
print(f"Cycles: {c.get_cycle_numbers()[:10]}")
print(f"Start time: {c.data.start_datetime}")

```


```python
c.data.steps.head()

```


```python
c.data.summary.head()

```

## Save the cell

Save in HDF5 / cellpy format.



```python
c.save("pec_data.h5")

```

## Load several tests for the same cell
In PEC testers setup at IFE, have LotID to differentiate between cells and tests performed on that cell in terms of TestID.

By default, cellpy allows merging up to **20 files** in a single `cellpy.get()` call. This limit exists to catch accidental over-selection (e.g. a glob matching hundreds of files). If you genuinely need to merge more files, raise the limit before loading — either in your script or in your config file.


```python
# Raise the merge limit if you need to combine more than 20 files.
# Option A - change it for the current session only:
from cellpy import config

config.reader.max_raw_files_to_merge = 50  # or whatever you need

# Option B - set it permanently in your cellpy.toml:
#   [reader]
#   max_raw_files_to_merge = 50

```

Multiple files can be loaded at once by passing a list of file paths to `cellpy.get()`. The files are sorted by the test number extracted from the file name.



```python
def test_number(path):
    """Extract the test number from the file name. Expects file names in the format "TestXXXXX.csv"."""
    return int(re.search(r"Test(\d+)\.csv$", path.name).group(1))

files = [
    Path("data/pec_multiple_tests/Test25195.csv"),
    Path("data/pec_multiple_tests/Test25205.csv"),
    Path("data/pec_multiple_tests/Test25209.csv"),
]

files = sorted(files, key=test_number)

c = cellpy.get(files, instrument="pec_csv")
c.make_step_table()
c.make_summary()

```
