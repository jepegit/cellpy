=========
Tutorials
=========


The cellpy command
==================

At the moment, only a very limited set of things can be achieved by running the ``cellpy`` command at the shell (or in
the cmd window).

.. code-block:: shell

    $ cellpy
    Usage: cellpy [OPTIONS] COMMAND [ARGS]...

    Options:
      --help  Show this message and exit.

    Commands:
      configloc
      setup
      version

A couple of commands are implemented to get some information about your cellpy environment (currently getting your
cellpy version and the location of your configuration file):

.. code-block:: shell

    $ cellpy version
    [cellpy] version: 0.1.11
    $
    $ cellpy configloc
    [cellpy] ->C:\Users\jepe\_cellpy_prms_jepe.conf


The most important command is probably the ``setup`` command (that should be run when you install cellpy for the first
time).


Configuring cellpy
==================

How the configuration parameters are set and read
-------------------------------------------------

When ``cellpy`` is imported, it sets a default set of parameters. Then it tries to read the parameters
from you .conf-file (located in your user directory). If it is successful, the paramteters set in your .conf-file
will over-ride the default ones.

The parameters are stored in the module ``cellpy.parameters.prms`` as a dictionary of dictionaries. I know, this is
probably not the most convenient method, but it is very easy (at least I think so) to change these into class-type
stuff in a later release of ``cellpy`` (using for example ``type(x, y, z)`` etc. or ``setattr`` etc).

If you during your script (or in your `jupyter notebook`) would like to change some of the settings (*e.g.* if you
want to use the cycle_mode option "cathode" instead of the default "anode"), then import the prms class and set new
values:

.. code-block:: python

    from cellpy import parameters.prms

    # Changing cycle_mode to cathode
    prms['Reader']['cycle_mode'] = 'cathode'

    # Changing delimiter to  ',' (used when saving .csv files)
    prms['Reader']['sep'] = ','


In some of the modules or classes, selected parameters are already 'transformed' to class attributes, and those can
be assigned intuitively:


.. code-block:: python

    from cellpy import dbreader as dr

    print(dr.db_sheet_cols.batch)
    # prints the column number for the column containing the "batch" label

    dr.db_sheet_cols.batch = 3
    # sets the column number for the column containing the "batch" label to 3

    print(dr.db_sheet_cols.batch)
    # prints '3', the new column number for the column containing the "batch" label


A more thorough description of this will come in later releases (0.2.0 and up).

The configuration file
----------------------

``cellpy`` tries to read your .conf-file when imported the first time, and looks in your user directory
(*e.g.* C:\Users\USERNAME on newer versions of windows) after files named ``_cellpy_prms_SOMENAME.conf``.
If you have run ``cellpy -setup`` in the cmd window or in the shell, a file named
``_cellpy_prms_USERNAME.conf`` (where USERNAME is
your username) should exist in your home directory. This is a YAML-file and it is reasonably easy to read and edit (but
remember that YAML is rather strict with regards to spaces and indentations). As an example, here are the first lines
from one of the authors configuration file:

.. code-block:: yaml

    ---
    DataSet:
      nom_cap: 3579
    Db:
      db_type: simple_excel_reader
    FileNames: {}
    Instruments:
      cell_configuration: anode
      tester: arbin
    Paths:
      cellpydatadir:  C:\ExperimentalData\BatteryTestData\Arbin\HDF5
      db_filename: 2017_Cell_Analysis_db_001.xlsx
      db_path: C:\Users\jepe\Documents\Databases\Experiments\arbin
      filelogdir: C:\Scripting\Processing\Celldata\outdata
      outdatadir: C:\Scripting\Processing\Celldata\outdata
      rawdatadir: I:\Org\ensys\EnergyStorageMaterials\Data-backup\Arbin
    Reader:
      auto_dirs: true
      cellpy_datadir: null
      chunk_size: null
      cycle_mode: anode
      daniel_number: 5
      .
      .

As you can see, the author of this particular file most likely works with silicon as anode material for lithium ion
batteries (the ``nom_cap`` is set to 3579 mAh/g, *i.e.* the theoretical gravimetric lithium capacity for silicon at
normal temperatures). And, he or she is using windows.

Looking further down in the file, you come to some sections related to the 'excel database reader':

.. code-block:: yaml

    excel_db_cols:
      A1: 28
      A2: 29
      A3: 30
      A4: 31
      .
      .

Here you can set custom column numbers for where the database reader should look for stuff. For example, if you have
your entry specifying active material (mass) in column 100, then edit your
configuration file entry ``active_material``:

.. code-block:: yaml

    excel_db_cols:
      .
      .
      active_material: 35
      .
      .

To:

.. code-block:: yaml

    excel_db_cols:
      .
      .
      active_material: 100
      .
      .

A more in-depth description of this will come in later releases (0.2.0 and up). By the way, if you are wondering what
the '.' means... it means nothing - it was just something I added in this tutorial text to indicate that there are
more stuff in the actual file than what is shown here.

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

Then define some settings and variables and create the cellpydata-object:

.. code-block:: python

    # These can also be set in the configuration file:
    raw_data_dir = r"C:\raw_data"
    out_data_dir = r"C:\processed_data"
    cellpy_data_dir = r"C:\cellpydata"
    cycle_mode = "anode" # default is usually "anode", but...
    electrode_mass = 0.658 # active mass of electrode in mg

    # list of files to read (Arbin .res type):
    raw_file = ["20170101_ife01_cc_01.res", "20170101_ife01_cc_02.res"]
    # the second file is a 'continuation' of the first file...


    # list consisting of file names with full path
    raw_files = [os.path.join(raw_data_dir, f) for f in raw_file]

    # creating the cellpydata object and sets the cycle mode:
    cell_data = cellreader.cellpydata()
    cell_data.set_cycle_mode(cycle_mode)

Now we will read the files, merge them, and create a summary:

.. code-block:: python

    # if the list of files are in a list they are automatically merged:
    cell_data.load_raw([raw_files])
    cell_data.set_mass(electrode_mass)
    cell_data.make_summary() # it will automatically run the create_step_table function if it does not exist.

And save it:

.. code-block:: python

    # defining a name for the cellpy_file (hdf5-format)
    cellpy_file = os.path.join(cellpy_data_dir, "20170101_ife01_cc2.h5")
    cellpy_file.save_test()

For convinience, ``cellpy`` also has a mecellpy_filethod that simplifies this process a little bit.
Using the ``loadcell`` method, you can specify both the raw file name(s) and the cellpy file name, and
``cellpy`` will check if the raw file is updated since the last time you saved the cellpy file - if not,
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

If you have loaded your data into a cellpydata-object, let's now consider how to extract current-voltage graphs
from your data. We assume that the name of your cellpydata-object is ``cell_data``:


.. code-block:: python

    cycle_number = 5
    charge_capacity, charge_voltage = cell_data.get_ccap(cycle_number)
    discharge_capacity, discharge_voltage = cell_data.get_dcap(cycle_number)


You can also get the capacity-voltage curves with both charge and discharge:

.. code-block:: python

    capacity, charge_voltage = cell_data.get_cap(cycle_number)
    # the second capacity (charge (delithiation) for typical anode half-cell experiments)
    # will be given "in reverse".

The ``cellpydata`` object has several get-methods, including getting current, timestamps, etc.

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

Saving data to cellpy format is done by the ``cellpydata.save`` method. To export data to csv format,
``cellpydata`` has a method called ``exportcsv``.

.. code-block:: python

    # export data to csv
    out_data_directory = r"C:\processed_data\csv"
    # this exports the summary data to a .csv file:
    cell_data.exportcsv(out_data_directory, sep=";", cycles=False, raw=False)
    # export also the current voltage cycles by setting cycles=True
    # export also the raw data by setting raw=True

Using some of the cellpy special utilities
==========================================

Fitting ocv-rlx data
--------------------

Data mining / using a database
==============================

Using the batch utilities
=========================

Working with the pandas.DataFrame objects directly
==================================================

The ``cellpydata`` object stores the data in several pandas.DataFrame objects.


