import logging
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from cellpy import log
from cellpy.readers.instruments.pec_csv import (
    DataLoader,
    group_pec_csv_files_by_lot,
    load_pec_csv_groups_by_lot,
)

from . import fdv

log.setup_logging(default_level=logging.DEBUG, testing=True)


def _header_line_after_skiprows(path: Path, skiprows: int) -> str:
    with path.open("r", encoding="utf-8-sig", errors="replace") as handle:
        for line_number, line in enumerate(handle, 1):
            if line_number == skiprows + 1:
                return line.strip()
    raise AssertionError(f"Could not read header line from {path}")


@pytest.mark.parametrize(
    "relative_path, expected_skiprows",
    [
        ("testdata/data/pec.csv", 32),
    ],
)
def test_detect_pec_header_row(relative_path, expected_skiprows):
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / relative_path
    loader = DataLoader()
    loader.name = path
    loader.copy_to_temporary()

    skiprows = loader._find_header_length()

    assert skiprows == expected_skiprows
    assert _header_line_after_skiprows(path, skiprows).startswith("Test,Cell,Rack,Shelf,Position,")


def test_loader_executor_parses_pec_export():
    repo_root = Path(__file__).resolve().parents[1]
    path = repo_root / "testdata/data/pec.csv"
    loader = DataLoader()

    data = loader.loader_executor(path)
    raw = data.raw
    headers = loader.headers_normal

    assert not raw.empty
    assert data.start_datetime == datetime(2019, 2, 22, 16, 21, 35)
    assert data.test_ID == "187"
    assert data.custom_info["pec_metadata"]["lot_id"] is None
    assert raw[headers.data_point_txt].iloc[0] == 1
    assert raw[headers.cycle_index_txt].min() == 1
    assert raw[headers.voltage_txt].iloc[0] == pytest.approx(3.272632)
    assert raw[headers.current_txt].iloc[5] == pytest.approx(-1.6339)
    assert raw[headers.discharge_capacity_txt].iloc[6] == pytest.approx(0.000455)
    assert raw[headers.discharge_energy_txt].iloc[6] == pytest.approx(0.001487)


def test_group_pec_csv_files_by_lot_sorts_by_numeric_test_id():
    repo_root = Path(__file__).resolve().parents[1]
    file_a = repo_root / "testdata/data/pec_multiple_tests/Test25205.csv"
    file_b = repo_root / "testdata/data/pec_multiple_tests/Test25195.csv"
    file_c = repo_root / "testdata/data/pec_multiple_tests/Test25209.csv"

    grouped = group_pec_csv_files_by_lot([file_a, file_b, file_c])

    assert list(grouped["839"]) == [file_b, file_a]
    assert list(grouped["841"]) == [file_c]


def test_load_pec_csv_groups_by_lot_updates_custom_info():
    repo_root = Path(__file__).resolve().parents[1]
    file_a = repo_root / "testdata/data/pec_multiple_tests/Test25205.csv"
    file_b = repo_root / "testdata/data/pec_multiple_tests/Test25195.csv"
    file_c = repo_root / "testdata/data/pec_multiple_tests/Test25209.csv"

    cells = load_pec_csv_groups_by_lot([file_a, file_b, file_c])

    assert sorted(cells.keys()) == ["839", "841"]

    cell_839 = cells["839"]
    assert cell_839.data.custom_info["pec_metadata"]["lot_id"] == "839"
    assert cell_839.data.custom_info["pec_group_metadata"]["lot_ids"] == ["839"]
    assert cell_839.data.custom_info["pec_group_metadata"]["source_test_ids"] == [
        25195,
        25205,
    ]
    assert cell_839.data.test_ID == "25195"


def test_set_instrument(cellpy_data_instance, parameters):
    instrument = "pec_csv"
    cellpy_data_instance.set_instrument(instrument=instrument)
    cellpy_data_instance.from_raw(parameters.pec_file_path)
    cellpy_data_instance.cycle_mode = "cathode"
    cellpy_data_instance.mass = 50_000
    cellpy_data_instance.make_step_table()
    cellpy_data_instance.make_summary()
    temp_dir = tempfile.mkdtemp()
    cellpy_data_instance.to_csv(datadir=temp_dir)
    shutil.rmtree(temp_dir)
