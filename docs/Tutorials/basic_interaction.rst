Basic interaction with your data
================================

Read cell data
--------------

We assume that we have cycled a cell and that we have two files with results (we had
to stop the experiment and re-start for some reason). The files are in
the .res format (Arbin).

First, import modules, including the cellreader-object from ``cellpy``:

.. code-block:: python

    import os
    from cellpy import cellreader

Then define some settings and variables and create the CellpyData-object:

.. code-block:: python

    raw_data_dir = r"C:\raw_data"
    out_data_dir = r"C:\processed_data"
    cellpy_data_dir = r"C:\CellpyData"
    cycle_mode = "anode" # default is usually "anode", but...
    # These can also be set in the configuration file

    electrode_mass = 0.658 # active mass of electrode in mg

    # list of files to read (Arbin .res type):
    raw_file = ["20170101_ife01_cc_01.res", "20170101_ife01_cc_02.res"]
    # the second file is a 'continuation' of the first file...

    # list consisting of file names with full path
    raw_files = [os.path.join(raw_data_dir, f) for f in raw_file]

    # creating the CellpyData object and sets the cycle mode:
    cell_data = cellreader.CellpyData()
    cell_data.set_cycle_mode(cycle_mode)

Now we will read the files, merge them, and create a summary:

.. code-block:: python

    # if the list of files are in a list they are automatically merged:
    cell_data.from_raw([raw_files])
    cell_data.set_mass(electrode_mass)
    cell_data.make_summary()
    # Note: make_summary will automatically run the
    # make_step_table function if it does not exist.

And save it:

.. code-block:: python

    # defining a name for the cellpy_file (hdf5-format)
    cellpy_file = os.path.join(cellpy_data_dir, "20170101_ife01_cc2.h5")
    cell_data.save(cellpy_file)

For convenience, ``cellpy`` also has a method that simplifies this process a little bit.
Using the ``loadcell`` method, you can specify both the raw file name(s) and the cellpy file name, and
``cellpy`` will check if the raw file(s) is/are updated since the last time you saved the cellpy file - if not,
then it will load the cellpy file instead (this is usually much faster than loading the raw file(s)).
You can also input the masses and enforce that it creates a summary automatically.

.. code-block:: python

    cell_data.loadcell(raw_files=[raw_files], cellpy_file=cellpy_file,
                           mass=[electrode_mass], summary_on_raw=True,
                           force_raw=False)

    if not cell_data.check():
        print("Could not load the data")

Extract current-voltage graphs
------------------------------

If you have loaded your data into a CellpyData-object, let's now consider how to extract current-voltage graphs
from your data. We assume that the name of your CellpyData-object is ``cell_data``:


.. code-block:: python

    cycle_number = 5
    charge_capacity, charge_voltage = cell_data.get_ccap(cycle_number)
    discharge_capacity, discharge_voltage = cell_data.get_dcap(cycle_number)


You can also get the capacity-voltage curves with both charge and discharge:

.. code-block:: python

    capacity, charge_voltage = cell_data.get_cap(cycle_number)
    # the second capacity (charge (delithiation) for typical anode half-cell experiments)
    # will be given "in reverse".

The ``CellpyData`` object has several get-methods, including getting current, timestamps, etc.

Extract summaries of runs
-------------------------

Summaries of runs includes data pr. cycle for your data set. Examples of summary data is charge- and
discharge-values, coulombic efficiencies and internal resistances. These are calculated by the
``make_summary`` method.

Create dQ/dV plots
------------------

The methods for creating incremental capacity curves is located in the ``cellpy.utils.ica`` module.

Save / export data
------------------

Saving data to cellpy format is done by the ``CellpyData.save`` method. To export data to csv format,
``CellpyData`` has a method called ``to_csv``.

.. code-block:: python

    # export data to csv
    out_data_directory = r"C:\processed_data\csv"
    # this exports the summary data to a .csv file:
    cell_data.to_csv(out_data_directory, sep=";", cycles=False, raw=False)
    # export also the current voltage cycles by setting cycles=True
    # export also the raw data by setting raw=True
