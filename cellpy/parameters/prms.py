"""cellpy parameters"""

import os
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
    "filestatuschecker": 'size',
    "force_step_table_creation": True,
    "force_all": False,  # not used yet - should be used when saving
    "sep": ";",
    "cycle_mode": 'anode',  # used in cellreader (593)
    "load_only_summary": False,
    "select_minimal": False,
    "limit_loaded_cycles": None,
    "ensure_step_table": False,
    "daniel_number": 5,
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
}
Db = box.Box(Db)

# --------------------------
# ExcelReader
# --------------------------
excel_db_cols = {"serial_number_position": 0,
                 "exists": 3,
                 "exists_txt": 4,
                 "fileid": 17,
                 "batch_no": 1,
                 "batch": 2,
                 "label": 13,
                 "group": 14,
                 "selected": 15,
                 "cell_name": 16,
                 "file_name_indicator": 17,
                 "comment_slurry": 18,
                 "finished_run": 19,
                 "hd5f_fixed": 20,
                 "LC": 27,
                 "active_material": 35,
                 "total_material": 39,
                 "loading": 42,
                 "general_comment": 47,
                 }
excel_db_cols = box.Box(excel_db_cols)

excel_db_filename_cols = {"serial_number_position": 0,
                          "serialno": 0,
                          "fileid": 1,
                          "files": 2,
                          }
excel_db_filename_cols = box.Box(excel_db_filename_cols)

# --------------------------
# Instruments
# --------------------------
Instruments = {
    "tester": "arbin",
    "max_res_filesize": 150000000,
    "chunk_size": None,
    "max_chunks": None,
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
    "dpi": 300,
    "markersize": 4,
    "symbol_label": "simple",
    "color_style_label": "seaborn-deep",
    "figure_type": "unlimited",
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

# used during development for testing new features

_res_chunk = 0
