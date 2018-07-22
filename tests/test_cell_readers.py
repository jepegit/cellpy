import os
import tempfile
import shutil
import datetime
import pytest
import logging

import cellpy.readers.core
from cellpy.exceptions import DeprecatedFeature
from cellpy import log
from . import fdv

log.setup_logging(default_level=logging.DEBUG)


@pytest.fixture
def cellpy_data_instance():
    from cellpy import cellreader
    return cellreader.CellpyData()


@pytest.fixture(scope="module")
def dataset():
    from cellpy import cellreader
    a = cellreader.CellpyData()
    a.from_raw(fdv.res_file_path)
    a.set_mass(1.0)
    a.make_summary(find_ocv=False, find_ir=True,
                   find_end_voltage=True)
    a.save(fdv.cellpy_file_path)

    b = cellreader.CellpyData()
    b.load(fdv.cellpy_file_path)
    return b


def test_create_cellpyfile(cellpy_data_instance):
    # create a cellpy file from the res-file (used for testing)
    cellpy_data_instance.from_raw(fdv.res_file_path)
    cellpy_data_instance.set_mass(1.0)
    cellpy_data_instance.make_summary(find_ocv=False, find_ir=True, find_end_voltage=True)
    print(f"trying to save the cellpy file to {fdv.cellpy_file_path}")
    cellpy_data_instance.save(fdv.cellpy_file_path)


@pytest.mark.parametrize("xldate, datemode, option, expected", [
    (0, 0, "to_datetime", datetime.datetime(1899, 12, 30, 0, 0)),
    (0, 1, "to_datetime", datetime.datetime(1904, 1, 1, 0, 0)),
    (100, 0, "to_datetime", datetime.datetime(1900, 4, 9, 0, 0)),
    (0, 0, "to_float", -2210889600.0),
    (0, 0, "to_string", "1899-12-30 00:00:00"),
    pytest.mark.xfail((0, 0, "to_datetime", 0)),
])
def test_xldate_as_datetime(xldate, datemode, option, expected):
    from cellpy import cellreader
    result = cellpy.readers.core.xldate_as_datetime(xldate, datemode, option)
    assert result == expected


@pytest.mark.parametrize("number", [0,pytest.mark.xfail(2, raises=IndexError)])
def test_validate_dataset_number(dataset, number):
    dataset._validate_dataset_number(number)


def test_merge(cellpy_data_instance):
    f1 = fdv.res_file_path
    f2 = fdv.res_file_path2
    assert os.path.isfile(f1)
    assert os.path.isfile(f2)
    cellpy_data_instance.from_raw(f1)
    cellpy_data_instance.from_raw(f2)

    assert len(cellpy_data_instance.datasets) == 2

    table_first = cellpy_data_instance.datasets[0].dfdata.describe()
    count_first = table_first.loc["count", "Data_Point"]

    table_second = cellpy_data_instance.datasets[1].dfdata.describe()
    count_second = table_second.loc["count", "Data_Point"]

    cellpy_data_instance.merge()
    assert len(cellpy_data_instance.datasets) == 2

    table_all = cellpy_data_instance.datasets[0].dfdata.describe()
    count_all = table_all.loc["count", "Data_Point"]
    assert len(cellpy_data_instance.datasets) == 1

    assert pytest.approx(count_all, 0.001) == (count_first + count_second)


def test_merge_auto_from_list():
    from cellpy import cellreader
    cdi1 = cellreader.CellpyData()
    cdi2 = cellreader.CellpyData()
    cdi3 = cellreader.CellpyData()

    f1 = fdv.res_file_path
    f2 = fdv.res_file_path2
    assert os.path.isfile(f1)
    assert os.path.isfile(f2)

    files = [f1, f2]
    cdi1.from_raw(f1)
    cdi2.from_raw(f2)
    cdi3.from_raw(files)

    len_first = len(cdi1.datasets)
    table_first = cdi1.datasets[0].dfdata.describe()
    count_first = table_first.loc["count", "Data_Point"]

    len_second = len(cdi2.datasets)
    table_second = cdi2.datasets[0].dfdata.describe()
    count_second = table_second.loc["count", "Data_Point"]

    len_all= len(cdi3.datasets)
    table_all = cdi3.datasets[0].dfdata.describe()
    count_all = table_all.loc["count", "Data_Point"]

    assert len_first == 1
    assert len_second == 1
    assert len_all == 1

    assert pytest.approx(count_all, 0.001) == (count_first + count_second)


@pytest.mark.xfail(raises=NotImplementedError)
def test_clean_up_normal_table(dataset):
    dataset._clean_up_normal_table()


def test_print_step_table(dataset):
    dataset.print_step_table()


@pytest.mark.xfail(raises=DeprecatedFeature)
def test_select_steps(dataset):
    step_dict = dict()
    dataset.select_steps(step_dict)


@pytest.mark.xfail(raises=DeprecatedFeature)
def test_populate_step_dict(dataset):
    dataset.populate_step_dict(step="charge")


@pytest.mark.xfail(raises=DeprecatedFeature)
def test_from_res(dataset):
    dataset.from_res()


def test_cap_mod_summary(dataset):
    summary = dataset.dataset.dfsummary
    dataset._cap_mod_summary(summary, "reset")


@pytest.mark.xfail(raises=NotImplementedError)
def test_cap_mod_summary_fail(dataset):
    summary = dataset.dataset.dfsummary
    dataset._cap_mod_summary(summary, "fix")


def test_cap_mod_normal(dataset):
    dataset._cap_mod_normal()


def test_get_number_of_tests(dataset):
    n = dataset.get_number_of_tests()
    assert n == 1


def test_sget_voltage(dataset):
    steps = dataset.get_step_numbers("charge")
    x = dataset.sget_voltage(3, steps[3])
    assert len(x) == 378


def test_sget_steptime(dataset):
    steps = dataset.get_step_numbers("charge")
    x = dataset.sget_steptime(3, steps[3])
    assert len(x) == 378


def test_sget_timestamp(dataset):
    steps = dataset.get_step_numbers("charge")
    x = dataset.sget_timestamp(3, steps[3])
    assert len(x) == 378
    assert x.iloc[0] == pytest.approx(287559.945, 0.01)


@pytest.mark.parametrize("cycle, in_minutes, full, expected", [
    (3, False, True, 248277.107),
    (3, True, True, 248277.107/60),
    (None, False, True, 300.010),
    pytest.mark.xfail((3, False, True, 1.0)),
])
def test_get_timestamp(dataset, cycle, in_minutes, full, expected):
    x = dataset.get_timestamp(cycle=cycle, in_minutes=in_minutes, full=full)
    assert x.iloc[0] == pytest.approx(expected, 0.001)


@pytest.mark.parametrize("cycle, in_minutes, full, expected", [
    (None, False, False, 248277.107),
])
def test_get_timestamp_list(dataset, cycle, in_minutes, full, expected):
    x = dataset.get_timestamp(cycle=cycle, in_minutes=in_minutes, full=full)
    assert x[2].iloc[0] == pytest.approx(expected, 0.001)


def test_get_number_of_cycles(dataset):
    n = dataset.get_number_of_cycles()
    assert n == 18


@pytest.mark.xfail(raises=DeprecatedFeature)
def test_get_ir(dataset):
    dataset.get_ir()


def test_get_diagnostics_plot(dataset):
    dataset.get_diagnostics_plots()


def test_set_testnumber(dataset):
    dataset.set_testnumber(0)
    n1 = dataset.selected_dataset_number
    assert n1 == 0
    dataset.set_testnumber(1)
    n2 = dataset.selected_dataset_number
    assert n2 == -1


def test_check64bit():
    from cellpy import cellreader
    cellpy.readers.core.check64bit()
    cellpy.readers.core.check64bit("os")


def test_search_for_files():
    import os
    from cellpy import filefinder
    run_files, cellpy_file = filefinder.search_for_files(fdv.run_name,
                                                         raw_file_dir=fdv.raw_data_dir,
                                                         cellpy_file_dir=fdv.output_dir)
    assert fdv.res_file_path in run_files
    assert os.path.basename(cellpy_file) == fdv.cellpy_file_name


def test_set_res_datadir_wrong(cellpy_data_instance):
    _ = r"X:\A_dir\That\Does\Not\Exist\random_random9103414"
    cellpy_data_instance.set_cellpy_datadir(_)
    assert _ != cellpy_data_instance.cellpy_datadir


def test_set_res_datadir_none(cellpy_data_instance):
    cellpy_data_instance.set_cellpy_datadir()
    assert cellpy_data_instance.cellpy_datadir is None


def test_set_res_datadir(cellpy_data_instance):
    cellpy_data_instance.set_cellpy_datadir(fdv.data_dir)
    assert fdv.data_dir == cellpy_data_instance.cellpy_datadir


def test_set_raw_datadir(dataset):
    print("missing test")


def test_set_logger(dataset):
    print("missing test")


def test_merge(dataset):
    print("missing test")
    print("maybe deprecated")


def test_fid(cellpy_data_instance):
    cellpy_data_instance.loadcell(fdv.res_file_path)
    my_test = cellpy_data_instance.dataset
    assert len(my_test.raw_data_files) == 1
    fid_object = my_test.raw_data_files[0]
    print(fid_object)
    print(fid_object.get_raw())
    print(fid_object.get_name())
    print(fid_object.get_size())
    print(fid_object.get_last())


def test_only_fid():
    from cellpy.readers.core import FileID
    my_fid_one = FileID()
    my_file = fdv.cellpy_file_path
    my_fid_one.populate(my_file)
    my_fid_two = FileID(my_file)
    assert my_fid_one.get_raw()[0] == my_fid_two.get_raw()[0]
    assert my_fid_one.get_size() == my_fid_two.get_size()


@pytest.mark.parametrize("cycle, step, expected_type, expected_info",
                         [(1, 8, "ocvrlx_down", "good"),
                          (2, 8, "ocvrlx_down", "good"),
                          (3, 6, "charge", "nan"),
                          pytest.mark.xfail(
                              (1, 8, "ocvrlx_up", "good")
                          ), ])
def test_load_step_specs_short(cellpy_data_instance, cycle, step,
                               expected_type, expected_info):
    cellpy_data_instance.from_raw(fdv.res_file_path)
    cellpy_data_instance.set_mass(1.0)
    file_name = fdv.short_step_table_file_path
    assert os.path.isfile(file_name)
    cellpy_data_instance.load_step_specifications(file_name, short=True)
    step_table = cellpy_data_instance.dataset.step_table
    t = step_table.loc[(step_table.cycle == cycle) &
                       (step_table.step == step), "type"].values[0]
    assert t == expected_type
    i = step_table.loc[(step_table.cycle == cycle) &
                       (step_table.step == step), "info"].values[0]
    assert str(i) == expected_info


def test_load_step_specs(cellpy_data_instance):
    cellpy_data_instance.from_raw(fdv.res_file_path)
    cellpy_data_instance.set_mass(1.0)
    file_name = fdv.step_table_file_path
    assert os.path.isfile(file_name)
    cellpy_data_instance.load_step_specifications(file_name)
    step_table = cellpy_data_instance.dataset.step_table
    t = step_table.loc[(step_table.cycle == 1) &
                       (step_table.step == 8), "type"].values[0]
    assert t == "ocvrlx_down"


def test_load_res(cellpy_data_instance):
    cellpy_data_instance.loadcell(fdv.res_file_path)
    run_number = 0
    data_point = 2283
    step_time = 1500.05
    sum_discharge_time = 362198.12
    my_test = cellpy_data_instance.datasets[run_number]
    assert my_test.dfsummary.loc[1, "Data_Point"] == data_point
    assert step_time == pytest.approx(my_test.dfdata.loc[4, "Step_Time"], 0.1)
    assert sum_discharge_time == pytest.approx(my_test.dfsummary.loc[:, "Discharge_Time"].sum(), 0.1)
    assert my_test.test_no == run_number

    # cellpy_data_instance.make_summary(find_ir=True)
    # cellpy_data_instance.make_step_table()
    # cellpy_data_instance.save(test_cellpy_file_full)


def test_make_summary(cellpy_data_instance):
    cellpy_data_instance.from_raw(fdv.res_file_path)
    cellpy_data_instance.set_mass(1.0)
    cellpy_data_instance.make_summary()
    s1 = cellpy_data_instance.datasets[0].dfsummary
    s2 = cellpy_data_instance.get_dataset().dfsummary
    s3 = cellpy_data_instance.get_summary()
    assert s1.columns.tolist() == s2.columns.tolist()
    assert s2.columns.tolist() == s3.columns.tolist()
    assert s2.iloc[:, 3].size == 18
    assert s2.iloc[5, 3] == s1.iloc[5, 3]


def test_summary_from_cellpyfile(cellpy_data_instance):
    cellpy_data_instance.load(fdv.cellpy_file_path)
    s1 = cellpy_data_instance.get_summary()
    mass = cellpy_data_instance.get_mass()
    cellpy_data_instance.set_mass(mass)
    cellpy_data_instance.make_summary(find_ocv=False, find_ir=True,
                                      find_end_voltage=True)
    s2 = cellpy_data_instance.get_summary()
    assert s1.columns.tolist() == s2.columns.tolist()
    assert s2.iloc[:, 3].size == 18
    assert s2.iloc[5, 3] == s1.iloc[5, 3]


def test_load_cellpyfile(cellpy_data_instance):
    cellpy_data_instance.load(fdv.cellpy_file_path)
    run_number = 0
    data_point = 2283
    step_time = 1500.05
    sum_test_time = 9301719.457
    my_test = cellpy_data_instance.datasets[run_number]
    unique_cycles = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
    unique_cycles_read = my_test.step_table.loc[:, "cycle"].unique()
    assert any(map(lambda v: v in unique_cycles_read, unique_cycles))
    assert my_test.dfsummary.loc[1, "Data_Point"] == data_point
    assert step_time == pytest.approx(my_test.dfdata.loc[4, "Step_Time"], 0.1)
    assert sum_test_time == pytest.approx(my_test.dfsummary.loc[:, "Test_Time"].sum(), 0.1)
    assert my_test.test_no == run_number


def test_get_current_voltage(dataset):
    v = dataset.get_voltage(cycle=5)
    assert len(v) == 498
    c = dataset.get_current(cycle=5)
    assert len(c) == 498


def test_get_capacity(dataset):
    cc, vcc = dataset.get_ccap(cycle=5)
    assert len(cc) == len(vcc)
    assert len(cc) == 214
    dc, vdc = dataset.get_dcap(cycle=5)
    assert len(dc) == len(vdc)
    assert len(dc) == 224
    c, v = dataset.get_cap(cycle=5)
    assert len(c) == len(v)


@pytest.mark.parametrize("test_input,expected", [
    ((1.0, 1.0), 1.0),
    ((1.0, 0.1), 0.1),
    ((0.1, 1.0), 10.0),
    pytest.mark.xfail(((1.0, 0.001), 1.0)),
])
def test_get_converter_to_specific(dataset, test_input, expected):
    c = dataset.get_converter_to_specific(mass=1.0, to_unit=test_input[0], from_unit=test_input[1])
    assert c == expected


def test_save_cellpyfile_with_extension(cellpy_data_instance):
    cellpy_data_instance.loadcell(fdv.res_file_path)
    cellpy_data_instance.make_summary(find_ir=True)
    cellpy_data_instance.make_step_table()
    tmp_file = next(tempfile._get_candidate_names())+".h5"
    cellpy_data_instance.save(tmp_file)
    assert os.path.isfile(tmp_file)
    os.remove(tmp_file)
    assert not os.path.isfile(tmp_file)


def test_save_cellpyfile_auto_extension(cellpy_data_instance):
    cellpy_data_instance.loadcell(fdv.res_file_path)
    cellpy_data_instance.make_summary(find_ir=True)
    cellpy_data_instance.make_step_table()
    tmp_file = next(tempfile._get_candidate_names())
    cellpy_data_instance.save(tmp_file)
    assert os.path.isfile(tmp_file+".h5")
    os.remove(tmp_file+".h5")
    assert not os.path.isfile(tmp_file+".h5")


def test_save_cvs(cellpy_data_instance):
    cellpy_data_instance.loadcell(fdv.res_file_path)
    cellpy_data_instance.make_summary(find_ir=True)
    cellpy_data_instance.make_step_table()
    temp_dir = tempfile.mkdtemp()
    cellpy_data_instance.to_csv(datadir=temp_dir)
    shutil.rmtree(temp_dir)
    # cellpy_data_instance.save(tmp_file)
    # assert os.path.isfile(tmp_file)
    # os.remove(tmp_file)
    # assert not os.path.isfile(tmp_file)


def test_str_cellpy_data_object(dataset):
    assert str(dataset.dataset).find("silicon") >= 0
    assert str(dataset.dataset).find("rosenborg") < 0


def test_check_cellpy_file(cellpy_data_instance):
    file_name = fdv.cellpy_file_path
    ids = cellpy_data_instance._check_cellpy_file(file_name)


