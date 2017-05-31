import os
import pytest

# -------- defining overall path-names etc ----------
current_file_path = os.path.dirname(os.path.realpath(__file__))
relative_test_data_dir = "../testdata"
test_data_dir = os.path.abspath(os.path.join(current_file_path, relative_test_data_dir))

test_data_dir_raw = os.path.join(test_data_dir, "data")
test_data_dir_out = os.path.join(test_data_dir, "out")
test_data_dir_cellpy = os.path.join(test_data_dir, "hdf5")
test_data_dir_db = os.path.join(test_data_dir, "db")

test_cellpy_file = "20160805_test001_45_cc.h5"
test_cellpy_file_full = os.path.join(test_data_dir_cellpy,test_cellpy_file)

test_cellpy_file_tmp = "tmpfile.h5"
test_cellpy_file_tmp_full = os.path.join(test_data_dir_cellpy,test_cellpy_file_tmp)

test_db_filename = "cellpy_db.xlsx"
test_db_filename_full = os.path.join(test_data_dir_db,test_db_filename)

test_run_name = "20160805_test001_45_cc"

test_res_file = "20160805_test001_45_cc_01.res"
test_res_file_full = os.path.join(test_data_dir_raw,test_res_file)


import logging
from cellpy import log
from cellpy.utils import batch

log.setup_logging(default_level=logging.DEBUG)

@pytest.fixture
def cellpy_data_instance():
    from cellpy import cellreader
    return cellreader.cellpydata()


@pytest.fixture
def dataset():
    from cellpy import cellreader
    d = cellreader.cellpydata()
    d.load(test_cellpy_file_full)
    return d


def test_init():
    b = batch.init()
    assert b.summaries is None
    assert b.project is None


def test_read_excel_db():
    name = "NameOfRun"
    project = "ProjectOfRun"
    log_level = "INFO"
    b = batch.init(name, project, default_log_level=log_level, batch_col=5)
    b.create_info_df()
    b.create_folder_structure()

    # b.save_info_df()
    # b.load_info_df(r"C:\Scripting\Processing\Celldata\outdata\SiBEC\cellpy_batch_bec_exp06.json")
    # print(b)
    # print("The info DataFrame:")
    # print(b.info_df.head(5))
    # b.load_and_save_raw()
    # b.make_summaries()
    # print("Finished!")


#
# def test_set_prm():
#     assert False
#
#
# def test_set_load():
#     assert False




# def test_ica_converter(dataset):
#     list_of_cycles = dataset.get_cycle_numbers()
#     number_of_cycles = len(list_of_cycles)
#     print("you have %i cycles" % number_of_cycles)
#     cycle = 5
#     print("looking at cycle %i" % cycle)
#     capacity, voltage = dataset.get_ccap(cycle)
#     converter = ica.Converter()
#     converter.set_data(capacity, voltage)
#     converter.inspect_data()
#     converter.pre_process_data()
#     converter.increment_data()
#     converter.post_process_data()
#
#
# @pytest.mark.parametrize("cycle", [1, 2, 3, 4, 5, 10])
# def test_ica_dqdv(dataset, cycle):
#     capacity, voltage = dataset.get_ccap(cycle)
#     ica.dqdv(voltage, capacity)
#
#
# def test_ica_value_bounds(dataset):
#     capacity, voltage = dataset.get_ccap(5)
#     c = ica.value_bounds(capacity)
#     v = ica.value_bounds(voltage)
#     assert c == pytest.approx((0.001106868, 1535.303235807), 0.0001)
#     assert v == pytest.approx((0.15119725465774536, 1.0001134872436523), 0.0001)
#
#
# def test_ica_index_bounds(dataset):
#     capacity, voltage = dataset.get_ccap(5)
#     c = ica.index_bounds(capacity)
#     v = ica.index_bounds(voltage)
#     assert c == pytest.approx((0.001106868, 1535.303235807), 0.0001)
#     assert v == pytest.approx((0.15119725465774536, 1.0001134872436523), 0.0001)
#
#
