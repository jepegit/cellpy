"""cellpy parameters"""

import os
from pathlib import Path
import sys
import box

# When adding prms, please
#   1) check / update the internal_settings.py file as well to ensure that copying / splitting cellpy objects
#   behaves properly.
#   2) check / update the .cellpy_prms_default.conf file

# locations etc for reading custom parameters
script_dir = os.path.abspath(os.path.dirname(__file__))
cur_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
user_dir = os.path.expanduser("~")

# --------------------------
# Paths
# --------------------------

Paths = {
    "outdatadir": cur_dir,
    "rawdatadir": cur_dir,
    "cellpydatadir": cur_dir,
    "db_path": cur_dir,
    "filelogdir": cur_dir,
    "examplesdir": cur_dir,
    "notebookdir": cur_dir,
    "batchfiledir": cur_dir,
    "db_filename": "cellpy_db.xlsx",
}
Paths = box.Box(Paths)
# --------------------------
# FileNames
# --------------------------
FileNames = {"file_name_format": "YYYYMMDD_[NAME]EEE_CC_TT_RR"}
FileNames = box.Box(FileNames)

# --------------------------
# Reader
# --------------------------
Reader = {
    "diagnostics": False,
    "filestatuschecker": "size",
    "force_step_table_creation": True,
    "force_all": False,  # not used yet - should be used when saving
    "sep": ";",
    "cycle_mode": "anode",  # used in cellreader (593)
    "sorted_data": True,  # finding step-types assumes sorted data
    "load_only_summary": False,
    "select_minimal": False,
    "limit_loaded_cycles": None,  # limit loading cycles to given cycle number
    "ensure_step_table": False,
    "daniel_number": 5,
    "voltage_interpolation_step": 0.01,
    "time_interpolation_step": 10.0,
    "capacity_interpolation_step": 2.0,
    "use_cellpy_stat_file": False,
    "raw_datadir": None,
    "cellpy_datadir": None,
    "auto_dirs": True,  # search in prm-file for res and hdf5 dirs in loadcell
}
Reader = box.Box(Reader)

# --------------------------
# DataSet
# --------------------------
DataSet = {
    "nom_cap": 3579
}  # mAh/g (used for finding c-rates) [should be moved to Materials]
DataSet = box.Box(DataSet)

# --------------------------
# Db
# --------------------------
Db = {
    "db_type": "simple_excel_reader",
    "db_table_name": "db_table",
    "db_header_row": 0,
    "db_unit_row": 1,
    "db_data_start_row": 2,
    "db_search_start_row": 2,
    "db_search_end_row": -1,
}
Db = box.Box(Db)

# -----------------------------
# New Excel Reader
#   attribute = (header, dtype)
# -----------------------------

DbCols = {
    "id": ("id", "int"),
    "exists": ("exists", "bol"),
    "batch": ("batch", "str"),
    "sub_batch_01": ("b01", "str"),
    "sub_batch_02": ("b02", "str"),
    "sub_batch_03": ("b03", "str"),
    "sub_batch_04": ("b04", "str"),
    "sub_batch_05": ("b05", "str"),
    "sub_batch_06": ("b06", "str"),
    "sub_batch_07": ("b07", "str"),
    "project": ("project", "str"),
    "label": ("label", "str"),
    "group": ("group", "int"),
    "selected": ("selected", "bol"),
    "cell_name": ("cell", "str"),
    "cell_type": ("cell_type", "cat"),
    "experiment_type": ("experiment_type", "cat"),
    "active_material": ("mass_active_material", "float"),
    "total_material": ("mass_total", "float"),
    "loading": ("loading_active_material", "float"),
    "nom_cap": ("nominal_capacity", "float"),
    "file_name_indicator": ("file_name_indicator", "str"),
    "instrument": ("instrument", "str"),
    "raw_file_names": ("raw_file_names", "list"),
    "cellpy_file_name": ("cellpy_file_name", "str"),
    "comment_slurry": ("comment_slurry", "str"),
    "comment_cell": ("comment_cell", "str"),
    "comment_general": ("comment_general", "str"),
    "freeze": ("freeze", "bol"),
}
DbCols = box.Box(DbCols)

# --------------------------
# Instruments
# --------------------------

Instruments = {"tester": "arbin", "custom_instrument_definitions_file": None}

Instruments = box.Box(Instruments)

# Pre-defined instruments:

Arbin = {
    "max_res_filesize": 150_000_000,
    "chunk_size": None,
    "max_chunks": None,
    "use_subprocess": False,
    "detect_subprocess_need": False,
    "sub_process_path": None,
    "office_version": "64bit",
    "SQL_server": r"localhost\SQLEXPRESS",
    "SQL_UID": "sa",
    "SQL_PWD": "Changeme123",
    "SQL_Driver": "SQL Server",
}

# Register pre-defined instruments:

Instruments["Arbin"] = Arbin

# --------------------------
# Materials
# --------------------------

Materials = {"cell_class": "Li-Ion", "default_material": "silicon", "default_mass": 1.0}
Materials = box.Box(Materials)

# --------------------------
# Batch-options
# --------------------------

Batch = {
    "template": "standard",
    "fig_extension": "png",
    "backend": "bokeh",
    "notebook": True,
    "dpi": 300,
    "markersize": 4,
    "symbol_label": "simple",
    "color_style_label": "seaborn-deep",
    "figure_type": "unlimited",
    "summary_plot_width": 900,
    "summary_plot_height": 800,
    "summary_plot_height_fractions": [0.2, 0.5, 0.3],
}

Batch = box.Box(Batch)

# --------------------------
# Other non-config
# --------------------------

_variable_that_is_not_saved_to_config = "Hei"
_prm_default_name = ".cellpy_prms_default.conf"
_prm_globtxt = ".cellpy_prms*.conf"
_odbcs = ["pyodbc", "ado", "pypyodbc"]
_odbc = "pyodbc"
_search_for_odbc_driver = True
_allow_multi_test_file = False
_use_filename_cache = True
_sub_process_path = Path(__file__) / "../../../bin/mdbtools-win/mdb-export"
_sub_process_path = _sub_process_path.resolve()
_sort_if_subprocess = True

_cellpyfile_root = "CellpyData"
_cellpyfile_raw = "/raw"
_cellpyfile_step = "/steps"
_cellpyfile_summary = "/summary"
_cellpyfile_fid = "/fid"

_cellpyfile_complevel = 1
_cellpyfile_complib = None  # currently defaults to "zlib"
_cellpyfile_raw_format = "table"
_cellpyfile_summary_format = "table"
_cellpyfile_stepdata_format = "table"
_cellpyfile_infotable_format = "fixed"
_cellpyfile_fidtable_format = "fixed"

# used as global variables
_globals_status = ""
_globals_errors = []
_globals_message = []


# used during development for testing new features

_res_chunk = 0
