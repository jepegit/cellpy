import os
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
from cellpy.utils import ocv_rlx

log.setup_logging(default_level=logging.DEBUG)

# @pytest.fixture
# def cellpy_data_instance():
#     from cellpy import cellreader
#     return cellreader.CellpyData()


@pytest.fixture
def dataset():
    from cellpy import cellreader
    d = cellreader.CellpyData()
    d.load(test_cellpy_file_full)
    return d


@pytest.mark.parametrize("variable,value", [("r0", 12.15126), ("r1", 15.29991),
    ("ir", 19.36777), ("c1", 48.06680), ("c0", 7.41526), ("ocv", 0.096818)])
def test_ocv_rlx_single(dataset, variable, value):
    ocv_fit = ocv_rlx.OcvFit()
    ocv_fit.set_cellpydata(dataset, 1)
    ocv_fit.set_zero_current(-0.001)
    ocv_fit.set_zero_voltage(0.05)
    ocv_fit.set_circuits(2)
    ocv_fit.create_model()
    ocv_fit.run_fit()
    r = ocv_fit.get_best_fit_parameters_translated()
    assert r[variable] == pytest.approx(value, 0.001)


def test_ocv_rlx_multi(dataset):
    cycles = [1, 2, 5]
    ocv_fit = ocv_rlx.MultiCycleOcvFit(dataset, cycles, circuits=3)
    ocv_fit.run_fitting(ocv_type="ocvrlx_up")
