import io
import logging
import os
import tempfile
from pathlib import Path

import pytest

from cellpy import log, prmreader, prms

from . import fdv

log.setup_logging(default_level="DEBUG", testing=True)

config_file_txt = """---
Paths:
  cellpydatadir: cellpy_data/cellpyfiles
  db_filename: cellpy_db.xlsx
  db_path: cellpy_data/db
  filelogdir: cellpy_data/logs
  outdatadir: cellpy_data/out
  rawdatadir: cellpy_data/raw
  examplesdir: cellpy_data/examples
  notebookdir: cellpy_data/notebooks
  templatedir: cellpy_data/templates
  batchfiledir: cellpy_data/batchfiles
  instrumentdir: cellpy_data/instruments
FileNames:
  file_name_format: YYYYMMDD_[NAME]EEE_CC_TT_RR
Db:
  db_type: simple_excel_reader
  db_table_name: db_table
  db_header_row: 0
  db_unit_row: 1
  db_data_start_row: 2
  db_search_start_row: 2
  db_search_end_row: -1
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
  sub_batch_02:
  - b02
  - str
  sub_batch_03:
  - b03
  - str
  sub_batch_04:
  - b04
  - str
  sub_batch_05:
  - b05
  - str
  sub_batch_06:
  - b06
  - str
  sub_batch_07:
  - b07
  - str
  project:
  - project
  - str
  label:
  - label
  - str
  group:
  - group
  - int
  selected:
  - selected
  - bol
  cell_name:
  - cell
  - str
  cell_type:
  - cell_type
  - cat
  instrument:
  - instrument
  - cat
  experiment_type:
  - experiment_type
  - cat
  active_material:
  - mass_active_material
  - float
  total_material:
  - mass_total
  - float
  loading:
  - loading_active_material
  - float
  nom_cap:
  - nominal_capacity
  - float
  file_name_indicator:
  - file_name_indicator
  - str
  raw_file_names:
  - raw_file_names
  - list
  cellpy_file_name:
  - cellpy_file_name
  - str
  comment_slurry:
  - comment_slurry
  - str
  comment_cell:
  - comment_cell
  - str
  comment_general:
  - comment_general
  - str
  freeze:
  - freeze
  - bol
DataSet:
  nom_cap: 3579
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
  daniel_number: 5
  voltage_interpolation_step: 0.01
  time_interpolation_step: 10.0
  capacity_interpolation_step: 2.0
  use_cellpy_stat_file: false
  auto_dirs: true
Instruments:
  tester: arbin_res
  custom_instrument_definitions_file:
  Arbin:
    chunk_size:
    detect_subprocess_need: false
    max_chunks:
    max_res_filesize: 150000000
    odbc_driver:
    office_version: 64bit
    sub_process_path:
    use_subprocess: false
    SQL_server: localhost
    SQL_UID:
    SQL_PWD:
    SQL_Driver: ODBC Driver 17 for SQL Server

Batch:
  template: standard
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
"""
config_file = io.StringIO(config_file_txt)


@pytest.fixture()
def clean_dir():
    new_path = tempfile.mkdtemp()
    return new_path


def test_set_prm_inside_cellpy(cellpy_data_instance):
    pass


def test_save_prm_file(clean_dir):
    tmp_config_file_name = os.path.join(clean_dir, "cellpy_test_config_1.yml")
    with open(tmp_config_file_name, "w") as f:
        f.write(config_file_txt)

    prmreader._read_prm_file(tmp_config_file_name)
    prms.Instruments.tester = "biologics"
    prms.Reader.cycle_mode = "cathode"
    prmreader._write_prm_file(tmp_config_file_name)
    prmreader._read_prm_file(tmp_config_file_name)
    assert prms.Instruments.tester == "biologics"

    # with open(tmp_config_file_name, "r") as f:
    #     lines = f.readlines()
    # for line in lines:
    #     print(line, end="")


def test_dataclass_prms_type_hint():
    assert isinstance(prms.Paths.outdatadir, (os.PathLike, str))
    prms.Paths.outdatadir = r"C:\my_data\processed"
    assert isinstance(prms.Paths.outdatadir, (os.PathLike, str))
    prms.Paths.outdatadir = Path(r"C:\my_data\processed")
    assert isinstance(prms.Paths.outdatadir, (os.PathLike, str))


def test_dataclass_prms_instruments_subclass():
    print(prms.Instruments.Arbin)
    detect_subprocess_need = prms.Instruments.Arbin.detect_subprocess_need
    print(detect_subprocess_need)
