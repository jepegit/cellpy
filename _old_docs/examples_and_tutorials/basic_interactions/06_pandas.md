# Working with the `pandas.DataFrame` objects directly

:::{note}
This chapter would benefit from some more love and care. Any help
on that would be highly appreciated.
:::

The `CellpyCell` object stores the data in several `pandas.DataFrame` objects.
The easies way to get to the DataFrames is by the following procedure:

```python
# Assumed name of the CellpyCell object: c

# get the 'test':
data = c.data
# data is now a cellpy Data object (cellpy.readers.cellreader.Data)

# pandas.DataFrame with data vs cycle number (coulombic efficiency, charge-capacity etc.):
summary_data = data.summary
# you could also get the summary data by:
summary_data = c.data.summary

# pandas.DataFrame with the raw data:
raw_data = data.raw

# pandas.DataFrame with statistics on each step and info about step type:
step_info = data.steps
```

You can then manipulate your data with the standard `pandas.DataFrame` methods
(and `pandas` methods in general).

Happy pandas-ing!
