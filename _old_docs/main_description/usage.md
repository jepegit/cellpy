# Usage

## 1. Simple usage as a python library

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

Then load the data into the data-class (this is data obtained using an Arbin battery tester,
for the moment we assume that you are using the default settings where the default
data-format is the Arbin .res format):

```
>>> c = cellpy.get(file_name, mass=mass)
```

Here we are choosing to go for the default options, and cellpy will load the file (using the file-loader "arbin_res" since
the filename extension is .res), create a summary (for each cycle) and generate a step table (parsing the
data and finding out what each step in each cycle is).

You can now save your data as a tester agnostic cellpy-file (uses hdf5 file format, and will
include your summary and step table):

```
>>> c.save("cellpyfiles/20141030_CELL_6_cc_0.h5")
```

You can also save your data in csv-format easily by:

```
>>> c.to_csv(out_folder)
```

Or maybe you want to take a closer look at the capacities for
the different cycles? No problem. Now you are set to extract data
for specific cycles and steps:

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

## 2. Convenience methods and tools

The `cellpy.get` method interprets the file-type from the file extension and automatically creates
the step table as well as the summary table:

```
>>> import cellpy
>>> c = cellpy.get(r"C:\data\20141030_CELL_6_cc_01.res", mass=0.982)
>>> # or load the cellpy-file:
>>> # cellpy.get("cellpyfiles/20141030_CELL_6_cc_0.h5")
```

If you provide the raw-file name and the cellpy-file name
as input, `cellpy.get` only loads the raw-file if the cellpy-file is older than the
raw-file:

```
>>> c = cellpy.get(raw_file_name, cellpyfile=cellpy_file_name)
```

Also, if your cell test consists of several raw files, you can provide a list of filenames:

```
>>> raw_files = [rawfile_01, rawfile_02]
>>> c.get(raw_files, cellpy_file)
```

`cellpy` will merge the two files for you and shift the running numbers (such as data-point) into
one "continuous" file.

`cellpy` contains a logger (the logs are saved in the cellpy logging
directory as defined in the config file). You can set the log level
(to the screen) by:

```
>>> from cellpy import log
>>> log.setup_logging(default_level="DEBUG")
```

If you would like to use more sophisticated methods (*e.g.* database readers),
take a look at the tutorial (if it exists), check the source code, or simply
send an e-mail to one of the authors.
