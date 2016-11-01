import os
import tempfile
import shutil
import pytest

# -------- defining overall path-names etc ----------
current_file_path = os.path.dirname(os.path.realpath(__file__))
relative_test_data_dir = "../cellpy/data_ex"
test_data_dir = os.path.abspath(os.path.join(current_file_path, relative_test_data_dir))
test_res_file = "20160805_test001_45_cc_01.res"
test_res_file_full = os.path.join(test_data_dir,test_res_file)
test_data_dir_out = os.path.join(test_data_dir, "out")
test_cellpy_file = "20160805_test001_45_cc.h5"
test_cellpy_file_tmp = "tmpfile.h5"
test_cellpy_file_full = os.path.join(test_data_dir,test_cellpy_file)
test_cellpy_file_tmp_full = os.path.join(test_data_dir,test_cellpy_file_tmp)
test_run_name = "20160805_test001_45_cc"

# TODO: use only functions where logical (remove TestCase)

@pytest.fixture
def cellpy_data_instance():
    from cellpy import cellreader
    return cellreader.cellpydata()


@pytest.fixture
def db_reader():
    from cellpy import dbreader
    return dbreader.reader()


def test_search_for_files():
    import os
    from cellpy import filefinder
    run_files, cellpy_file = filefinder.search_for_files(test_run_name,
                                                         raw_file_dir=test_data_dir,
                                                         cellpy_file_dir=test_data_dir_out)
    assert test_res_file_full in run_files
    assert os.path.basename(cellpy_file) == test_cellpy_file


def test_set_res_datadir_wrong(cellpy_data_instance):
    _ = r"X:\A_dir\That\Does\Not\Exist\random_random9103414"
    cellpy_data_instance.set_cellpy_datadir(_)
    assert _ != cellpy_data_instance.cellpy_datadir


def test_set_res_datadir_none(cellpy_data_instance):
    cellpy_data_instance.set_cellpy_datadir()
    assert cellpy_data_instance.cellpy_datadir is None


def test_set_res_datadir(cellpy_data_instance):
    cellpy_data_instance.set_cellpy_datadir(test_data_dir)
    assert test_data_dir == cellpy_data_instance.cellpy_datadir


def test_load_res(cellpy_data_instance):
    cellpy_data_instance.loadcell(test_res_file_full)
    run_number = 0
    data_point = 2283
    step_time = 1500.05
    sum_discharge_time = 362198.12
    my_test = cellpy_data_instance.tests[run_number]
    assert my_test.dfsummary.loc[1,"Data_Point"] == data_point
    assert step_time == pytest.approx(my_test.dfdata.loc[4,"Step_Time"],0.1)
    assert sum_discharge_time == pytest.approx(my_test.dfsummary.loc[:,"Discharge_Time"].sum(),0.1)
    assert my_test.test_no == run_number

    # cellpy_data_instance.make_summary(find_ir=True)
    # cellpy_data_instance.create_step_table()
    # cellpy_data_instance.save_test(test_cellpy_file_full)


def test_load_cellpyfile(cellpy_data_instance):
    cellpy_data_instance.load(test_cellpy_file_full)
    run_number = 0
    data_point = 2283
    step_time = 1500.05
    sum_test_time = 9301719.457
    my_test = cellpy_data_instance.tests[run_number]
    unique_cycles = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
    unique_cycles_read = my_test.step_table.loc[:, "cycle"].unique()
    assert any(map(lambda v: v in unique_cycles_read, unique_cycles))
    assert my_test.dfsummary.loc[1, "Data_Point"] == data_point
    assert step_time == pytest.approx(my_test.dfdata.loc[4, "Step_Time"], 0.1)
    assert sum_test_time == pytest.approx(my_test.dfsummary.loc[:, "Test_Time"].sum(), 0.1)
    assert my_test.test_no == run_number


def test_save_cellpyfile_with_extension(cellpy_data_instance):
    cellpy_data_instance.loadcell(test_res_file_full)
    cellpy_data_instance.make_summary(find_ir=True)
    cellpy_data_instance.create_step_table()
    tmp_file = next(tempfile._get_candidate_names())+".h5"
    cellpy_data_instance.save_test(tmp_file)
    assert os.path.isfile(tmp_file)
    os.remove(tmp_file)
    assert not os.path.isfile(tmp_file)


def test_save_cellpyfile_auto_extension(cellpy_data_instance):
    cellpy_data_instance.loadcell(test_res_file_full)
    cellpy_data_instance.make_summary(find_ir=True)
    cellpy_data_instance.create_step_table()
    tmp_file = next(tempfile._get_candidate_names())
    cellpy_data_instance.save_test(tmp_file)
    assert os.path.isfile(tmp_file+".h5")
    os.remove(tmp_file+".h5")
    assert not os.path.isfile(tmp_file+".h5")


def test_save_cvs(cellpy_data_instance):
    cellpy_data_instance.loadcell(test_res_file_full)
    cellpy_data_instance.make_summary(find_ir=True)
    cellpy_data_instance.create_step_table()
    temp_dir = tempfile.mkdtemp()
    cellpy_data_instance.exportcsv(datadir=temp_dir)
    shutil.rmtree(temp_dir)
    # cellpy_data_instance.save_test(tmp_file)
    # assert os.path.isfile(tmp_file)
    # os.remove(tmp_file)
    # assert not os.path.isfile(tmp_file)


def test_filter_select(db_reader):
    # print my_reader.db_file
    # print my_reader.table.head()
    db_reader.print_serial_number_info(615)
    column_numbers = [db_reader.db_sheet_cols.FEC, db_reader.db_sheet_cols.VC]
    o = db_reader.filter_by_col(column_numbers)
    print 60*"-"
    print o
    assert True
