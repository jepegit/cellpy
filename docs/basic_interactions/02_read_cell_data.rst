Interacting with your data
==========================

Read cell data
--------------

We assume that we have cycled a cell and that we have two files
with results (we had to stop the experiment and re-start for some
reason). The files are in the .res format (Arbin).

The easiest way to load data is to use the ``cellpy.get`` method:

.. code-block:: python

    import cellpy

    electrode_mass = 0.658 # active mass of electrode in mg
    file_name = "20170101_ife01_cc_01.res"
    cell_data = cellpy.get(file_name, mass=electrode_mass, cycle_mode="anode")

If you prefer, you can obtain the same by using ``cellpy.cellreader.CellpyCell`` object directly. However, we
recommend using the ``cellpy.get`` method. But just in case you want to know how to do it:

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

    # creating the CellpyCell object and set the cycle mode:
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


Save / export data
------------------

When you have loaded your data and created your ``CellpyCell`` object, it is
time to save everything in the cellpy-format:

.. code-block:: python

    # defining a name for the cellpy_file (hdf5-format)
    cellpy_data_dir = r"C:\cellpy_data\cellpy_files"
    cellpy_file = os.path.join(cellpy_data_dir, "20170101_ife01_cc2.h5")
    cell_data.save(cellpy_file)

The cellpy format is much faster to load than the raw-file formats typically
encountered. It also includes the summary and step-tables, and it is easy to
add more data to the file later on.

To export data to csv format,
``CellpyCell`` has a method called ``to_csv``.

.. code-block:: python

    # export data to csv
    out_data_directory = r"C:\processed_data\csv"
    # this exports the summary data to a .csv file:
    cell_data.to_csv(out_data_directory, sep=";", cycles=False, raw=False)
    # export also the current voltage cycles by setting cycles=True
    # export also the raw data by setting raw=True


.. note::
    ``CellpyCell`` objects store the data (including the summary and step-tables)
    in ``pandas DataFrames``. This means that you can easily export the data to
    other formats, such as Excel, by using the ``to_excel`` method of the
    DataFrame object.
