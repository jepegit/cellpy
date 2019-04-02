"""cellpy parameters"""

import os
from pathlib import Path
import sys
import box

# class Parameter(object):
#     """class for storing parameters"""
#     def __init__(self, name, prm_dict):
#         self.name = name
#         for key in prm_dict:
#             setattr(self, key, prm_dict[key])
#
#     def __repr__(self):
#         return "<cellpy_prms: %s>" % self.__dict__

# locations etc for reading custom parameters
script_dir = os.path.abspath(os.path.dirname(__file__))
cur_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
user_dir = os.path.expanduser("~")

# search_path = dict()
# search_path["curdir"] = cur_dir
# search_path["filedir"] = script_dir
# search_path["userdir"] = user_dir
#
# search_order = ["curdir", "filedir", "userdir"]
# default_name = "_cellpy_prms_default.ini"
# prm_default = os.path.join(script_dir, default_name)
# prm_filename = prm_default

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
    "db_filename": "cellpy_db.xlsx",
}
Paths = box.Box(Paths)
# --------------------------
# FileNames
# --------------------------
FileNames = {
}
FileNames = box.Box(FileNames)

# --------------------------
# Reader
# --------------------------
Reader = {
    "diagnostics": False,
    "filestatuschecker": 'size',
    "force_step_table_creation": True,
    "force_all": False,  # not used yet - should be used when saving
    "sep": ";",
    "cycle_mode": 'anode',  # used in cellreader (593)
    "sorted_data": True,  # finding step-types assumes sorted data
    "load_only_summary": False,
    "select_minimal": False,
    "limit_loaded_cycles": None,
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
    "nom_cap": 3579,  # mAh/g (used for finding c-rates)
}
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

# --------------------------
# New Excel Reader
#   attribute = (header, dtype)
#---------------------------

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
    "file_name_indicator": ("file_name_indicator", "str"),
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
Instruments = {
    "tester": "arbin",
    "max_res_filesize": 150000000,
    "chunk_size": None,
    "max_chunks": None,
    "use_subprocess": False,
    "detect_subprocess_need": False,
    "sub_process_path": None,
    "office_version": "64bit",
    "custom_instrument_definitions_file": None,
}
Instruments = box.Box(Instruments)

# --------------------------
# Materials
# --------------------------

Materials = {
    "cell_class": "Li-Ion",
    "default_material": "silicon",
    "default_mass": 1.0,
}
Materials = box.Box(Materials)

# --------------------------
# Batch-options
# --------------------------

Batch = {
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
_prm_default_name = "_cellpy_prms_default.conf"
_prm_globtxt = "_cellpy_prms*.conf"
_odbcs = ["pyodbc", "ado", "pypyodbc"]
_odbc = "pyodbc"
_search_for_odbc_driver = True
_use_filename_cache = True
_sub_process_path = Path(__file__) / "../../../bin/mdbtools-win/mdb-export"
_sub_process_path = _sub_process_path.resolve()
_sort_if_subprocess = True

_cellpyfile_root = "CellpyData"
_cellpyfile_complevel = 1
_cellpyfile_complib = None  # currentlty defaults to "zlib"
_cellpyfile_dfdata_format = "table"
_cellpyfile_dfsummary_format = "table"
_cellpyfile_stepdata_format = "table"
_cellpyfile_infotable_format = "fixed"
_cellpyfile_fidtable_format = "fixed"

# used during development for testing new features

_res_chunk = 0


