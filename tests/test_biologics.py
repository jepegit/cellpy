import os
import tempfile
import shutil
import pytest

# -------- defining overall path-names etc ----------
current_file_path = os.path.dirname(os.path.realpath(__file__))
# relative_test_data_dir = "../cellpy/data_ex"
relative_test_data_dir = "../testdata"
test_data_dir = os.path.abspath(os.path.join(current_file_path, relative_test_data_dir))
test_data_dir_raw = os.path.join(test_data_dir, "data")

test_raw_file = "geis.mpr"
test_raw_file_full = os.path.join(test_data_dir_raw, test_raw_file)

test_data_dir_out = os.path.join(test_data_dir, "out")

test_data_dir_cellpy = os.path.join(test_data_dir, "hdf5")
test_cellpy_file = "geis.h5"
test_cellpy_file_tmp = "tmpfile.h5"
test_cellpy_file_full = os.path.join(test_data_dir_cellpy,test_cellpy_file)
test_cellpy_file_tmp_full = os.path.join(test_data_dir_cellpy,test_cellpy_file_tmp)


import logging
from cellpy import log
log.setup_logging(default_level=logging.DEBUG)


@pytest.fixture
def cellpy_data_instance():
    from cellpy import cellreader
    return cellreader.CellpyData()

@pytest.fixture
def dataset():
    from cellpy import cellreader
    d = cellreader.CellpyData()
    d.load(test_cellpy_file_full)
    return d


def test_set_instrument(cellpy_data_instance):
    instrument = "biologics_mpr"
    cellpy_data_instance.set_instrument(instrument=instrument)
    # cellpy_data_instance.from_raw(test_raw_file_full)
    # cellpy_data_instance.make_step_table()
    # cellpy_data_instance.make_summary()
    # temp_dir = tempfile.mkdtemp()
    # cellpy_data_instance.to_csv(datadir=temp_dir)
    # shutil.rmtree(temp_dir)
