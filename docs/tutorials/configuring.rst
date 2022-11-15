Configuring cellpy
==================

How the configuration parameters are set and read
-------------------------------------------------

When ``cellpy`` is imported, it sets a default set of parameters.
Then it tries to read the parameters
from your .conf-file (located in your user directory). If it is successful,
the parameters set in your .conf-file
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
and looks in your user directory on posix or in the documents folder on
windows (*e.g.* C:\\Users\\USERNAME\\Documents on not-too-old versions of windows) after
files named ``.cellpy_prms_SOMENAME.conf``.

If you have run ``cellpy setup`` in the cmd window or in the shell, the
configuration file will be placed in the appropriate place.
It will have the name ``.cellpy_prms_USERNAME.conf`` (where USERNAME is your username).

The configuration file is a YAML-file and it is reasonably easy to read and edit (but
remember that YAML is rather strict with regards to spaces and indentations).

As an example, here are the first lines
from one of the authors' configuration file:

.. code-block:: yaml

    ---
    Paths:
      outdatadir: C:\scripts\processing_cellpy\out
      rawdatadir: I:\Org\MPT-BAT-LAB\Arbin-data
      cellpydatadir: C:\scripts\processing_cellpy\cellpyfiles
      db_path: C:\scripts\processing_cellpy\db
      filelogdir: C:\scripts\processing_cellpy\logs
      examplesdir: C:\scripts\processing_cellpy\examples
      notebookdir: C:\scripts\processing_cellpy\notebooks
      templatedir: C:\scripting\processing_cellpy\templates
      batchfiledir: C:\scripts\processing_cellpy\batchfiles
      db_filename: 2020_Cell_Analysis_db_001.xlsx

    FileNames:
      file_name_format: YYYYMMDD_[NAME]EEE_CC_TT_RR


The first part contains definitions of the different paths, files and file-patterns
that ``cellpy`` will use. This is probably the place
where you most likely will have to do some edits sometime.

Next comes definitions needed when using a db.

.. code-block:: yaml

    # settings related to the db used in the batch routine
    Db:
      db_type: simple_excel_reader
      db_table_name: db_table
      db_header_row: 0
      db_unit_row: 1
      db_data_start_row: 2
      db_search_start_row: 2
      db_search_end_row: -1

    # definitions of headers for the simple_excel_reader
    DbCols:
      id:
      - id
      - int
      exists:
      - exists
      - bol
      batch:
      - batch
      - str
      sub_batch_01:
      - b01
      - str
      .
      .


Its rather long (since it needs to define the column names used in the db excel sheet).
After this, the settings the datasets and the ``cellreader`` comes, as well as for the different instruments.
You will also find the settings for the ``batch`` utility at the bottom.

.. code-block:: yaml

    # settings related to your data
    DataSet:
      nom_cap: 3579

    # settings related to the reader
    Reader:
      Reader:
        diagnostics: false
        filestatuschecker: size
        force_step_table_creation: true
        force_all: false
        sep: ;
        cycle_mode: anode
        sorted_data: true
        load_only_summary: false
        select_minimal: false
        limit_loaded_cycles:
        ensure_step_table: false
        voltage_interpolation_step: 0.01
        time_interpolation_step: 10.0
        capacity_interpolation_step: 2.0
        use_cellpy_stat_file: false
        auto_dirs: true

    # settings related to the instrument loader
    # (each instrument can have its own set of settings)
    Instruments:
      tester: arbin
      custom_instrument_definitions_file:

      Arbin:
        max_res_filesize: 1000000000
        chunk_size:
        max_chunks:
        use_subprocess: false
        detect_subprocess_need: false
        sub_process_path:
        office_version: 64bit
        SQL_server: localhost
        SQL_UID:
        SQL_PWD:
        SQL_Driver: ODBC Driver 17 for SQL Server
        odbc_driver:
      Maccor:
        default_model: one

    # settings related to running the batch procedure
    Batch:
      fig_extension: png
      backend: bokeh
      notebook: true
      dpi: 300
      markersize: 4
      symbol_label: simple
      color_style_label: seaborn-deep
      figure_type: unlimited
      summary_plot_width: 900
      summary_plot_height: 800
      summary_plot_height_fractions:
      - 0.2
      - 0.5
      - 0.3
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
