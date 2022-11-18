import logging
import shutil
import tempfile

import pytest

from cellpy import get, log, prms

log.setup_logging(default_level=logging.DEBUG, testing=True)


@pytest.fixture
def neware_cell(cellpy_data_instance, parameters):
    return cellpy_data_instance.load(parameters.nw_cellpy_file_path)


def test_get_neware_from_csv(parameters):
    c = get(
        filename=parameters.nw_file_path,
        instrument="neware_txt",
        model="UIO",
        mass=2.08,
    )
    assert len(c.data.raw) == 9065
    assert len(c.data.summary) == 4


def test_get_neware_from_h5(neware_cell):
    assert len(neware_cell.data.raw) == 9065
    assert len(neware_cell.data.summary) == 4
