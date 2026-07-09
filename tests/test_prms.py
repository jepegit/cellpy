import io
import logging
import os
import tempfile
from pathlib import Path

import pytest

from cellpy import log, prmreader, prms
from cellpy.internals.connections import OtherPath

from .prms_support import (
    EXPECTED_PRMS_INVENTORY,
    assert_inventory_equal,
    collect_prms_inventory,
    write_minimal_prm_file,
)

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
  env_file: .env_cellpy
FileNames:
  file_name_format: YYYYMMDD_[NAME]EEE_CC_TT_RR
Db:
  db_type: simple_excel_reader
  db_connection:
  db_table_name: db_table
  db_header_row: 0
  db_unit_row: 1
  db_data_start_row: 2
  db_search_start_row: 2
  db_search_end_row: -1
DbCols:
  id: id
  exists: exists
  batch: batch
  sub_batch_01: b01
  sub_batch_02: b02
  sub_batch_03: b03
  sub_batch_04: b04
  sub_batch_05: b05
  sub_batch_06: b06
  sub_batch_07: b07
  project: project
  label: label
  group: group
  selected: selected
  cell_name: cell
  cell_type: cell_type
  instrument: instrument
  experiment_type: experiment_type
  mass_active: mass_active_material
  mass_total: mass_total
  loading: loading_active_material
  nom_cap: nominal_capacity
  file_name_indicator: file_name_indicator
  raw_file_names: raw_file_names
  cellpy_file_name: cellpy_file_name
  comment_slurry: comment_slurry
  comment_cell: comment_cell
  comment_general: comment_general
  freeze: freeze
  argument: argument
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
  comment: testing
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


config_file2_txt = """---
Paths:
  cellpydatadir: scp://my@server.no/home/me/data/cellpy_data/cellpyfiles
  db_filename: cellpy_db.xlsx
  db_path: cellpy_data/db
  filelogdir: cellpy_data/logs
  outdatadir: cellpy_data/out
  rawdatadir: scp://my@server.no/home/me/data/raw
  examplesdir: cellpy_data/examples
  notebookdir: cellpy_data/notebooks
  templatedir: cellpy_data/templates
  batchfiledir: cellpy_data/batchfiles
  instrumentdir: cellpy_data/instruments
  env_file: .env_cellpy
FileNames:
  file_name_format: YYYYMMDD_[NAME]EEE_CC_TT_RR
Db:
  db_type: simple_excel_reader
  db_connection:
  db_table_name: db_table
  db_header_row: 0
  db_unit_row: 1
  db_data_start_row: 2
  db_search_start_row: 2
  db_search_end_row: -1
DbCols:
  id: id
  exists: exists
  batch: batch
  sub_batch_01: b01
  sub_batch_02: b02
  sub_batch_03: b03
  sub_batch_04: b04
  sub_batch_05: b05
  sub_batch_06: b06
  sub_batch_07: b07
  project: project
  label: label
  group: group
  selected: selected
  cell_name: cell
  cell_type: cell_type
  instrument: instrument
  experiment_type: experiment_type
  mass_active: mass_active_material
  mass_total: mass_total
  loading: loading_active_material
  nom_cap: nominal_capacity
  file_name_indicator: file_name_indicator
  raw_file_names: raw_file_names
  cellpy_file_name: cellpy_file_name
  comment_slurry: comment_slurry
  comment_cell: comment_cell
  comment_general: comment_general
  freeze: freeze
  argument: argument
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
  comment: testing
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
config_file2 = io.StringIO(config_file2_txt)


@pytest.fixture()
def clean_dir():
    new_path = tempfile.mkdtemp()
    return new_path


def test_set_prm_inside_cellpy(cellpy_data_instance):
    pass


def test_save_otherpath_prms_cellpy(clean_dir):
    from cellpy.internals.connections import OtherPath

    logging.debug("OBS! PRMS CHANGED")
    tmp_config_file_name = os.path.join(clean_dir, "cellpy_test_config_2.yml")
    with open(tmp_config_file_name, "w") as f:
        f.write(config_file2_txt)
    prmreader._read_prm_file(tmp_config_file_name)
    assert isinstance(prms.Paths.rawdatadir, OtherPath)
    assert isinstance(prms.Paths.cellpydatadir, OtherPath)
    assert prms.Paths.rawdatadir.full_path == "scp://my@server.no/home/me/data/raw"
    prmreader._write_prm_file(tmp_config_file_name)
    prmreader._read_prm_file(tmp_config_file_name)
    assert isinstance(prms.Paths.rawdatadir, OtherPath)
    assert isinstance(prms.Paths.cellpydatadir, OtherPath)
    assert prms.Paths.rawdatadir.full_path == "scp://my@server.no/home/me/data/raw"


def test_save_prm_file(clean_dir):
    logging.debug("OBS! PRMS CHANGED")
    tmp_config_file_name = os.path.join(clean_dir, "cellpy_test_config_1.yml")
    with open(tmp_config_file_name, "w") as f:
        f.write(config_file_txt)

    prmreader._read_prm_file(tmp_config_file_name)
    prms.Instruments.tester = "biologics_mpr"
    prms.Reader.cycle_mode = "cathode"
    prmreader._write_prm_file(tmp_config_file_name)
    prmreader._read_prm_file(tmp_config_file_name)
    assert prms.Instruments.tester == "biologics_mpr"


def test_dataclass_prms_type_hint():
    from cellpy.internals.connections import OtherPath

    assert isinstance(prms.Paths.outdatadir, (os.PathLike, str))
    prms.Paths.outdatadir = r"C:\my_data\processed"
    assert isinstance(prms.Paths.outdatadir, (os.PathLike, str))
    prms.Paths.outdatadir = Path(r"C:\my_data\processed")
    assert isinstance(prms.Paths.outdatadir, (os.PathLike, str))
    prms.Paths.rawdatadir = OtherPath(r"C:\my_data\processed")
    assert isinstance(prms.Paths.rawdatadir, (os.PathLike, str))


def test_dataclass_otherpath_prms_instruments():
    from cellpy.internals.connections import OtherPath

    assert isinstance(prms.Paths.rawdatadir, OtherPath)
    assert isinstance(prms.Paths.cellpydatadir, OtherPath)


def test_dataclass_prms_instruments_subclass():
    print(prms.Instruments.Arbin)
    detect_subprocess_need = prms.Instruments.Arbin.detect_subprocess_need
    print(detect_subprocess_need)


@pytest.mark.essential
def test_prms_inventory_parity():
    actual = collect_prms_inventory()
    assert_inventory_equal(
        actual, sorted(EXPECTED_PRMS_INVENTORY, key=lambda t: (t[0], t[1]))
    )


@pytest.mark.essential
def test_prms_config_full_section_roundtrip(clean_dir):
    tmp_config = os.path.join(clean_dir, "cellpy_roundtrip.yml")
    write_minimal_prm_file(Path(tmp_config), config_file_txt)

    prmreader._read_prm_file(tmp_config)
    prms.Reader.cycle_mode = "cathode"
    prms.Batch.backend = "bokeh"
    prms.DbCols.project = "roundtrip_project"
    prms.Materials.default_material = "graphite"
    prms.Instruments.tester = "maccor"
    prms.Paths.outdatadir = str(Path(clean_dir) / "custom_out")

    prmreader._write_prm_file(tmp_config)
    prmreader._read_prm_file(tmp_config)

    assert prms.Reader.cycle_mode == "cathode"
    assert prms.Batch.backend == "bokeh"
    assert prms.DbCols.project == "roundtrip_project"
    assert prms.Materials.default_material == "graphite"
    assert prms.Instruments.tester == "maccor"
    assert str(prms.Paths.outdatadir).endswith("custom_out")

    reloaded = prmreader._read_prm_file_without_updating(tmp_config)
    for section in ("Paths", "Reader", "Batch", "DbCols", "Materials", "Instruments"):
        assert section in reloaded


@pytest.mark.essential
def test_prms_precedence_file_runtime_write(clean_dir):
    tmp_config = os.path.join(clean_dir, "cellpy_precedence.yml")
    write_minimal_prm_file(Path(tmp_config), config_file_txt)

    prmreader._read_prm_file(tmp_config)
    prms.Reader.cycle_mode = "cathode"
    assert prms.Reader.cycle_mode == "cathode"

    prmreader._read_prm_file(tmp_config)
    assert prms.Reader.cycle_mode == "anode"

    prms.Reader.cycle_mode = "cathode"
    prmreader._write_prm_file(tmp_config)
    prmreader._read_prm_file(tmp_config)
    assert prms.Reader.cycle_mode == "cathode"

    on_disk = prmreader._read_prm_file_without_updating(tmp_config)
    assert on_disk["Reader"]["cycle_mode"] == "cathode"


@pytest.mark.essential
def test_prms_otherpath_coercion_smoke(clean_dir):
    config_txt = f"""---
Paths:
  outdatadir: {clean_dir}/rel_out
  rawdatadir: {clean_dir}/rel_raw
  cellpydatadir: {clean_dir}/rel_cellpy
  db_path: {clean_dir}/db
  filelogdir: {clean_dir}/logs
  examplesdir: {clean_dir}/examples
  notebookdir: {clean_dir}/notebooks
  templatedir: {clean_dir}/templates
  batchfiledir: {clean_dir}/batchfiles
  instrumentdir: {clean_dir}/instruments
  db_filename: cellpy_db.xlsx
  env_file: .env_cellpy
...
"""
    tmp_config = os.path.join(clean_dir, "otherpath_coerce.yml")
    write_minimal_prm_file(Path(tmp_config), config_txt)
    prmreader._read_prm_file(tmp_config, resolve_paths=True)

    assert isinstance(prms.Paths.rawdatadir, OtherPath)
    assert isinstance(prms.Paths.cellpydatadir, OtherPath)
    assert isinstance(prms.Paths.db_filename, str)
    assert Path(prms.Paths.outdatadir).is_absolute()

    paths_dict = prmreader._convert_paths_to_dict(prms.Paths)
    assert "rel_raw" in paths_dict["rawdatadir"]


def test_prms_otherpath_local_resolve(clean_dir):
    rel = Path("nested_raw")
    config_txt = f"""---
Paths:
  outdatadir: {clean_dir}
  rawdatadir: {rel}
  cellpydatadir: {clean_dir}
  db_path: {clean_dir}
  filelogdir: {clean_dir}
  examplesdir: {clean_dir}
  notebookdir: {clean_dir}
  templatedir: {clean_dir}
  batchfiledir: {clean_dir}
  instrumentdir: {clean_dir}
  db_filename: cellpy_db.xlsx
  env_file: .env_cellpy
...
"""
    tmp_config = os.path.join(clean_dir, "otherpath_resolve.yml")
    write_minimal_prm_file(Path(tmp_config), config_txt)
    prmreader._read_prm_file(tmp_config, resolve_paths=True)
    assert Path(prms.Paths.rawdatadir.raw_path).is_absolute()


@pytest.mark.essential
def test_prms_env_file_loads_secrets(clean_dir, parameters, monkeypatch):
    for key in ("CELLPY_USER", "CELLPY_HOST", "CELLPY_PASSWORD", "CELLPY_KEY_FILENAME"):
        monkeypatch.delenv(key, raising=False)

    env_path = Path(clean_dir) / ".env_cellpy"
    env_path.write_text(
        "\n".join(
            [
                f"CELLPY_USER={parameters.env_cellpy_user}",
                f"CELLPY_HOST={parameters.env_cellpy_host}",
                f"CELLPY_PASSWORD={parameters.env_cellpy_password}",
            ]
        ),
        encoding="utf-8",
    )
    prms.Paths.env_file = env_path
    prmreader._load_env_file()

    assert os.getenv("CELLPY_USER") == parameters.env_cellpy_user
    assert os.getenv("CELLPY_HOST") == parameters.env_cellpy_host
    assert os.getenv("CELLPY_PASSWORD") == parameters.env_cellpy_password


def test_prms_env_reaches_otherpath_connection_info(clean_dir, parameters, monkeypatch):
    for key in ("CELLPY_USER", "CELLPY_HOST", "CELLPY_PASSWORD", "CELLPY_KEY_FILENAME"):
        monkeypatch.delenv(key, raising=False)

    env_path = Path(clean_dir) / ".env_cellpy"
    env_path.write_text(
        f"CELLPY_PASSWORD={parameters.env_cellpy_password}\n",
        encoding="utf-8",
    )
    prms.Paths.env_file = env_path
    prmreader._load_env_file()

    remote = OtherPath(
        f"ssh://{parameters.env_cellpy_user}@{parameters.env_cellpy_host}/tmp/file.res"
    )
    connect_kwargs, host = remote.connection_info(testing=True)
    assert host == f"{parameters.env_cellpy_user}@{parameters.env_cellpy_host}"
    assert connect_kwargs["password"] == parameters.env_cellpy_password
