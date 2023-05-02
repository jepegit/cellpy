"""cellpy parameters"""
from __future__ import annotations
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Tuple, Union, Optional, TYPE_CHECKING

# Using TYPE_CHECKING to avoid circular imports
# (this will only work without from __future__ import annotations for python 3.11 and above)
from cellpy.internals.core import OtherPath

import box

# When adding prms, please
#   1) check / update the internal_settings.py file as well to
#      ensure that copying / splitting cellpy objects
#      behaves properly.
#   2) check / update the .cellpy_prms_default.conf file

# locations etc. for reading custom parameters
script_dir = os.path.abspath(os.path.dirname(__file__))
cur_dir = os.path.abspath(os.path.dirname(sys.argv[0]))
user_dir = Path.home()
wdir = Path(cur_dir)
op_wdir = str(wdir)


@dataclass
class CellPyDataConfig:
    """Settings that can be unique for each CellpyCell instance."""

    ...


@dataclass
class CellPyConfig:
    """Session settings (global)."""

    def keys(self):
        return self.__dataclass_fields__.keys()


# If updating this, you will have to do a lot of tweaks.
#   .cellpy_prms_default.conf
#   cli.py (_update_paths)
#   test_cli_setup_interactive (NUMBER_OF_DIRS)
#   test_prms.py (config_file_txt)
#   _convert_paths_to_dict


# This can stay global:
@dataclass
class PathsClass(CellPyConfig):
    outdatadir: Union[Path, str] = wdir
    _rawdatadir: Union[OtherPath, str] = op_wdir
    _cellpydatadir: Union[OtherPath, str] = op_wdir
    db_path: Union[Path, str] = wdir  # used for simple excel db reader
    filelogdir: Union[Path, str] = wdir
    examplesdir: Union[Path, str] = wdir
    notebookdir: Union[Path, str] = wdir
    templatedir: Union[Path, str] = wdir
    batchfiledir: Union[Path, str] = wdir
    instrumentdir: Union[Path, str] = wdir
    db_filename: str = "cellpy_db.xlsx"  # used for simple excel db reader
    env_file: Union[Path, str] = user_dir / ".env_cellpy"

    @property
    def rawdatadir(self) -> OtherPath:
        return OtherPath(self._rawdatadir)

    @rawdatadir.setter
    def rawdatadir(self, value: Union[OtherPath, Path, str]):
        self._rawdatadir = OtherPath(value)

    @property
    def cellpydatadir(self) -> OtherPath:
        return OtherPath(self._cellpydatadir)

    @cellpydatadir.setter
    def cellpydatadir(self, value: Union[OtherPath, Path, str]):
        self._cellpydatadir = OtherPath(value)


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
    summary_plot_height_fractions: List[float] = field(
        default_factory=lambda: [0.2, 0.5, 0.3]
    )


@dataclass
class FileNamesClass(CellPyConfig):
    file_name_format: str = "YYYYMMDD_[NAME]EEE_CC_TT_RR"
    raw_extension: str = "res"
    reg_exp: str = None
    sub_folders: bool = True
    file_list_location: str = None
    file_list_type: str = None
    file_list_name: str = None
    cellpy_file_extension: str = "h5"


@dataclass
class ReaderClass(CellPyConfig):
    diagnostics: bool = False
    filestatuschecker: str = "size"
    force_step_table_creation: bool = True
    force_all: bool = False  # not used yet - should be used when saving
    sep: str = ";"
    cycle_mode: str = "anode"
    sorted_data: bool = True  # finding step-types assumes sorted data
    select_minimal: bool = False
    limit_loaded_cycles: Optional[
        int
    ] = None  # limit loading cycles to given cycle number
    ensure_step_table: bool = False
    ensure_summary_table: bool = False
    voltage_interpolation_step: float = 0.01
    time_interpolation_step: float = 10.0
    capacity_interpolation_step: float = 2.0
    use_cellpy_stat_file: bool = False
    auto_dirs: bool = True  # search in prm-file for res and hdf5 dirs in cellpy.get()


@dataclass
class DbClass(CellPyConfig):
    db_type: str = "simple_excel_reader"
    db_table_name: str = "db_table"  # used for simple excel db reader
    db_header_row: int = 0  # used for simple excel db reader
    db_unit_row: int = 1  # used for simple excel db reader
    db_data_start_row: int = 2  # used for simple excel db reader
    db_search_start_row: int = 2  # used for simple excel db reader
    db_search_end_row: int = -1  # used for simple excel db reader
    db_file_sqlite: str = "excel.db"  # used when converting from Excel to sqlite
    # database connection string - used for more advanced db readers:
    db_connection: Optional[str] = None


@dataclass
class DbColsClass(CellPyConfig):  # used for simple excel db reader
    # Note to developers:
    #  1) This is ONLY for the excel-reader (dbreader.py)! More advanced
    #     readers should get their own way of handling the db-columns.
    #  2) If you would like to change the names of the attributes,
    #     you will have to change the names in the
    #        a .cellpy_prms_default.conf
    #        b. dbreader.py
    #        c. test_dbreader.py
    #        d. internal_settings.py (renaming when making sqlite from Excel)
    #     As well as the DbColsTypeClass below.

    id: str = "id"
    exists: str = "exists"
    project: str = "project"
    label: str = "label"
    group: str = "group"
    selected: str = "selected"
    cell_name: str = "cell"
    cell_type: str = "cell_type"
    experiment_type: str = "experiment_type"
    mass_active: str = "mass_active_material"
    area: str = "area"
    mass_total: str = "mass_total"
    loading: str = "loading_active_material"
    nom_cap: str = "nominal_capacity"
    file_name_indicator: str = "file_name_indicator"
    instrument: str = "instrument"
    raw_file_names: str = "raw_file_names"
    cellpy_file_name: str = "cellpy_file_name"
    comment_slurry: str = "comment_slurry"
    comment_cell: str = "comment_cell"
    comment_general: str = "comment_general"
    freeze: str = "freeze"
    argument: str = "argument"

    batch: str = "batch"
    sub_batch_01: str = "b01"
    sub_batch_02: str = "b02"
    sub_batch_03: str = "b03"
    sub_batch_04: str = "b04"
    sub_batch_05: str = "b05"
    sub_batch_06: str = "b06"
    sub_batch_07: str = "b07"


@dataclass
class DbColsUnitClass(CellPyConfig):
    # Note to developers:
    #  1) This is ONLY for the excel-reader (dbreader.py)! More advanced
    #     readers should get their own way of handling the db-columns.

    id: str = "str"
    exists: str = "int"
    project: str = "str"
    label: str = "str"
    group: str = "str"
    selected: str = "int"
    cell_name: str = "str"
    cell_type: str = "str"
    experiment_type: str = "str"
    mass_active: str = "float"
    area: str = "float"
    mass_total: str = "float"
    loading: str = "float"
    nom_cap: str = "float"
    file_name_indicator: str = "str"
    instrument: str = "str"
    raw_file_names: str = "str"
    cellpy_file_name: str = "str"
    comment_slurry: str = "str"
    comment_cell: str = "str"
    comment_general: str = "str"
    freeze: str = "int"
    argument: str = "str"

    batch: str = "str"
    sub_batch_01: str = "str"
    sub_batch_02: str = "str"
    sub_batch_03: str = "str"
    sub_batch_04: str = "str"
    sub_batch_05: str = "str"
    sub_batch_06: str = "str"
    sub_batch_07: str = "str"


@dataclass
class CellInfoClass(CellPyDataConfig):
    """Values used for setting the parameters related to the cell and the cycling"""

    voltage_lim_low: float = 0.0
    voltage_lim_high: float = 1.0
    active_electrode_area: float = 1.0
    active_electrode_thickness: float = 1.0
    electrolyte_volume: float = 1.0

    electrolyte_type: str = "standard"
    active_electrode_type: str = "standard"
    counter_electrode_type: str = "standard"
    reference_electrode_type: str = "standard"
    experiment_type: str = "cycling"
    cell_type: str = "standard"
    separator_type: str = "standard"
    active_electrode_current_collector: str = "standard"
    reference_electrode_current_collector: str = "standard"
    comment: str = ""


@dataclass
class MaterialsClass(CellPyDataConfig):
    """Default material-specific values used in processing the data."""

    cell_class: str = "Li-Ion"
    default_material: str = "silicon"
    default_mass: float = 1.0
    default_nom_cap: float = 1.0
    default_nom_cap_specifics: str = "gravimetric"


Paths = PathsClass()
FileNames = FileNamesClass()
Reader = ReaderClass()
Db = DbClass()
DbCols = DbColsClass()
CellInfo = CellInfoClass()
Materials = MaterialsClass()
Batch = BatchClass(summary_plot_height_fractions=[0.2, 0.5, 0.3])


# ------------------------------------------------------------------------------
# Instruments
#
#  This should be updated - currently using dicts instead of subclasses of
#  dataclasses. I guess I could update this but is a bit challenging
#  so maybe replace later  using e.g. pydantic
# ------------------------------------------------------------------------------


# This can stay global:
# remark! using box.Box for each instrument
@dataclass
class InstrumentsClass(CellPyConfig):
    tester: Union[str, None]
    custom_instrument_definitions_file: Union[str, None]
    Arbin: box.Box
    Maccor: box.Box
    Neware: box.Box


# Pre-defined instruments:
# These can stay global:
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
    "SQL_PWD": "ChangeMe123",
    "SQL_Driver": "SQL Server",
}

Arbin = box.Box(Arbin)

Maccor = {"default_model": "one"}
Maccor = box.Box(Maccor)

Neware = {"default_model": "one"}
Neware = box.Box(Neware)

Instruments = InstrumentsClass(
    tester=None,  # TODO: moving this to DataSetClass (deprecate)
    custom_instrument_definitions_file=None,
    Arbin=Arbin,
    Maccor=Maccor,
    Neware=Neware,
)


# ------------------------------------------------------------------------------
# Other secret- or non-config (only for developers)
# ------------------------------------------------------------------------------

_db_cols_unit = DbColsUnitClass()
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
_cellpyfile_common_meta = "/info"
_cellpyfile_test_dependent_meta = "/info_test_dependent"

_cellpyfile_raw_unit_pre_id = "raw_unit_"
_cellpyfile_raw_limit_pre_id = ""

_cellpyfile_complevel = 1
_cellpyfile_complib = None  # currently, defaults to "zlib"
_cellpyfile_raw_format = "table"
_cellpyfile_summary_format = "table"
_cellpyfile_stepdata_format = "table"
_cellpyfile_infotable_format = "fixed"
_cellpyfile_fidtable_format = "fixed"

# templates
_standard_template_uri = "https://github.com/jepegit/cellpy_cookies.git"

_registered_templates = {
    "standard": (_standard_template_uri, "standard"),  # (repository, name-of-folder)
    "ife": (_standard_template_uri, "ife"),
}

# used as global variables
_globals_status = ""
_globals_errors = []
_globals_message = []


# general settings for loaders
_minimum_columns_to_keep_for_raw_if_exists = [
    "data_point_txt",
    "datetime_txt",
    "test_time_txt",
    "step_time_txt",
    "cycle_index_txt",
    "step_time_txt",
    "step_index_txt",
    "current_txt",
    "voltage_txt",
    "charge_capacity_txt",
    "discharge_capacity_txt",
    "power_txt",
]

# used during development for testing new features

_res_chunk = 0
