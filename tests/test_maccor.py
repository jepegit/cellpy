import tempfile
import shutil
import pytest
import logging
from cellpy import log, get
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
    d.load(fdv.mpr_cellpy_file_path)
    return d


def test_set_instrument(cellpy_data_instance):
    import os
    instrument = "maccor_txt"
    cellpy_data_instance.set_instrument(instrument=instrument)
    cellpy_data_instance.from_raw(fdv.mcc_file_path, sep="\t")
    cellpy_data_instance.make_step_table()
    cellpy_data_instance.make_summary()
    assert len(cellpy_data_instance.cell.raw) == 6704
    temp_dir = tempfile.mkdtemp()
    logging.debug(f"created a temporary directory and dumping csv there ({temp_dir})")
    cellpy_data_instance.to_csv(datadir=temp_dir)
    assert len(os.listdir(temp_dir)) > 0
    shutil.rmtree(temp_dir)


def test_cellpy_get(cellpy_data_instance):
    instrument = "maccor_txt"
    c = get(fdv.mcc_file_path, instrument=instrument, sep="\t")
    assert len(c.cell.raw) == 6704
