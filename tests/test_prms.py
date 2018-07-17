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
DataSet:
  nom_cap: 3579
Db:
  db_type: simple_excel_reader
FileNames: {}
Instruments:
  tester: arbin
Paths:
  cellpydatadir: C:\Scripting\MyFiles\development_cellpy\cellpy\parameters
  db_filename: cellpy_db.xlsx
  db_path: C:\Scripting\MyFiles\development_cellpy\cellpy\parameters
  filelogdir: C:\Scripting\MyFiles\development_cellpy\cellpy\parameters
  outdatadir: C:\Scripting\MyFiles\development_cellpy\cellpy\parameters
  rawdatadir: C:\Scripting\MyFiles\development_cellpy\cellpy\parameters
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
excel_db_cols:
  A1: 28
  A2: 29
  A3: 30
  A4: 31
  A5: 32
  A6: 33
  B: 25
  F: 19
  FEC: 22
  IPA: 24
  LC: 27
  LS: 23
  M: 19
  RATE: 26
  Si: 40
  VC: 21
  active_material: 35
  am: 35
  b01: 5
  b02: 6
  b03: 7
  b04: 8
  b05: 9
  b06: 10
  b07: 11
  b08: 12
  batch: 2
  batch_no: 1
  cell_name: 16
  channel: 34
  comment_slurry: 18
  exists: 3
  exists_txt: 4
  fi: 17
  file_name_indicator: 17
  fileid: 17
  finished_run: 19
  freeze: 20
  general_comment: 47
  group: 14
  hd5f_fixed: 20
  label: 13
  loading: 42
  selected: 15
  serial_number_position: 0
  tm: 39
  total_material: 39
  weight_percent_Si: 40
  wtSi: 40
excel_db_filename_cols:
  fileid: 1
  files: 2
  serial_number_position: 0
  serialno: 0
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
