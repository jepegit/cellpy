# Basic usage

As with most software, you are encouraged to play a little with it.
In this section, we provide a very short overview of the basic functions.
Some examples are provided in Examples & Tutorials (this is a work
in progress and will hopefully be updated and extended in the future).
In addition, we hope there are some useful stuff in the code
repository (for example in the [examples
folder](https://github.com/jepegit/cellpy/tree/master/examples)).

:::{hint}
The `cellpy pull` command can assist in downloading
both examples and tests.
:::

## Simple usage as a python library

To use `cellpy`, start with importing it:

```
>>> import cellpy
```

Let us define some variables:

```
>>> file_name = r"C:\data\20141030_CELL_6_cc_01.res"
>>> mass = 0.982 # mass of active material in mg
>>> out_folder = r"C:\processed_data"
```

To **load the data**, we use the `cellpy.get()` function. This function loads the data
into the data-class (this was data obtained using an Arbin battery tester,
for the moment we assume that you are using the default settings where the default
data-format is the Arbin .res format):

```
>>> c = cellpy.get(file_name, mass=mass)
```

Here we choose to go for the default options, and `cellpy` will load the file (using the
file-loader "arbin_res" since the filename extension is .res), create a summary (for each cycle)
and generate a step table (parsing the data and finding out what each step in each cycle is).

You can now **save your data** as a tester-agnostic `cellpy`-file. The `cellpy` standard is
the HDF5 file format, and will include the data as well as your summary and step table:

```
>>> c.save("cellpyfiles/20141030_CELL_6_cc_0.h5")
```

You can also save your data in csv-format easily by:

```
>>> c.to_csv(out_folder)
```

Or maybe you want to take a closer look at the capacities for the different cycles?
No problem. Now you are set to extract data for specific cycles and steps:

```
>>> list_of_cycles = c.get_cycle_numbers()
>>> number_of_cycles = len(list_of_cycles)
>>> print(f"you have {number_of_cycles} cycles")
you have 658 cycles
>>> current_voltage_df = c.get_cap(5) # current and voltage for cycle 5 (as pandas.DataFrame)
```

You can also look for open circuit voltage steps:

```
>>> cycle = 44
>>> time_voltage_df1 = c.get_ocv(ocv_type='ocvrlx_up', cycle_number=cycle)
>>> time_voltage_df2 = c.get_ocv(ocv_type='ocvrlx_down', cycle_number=cycle)
```

There are many more methods available, including methods
for selecting steps and cycles (`get_current`, `get_voltage`, *etc.*)
or tuning the data (*e.g.* `split` and `merge`).

Take a look at the index page ({doc}`modules <source/modules>`), some of
the tutorials ({doc}`tutorials <basics>`) or notebook examples ({doc}`Example notebooks <notebooks>`).

## Convenience methods and tools

For more details refer to examples
