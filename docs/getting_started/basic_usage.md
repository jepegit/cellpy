# Basic usage

As with most software, you are encouraged to play a little with it.
In this section, we provide a very short overview of the basic functions.
Some examples are provided in [Examples & tutorials](/examples/index.md) (this is a work
in progress and will hopefully be updated and extended in the future).
In addition, we hope there are some useful stuff in the code
repository (for example in the [examples
folder](https://github.com/jepegit/cellpy/tree/master/examples)).

:::{hint}
The `cellpy pull` command can assist in downloading
both examples and tests.
:::

## Simple usage as a python library

Here is one very simple potential workflow using cellpy:

### 1. Import

To use `cellpy`, start with importing it:

```python
>>> import cellpy
```

Let us define some variables:

```python
>>> file_name = r"C:\data\20141030_CELL_6_cc_01.res"
>>> mass = 0.982 # mass of active material in mg
>>> out_folder = r"C:\processed_data"
```

### 2. Loading data

To load the data, we use the `cellpy.get()` function. This function loads the data
into the data-class (this was data obtained using an Arbin battery tester,
for the moment we assume that you are using the default settings where the default
data-format is the Arbin .res format):

```python
>>> c = cellpy.get(file_name, mass=mass)
```

Here we choose to go for the default options, and `cellpy` will load the file (using the
file-loader "arbin_res" since the filename extension is .res), create a summary (for each cycle)
and generate a step table (parsing the data and finding out what each step in each cycle is).

### 3. Saving data

You can now save your data as a tester-agnostic `cellpy`-file. The `cellpy` standard is
the HDF5 file format, and will include the data as well as your summary and step table:

```python
>>> c.save("cellpyfiles/20141030_CELL_6_cc_0.h5")
```

The cellpy format is much faster to load than the raw-file formats typically encountered.
It also includes the summary and step-tables, and it is easy to add more data to the file later on.

You can also save your data in csv-format easily by using the method `to_csv´:

```python
>>> c.to_csv(out_folder)
```

:::{note}
The CellpyCell objects store the data (including the summary and step-tables) in pandas DataFrames.
This means that you can easily export the data to other formats, such as Excel, by using the to_excel method of the DataFrame object. In addition, CellpyCell objects have a method called to_excel that exports the data to an Excel file.
:::

### 4. Basic operations

Maybe you want to take a closer look at the capacities for the different cycles?
No problem. Now you are set to extract data for specific cycles and steps:

```python
>>> list_of_cycles = c.get_cycle_numbers()
>>> number_of_cycles = len(list_of_cycles)
>>> print(f"you have {number_of_cycles} cycles")
you have 658 cycles
>>> current_voltage_df = c.get_cap(5) # current and voltage for cycle 5 (as pandas.DataFrame)
```

You can also look for open circuit voltage steps within a selected cycle:

```python
>>> cycle = 44
>>> time_voltage_df1 = c.get_ocv(ocv_type='ocvrlx_up', cycle_number=cycle)
>>> time_voltage_df2 = c.get_ocv(ocv_type='ocvrlx_down', cycle_number=cycle)
```

There are many more methods available, including methods
for selecting steps and cycles (`get_current`, `get_voltage`, *etc.*)
or tuning the data (*e.g.* `split` and `merge`).

Have a look at the examples & tutorials [here](/examples/index.md) or on [Github](https://github.com/jepegit/cellpy/tree/master/examples).

## Convenience methods and tools

Now lets try to create some dQ/dV plots. dQ/dV is a plot of the change in capacity (Q) with respect to the change in voltage (V). It is often used in battery analysis to observe specific electrochemical reactions.
Here’s how to create and plot one:

```python
>>> import matplotlib.pyplot as plt
>>> import cellpy.utils.ica as ica

>>> dqdv = ica.dqdv_frames(c, cycle=[1, 10, 100], voltage_resolution=0.01)

>>> plt.figure(figsize=(10, 8))
>>> plt.plot(dqdv["v"], dqdv["dq"], label="dQ/dV")
>>> plt.xlabel("Voltage (V)")
>>> plt.ylabel("dQ/dV (Ah/V)")
>>> plt.legend()
>>> plt.grid(True)
>>> plt.show()
```

Remember that the process of creating a dQ/dV plot can be quite memory-intensive, especially for large datasets, so it may take a while for the plot to appear.

For more examples, have a look at [examples & tutorials](/examples/index.md).
