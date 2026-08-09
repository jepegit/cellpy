# Loading PEC CSV Data

This notebook shows a minimal PEC workflow with the built-in `pec_csv` loader. It uses the example export that ships with `cellpy`, inspects the raw file header, loads the cycling data, and generates step and summary tables.


```python
from pathlib import Path
import sys
import re

# Changes to the cellpy repo can directly be used without installing the package. This is useful for development and testing.
repo_root = next(
    (path for path in [Path.cwd(), Path.cwd().parent] if (path / "cellpy" / "__init__.py").exists()),
    None,
)
if repo_root is not None and str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
# IF not using the cellpy repo, make sure to install cellpy in the current environment (e.g., pip install cellpy) and comment the above code.
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


```python
# Let's take a look at the first few lines of the PEC file to understand its structure.
with open(pec_file, encoding="utf-8-sig") as handle:
    for line_number, line in zip(range(1, 13), handle):
        print(f"{line_number:02d}: {line.rstrip()}")
```


```python
# Now we can load the PEC data using cellpy. We specify the instrument type as "pec_csv" and set the mass to 1.0 (this is a parameter that can be adjusted based on the specific dataset).
cell = cellpy.get(
    filename=pec_file,
    instrument="pec_csv",
    mass=1.0,
    auto_summary=False,
)
cell
```


```python
# Now that we have loaded the data, we can take a look at the raw data to see what it looks like. The raw data is stored in a pandas DataFrame, and we can use the `head()` method to see the first few rows.
# Prefer c.schema so column names track the native 2.0 headers.
raw = cell.data.raw
r = cell.schema.raw
raw[[r.datapoint_num, r.cycle_num, r.step_num, r.test_time, r.current, r.potential]].head()
```


```python
# After loading the data, we need to make the step table and summary to have access to the cycle and step information.
cell.make_step_table()
cell.make_summary()

print(f"Loaded rows: {len(cell.data.raw)}")
print(f"Cycles: {cell.get_cycle_numbers()[:10]}")
print(f"Start time: {cell.data.start_datetime}")
```


```python
cell.data.steps.head()
```


```python
cell.data.summary.head()
```


```python
# Save in h5 format
cell.save("pec_data.h5")
```

# Loading Multiple tests for the same CellID
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


```python
# Multiple files can be loaded at once by passing a list of file paths to the cellpy.get() function. The files will be sorted based on the test number extracted from the file name.

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


```python

```
