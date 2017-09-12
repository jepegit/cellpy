from __future__ import print_function
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
from cellpy.utils import ica

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


def test_ica_converter(dataset):
    list_of_cycles = dataset.get_cycle_numbers()
    number_of_cycles = len(list_of_cycles)
    print("you have %i cycles" % number_of_cycles)
    cycle = 5
    print("looking at cycle %i" % cycle)
    capacity, voltage = dataset.get_ccap(cycle)
    converter = ica.Converter()
    converter.set_data(capacity, voltage)
    converter.inspect_data()
    converter.pre_process_data()
    converter.increment_data()
    converter.post_process_data()


@pytest.mark.parametrize("cycle", [1, 2, 3, 4, 5, 10])
def test_ica_dqdv(dataset, cycle):
    capacity, voltage = dataset.get_ccap(cycle)
    ica.dqdv(voltage, capacity)


def test_ica_value_bounds(dataset):
    capacity, voltage = dataset.get_ccap(5)
    c = ica.value_bounds(capacity)
    v = ica.value_bounds(voltage)
    assert c == pytest.approx((0.001106868, 1535.303235807), 0.0001)
    assert v == pytest.approx((0.15119725465774536, 1.0001134872436523), 0.0001)


def test_ica_index_bounds(dataset):
    capacity, voltage = dataset.get_ccap(5)
    c = ica.index_bounds(capacity)
    v = ica.index_bounds(voltage)
    assert c == pytest.approx((0.001106868, 1535.303235807), 0.0001)
    assert v == pytest.approx((0.15119725465774536, 1.0001134872436523), 0.0001)


