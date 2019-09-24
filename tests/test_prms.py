import pytest
import tempfile
import os
import io
import logging
from cellpy import log
from cellpy import prms
from cellpy import prmreader
from . import fdv

log.setup_logging(default_level="DEBUG")

config_file_txt = """---
Batch:
  color_style_label: seaborn-deep
  dpi: 300
  fig_extension: png
  figure_type: unlimited
  markersize: 4
  symbol_label: simple
DataSet:
  nom_cap: 3579
Db:
  db_data_start_row: 2
  db_header_row: 0
  db_search_end_row: -1
  db_search_start_row: 2
  db_table_name: db_table
  db_type: simple_excel_reader
  db_unit_row: 1
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
  cell_type: !!python/tuple
  - cell_type
  - cat
  cellpy_file_name: !!python/tuple
  - cellpy_file_name
  - str
  comment_cell: !!python/tuple
  - comment_cell
  - str
  comment_general: !!python/tuple
  - comment_general
  - str
  comment_slurry: !!python/tuple
  - comment_slurry
  - str
  exists: !!python/tuple
  - exists
  - bol
  experiment_type: !!python/tuple
  - experiment_type
  - cat
  file_name_indicator: !!python/tuple
  - file_name_indicator
  - str
  freeze: !!python/tuple
  - freeze
  - bol
  group: !!python/tuple
  - group
  - int
  id: !!python/tuple
  - id
  - int
  label: !!python/tuple
  - label
  - str
  loading: !!python/tuple
  - loading_active_material
  - float
  project: !!python/tuple
  - project
  - str
  raw_file_names: !!python/tuple
  - raw_file_names
  - list
  selected: !!python/tuple
  - selected
  - bol
  sub_batch_01: !!python/tuple
  - b01
  - str
  sub_batch_02: !!python/tuple
  - b02
  - str
  sub_batch_03: !!python/tuple
  - b03
  - str
  sub_batch_04: !!python/tuple
  - b04
  - str
  sub_batch_05: !!python/tuple
  - b05
  - str
  sub_batch_06: !!python/tuple
  - b06
  - str
  sub_batch_07: !!python/tuple
  - b07
  - str
  total_material: !!python/tuple
  - mass_total
  - float
FileNames: {}
Instruments:
  custom_instrument_definitions_file: null
  tester: arbin
  Arbin:
      chunk_size: null
      detect_subprocess_need: false
      max_chunks: null
      max_res_filesize: 150000000
      office_version: 64bit
      sub_process_path: None
      use_subprocess: false
Paths:
  cellpydatadir: cellpy_data/h5
  db_filename: cellpy_db.xlsx
  db_path: cellpy_data/db
  filelogdir: cellpy_data/log
  outdatadir: cellpy_data/out
  rawdatadir: cellpy_data/raw
Reader:
  auto_dirs: true
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
  use_cellpy_stat_file: false
...
"""
config_file = io.StringIO(config_file_txt)


@pytest.fixture(scope="module")
def cellpy_data_instance():
    from cellpy import cellreader

    return cellreader.CellpyData()


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
    prms.Instruments["tester"] = "biologics"
    prms.Reader.cycle_mode = "cathode"
    prmreader._write_prm_file(tmp_config_file_name)
    prmreader._read_prm_file(tmp_config_file_name)
    assert prms.Instruments.tester == "biologics"

    # with open(tmp_config_file_name, "r") as f:
    #     lines = f.readlines()
    # for line in lines:
    #     print(line, end="")
