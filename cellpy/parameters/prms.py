"""cellpy parameters"""

import os, sys


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
search_path = dict()
search_path["curdir"] = os.path.abspath(os.path.dirname(sys.argv[0]))
search_path["filedir"] = script_dir
search_path["userdir"] = os.path.expanduser("~")
search_order = ["curdir", "filedir", "userdir"]
default_name = "_cellpy_prms_default.ini"
prm_default = os.path.join(script_dir, default_name)
prm_filename = prm_default

# --------------------------
# Paths
# --------------------------
outdatadir = "..\outdata"
rawdatadir = "..\indata"
cellpydatadir = "..\indata"
db_path = "..\databases"

Paths = {
    "outdatadir": "..\outdata",
    "rawdatadir": "..\indata",
    "cellpydatadir": "..\indata",
    "db_path": "..\databases",
    }

# --------------------------
# FileNames
# --------------------------
filelogdir = "..\databases"
db_filename = "cellpy_db.xlsx"


FileNames = {
    "filelogdir": "..\databases",
    "db_filename": "cellpy_db.xlxs",
    }

# --------------------------
# Reader
# --------------------------
filestatuschecker = 'size'
force_step_table_creation = True
force_all = False  # not used yet - should be used when saving
sep = ";"
cycle_mode = 'anode'
max_res_filesize = 150000000  # instrument specific - move!
load_only_summary = False
select_minimal = False
chunk_size = None    # instrument specific - move!
max_chunks = None    # instrument specific - move!
last_chunk = None    # instrument specific - move!
limit_loaded_cycles = None
load_until_error = False
ensure_step_table = False
daniel_number = 5
raw_datadir = None
cellpy_datadir = None
auto_dirs = True  # search in prm-file for res and hdf5 dirs in loadcell

Reader = {
    "filestatuschecker": 'size',
    "force_step_table_creation": True,
    "force_all": False,  # not used yet - should be used when saving
    "sep": ";",
    "cycle_mode": 'anode',
    "max_res_filesize": 150000000,  # instrument specific - move!
    "load_only_summary": False,
    "select_minimal": False,
    "chunk_size": None,    # instrument specific - move!
    "max_chunks": None,    # instrument specific - move!
    "last_chunk": None,    # instrument specific - move!
    "limit_loaded_cycles": None,
    "load_until_error": False,
    "ensure_step_table": False,
    "daniel_number": 5,
    "raw_datadir": None,
    "cellpy_datadir": None,
    "auto_dirs": True,  # search in prm-file for res and hdf5 dirs in loadcell
}

# --------------------------
# DataSet
# --------------------------
nom_cap = 3579  # mAh/g (used for finding c-rates)

DataSet = {
    "nom_cap": 3579,  # mAh/g (used for finding c-rates)
}
# --------------------------
# Db
# --------------------------
db_type = "simple_excel_reader"

Db = {
    "db_type": "simple_excel_reader",
}

# --------------------------
# ExcelReader
# --------------------------
excel_db_cols = {"serial_number_position": 0,
                    "exists": 3,
                    "exists_txt": 4,
                    "fileid": 17,
                    "batch_no": 1,
                    "batch": 2,
                    "b01": 5,
                    "b02": 6,
                    "b03": 7,
                    "b04": 8,
                    "b05": 9,
                    "b06": 10,
                    "b07": 11,
                    "b08": 12,
                    "label": 13,
                    "group": 14,
                    "selected": 15,
                    "cell_name": 16,
                    "fi": 17,
                    "file_name_indicator": 17,
                    "comment_slurry": 18,
                    "finished_run": 19,
                    "F": 19,
                    "M": 19,
                    "hd5f_fixed": 20,
                    "freeze": 20,
                    "VC": 21,
                    "FEC": 22,
                    "LS": 23,
                    "IPA": 24,
                    "B": 25,
                    "RATE": 26,
                    "LC": 27,
                    "A1": 28,
                    "A2": 29,
                    "A3": 30,
                    "A4": 31,
                    "A5": 32,
                    "A6": 33,
                    "channel": 34,
                    "am": 35,
                    "active_material": 35,
                    "tm": 39,
                    "total_material": 39,
                    "wtSi": 40,
                    "weight_percent_Si": 40,
                    "Si": 40,
                    "loading": 42,
                    "general_comment": 47,
}

excel_db_filename_cols = {"serial_number_position": 0,
                            "serialno": 0,
                            "fileid": 1,
                            "files": 2,
}

# --------------------------
# Instruments
# --------------------------
tester = "arbin"
cell_configuration = "anode"

Instruments = {
    "tester": "arbin",
    "cell_configuration": "anode",
}

# --------------------------
# Materials
# --------------------------
cell_class = "Li-Ion"
default_material = "silicon"
default_mass = 1.0


Materials = {
"cell_class": "Li-Ion",
"default_material": "silicon",
"default_mass": 1.0,

}

def set_defaults():
    pass
