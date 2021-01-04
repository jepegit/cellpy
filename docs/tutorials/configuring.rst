Configuring cellpy
==================

How the configuration parameters are set and read
-------------------------------------------------

When ``cellpy`` is imported, it sets a default set of parameters.
Then it tries to read the parameters
from your .conf-file (located in your user directory). If it is successful,
the paramteters set in your .conf-file
will over-ride the default ones.

The parameters are stored in the module ``cellpy.parameters.prms``.

If you during your script (or in your ``jupyter notebook``) would like to
change some of the settings (*e.g.* if you
want to use the ``cycle_mode`` option "cathode" instead of the
default "anode"), then import the prms class and set new
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

``cellpy`` tries to read your .conf-file when imported the first time,
and looks in your user directory
(*e.g.* C:\\Users\\USERNAME on not-too-old versions of windows) after
files named ``_cellpy_prms_SOMENAME.conf``.
If you have run ``cellpy setup`` in the cmd window or in the shell, a
file named
``_cellpy_prms_USERNAME.conf`` (where USERNAME is
your username) should exist in your home directory. This is a YAML-file and
it is reasonably easy to read and edit (but
remember that YAML is rather strict with regards to spaces and indentations).
As an example, here are the first lines
from one of the authors' configuration file:

.. code-block:: yaml

    ---
    # settings related to running the batch procedure
    Batch:
      backend: bokeh
      color_style_label: seaborn-deep
      dpi: 300
      fig_extension: png
      figure_type: unlimited
      markersize: 4
      notebook: true
      summary_plot_height: 800
      summary_plot_height_fractions:
      - 0.2
      - 0.5
      - 0.3
      summary_plot_width: 900
      symbol_label: simple

    # settings related to your data
    DataSet:
      nom_cap: 3579

    # settings related to the db used in the batch routine
    Db:
      db_data_start_row: 2
      db_header_row: 0
      db_search_end_row: -1
      db_search_start_row: 2
      db_table_name: db_table
      db_type: simple_excel_reader
      db_unit_row: 1

    # definitions of headers for the simple_excel_reader
    DbCols:
      active_material: !!python/tuple
      - mass_active_material
      - float
      batch: !!python/tuple
      - batch
      - str
      cell_name: !!python/tuple
      - cell
      - str
      .
      .

Then follows a lot of column name definitions. After this, the settings
for the different instruments, the paths cellpy uses for finding files
and storing files (e.g. where to store cellpy-files). In addition, several
settings used by cellreader is given in the end (might be moved to a
more sensible place in later versions).

.. code-block:: yaml

    FileNames: {}
    Instruments:
      chunk_size: null
      custom_instrument_definitions_file: null
      detect_subprocess_need: false
      max_chunks: null
      max_res_filesize: 150000000
      office_version: 64bit
      sub_process_path: None
      tester: arbin
      use_subprocess: false
    Paths:
      cellpydatadir: C:\ExperimentalData\BatteryTestData\Arbin\HDF5
      db_filename: 2017_Cell_Analysis_db_001.xlsx
      db_path: C:\Users\jepe\Documents\Databases\Experiments\arbin
      examplesdir: C:\Scripting\Processing\Celldata\examples
      filelogdir: C:\Scripting\Processing\Celldata\outdata
      outdatadir: C:\Scripting\Processing\Celldata\outdata
      rawdatadir: I:\Org\ensys\EnergyStorageMaterials\Data-backup\Arbin
    Reader:
      auto_dirs: true
      capacity_interpolation_step: 2.0
      cellpy_datadir: null
      chunk_size: null
      cycle_mode: anode
      daniel_number: 5
      ensure_step_table: false
      filestatuschecker: size
      force_all: false
      force_step_table_creation: true
      last_chunk: null
      limit_loaded_cycles: null
      load_only_summary: false
      max_chunks: null
      max_res_filesize: 150000000
      raw_datadir: null
      select_minimal: false
      sep: ;
      sorted_data: true
      time_interpolation_step: 10.0
      use_cellpy_stat_file: false
      voltage_interpolation_step: 0.01
    ...

As you can see, the author of this particular file most likely works with
silicon as anode material for lithium ion
batteries (the ``nom_cap`` is set to 3579 mAh/g, *i.e.* the theoretical
gravimetric lithium capacity for silicon at
normal temperatures). And, he or she is using windows.

By the way, if you are wondering what
the '.' means... it means nothing - it was just something I added in this
tutorial text to indicate that there are
more stuff in the actual file than what is shown here.
