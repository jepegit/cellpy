import tempfile
import shutil
import logging

import pytest

from cellpy import log

log.setup_logging(default_level=logging.DEBUG, testing=True)


@pytest.fixture
def mpr_cell(cellpy_data_instance, parameters):
    return cellpy_data_instance.load(parameters.mpr_cellpy_file_path)


def test_load_mpr(cellpy_data_instance, parameters):
    instrument = "biologics_mpr"
    cellpy_data_instance.set_instrument(instrument=instrument)
    cellpy_data_instance.from_raw(parameters.mpr_file_path)
    cellpy_data_instance.make_step_table()
    cellpy_data_instance.make_summary()
    temp_dir = tempfile.mkdtemp()
    cellpy_data_instance.to_csv(datadir=temp_dir)
    shutil.rmtree(temp_dir)


def test_get_mpr(parameters):
    import cellpy

    instrument = "biologics_mpr"
    cellpy.get(parameters.mpr_file_path, instrument=instrument)
