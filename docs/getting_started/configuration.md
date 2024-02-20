# Setup and configuration

To get the most out of `cellpy` it is to best to set it up properly.

To help with this, you can use the `setup` command. If you include
the  `-i` option, the setup will be done interactively, and you will
be prompted for your preferred location for the different folders and
directories `cellpy` uses:

```shell
cellpy setup -i
```

This creates the cellpy configuration file `.cellpy_prms_USERNAME.conf`
in your home directory (USERNAME = your user name), or update it if it exists,
and try to create the following directory structure:

```shell
batchfiles/
cellpyfiles/
db/
examples/
instruments/
logs/
notebooks/
out/
raw/
templates/
```

If you want to specify a root folder different from the default (your HOME
folder), you can use the `-d` option *e.g.*
`cellpy setup -i -d /Users/kingkong/cellpydir`

:::{hint}
You can always edit your configurations directly in the cellpy configuration
file `.cellpy_prms_USER.conf`. This file should be located inside your
home directory, /. in posix and c:usersUSERNAME in not-too-old windows.
:::

To check, where your configuration file is actually located, you can run:

```shell
$ cellpy info --configloc
[cellpy] -> C:\Users\jepe\.cellpy_prms_jepe.conf
```

To get the filepath to your config file AND other cellpy info, run:

```console
cellpy info -l
```

:::{note}
It is recommended to re-run setup each time you update `cellpy`.
:::

## The configuration file

The paths to raw data, the cellpy data base file, file locations etc. are set in
the `.cellpy_prms_USER.conf` file that is located in your home directory.
`cellpy` tries to read this .conf file when imported the first time,
and looks in your user directory after files named `.cellpy_prms_SOMENAME.conf`.
(If you have run `cellpy setup`, the configuration file will be placed in
the appropriate place with the appropriate filename.)

The configuration file is a YAML-file and it is reasonably easy to read and edit
in a text editor (remember that YAML is rather strict with regards to spaces and
indentations).

Within the config file, the paths are the most important parts that need to
be set up correctly. This tells `cellpy` where to find (and save) different files,
such as the database file and raw data.

Furthermore, the config file contains details about the database-file
(see below {ref}`_Cellpy_Database_File`) to be used for cell info and metadata
(i.e. type and structure of the database file such as column headers etc.).

### Configuration file - example

As an example, here are the first lines
from one of the authors' configuration file:

```yaml
---
Paths:
    outdatadir: C:\scripts\cellpy_data\out
    rawdatadir: I:\Org\MPT-BAT-LAB\Arbin-data
    cellpydatadir: C:\scripts\cellpy_data\cellpyfiles
    db_path: C:\scripts\cellpy_data\db
    filelogdir: C:\scripts\cellpy_data\logs
    examplesdir: C:\scripts\cellpy_data\examples
    notebookdir: C:\scripts\cellpy_data\notebooks
    templatedir: C:\scripting\cellpy_data\templates
    batchfiledir: C:\scripts\cellpy_data\batchfiles
    instrumentfiledir: C:\scripts\cellpy_data\instruments
    db_filename: cellpy_db.xlsx
    env_file: .env_cellpy


FileNames:
    file_name_format: YYYYMMDD_[NAME]EEE_CC_TT_RR
    raw_extension: res
    reg_exp:
    sub_folders:
    file_list_location:
    file_list_type:
    file_list_name:
    cellpy_file_extension: h5
```

The first part contains definitions of the different paths, files and file-patterns
that `cellpy` will use. This is the place where you most likely will have to do
some edits sometime.

The next part contains definitions required when using a database:

```yaml
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
```

This part is rather long (since it needs to define the column names used in the db excel sheet).

The next part contains settings regarding your cell/dataset and the `cellreader`, as well as for
the different `instruments`. At the bottom you will find the settings for the `batch` utility.

```yaml
# settings related to your cell
CellInfo:
    voltage_lim_low: 0.0
    voltage_lim_high: 1.0
    active_electrode_area: 1.0
    active_electrode_thickness: 1.0
    electrolyte_volume: 1.0
    electrolyte_type: standard
    active_electrode_type: standard
    counter_electrode_type: standard
    reference_electrode_type: standard
    experiment_type: cycling
    cell_type: standard
    separator_type: standard
    active_electrode_current_collector: standard
    reference_electrode_current_collector: standard
    comment:

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
        select_minimal: false
        limit_loaded_cycles:
        ensure_step_table: false
        ensure_summary_table: false
        voltage_interpolation_step: 0.01
        time_interpolation_step: 10.0
        capacity_interpolation_step: 2.0
        use_cellpy_stat_file: false
        auto_dirs: true

# settings related to the instrument loader
# (each instrument can have its own set of settings)
Instruments:
    tester: arbin_res
    custom_instrument_definitions_file:
    Arbin:
        max_res_filesize: 150000000
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
    Neware:
        default_model: one

# settings related to running the batch procedure
Batch:
    auto_use_file_list: false
    template: standard
    fig_extension: png
    backend: matplotlib
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
```

(cellpy-database-file)=

## The 'database' file

The database file should contain information (cell name, type, mass loading etc.)
on your cells (as specified in the config file), so that `cellpy` can find and
link the test data to the provided metadata.

The database file is also useful when working with the `cellpy` batch routine.

## How the configuration parameters are set and read

When `cellpy` is imported, a default set of parameters is set.
Then it tries to read the parameters from your .conf file
(located in your user directory). If successful,
the parameters set in your .conf file will over-ride the default.

The parameters are stored in the module `cellpy.parameters.prms`.

If you would like to change some of the settings during your script
(or in your `jupyter notebook`), *e.g.* if you
want to use the `cycle_mode` option "cathode" instead of the
default "anode", then import the prms class and set new
values:

```python
from cellpy import parameters.prms

# Changing cycle_mode to cathode
prms.Reader.cycle_mode = 'cathode'

# Changing delimiter to  ',' (used when saving .csv files)
prms.Reader.sep = ','

# Changing the default folder for processed (output) data
prms.Paths.outdatadir = 'experiment01/processed_data'
```
