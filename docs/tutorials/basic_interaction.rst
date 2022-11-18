Interacting with your data
==========================

Read cell data
--------------

We assume that we have cycled a cell and that we have two files
with results (we had to stop the experiment and re-start for some
reason).
The files are in the .res format (Arbin).

The easiest way to load data is to use the
``cellpy.get`` method.

.. code-block:: python

    import cellpy

    electrode_mass = 0.658 # active mass of electrode in mg
    cell_data = cellpy.get("20170101_ife01_cc_01.res", mass=electrode_mass, cycle_mode="anode")

If you prefer, you can obtain the same by using ``cellpy.cellreader.CellpyCell`` object directly:
First, import the cellreader-object from ``cellpy``:

.. code-block:: python

    import os
    from cellpy import cellreader

Then define some settings and variables and create the CellpyCell-object:

.. code-block:: python

    raw_data_dir = r"C:\raw_data"
    out_data_dir = r"C:\processed_data"
    cellpy_data_dir = r"C:\CellpyCell"
    cycle_mode = "anode" # default is usually "anode", but...
    # These can also be set in the configuration file

    electrode_mass = 0.658 # active mass of electrode in mg

    # list of files to read (Arbin .res type):
    raw_file = ["20170101_ife01_cc_01.res", "20170101_ife01_cc_02.res"]
    # the second file is a 'continuation' of the first file...

    # list consisting of file names with full path
    raw_files = [os.path.join(raw_data_dir, f) for f in raw_file]

    # creating the CellpyCell object and sets the cycle mode:
    cell_data = cellreader.CellpyCell()
    cell_data.cycle_mode = cycle_mode

Now we will read the files, merge them, and create a summary:

.. code-block:: python

    # if the list of files are in a list they are automatically merged:
    cell_data.from_raw([raw_files])
    cell_data.set_mass(electrode_mass)
    cell_data.make_summary()
    # Note: make_summary will automatically run the
    # make_step_table function if it does not exist.

Then its probably best to save the data in the cellpy-format:

.. code-block:: python

    # defining a name for the cellpy_file (hdf5-format)
    cellpy_file = os.path.join(cellpy_data_dir, "20170101_ife01_cc2.h5")
    cell_data.save(cellpy_file)

For convenience, ``cellpy`` also has a method that can be used to select whether-or-not to load
directly from the raw-file.
Using the ``loadcell`` method, you can specify both the raw
file name(s) and the cellpy file name, and
``cellpy`` will check if the raw file(s) is/are updated since
the last time you saved the cellpy file - if not,
then it will load the cellpy file instead (this is usually much faster
than loading the raw file(s)).
You can also input the masses and enforce that it creates a
summary automatically.

.. code-block:: python

    cell_data.loadcell(raw_files=[raw_files], cellpy_file=cellpy_file,
                           mass=[electrode_mass], summary_on_raw=True,
                           force_raw=False)

    if not cell_data.check():
        print("Could not load the data")

More about the ``cellpy.get`` method
------------------------------------

The following keyword arguments is current supported by ``cellpy.get``:

.. code-block:: python

    # from the docstring:
    Args:
        filename (str, os.PathLike, or list of raw-file names): path to file(s)
        mass (float): mass of active material (mg) (defaults to mass given in cellpy-file or 1.0)
        instrument (str): instrument to use (defaults to the one in your cellpy config file) (arbin_res, arbin_sql, arbin_sql_csv, arbin_sql_xlxs)
        instrument_file (str or path): yaml file for custom file type
        nominal_capacity (float): nominal capacity for the cell (e.g. used for finding C-rates)
        logging_mode (str): "INFO" or "DEBUG"
        cycle_mode (str): the cycle mode (e.g. "anode" or "full_cell")
        auto_summary (bool): (re-) create summary.
        testing (bool): set to True if testing (will for example prevent making .log files)
        **kwargs: sent to the loader

Reading a cellpy file:

.. code-block:: python

    c = cellpy.get("my_cellpyfile.cellpy")
    # or
    c = cellpy.get("my_cellpyfile.h5")

Reading anode half-cell data from arbin sql:

.. code-block:: python

    c = cellpy.get("my_cellpyfile", instrument="arbin_sql", cycle_mode="anode")
    # Remark! if sql prms are not set in your config-file you have to set them manually (e.g. setting values in
    #    prms.Instruments.Arbin.VAR)

Reading data obtained by exporting csv from arbin sql using non-default delimiter sign:

.. code-block:: python

    c = cellpy.get("my_cellpyfile.csv", instrument="arbin_sql_csv", sep=";")

Reading data obtained by exporting a csv file from Maccor
using a sub-model (this example uses one of the models already available inside ``cellpy``):

.. code-block:: python

    c = cellpy.get(filename="name.txt", instrument="maccor_txt", model="one", mass=1.0)

Reading csv file using the custom loader where the format definitions are given in a user-supplied
yaml-file:

.. code-block:: python

    c = cellpy.get(filename="name.txt", instrument_file="my_custom_file_format.yml")


Extract current-voltage graphs
------------------------------

If you have loaded your data into a CellpyCell-object,
let's now consider how to extract current-voltage graphs
from your data. We assume that the name of your
CellpyCell-object is ``cell_data``:


.. code-block:: python

    cycle_number = 5
    charge_capacity, charge_voltage = cell_data.get_ccap(cycle_number)
    discharge_capacity, discharge_voltage = cell_data.get_dcap(cycle_number)


You can also get the capacity-voltage curves with both charge and discharge:

.. code-block:: python

    capacity, charge_voltage = cell_data.get_cap(cycle_number)
    # the second capacity (charge (delithiation) for typical anode half-cell experiments)
    # will be given "in reverse".

The ``CellpyCell`` object has several get-methods, including getting current,
timestamps, etc.

Extract summaries of runs
-------------------------

Summaries of runs includes data pr. cycle for your data set. Examples of
summary data is charge- and
discharge-values, coulombic efficiencies and internal resistances.
These are calculated by the
``make_summary`` method.

Remark that note all the possible summary statistics are calculated as
default. This means that you might have to re-run the ``make_summary`` method
with appropriate parameters as input (e.g. ``normalization_cycle``,
to give the appropriate cycle numbers to use for finding nominal capacity).

Another method is responsible for investigating the individual steps in the
data (``make_step_table``). It is typically run automatically before creating
the summaries (since the summary creation depends on the step_table). This
table is interesting in itself since it contains delta, minimum, maximum and
average values for the measured values pr. step. This is used to find out
what type of step it is, *e.g.* a charge-step or maybe a ocv-step. It is
possible to provide information to this function if you already knows what
kind of step each step is. This saves ``Cellpy`` for a lot of work.

Remark that the default is to calculate values for each unique (step-number -
cycle-number) pair. For some experiments, a step can be repeated many times
pr. cycle. And if you need for example average values of the voltage for each
step (for example if you are doing GITT experiments), you would need to
tell ``make_step_table`` that it should calculate for all the steps
(``all_steps=True``).

Create dQ/dV plots
------------------

The methods for creating incremental capacity curves is located in
the ``cellpy.utils.ica`` module.

Save / export data
------------------

Saving data to cellpy format is done by the ``CellpyCell.save`` method.
To export data to csv format,
``CellpyCell`` has a method called ``to_csv``.

.. code-block:: python

    # export data to csv
    out_data_directory = r"C:\processed_data\csv"
    # this exports the summary data to a .csv file:
    cell_data.to_csv(out_data_directory, sep=";", cycles=False, raw=False)
    # export also the current voltage cycles by setting cycles=True
    # export also the raw data by setting raw=True
