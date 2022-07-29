import pandas as pd
import pytest

from cellpy import log
from cellpy.readers.instruments import arbin_sql
from cellpy.readers.instruments import base
from cellpy.readers.core import Cell

log.setup_logging(default_level="DEBUG", testing=True)


@pytest.fixture
def raw_mock(parameters):
    raw = pd.read_excel(parameters.mock_file_path, sheet_name="arbin_sql")
    raw.Date_Time = raw.Date_Time.astype('Int64')
    return raw


def test_import_arbin_sql():
    loader = arbin_sql.ArbinSQLLoader()
    assert isinstance(loader, base.Loader)


def test_post_process_rename_headers_defined():
    keywords = {
        "fix_datetime": False,
        "set_index": False,
        "rename_headers": True,
        "extract_start_datetime": False,
    }
    loader = arbin_sql.ArbinSQLLoader()

    # creating a mock raw data
    data = Cell()
    n = arbin_sql.normal_headers_renaming_dict
    raw = pd.DataFrame(columns=n.values())
    data.raw = raw
    loader._post_process(data, **keywords)


def test_post_process_rename_headers_from_file(raw_mock):
    keywords = {
        "fix_datetime": True,
        "set_index": True,
        "rename_headers": True,
        "extract_start_datetime": True,
    }
    loader = arbin_sql.ArbinSQLLoader()

    data = Cell()
    data.raw = raw_mock
    loader._post_process(data, **keywords)

