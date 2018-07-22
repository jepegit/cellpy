Configuring cellpy
==================

How the configuration parameters are set and read
-------------------------------------------------

When ``cellpy`` is imported, it sets a default set of parameters. Then it tries to read the parameters
from your .conf-file (located in your user directory). If it is successful, the paramteters set in your .conf-file
will over-ride the default ones.

The parameters are stored in the module ``cellpy.parameters.prms``.

If you during your script (or in your ``jupyter notebook``) would like to change some of the settings (*e.g.* if you
want to use the ``cycle_mode`` option "cathode" instead of the default "anode"), then import the prms class and set new
values:

.. code-block:: python

    from cellpy import parameters.prms

    # Changing cycle_mode to cathode
    prms.Reader.cycle_mode = 'cathode'

    # Changing delimiter to  ',' (used when saving .csv files)
    prms.Reader.sep = ','

    # Changing the default folder for processed (output) data
    prms.Paths.outdatadir = 'experiment01/processed_data'


The configuration file
----------------------

``cellpy`` tries to read your .conf-file when imported the first time, and looks in your user directory
(*e.g.* C:\\Users\\USERNAME on not-too-old versions of windows) after files named ``_cellpy_prms_SOMENAME.conf``.
If you have run ``cellpy -setup`` in the cmd window or in the shell, a file named
``_cellpy_prms_USERNAME.conf`` (where USERNAME is
your username) should exist in your home directory. This is a YAML-file and it is reasonably easy to read and edit (but
remember that YAML is rather strict with regards to spaces and indentations). As an example, here are the first lines
from one of the authors' configuration file:

.. code-block:: yaml

    ---
    DataSet:
      nom_cap: 3579
    Db:
      db_type: simple_excel_reader
    FileNames: {}
    Instruments:
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
