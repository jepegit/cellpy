# import tempfile
# import shutil
import pytest
import logging
from cellpy import log
from . import fdv
log.setup_logging(default_level=logging.DEBUG)


@pytest.fixture
def cellpy_data_instance():
    from cellpy import cellreader
    return cellreader.CellpyData()


@pytest.fixture
def dataset():
    from cellpy import cellreader
    d = cellreader.CellpyData()
    d.load(fdv.test_mpr_cellpy_file_full)
    return d


def test_set_instrument(cellpy_data_instance):
    instrument = "biologics_mpr"
    cellpy_data_instance.set_instrument(instrument=instrument)
    cellpy_data_instance.from_raw(fdv.test_mpr_file_full)
    # cellpy_data_instance.make_step_table()
    # cellpy_data_instance.make_summary()
    # temp_dir = tempfile.mkdtemp()
    # cellpy_data_instance.to_csv(datadir=temp_dir)
    # shutil.rmtree(temp_dir)
