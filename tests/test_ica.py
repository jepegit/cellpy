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

test_res_file = "20160805_test001_45_cc_01.res"
test_res_file_full = os.path.join(test_data_dir_raw,test_res_file)

test_data_dir_out = os.path.join(test_data_dir, "out")

test_data_dir_cellpy = os.path.join(test_data_dir, "hdf5")
test_cellpy_file = "20160805_test001_45_cc.h5"
test_cellpy_file_tmp = "tmpfile.h5"
test_cellpy_file_full = os.path.join(test_data_dir_cellpy,test_cellpy_file)
test_cellpy_file_tmp_full = os.path.join(test_data_dir_cellpy,test_cellpy_file_tmp)

test_run_name = "20160805_test001_45_cc"

import logging
from cellpy import log
from cellpy.utils import ica

log.setup_logging(default_level=logging.DEBUG)


@pytest.fixture(scope="module")
def cellpy_data():
    from cellpy import cellreader
    cellpy_data_instance = cellreader.cellpydata()
    cellpy_data_instance.loadcell(test_res_file_full)
    run_number = 0
    my_run = cellpy_data_instance.tests[run_number]
    return my_run


@pytest.fixture()
def clean_dir():
    new_path = tempfile.mkdtemp()
    return new_path


def setup_module():
    import os
    try:
        os.mkdir(test_data_dir_out)
    except WindowsError:
        print "could not make output directory"


def test_xxx(cellpy_data):
    r = None
    assert r is None


def teardown_module():
    import shutil
    shutil.rmtree(test_data_dir_out)



