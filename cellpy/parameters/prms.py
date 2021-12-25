"""cellpy parameters"""

import os
from dataclasses import dataclass, field
from pathlib import Path
import sys
from typing import Union, Tuple, List

import box

# When adding prms, please
#   1) check / update the internal_settings.py file as well to ensure that copying / splitting cellpy objects
#   behaves properly.
#   2) check / update the .cellpy_prms_default.conf file

# locations etc for reading custom parameters
script_dir = os.path.abspath(os.path.dirname(__file__))
cur_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
user_dir = os.path.expanduser("~")

# -----------------------------------
# Test using dataclass instead of box
# -----------------------------------

wdir = Path(cur_dir)


@dataclass
class CellPyConfig:
    ...


@dataclass
class PathsClass(CellPyConfig):
    outdatadir: Union[Path, str] = wdir
    rawdatadir: Union[Path, str] = wdir
    cellpydatadir: Union[Path, str] = wdir
    db_path: Union[Path, str] = wdir
    filelogdir: Union[Path, str] = wdir
    examplesdir: Union[Path, str] = wdir
    notebookdir: Union[Path, str] = wdir
    batchfiledir: Union[Path, str] = wdir
    db_filename: str = "cellpy_db.xlsx"


# --------------------------
# Paths
# --------------------------
#
# Paths = {
#     "outdatadir": cur_dir,
#     "rawdatadir": cur_dir,
#     "cellpydatadir": cur_dir,
#     "db_path": cur_dir,
#     "filelogdir": cur_dir,
#     "examplesdir": cur_dir,
#     "notebookdir": cur_dir,
#     "batchfiledir": cur_dir,
#     "db_filename": "cellpy_db.xlsx",
# }

Paths = PathsClass()
# --------------------------
# FileNames
# --------------------------
# FileNames = {"file_name_format": "YYYYMMDD_[NAME]EEE_CC_TT_RR"}
# FileNames = box.Box(FileNames)


@dataclass
class FileNamesClass(CellPyConfig):
    file_name_format: str = "YYYYMMDD_[NAME]EEE_CC_TT_RR"


FileNames = FileNamesClass()


# --------------------------
# Reader
# --------------------------
# Reader = {
#     "diagnostics": False,
#     "filestatuschecker": "size",
#     "force_step_table_creation": True,
#     "force_all": False,  # not used yet - should be used when saving
#     "sep": ";",
#     "cycle_mode": "anode",  # used in cellreader (593)
#     "sorted_data": True,  # finding step-types assumes sorted data
#     "load_only_summary": False,
#     "select_minimal": False,
#     "limit_loaded_cycles": None,  # limit loading cycles to given cycle number
#     "ensure_step_table": False,
#     "daniel_number": 5,
#     "voltage_interpolation_step": 0.01,
#     "time_interpolation_step": 10.0,
#     "capacity_interpolation_step": 2.0,
#     "use_cellpy_stat_file": False,
#     "raw_datadir": None,
#     "cellpy_datadir": None,
#     "auto_dirs": True,  # search in prm-file for res and hdf5 dirs in loadcell
# }
# Reader = box.Box(Reader)


@dataclass
class ReaderClass(CellPyConfig):
    diagnostics: bool = False
    filestatuschecker: str = "size"
    force_step_table_creation: bool = True
    force_all: bool = False  # not used yet - should be used when saving
    sep: str = ";"
    cycle_mode: str = "anode"
    sorted_data: bool = True  # finding step-types assumes sorted data
    load_only_summary: bool = False
    select_minimal: bool = False
    limit_loaded_cycles: Union[
        int, None
    ] = None  # limit loading cycles to given cycle number
    ensure_step_table: bool = False
    daniel_number: int = 5
    voltage_interpolation_step: float = 0.01
    time_interpolation_step: float = 10.0
    capacity_interpolation_step: float = 2.0
    use_cellpy_stat_file: bool = False
    raw_datadir: Union[str, None] = None
    cellpy_datadir: Union[str, None] = None
    auto_dirs: bool = True  # search in prm-file for res and hdf5 dirs in loadcell
    chunk_size: Union[int, None] = None
    last_chunk: Union[int, None] = None
    max_chunks: Union[int, None] = None
    max_res_filesize: int = 150000000


Reader = ReaderClass()


# --------------------------
# DataSet
# --------------------------
# DataSet = {
#     "nom_cap": 3579
# }  # mAh/g (used for finding c-rates) [should be moved to Materials]
# DataSet = box.Box(DataSet)


@dataclass
class DataSetClass(CellPyConfig):
    """Values used when processing the data (will be deprecated)"""

    nom_cap: float = 3579


DataSet = DataSetClass()


# --------------------------
# Db
# --------------------------
# Db = {
#     "db_type": "simple_excel_reader",
#     "db_table_name": "db_table",
#     "db_header_row": 0,
#     "db_unit_row": 1,
#     "db_data_start_row": 2,
#     "db_search_start_row": 2,
#     "db_search_end_row": -1,
# }
# Db = box.Box(Db)


@dataclass
class DbClass(CellPyConfig):
    db_type: str = "simple_excel_reader"
    db_table_name: str = "db_table"
    db_header_row: int = 0
    db_unit_row: int = 1
    db_data_start_row: int = 2
    db_search_start_row: int = 2
    db_search_end_row: int = -1


Db = DbClass()

# -----------------------------
# New Excel Reader
#   attribute = (header, dtype)
# -----------------------------
#
# DbCols = {
#     "id": ("id", "int"),
#     "exists": ("exists", "bol"),
#     "batch": ("batch", "str"),
#     "sub_batch_01": ("b01", "str"),
#     "sub_batch_02": ("b02", "str"),
#     "sub_batch_03": ("b03", "str"),
#     "sub_batch_04": ("b04", "str"),
#     "sub_batch_05": ("b05", "str"),
#     "sub_batch_06": ("b06", "str"),
#     "sub_batch_07": ("b07", "str"),
#     "project": ("project", "str"),
#     "label": ("label", "str"),
#     "group": ("group", "int"),
#     "selected": ("selected", "bol"),
#     "cell_name": ("cell", "str"),
#     "cell_type": ("cell_type", "cat"),
#     "experiment_type": ("experiment_type", "cat"),
#     "active_material": ("mass_active_material", "float"),
#     "total_material": ("mass_total", "float"),
#     "loading": ("loading_active_material", "float"),
#     "nom_cap": ("nominal_capacity", "float"),
#     "file_name_indicator": ("file_name_indicator", "str"),
#     "instrument": ("instrument", "str"),
#     "raw_file_names": ("raw_file_names", "Tuple[str, str]"),
#     "cellpy_file_name": ("cellpy_file_name", "str"),
#     "comment_slurry": ("comment_slurry", "str"),
#     "comment_cell": ("comment_cell", "str"),
#     "comment_general": ("comment_general", "str"),
#     "freeze": ("freeze", "bol"),
# }
# DbCols = box.Box(DbCols)


@dataclass
class DbColsClass(CellPyConfig):
    id: Tuple[str, str] = ("id", "int")
    exists: Tuple[str, str] = ("exists", "bol")
    batch: Tuple[str, str] = ("batch", "str")
    sub_batch_01: Tuple[str, str] = ("b01", "str")
    sub_batch_02: Tuple[str, str] = ("b02", "str")
    sub_batch_03: Tuple[str, str] = ("b03", "str")
    sub_batch_04: Tuple[str, str] = ("b04", "str")
    sub_batch_05: Tuple[str, str] = ("b05", "str")
    sub_batch_06: Tuple[str, str] = ("b06", "str")
    sub_batch_07: Tuple[str, str] = ("b07", "str")
    project: Tuple[str, str] = ("project", "str")
    label: Tuple[str, str] = ("label", "str")
    group: Tuple[str, str] = ("group", "int")
    selected: Tuple[str, str] = ("selected", "bol")
    cell_name: Tuple[str, str] = ("cell", "str")
    cell_type: Tuple[str, str] = ("cell_type", "cat")
    experiment_type: Tuple[str, str] = ("experiment_type", "cat")
    active_material: Tuple[str, str] = ("mass_active_material", "float")
    total_material: Tuple[str, str] = ("mass_total", "float")
    loading: Tuple[str, str] = ("loading_active_material", "float")
    nom_cap: Tuple[str, str] = ("nominal_capacity", "float")
    file_name_indicator: Tuple[str, str] = ("file_name_indicator", "str")
    instrument: Tuple[str, str] = ("instrument", "str")
    raw_file_names: Tuple[str, str] = ("raw_file_names", "Tuple[str, str]")
    cellpy_file_name: Tuple[str, str] = ("cellpy_file_name", "str")
    comment_slurry: Tuple[str, str] = ("comment_slurry", "str")
    comment_cell: Tuple[str, str] = ("comment_cell", "str")
    comment_general: Tuple[str, str] = ("comment_general", "str")
    freeze: Tuple[str, str] = ("freeze", "bol")


DbCols = DbColsClass()


# --------------------------
# Materials
# --------------------------


@dataclass
class MaterialsClass(CellPyConfig):
    """Default material-specific values used in processing the data."""

    cell_class: str = "Li-Ion"
    default_material: str = "silicon"
    default_mass: float = 1.0
    default_nom_cap: float = 1.0  # not used yet - should replace the DataSet class


Materials = MaterialsClass()

# --------------------------
# Batch-options
# --------------------------
#
# Batch = {
#     "template": "standard",
#     "fig_extension": "png",
#     "backend": "bokeh",
#     "notebook": True,
#     "dpi": 300,
#     "markersize": 4,
#     "symbol_label": "simple",
#     "color_style_label": "seaborn-deep",
#     "figure_type": "unlimited",
#     "summary_plot_width": 900,
#     "summary_plot_height": 800,
#     "summary_plot_height_fractions": [0.2, 0.5, 0.3],
# }
#
# Batch = box.Box(Batch)


#
@dataclass
class BatchClass(CellPyConfig):
    template: str = "standard"
    fig_extension: str = "png"
    backend: str = "bokeh"
    notebook: bool = True
    dpi: int = 300
    markersize: int = 4
    symbol_label: str = "simple"
    color_style_label: str = "seaborn-deep"
    figure_type: str = "unlimited"
    summary_plot_width: int = 900
    summary_plot_height: int = 800
    summary_plot_height_fractions: List[int] = field(
        default_factory=lambda: [0.2, 0.5, 0.3]
    )


Batch = BatchClass(summary_plot_height_fractions=[0.2, 0.5, 0.3])


# ------------------------------------------------------------------------------
# Instruments
#
#  This should be updated - currently using dicts instead of sub-classes of
#  dataclasses. I guess I could update this but is a bit challenging
#  so maybe replace later  using e.g. pydantic
# ------------------------------------------------------------------------------

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

Arbin = box.Box(Arbin)


Maccor = {}

maccor_model_1 = {
    "name": "one",
    "skiprows": 2,  # 12 for other file
    "sep": "\t",
    "header": 1,  # 0 for other file
    "encoding": "ISO-8859-1",  # options: "ISO-8859-1", "utf-8", "cp1252"
}

maccor_model_2 = {
    "name": "two",
    "skiprows": 12,
    "sep": "\t",
    "header": 0,
    "encoding": "ISO-8859-1",
}

Maccor["one"] = maccor_model_1
Maccor["two"] = maccor_model_2
Maccor["default_model"] = "one"

Maccor = box.Box(Maccor)


# remark! using box.Box for each instrument
@dataclass
class InstrumentsClass(CellPyConfig):
    tester: str
    custom_instrument_definitions_file: str
    Arbin: box.Box
    Maccor: box.Box


Instruments = InstrumentsClass(
    tester="arbin", custom_instrument_definitions_file=None, Arbin=Arbin, Maccor=Maccor
)


# ---------------------------
# Other secret- or non-config
# ---------------------------

_debug = False
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
