import os
import tempfile
import shutil
import datetime
import pytest
import logging

import cellpy.readers.core
from cellpy.exceptions import DeprecatedFeature
from cellpy import log, prms
from . import fdv

log.setup_logging(default_level="DEBUG")

# TODO: refactor from 'dataset' to 'cell' manually (PyCharm cannot handle pytest)


@pytest.fixture
def cellpy_data_instance():
    from cellpy import cellreader

    return cellreader.CellpyData()


# TODO: fix this: dont save a file that is used in other test modules
@pytest.fixture(scope="module")
def dataset():
    from cellpy import cellreader

    a = cellreader.CellpyData()
    a.from_raw(fdv.res_file_path)
    a.set_mass(1.0)
    a.make_summary(find_ocv=False, find_ir=True, find_end_voltage=True)
    a.save(fdv.cellpy_file_path)

    b = cellreader.CellpyData()
    b.load(fdv.cellpy_file_path)
    return b


# TODO: fix this: not smart to save cellpyfile that will be used by other modules
def test_create_cellpyfile(cellpy_data_instance):
    # create a cellpy file from the res-file (used for testing)
    cellpy_data_instance.from_raw(fdv.res_file_path)
    cellpy_data_instance.set_mass(1.0)
    cellpy_data_instance.make_summary(
        find_ocv=False, find_ir=True, find_end_voltage=True
    )
    print(f"trying to save the cellpy file to {fdv.cellpy_file_path}")
    cellpy_data_instance.save(fdv.cellpy_file_path)


@pytest.mark.parametrize(
    "xldate, datemode, option, expected",
    [
        (0, 0, "to_datetime", datetime.datetime(1899, 12, 30, 0, 0)),
        (0, 1, "to_datetime", datetime.datetime(1904, 1, 1, 0, 0)),
        (100, 0, "to_datetime", datetime.datetime(1900, 4, 9, 0, 0)),
        (0, 0, "to_float", -2210889600.0),
        (0, 0, "to_string", "1899-12-30 00:00:00"),
        pytest.param(0, 0, "to_datetime", 0, marks=pytest.mark.xfail),
    ],
)
def test_xldate_as_datetime(xldate, datemode, option, expected):

    result = cellpy.readers.core.xldate_as_datetime(xldate, datemode, option)
    assert result == expected


def test_raw_bad_data_cycle_and_step(cellpy_data_instance):
    cycle = 5
    step = 10
    step_left = 11
    step_header = "step_index"
    cycle_header = "cycle_index"

    cellpy_data_instance.from_raw(fdv.res_file_path, bad_steps=((cycle, step),))

    r = cellpy_data_instance.cell.raw
    steps = r.loc[r[cycle_header] == cycle, step_header].unique()
    assert step not in steps
    assert step_left in steps


def test_raw_data_from_data_point(cellpy_data_instance):
    data_point_header = "data_point"
    cellpy_data_instance.from_raw(fdv.res_file_path, data_points=(10_000, None))

    p1 = cellpy_data_instance.cell.raw[data_point_header].iloc[0]
    assert p1 == 10_000


def test_raw_data_data_point(cellpy_data_instance):
    data_point_header = "data_point"
    cellpy_data_instance.from_raw(fdv.res_file_path, data_points=(10_000, 10_200))

    p1 = cellpy_data_instance.cell.raw[data_point_header].iloc[0]
    p2 = cellpy_data_instance.cell.raw[data_point_header].iloc[-1]
    assert p1 == 10_000
    assert p2 == 10_200


def test_raw_limited_loaded_cycles_prm(cellpy_data_instance):
    try:
        prms.Reader["limit_loaded_cycles"] = [2, 6]
        cellpy_data_instance.from_raw(fdv.res_file_path)
        cycles = cellpy_data_instance.get_cycle_numbers()
    finally:
        prms.Reader["limit_loaded_cycles"] = None

    assert all(cycles == [3, 4, 5])


@pytest.mark.parametrize("number", [0, pytest.param(2, marks=pytest.mark.xfail)])
def test_validate_dataset_number(dataset, number):
    dataset._validate_dataset_number(number)


def test_cellpy_version_4(cellpy_data_instance):
    f_old = fdv.cellpy_file_path_v4
    d = cellpy_data_instance.load(f_old, accept_old=True)
    v = d.cell.cellpy_file_version
    print(f"\nfile name: {f_old}")
    print(f"cellpy version: {v}")


def test_cellpy_version_5(cellpy_data_instance):
    f_old = fdv.cellpy_file_path_v5
    d = cellpy_data_instance.load(f_old, accept_old=True)
    v = d.cell.cellpy_file_version
    print(f"\nfile name: {f_old}")
    print(f"cellpy version: {v}")


def test_merge(cellpy_data_instance):
    f1 = fdv.res_file_path
    f2 = fdv.res_file_path2
    assert os.path.isfile(f1)
    assert os.path.isfile(f2)
    cellpy_data_instance.from_raw(f1)
    cellpy_data_instance.from_raw(f2)

    assert len(cellpy_data_instance.datasets) == 2

    table_first = cellpy_data_instance.datasets[0].raw.describe()
    count_first = table_first.loc["count", "data_point"]

    table_second = cellpy_data_instance.datasets[1].raw.describe()
    count_second = table_second.loc["count", "data_point"]

    cellpy_data_instance.merge()
    assert len(cellpy_data_instance.datasets) == 2

    table_all = cellpy_data_instance.datasets[0].raw.describe()
    count_all = table_all.loc["count", "data_point"]
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

    len_first = len(cdi1.cells)
    table_first = cdi1.cells[0].raw.describe()
    count_first = table_first.loc["count", "data_point"]

    len_second = len(cdi2.cells)
    table_second = cdi2.cells[0].raw.describe()
    count_second = table_second.loc["count", "data_point"]

    len_all = len(cdi3.cells)
    table_all = cdi3.cells[0].raw.describe()
    count_all = table_all.loc["count", "data_point"]

    assert len_first == 1
    assert len_second == 1
    assert len_all == 1

    assert pytest.approx(count_all, 0.001) == (count_first + count_second)


@pytest.mark.xfail(raises=NotImplementedError)
def test_clean_up_normal_table(dataset):
    dataset._clean_up_normal_table()


def test_validate_step_table(dataset):
    validated = dataset._validate_step_table()
    assert validated


def test_print_step_table(dataset):
    dataset.print_steps()


def test_c_rate_calc(dataset):
    table = dataset.cell.steps
    assert 0.09 in table["rate_avr"].unique()


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
    summary = dataset.cell.summary
    dataset._cap_mod_summary(summary, "reset")


@pytest.mark.xfail(raises=NotImplementedError)
def test_cap_mod_summary_fail(dataset):
    summary = dataset.cell.summary
    dataset._cap_mod_summary(summary, "fix")


def test_cap_mod_normal(dataset):
    dataset._cap_mod_normal()


def test_get_number_of_tests(dataset):
    n = dataset.get_number_of_tests()
    assert n == 1


def test_get_step_numbers(dataset):
    cycle_steps = dataset.get_step_numbers(steptype="charge", cycle_number=7)

    cycles_steps = dataset.get_step_numbers(steptype="charge", cycle_number=[7, 8])

    all_cycles_steps = dataset.get_step_numbers("charge")

    frame_steps = dataset.get_step_numbers(
        steptype="charge",
        allctypes=True,
        pdtype=True,
        cycle_number=None,
        dataset_number=None,
        steptable=None,
    )

    assert isinstance(cycle_steps, dict)
    assert isinstance(cycles_steps, dict)
    assert len(all_cycles_steps) > 10  # could use get_cycles here to compare
    assert not frame_steps.empty


def test_sget_voltage(dataset):
    steps = dataset.get_step_numbers("charge")
    cycle = 3
    step = steps[cycle]
    x = dataset.sget_voltage(cycle, step)
    assert len(x) == 378


def test_sget_steptime(dataset):
    steps = dataset.get_step_numbers("charge")
    x = dataset.sget_steptime(3, steps[3][0])
    assert len(x) == 378


def test_sget_timestamp(dataset):
    steps = dataset.get_step_numbers("charge")
    x = dataset.sget_timestamp(3, steps[3][0])
    assert len(x) == 378
    assert x.iloc[0] == pytest.approx(287559.945, 0.01)


@pytest.mark.parametrize(
    "cycle, in_minutes, full, expected",
    [
        (3, False, True, 248277.107),
        (3, True, True, 248277.107 / 60),
        (None, False, True, 300.010),
        pytest.param(3, False, True, 1.0, marks=pytest.mark.xfail),
    ],
)
def test_get_timestamp(dataset, cycle, in_minutes, full, expected):
    x = dataset.get_timestamp(cycle=cycle, in_minutes=in_minutes, full=full)
    assert x.iloc[0] == pytest.approx(expected, 0.001)


@pytest.mark.parametrize(
    "cycle, in_minutes, full, expected", [(None, False, False, 248277.107)]
)
def test_get_timestamp_list(dataset, cycle, in_minutes, full, expected):
    x = dataset.get_timestamp(cycle=cycle, in_minutes=in_minutes, full=full)
    assert x[2].iloc[0] == pytest.approx(expected, 0.001)


def test_get_number_of_cycles(dataset):
    n = dataset.get_number_of_cycles()
    assert n == 18


@pytest.mark.xfail(raises=DeprecatedFeature)
def test_get_ir(dataset):
    dataset.get_ir()


@pytest.mark.xfail(raises=DeprecatedFeature)
def test_get_diagnostics_plot(dataset):
    dataset.get_diagnostics_plots()


def test_set_cellnumber(dataset):
    dataset.set_cellnumber(0)
    n1 = dataset.selected_cell_number
    assert n1 == 0
    dataset.set_cellnumber(1)
    n2 = dataset.selected_cell_number
    assert n2 == -1


def test_check64bit():
    a = cellpy.readers.core.check64bit()
    b = cellpy.readers.core.check64bit("os")
    logging.debug(f"Python 64bit? {a}")
    logging.debug(f"OS 64bit? {b}")


def test_search_for_files():
    import os
    from cellpy import filefinder

    run_files, cellpy_file = filefinder.search_for_files(
        fdv.run_name, raw_file_dir=fdv.raw_data_dir, cellpy_file_dir=fdv.output_dir
    )

    assert fdv.res_file_path in run_files
    assert os.path.basename(cellpy_file) == fdv.cellpy_file_name


def test_set_res_datadir_wrong(cellpy_data_instance):
    _ = r"X:\A_dir\That\Does\Not\Exist\random_random9103414"
    before = cellpy_data_instance.cellpy_datadir
    cellpy_data_instance.set_cellpy_datadir(_)
    after = cellpy_data_instance.cellpy_datadir
    assert _ != cellpy_data_instance.cellpy_datadir
    assert before == after


def test_set_res_datadir_none(cellpy_data_instance):
    before = cellpy_data_instance.cellpy_datadir
    cellpy_data_instance.set_cellpy_datadir()
    after = cellpy_data_instance.cellpy_datadir
    assert before == after


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
    my_test = cellpy_data_instance.cell
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


@pytest.mark.parametrize(
    "cycle, step, expected_type, expected_info",
    [
        (1, 8, "ocvrlx_down", "good"),
        (2, 8, "ocvrlx_down", "good"),
        (3, 6, "charge", "nan"),
        pytest.param(1, 8, "ocvrlx_up", "good", marks=pytest.mark.xfail),
    ],
)
def test_load_step_specs_short(
    cellpy_data_instance, cycle, step, expected_type, expected_info
):
    cellpy_data_instance.from_raw(fdv.res_file_path)
    cellpy_data_instance.set_mass(1.0)
    file_name = fdv.short_step_table_file_path
    assert os.path.isfile(file_name)
    cellpy_data_instance.load_step_specifications(file_name, short=True)
    step_table = cellpy_data_instance.cell.steps
    t = step_table.loc[
        (step_table.cycle == cycle) & (step_table.step == step), "type"
    ].values[0]
    assert t == expected_type
    i = step_table.loc[
        (step_table.cycle == cycle) & (step_table.step == step), "info"
    ].values[0]
    assert str(i) == expected_info


@pytest.mark.slowtest
def test_load_step_specs(cellpy_data_instance):
    cellpy_data_instance.from_raw(fdv.res_file_path)
    cellpy_data_instance.set_mass(1.0)
    file_name = fdv.step_table_file_path
    assert os.path.isfile(file_name)
    cellpy_data_instance.load_step_specifications(file_name)
    step_table = cellpy_data_instance.cell.steps
    t = step_table.loc[(step_table.cycle == 1) & (step_table.step == 8), "type"].values[
        0
    ]
    assert t == "ocvrlx_down"


def test_loadcell_raw(cellpy_data_instance):
    cellpy_data_instance.loadcell(fdv.res_file_path)
    run_number = 0
    data_point = 2283
    step_time = 1500.05
    sum_discharge_time = 362198.12
    my_test = cellpy_data_instance.cells[run_number]
    assert my_test.summary.loc["1", "data_point"] == data_point
    assert step_time == pytest.approx(my_test.raw.loc[5, "step_time"], 0.1)
    assert sum_discharge_time == pytest.approx(
        my_test.summary.loc[:, "discharge_time"].sum(), 0.1
    )
    assert my_test.cell_no == run_number

    # cellpy_data_instance.make_summary(find_ir=True)
    # cellpy_data_instance.make_step_table()
    # cellpy_data_instance.save(test_cellpy_file_full)


def test_make_step_table(cellpy_data_instance):
    cellpy_data_instance.from_raw(fdv.res_file_path)
    cellpy_data_instance.set_mass(1.0)
    cellpy_data_instance.make_step_table()


def test_make_new_step_table(cellpy_data_instance):
    cellpy_data_instance.from_raw(fdv.res_file_path)
    cellpy_data_instance.set_mass(1.0)
    cellpy_data_instance.make_step_table(profiling=True)
    assert len(cellpy_data_instance.cell.steps) == 103


def test_make_step_table_all_steps(cellpy_data_instance):
    # need a new test data-file for GITT
    cellpy_data_instance.from_raw(fdv.res_file_path)
    cellpy_data_instance.set_mass(1.0)
    cellpy_data_instance.make_step_table(profiling=True, all_steps=True)
    assert len(cellpy_data_instance.cell.steps) == 103


def test_make_step_table_no_rate(cellpy_data_instance):
    cellpy_data_instance.from_raw(fdv.res_file_path)
    cellpy_data_instance.set_mass(1.0)
    cellpy_data_instance.make_step_table(profiling=True, add_c_rate=False)
    assert "rate_avr" not in cellpy_data_instance.cell.steps.columns


def test_make_step_table_skip_steps(cellpy_data_instance):
    cellpy_data_instance.from_raw(fdv.res_file_path)
    cellpy_data_instance.set_mass(1.0)
    cellpy_data_instance.make_step_table(profiling=True, skip_steps=[1, 10])
    print(cellpy_data_instance.cell.steps)
    assert len(cellpy_data_instance.cell.steps) == 87


def test_make_summary(cellpy_data_instance):
    cellpy_data_instance.from_raw(fdv.res_file_path)
    cellpy_data_instance.set_mass(1.0)
    cellpy_data_instance.make_summary()
    s1 = cellpy_data_instance.cells[0].summary
    s2 = cellpy_data_instance.get_cell().summary
    s3 = cellpy_data_instance.get_summary()
    assert s1.columns.tolist() == s2.columns.tolist()
    assert s2.columns.tolist() == s3.columns.tolist()
    assert s2.iloc[:, 3].size == 18
    assert s2.iloc[5, 3] == s1.iloc[5, 3]


def test_make_summary_with_c_rate(cellpy_data_instance):
    cellpy_data_instance.from_raw(fdv.res_file_path)
    cellpy_data_instance.set_mass(1.0)
    cellpy_data_instance.make_summary(add_c_rate=True)


def test_summary_from_cellpyfile(cellpy_data_instance):
    cellpy_data_instance.load(fdv.cellpy_file_path)
    s1 = cellpy_data_instance.get_summary()
    mass = cellpy_data_instance.get_mass()
    cellpy_data_instance.set_mass(mass)
    cellpy_data_instance.make_summary(
        find_ocv=False, find_ir=True, find_end_voltage=True
    )
    s2 = cellpy_data_instance.get_summary()
    assert s1.columns.tolist() == s2.columns.tolist()
    assert s2.iloc[:, 3].size == 18
    assert s2.iloc[5, 3] == s1.iloc[5, 3]


def test_load_cellpyfile(cellpy_data_instance):
    cellpy_data_instance.load(fdv.cellpy_file_path)
    run_number = 0
    cycle_number = 1
    data_point = 1457
    step_time = 1500.05
    sum_test_time = 9301719.457
    my_test = cellpy_data_instance.cells[run_number]
    unique_cycles = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
    unique_cycles_read = my_test.steps.loc[:, "cycle"].unique()
    assert any(map(lambda v: v in unique_cycles_read, unique_cycles))
    assert my_test.summary.loc[cycle_number, "data_point"] == data_point
    assert step_time == pytest.approx(my_test.raw.loc[5, "step_time"], 0.1)
    assert sum_test_time == pytest.approx(
        my_test.summary.loc[:, "test_time"].sum(), 0.1
    )
    assert my_test.cell_no == run_number


def test_get_current_voltage(dataset):
    v = dataset.get_voltage(cycle=5)
    assert len(v) == 498
    c = dataset.get_current(cycle=5)
    assert len(c) == 498
    c_all = dataset.get_current()  # pd.Series
    c_all2 = dataset.get_current(full=False)  # list of pd.Series


def test_get_capacity(dataset):
    cc, vcc = dataset.get_ccap(cycle=5)
    assert len(cc) == len(vcc)
    assert len(cc) == 214
    dc, vdc = dataset.get_dcap(cycle=5)
    assert len(dc) == len(vdc)
    assert len(dc) == 224
    df = dataset.get_cap(cycle=5)  # new: returns dataframe as default
    assert len(df) == 438


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ((1.0, 1.0), 1.0),
        ((1.0, 0.1), 0.1),
        ((0.1, 1.0), 10.0),
        pytest.param((1.0, 0.001), 1.0, marks=pytest.mark.xfail),
    ],
)
def test_get_converter_to_specific(dataset, test_input, expected):
    c = dataset.get_converter_to_specific(
        mass=1.0, to_unit=test_input[0], from_unit=test_input[1]
    )
    assert c == expected


def test_save_cellpyfile_with_extension(cellpy_data_instance):
    cellpy_data_instance.loadcell(fdv.res_file_path)
    cellpy_data_instance.make_summary(find_ir=True)
    cellpy_data_instance.make_step_table()
    tmp_file = next(tempfile._get_candidate_names()) + ".h5"
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
    assert os.path.isfile(tmp_file + ".h5")
    os.remove(tmp_file + ".h5")
    assert not os.path.isfile(tmp_file + ".h5")


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
    assert str(dataset.cell).find("silicon") >= 0
    assert str(dataset.cell).find("rosenborg") < 0


def test_check_cellpy_file(cellpy_data_instance):
    file_name = fdv.cellpy_file_path
    ids = cellpy_data_instance._check_cellpy_file(file_name)


def test_cellpyfile_roundtrip():
    from cellpy import cellreader

    cdi = cellreader.CellpyData()

    # create a cellpy file from the res-file
    cdi.from_raw(fdv.res_file_path)
    cdi.set_mass(1.0)
    cdi.make_summary(find_ocv=False, find_ir=True, find_end_voltage=True)
    cdi.save(fdv.cellpy_file_path)

    # load the cellpy file
    cdi = cellreader.CellpyData()
    cdi.load(fdv.cellpy_file_path)
    cdi.make_step_table()
    cdi.make_summary(find_ocv=False, find_ir=True, find_end_voltage=True)


def test_load_custom_default(cellpy_data_instance):
    from cellpy import prms

    file_name = fdv.custom_file_paths
    prms.Instruments.custom_instrument_definitions_file = None
    cellpy_data_instance.set_instrument("custom")
    cellpy_data_instance.from_raw(file_name)
    cellpy_data_instance.make_step_table()
    cellpy_data_instance.make_summary()
    summary = cellpy_data_instance.cell.summary
    val = summary.loc[2, "shifted_discharge_capacity_u_mAh_g"]
    assert 593.031 == pytest.approx(val, 0.1)


def test_group_by_interpolate(dataset):
    data = dataset.cell.raw
    interpolated_data1 = cellpy.readers.core.group_by_interpolate(data)
    interpolated_data2 = cellpy.readers.core.group_by_interpolate(data, tidy=True)
    interpolated_data3 = cellpy.readers.core.group_by_interpolate(
        data, individual_x_cols=True
    )


def test_get():
    c_h5 = cellpy.get(fdv.cellpy_file_path)
    c_res = cellpy.get(fdv.res_file_path, instrument="arbin", mass=0.045)


def test_get_advanced():
    c_many = cellpy.get(
        [fdv.res_file_path, fdv.res_file_path2], logging_mode="DEBUG", mass=0.035
    )


def test_get_empty():
    c_empty = cellpy.get()


@pytest.mark.parametrize("val,validated", [(2.3, None), ([2.3], None), ([2.3], [True])])
def test_set_total_mass(dataset, val, validated):
    dataset.set_tot_mass(val, validated=validated)
    assert dataset.cell.tot_mass == 2.3


@pytest.mark.parametrize(
    "val,validated",
    [
        (372.3, None),
        ([372.3], None),
        ([372.3], [True]),
        pytest.param(372.5, None, marks=pytest.mark.xfail),
    ],
)
def test_set_nominal_capacity(dataset, val, validated):
    dataset.set_nom_cap(val, validated=validated)
    assert dataset.cell.nom_cap == 372.3


@pytest.mark.parametrize(
    "n,s",
    [
        (0, 0),
        (2, -1),
        ("first", 0),
        ("last", -1),
        pytest.param(-1, -1, marks=pytest.mark.xfail),
    ],
)
def test_set_testnumbers(dataset, n, s):
    dataset.set_cellnumber(n)
    assert dataset.selected_cell_number == s


@pytest.mark.xfail
@pytest.mark.filterwarnings("error")
def test_deprecations(dataset):
    dataset._check_file_type("my_file.res")
