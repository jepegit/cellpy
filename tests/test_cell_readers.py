import collections
import datetime
import logging
import os
import pathlib
import shutil
import tempfile

import pytest

import cellpy.readers.core
from cellpy import log, prms
from cellpy.exceptions import DeprecatedFeature, WrongFileVersion
from cellpy.parameters.internal_settings import get_headers_summary
from cellpy.internals.core import OtherPath

log.setup_logging(default_level="DEBUG", testing=True)


# TODO: refactor from 'dataset' to 'cell' manually (PyCharm cannot handle pytest)
# TODO: fix this: not smart to save cellpyfile that will be used by other modules
def test_create_cellpyfile(cellpy_data_instance, tmp_path, parameters):
    # create a cellpy file from the res-file (used for testing)
    cellpy_data_instance.from_raw(parameters.res_file_path)
    print()
    print(cellpy_data_instance)
    cellpy_data_instance.mass = 1.0
    cellpy_data_instance.make_summary(find_ir=True, find_end_voltage=True)
    name = pathlib.Path(tmp_path) / pathlib.Path(parameters.cellpy_file_path).name
    logging.info(f"trying to save the cellpy file to {name}")
    cellpy_data_instance.save(name)


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


def test_raw_bad_data_cycle_and_step(cellpy_data_instance, parameters):
    # TODO @jepe: refactor and use col names directly from HeadersNormal instead
    cycle = 5
    step = 10
    step_left = 11
    step_header = "step_index"
    cycle_header = "cycle_index"

    cellpy_data_instance.from_raw(parameters.res_file_path, bad_steps=((cycle, step),))

    r = cellpy_data_instance.data.raw
    steps = r.loc[r[cycle_header] == cycle, step_header].unique()
    assert step not in steps
    assert step_left in steps


def test_raw_data_from_data_point(cellpy_data_instance, parameters):
    # TODO @jepe: refactor and use col names directly from HeadersNormal instead
    data_point_header = "data_point"
    cellpy_data_instance.from_raw(parameters.res_file_path, data_points=(10_000, None))

    p1 = cellpy_data_instance.data.raw[data_point_header].iloc[0]
    assert p1 == 10_000


def test_raw_data_data_point(cellpy_data_instance, parameters):
    # TODO @jepe: refactor and use col names directly from HeadersNormal instead
    data_point_header = "data_point"
    cellpy_data_instance.from_raw(
        parameters.res_file_path, data_points=(10_000, 10_200)
    )

    p1 = cellpy_data_instance.data.raw[data_point_header].iloc[0]
    p2 = cellpy_data_instance.data.raw[data_point_header].iloc[-1]
    assert p1 == 10_000
    assert p2 == 10_200


def test_raw_limited_loaded_cycles_prm(cellpy_data_instance, parameters):
    try:
        prms.Reader.limit_loaded_cycles = [2, 6]
        cellpy_data_instance.from_raw(parameters.res_file_path)
        cycles = cellpy_data_instance.get_cycle_numbers()
    finally:
        prms.Reader.limit_loaded_cycles = None

    assert all(cycles == [3, 4, 5])


@pytest.mark.xfail(WrongFileVersion)
def test_cellpy_version_4(cellpy_data_instance, parameters):
    f_old = parameters.cellpy_file_path_v4
    d = cellpy_data_instance.load(f_old, accept_old=True)
    # v = d.data.cellpy_file_version
    print(f"\nfile name: {f_old}")
    # print(f"cellpy version: {v}")


def test_cellpy_version_5(cellpy_data_instance, parameters):
    f_old = parameters.cellpy_file_path_v5
    d = cellpy_data_instance.load(f_old, accept_old=True)
    # v = d.data.cellpy_file_version
    print(f"\nfile name: {f_old}")
    # print(f"cellpy version: {v}")


def test_merge(cellpy_data_instance, parameters):
    # TODO @jepe: refactor and use col names directly from HeadersNormal instead
    f1 = parameters.res_file_path
    f2 = parameters.res_file_path2
    assert os.path.isfile(f1)
    assert os.path.isfile(f2)
    cellpy_data_instance.from_raw(f1)
    cellpy_data_instance.from_raw(f2)

    assert len(cellpy_data_instance.datasets) == 2

    table_first = cellpy_data_instance.data.raw.describe()
    count_first = table_first.loc["count", "data_point"]

    table_second = cellpy_data_instance.datasets[1].raw.describe()
    count_second = table_second.loc["count", "data_point"]

    cellpy_data_instance.merge()
    assert len(cellpy_data_instance.datasets) == 2

    table_all = cellpy_data_instance.datasets[0].raw.describe()
    count_all = table_all.loc["count", "data_point"]
    assert len(cellpy_data_instance.datasets) == 1

    assert pytest.approx(count_all, 0.001) == (count_first + count_second)


def test_merge_auto_from_list(parameters):
    # TODO @jepe: refactor and use col names directly from HeadersNormal instead
    from cellpy import cellreader

    cdi1 = cellreader.CellpyCell()
    cdi2 = cellreader.CellpyCell()
    cdi3 = cellreader.CellpyCell()

    f1 = parameters.res_file_path
    f2 = parameters.res_file_path2
    assert os.path.isfile(f1)
    assert os.path.isfile(f2)

    files = [f1, f2]
    cdi1.from_raw(f1)
    cdi2.from_raw(f2)
    cdi3.from_raw(files)

    table_first = cdi1.data.raw.describe()
    count_first = table_first.loc["count", "data_point"]

    table_second = cdi2.data.raw.describe()
    count_second = table_second.loc["count", "data_point"]

    table_all = cdi3.data.raw.describe()
    count_all = table_all.loc["count", "data_point"]

    assert pytest.approx(count_all, 0.001) == (count_first + count_second)


def test_validate_step_table(dataset):
    validated = dataset._validate_step_table()
    assert validated


def test_print_step_table(dataset):
    dataset.print_steps()


def test_c_rate_calc(dataset):
    # TODO @jepe: refactor and use col names directly from HeadersStepTable instead
    table = dataset.data.steps
    unique = table["rate_avr"].unique()
    assert len(unique) == 6


@pytest.mark.xfail(raises=DeprecatedFeature)
def test_select_steps(dataset):
    step_dict = dict()
    dataset.select_steps(step_dict)


@pytest.mark.xfail(raises=DeprecatedFeature)
def test_populate_step_dict(dataset):
    dataset.populate_step_dict(step="charge")


def test_cap_mod_summary(dataset):
    summary = dataset.data.summary
    dataset._cap_mod_summary(summary, "reset")


def test_return_df_get_ccap(dataset):
    df = dataset.get_ccap(cycle=1, as_frame=True)
    cc, v = dataset.get_ccap(cycle=1, as_frame=False)
    assert (df.columns == [v.name, cc.name]).all


def test_return_df_get_dcap(dataset):
    df = dataset.get_dcap(cycle=1, as_frame=True)
    dc, v = dataset.get_dcap(cycle=1, as_frame=False)
    assert (df.columns == [v.name, dc.name]).all


@pytest.mark.xfail(raises=NotImplementedError)
def test_cap_mod_summary_fail(dataset):
    summary = dataset.data.summary
    dataset._cap_mod_summary(summary, "fix")


def test_cap_mod_normal(dataset):
    dataset._cap_mod_normal()


def test_get_step_numbers(dataset):
    cycle_steps = dataset.get_step_numbers(steptype="charge", cycle_number=7)

    cycles_steps = dataset.get_step_numbers(steptype="charge", cycle_number=[7, 8])

    all_cycles_steps = dataset.get_step_numbers("charge")

    frame_steps = dataset.get_step_numbers(
        steptype="charge",
        allctypes=True,
        pdtype=True,
        cycle_number=None,
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
    "cycle, units, expected",
    [
        (1, "seconds", 300.01048193),
        (1, "minutes", 5.00017469),
        (1, "hours", 0.08333624),
    ],
)
def test_get_timestamp(dataset, cycle, units, expected):
    from pprint import pprint

    x = dataset.get_timestamp(cycle=cycle, units=units)
    pprint(x)
    assert x.iloc[0, -1] == pytest.approx(expected, 0.001)


@pytest.mark.parametrize(
    "cycle, units, as_frame, expected", [(None, "seconds", False, 300.01048193)]
)
def test_get_timestamp_list(dataset, cycle, units, as_frame, expected):
    from pprint import pprint

    x = dataset.get_timestamp(cycle=cycle, units=units, as_frame=as_frame)
    assert x[0][0] == pytest.approx(expected, 0.001)


def test_get_number_of_cycles(dataset):
    n = dataset.get_number_of_cycles()
    assert n == 18


@pytest.mark.xfail(raises=DeprecatedFeature)
def test_get_ir(dataset):
    dataset.get_ir()


def test_check64bit():
    a = cellpy.readers.core.check64bit()
    b = cellpy.readers.core.check64bit("os")
    logging.debug(f"Python 64bit? {a}")
    logging.debug(f"OS 64bit? {b}")


def test_search_for_files(parameters):
    import os

    from cellpy import filefinder

    run_files, cellpy_file = filefinder.search_for_files(
        parameters.run_name,
        raw_file_dir=OtherPath(parameters.raw_data_dir),
        cellpy_file_dir=OtherPath(parameters.output_dir),
    )
    print(f"parameters.res_file_path: {OtherPath(parameters.res_file_path)}")
    print(f"run_files: {run_files}")
    for r in run_files:
        print(f"{r=} :: {type(r)=}")
    print(f"{cellpy_file=} :: {type(cellpy_file)=}")
    # TODO: fix this now that we have OtherPath
    assert parameters.res_file_path in run_files
    assert os.path.basename(cellpy_file) == parameters.cellpy_file_name


def test_set_res_datadir_wrong(cellpy_data_instance):
    _ = r"X:\A_dir\That\Does\Not\Exist\random_random9103414"
    before = cellpy_data_instance.cellpy_datadir
    print(f"{before=} :: {type(before)=}")
    cellpy_data_instance.set_cellpy_datadir(_)
    after = cellpy_data_instance.cellpy_datadir
    print(f"{after=} :: {type(after)=}")
    assert _ != cellpy_data_instance.cellpy_datadir
    assert before == after


def test_set_res_datadir_none(cellpy_data_instance):
    before = cellpy_data_instance.cellpy_datadir
    cellpy_data_instance.set_cellpy_datadir()
    after = cellpy_data_instance.cellpy_datadir
    assert before == after


def test_set_res_datadir(cellpy_data_instance, parameters):
    cellpy_data_instance.set_cellpy_datadir(parameters.data_dir)
    assert parameters.data_dir == cellpy_data_instance.cellpy_datadir


def test_set_raw_datadir(dataset):
    print("missing test")


def test_set_logger(dataset):
    print("missing test")


def test_merge(dataset):
    print("missing test")
    print("maybe deprecated")


def test_fid(cellpy_data_instance, parameters):
    cellpy_data_instance.from_raw(parameters.res_file_path)
    my_test = cellpy_data_instance.data
    assert len(my_test.raw_data_files) == 1
    fid_object = my_test.raw_data_files[0]
    print(fid_object)
    print(fid_object.get_raw())
    print(fid_object.get_name())
    print(fid_object.get_size())
    print(fid_object.get_last())


def test_fid_with_otherpath(cellpy_data_instance, parameters):
    raw_file = parameters.res_file_path


def test_only_fid_raw(parameters):
    from cellpy.readers.core import FileID

    my_fid_one = FileID()
    my_file = parameters.cellpy_file_path
    my_fid_one.populate(my_file)
    my_fid_two = FileID(my_file)
    assert my_fid_one.get_raw()[0] == my_fid_two.get_raw()[0]
    assert my_fid_one.get_size() == my_fid_two.get_size()


def test_only_fid_otherpath_local(parameters):
    from cellpy.readers.core import FileID
    from cellpy.internals.core import OtherPath

    my_fid_one = FileID()
    my_file = OtherPath(parameters.cellpy_file_path)
    my_fid_one.populate(my_file)
    my_fid_two = FileID(my_file)
    assert my_fid_one.get_raw()[0] == my_fid_two.get_raw()[0]
    assert my_fid_one.get_size() == my_fid_two.get_size()


@pytest.mark.skip(reason="only run locally")
def test_only_fid_otherpath_external(parameters):
    from cellpy.readers.core import FileID
    from cellpy.internals.core import OtherPath

    my_fid_one = FileID()
    my_file = OtherPath(parameters.cellpy_file_path_external)
    my_fid_one.populate(my_file)
    my_fid_two = FileID(my_file)
    assert my_fid_one.get_raw()[0] == my_fid_two.get_raw()[0]
    assert my_fid_one.get_size() == my_fid_two.get_size()


@pytest.mark.skip(reason="only run locally")
def test_local_only_fid_otherpath_external(parameters):
    """This test is only ran if you are working on your local machine.

    It is used to test the OtherPath class when the path is pointing to a file
    on a remote server. The test is skipped if you are running the tests on
    the CI server.

    For it to work, you will need to have a folder called local in the root
    of the cellpy repository. In this folder you will need to have a file called
    .env_cellpy_local. This file should contain the following lines:


    """
    import pathlib
    import dotenv
    import os

    from cellpy.readers.core import FileID
    from cellpy.internals.core import OtherPath
    from cellpy import cellreader

    # This should only be run on your local machine:
    try:
        env_file = pathlib.Path("../local/.env_cellpy_local").resolve()
        assert env_file.is_file()
    except Exception as e:
        logging.debug("skipping test (not on local machine?)")
        print(e)
        return

    dotenv.load_dotenv(env_file)
    cellpy_file = OtherPath(os.getenv("CELLPY_TEST_CELLPY_FILE_PATH"))
    missing_file = OtherPath(os.getenv("CELLPY_TEST_MISSING_FILE_PATH"))
    raw_file = OtherPath(os.getenv("CELLPY_TEST_RAW_FILE_PATH"))

    print(f"{cellpy_file=} :: {type(cellpy_file)=}")
    print(f"{raw_file=} :: {type(raw_file)=}")
    print(f"{missing_file=} :: {type(missing_file)=}")
    print(f"{cellpy_file.is_file()=}")
    print(f"{raw_file.is_file()=}")
    print(f"{missing_file.is_file()=}")

    # checking if the files exist and that OtherPath is working as expected:
    assert cellpy_file.is_file()
    assert raw_file.is_file()
    # assert not missing_file.is_file()  # OtherPath does not check if file exists when it is external yet.

    my_fid_one = FileID()
    my_fid_one.populate(raw_file)
    my_fid_two = FileID(raw_file)
    assert my_fid_one.get_raw()[0] == my_fid_two.get_raw()[0]
    assert my_fid_one.get_size() == my_fid_two.get_size()

    # checking check_file_ids:
    c = cellreader.CellpyCell()
    check = c.check_file_ids(rawfiles=raw_file, cellpyfile=cellpy_file)
    assert check

    print(f"{raw_file.stat()=}")
    print(f"{cellpy_file.stat()=}")

    c = cellpy.get(raw_file)
    print(c.data.raw_data_files[0].get_raw())


def test_check_file_ids(parameters):
    from cellpy import cellreader

    c = cellreader.CellpyCell()
    cellpy_file = OtherPath(parameters.cellpy_file_path)
    raw_file = OtherPath(parameters.res_file_path)

    print(f"{cellpy_file=} :: {type(cellpy_file)=}")
    print(f"{raw_file=} :: {type(raw_file)=}")
    print(f"{cellpy_file.exists()=}")
    print(f"{raw_file.exists()=}")

    check = c.check_file_ids(rawfiles=raw_file, cellpyfile=cellpy_file)
    assert check


def test_check_file_ids_external_not_accessible(parameters):
    from cellpy import cellreader

    c = cellreader.CellpyCell()
    cellpy_file = OtherPath(parameters.cellpy_file_path_external)
    raw_file = OtherPath(parameters.res_file_path)

    print(f"{cellpy_file=} :: {type(cellpy_file)=}")
    print(f"{raw_file=} :: {type(raw_file)=}")
    print(f"{cellpy_file.exists()=}")
    print(f"{raw_file.exists()=}")

    check = c.check_file_ids(rawfiles=raw_file, cellpyfile=cellpy_file)
    assert not check


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
    cellpy_data_instance, cycle, step, expected_type, expected_info, parameters
):
    cellpy_data_instance.from_raw(parameters.res_file_path)
    cellpy_data_instance.mass = 1.0
    file_name = parameters.short_step_table_file_path
    assert os.path.isfile(file_name)
    cellpy_data_instance.load_step_specifications(file_name, short=True)
    step_table = cellpy_data_instance.data.steps
    t = step_table.loc[
        (step_table.cycle == cycle) & (step_table.step == step), "type"
    ].values[0]
    assert t == expected_type
    i = step_table.loc[
        (step_table.cycle == cycle) & (step_table.step == step), "info"
    ].values[0]
    assert str(i) == expected_info


def test_pack_meta_convert2fid_table(parameters):
    import collections

    from cellpy import cellreader
    from cellpy import prms

    import pandas as pd

    raw_file = OtherPath(parameters.res_file_path)
    c = cellpy.get(raw_file)
    data = c.data
    fid_table = c._convert2fid_table(data)
    assert isinstance(fid_table, collections.OrderedDict)
    assert len(fid_table) == 9
    assert fid_table["raw_data_name"][0] == raw_file.name


def test_extract_fids_from_cellpy_file(parameters, tmp_path):
    from cellpy import cellreader
    from cellpy import prms

    import pandas as pd

    fid_dir = prms._cellpyfile_fid
    parent_level = prms._cellpyfile_root

    cellpy_file = OtherPath(parameters.cellpy_file_path)

    c = cellreader.CellpyCell()
    with pd.HDFStore(cellpy_file) as store:
        fid_table, fid_table_selected = c._extract_fids_from_cellpy_file(
            fid_dir, parent_level, store
        )

    raw_file = OtherPath(parameters.res_file_path)
    new_cellpy_file_path = tmp_path / cellpy_file.name
    c0 = cellpy.get(raw_file)
    c0.save(new_cellpy_file_path)

    fids0 = c0.data.raw_data_files

    with pd.HDFStore(new_cellpy_file_path) as store:
        fid_table2, fid_table_selected2 = c._extract_fids_from_cellpy_file(
            fid_dir, parent_level, store
        )
    assert fid_table["raw_data_name"][0] == fid_table2["raw_data_name"][0]
    assert fid_table2["raw_data_name"][0] == fids0[0].name


@pytest.mark.slowtest
def test_load_step_specs(cellpy_data_instance, parameters):
    cellpy_data_instance.from_raw(parameters.res_file_path)
    cellpy_data_instance.set_mass(1.0)
    file_name = parameters.step_table_file_path
    assert os.path.isfile(file_name)
    cellpy_data_instance.load_step_specifications(file_name)
    step_table = cellpy_data_instance.data.steps
    t = step_table.loc[(step_table.cycle == 1) & (step_table.step == 8), "type"].values[
        0
    ]
    assert t == "ocvrlx_down"


def test_load_arbin_res_aux_single(cellpy_data_instance, parameters):
    cellpy_data_instance.from_raw(parameters.res_file_path4)
    assert "aux_0_u_C" in cellpy_data_instance.data.raw.columns
    assert "aux_d_0_dt_u_dC_dt" in cellpy_data_instance.data.raw.columns
    assert cellpy_data_instance.data.raw.size == 195345


def test_load_arbin_res_aux_multiple(cellpy_data_instance, parameters):
    cellpy_data_instance.from_raw(parameters.res_file_path3)
    assert "aux_0_u_V" in cellpy_data_instance.data.raw.columns
    assert "aux_11_u_V" in cellpy_data_instance.data.raw.columns
    assert cellpy_data_instance.data.raw.size == 134976


def test_from_raw_local(cellpy_data_instance, parameters):
    cellpy_data_instance.from_raw(parameters.res_file_path)
    cellpy_data_instance.make_summary()
    data_point = 1457
    step_time = 1500.05
    sum_discharge_time = 362198.12
    my_test = cellpy_data_instance.data
    summary = my_test.summary
    print(summary.head().T)
    assert my_test.summary.loc[1, "data_point"] == data_point
    assert step_time == pytest.approx(my_test.raw.loc[5, "step_time"], 0.1)


def test_make_step_table(cellpy_data_instance, parameters):
    cellpy_data_instance.from_raw(parameters.res_file_path)
    cellpy_data_instance.mass = 1.0
    cellpy_data_instance.make_step_table()


def test_make_new_step_table(cellpy_data_instance, parameters):
    cellpy_data_instance.from_raw(parameters.res_file_path)
    cellpy_data_instance.mass = 1.0
    cellpy_data_instance.make_step_table(profiling=True)
    assert len(cellpy_data_instance.data.steps) == 103


def test_make_step_table_all_steps(cellpy_data_instance, parameters):
    # need a new test data-file for GITT
    cellpy_data_instance.from_raw(parameters.res_file_path)
    cellpy_data_instance.mass = 1.0
    cellpy_data_instance.make_step_table(profiling=True, usteps=True)
    assert len(cellpy_data_instance.data.steps) == 103


def test_make_step_table_no_rate(cellpy_data_instance, parameters):
    cellpy_data_instance.from_raw(parameters.res_file_path)
    cellpy_data_instance.mass = 1.0
    cellpy_data_instance.make_step_table(profiling=True, add_c_rate=False)
    assert "rate_avr" not in cellpy_data_instance.data.steps.columns


def test_make_step_table_skip_steps(cellpy_data_instance, parameters):
    cellpy_data_instance.from_raw(parameters.res_file_path)
    cellpy_data_instance.mass = 1.0
    cellpy_data_instance.make_step_table(profiling=True, skip_steps=[1, 10])
    print(cellpy_data_instance.data.steps)
    assert len(cellpy_data_instance.data.steps) == 87


def test_make_summary(cellpy_data_instance, parameters):
    cellpy_data_instance.from_raw(parameters.res_file_path)
    cellpy_data_instance.mass = 1.0
    cellpy_data_instance.make_summary()
    s2 = cellpy_data_instance.data.summary
    s3 = cellpy_data_instance.data.summary
    assert s2.columns.tolist() == s3.columns.tolist()
    assert s2.iloc[:, 3].size == 18


def test_v6(parameters):
    # c = cellpy.get(logging_mode="DEBUG", testing=True)
    c2 = cellpy.get(parameters.cellpy_file_path_v6, logging_mode="DEBUG", testing=True)
    # c.load(parameters.cellpy_file_path_v6)


def test_get_step_number_usteps(gitt_datasett):
    step_numbers_01 = gitt_datasett.get_step_numbers(
        steptype="charge",
        cycle_number=4,
    )

    gitt_datasett.make_step_table(
        usteps=True,
    )

    step_numbers_02 = gitt_datasett.get_step_numbers(
        steptype="charge",
        cycle_number=4,
        usteps=True,
    )
    assert len(step_numbers_01[4]) < len(step_numbers_02[4])
    assert len(step_numbers_01[4]) == 1
    assert len(step_numbers_02[4]) == 92


def test_get_ccap_usteps(gitt_datasett):
    gitt_datasett.make_step_table(
        usteps=True,
    )
    df = gitt_datasett.get_ccap(cycle=4, usteps=True)
    assert df.shape == (3104, 2)


def test_sget_timestamp_usteps(gitt_datasett):
    gitt_datasett.make_step_table(
        usteps=True,
    )
    df = gitt_datasett.sget_timestamp(cycle=4, step=2)
    assert df.shape == (3104,)


def test_get_cap_usteps(gitt_datasett):
    df0 = gitt_datasett.get_cap(cycle=4)
    assert df0.shape == (7592, 2)
    df0 = gitt_datasett.get_cap(cycle=4, usteps=False)
    assert df0.shape == (7592, 2)

    gitt_datasett.make_step_table(
        usteps=True,
    )
    df = gitt_datasett.get_cap(cycle=4)
    assert df.shape == (7592, 2)
    df = gitt_datasett.get_cap(cycle=4, usteps=True)
    assert df.shape == (7592, 2)


def test_make_summary_new_version(parameters):
    c_raw = cellpy.get(logging_mode="DEBUG", testing=True)
    c_raw.from_raw(parameters.res_file_path)
    c_raw.mass = 1.0
    c_raw.make_summary()

    s1 = c_raw.data.summary
    c_h5 = cellpy.get(logging_mode="DEBUG", testing=True)
    c_h5.load(parameters.cellpy_file_path_v6)
    s2 = c_h5.data.summary

    print()
    print(80 * "=")
    print("FROM RAW:")
    print(s1.columns)
    print("FROM H5:")
    print(s2.columns)


def test_select_without(rate_dataset):
    """Test the _select_without method for filtering and modifying cell cycling data.

    This test verifies that:
    1. The method returns correct data when no exclusions are specified
    2. It properly excludes specified step types
    3. It properly excludes specified steps
    4. It correctly adjusts the data values by subtracting excluded step contributions
    5. It handles NaN values appropriately
    """

    print("\n=== TEST SELECT WITHOUT ===")
    # Test 1: No exclusions
    result1 = rate_dataset._select_without()
    print("\nResult 1 (no exclusions):")
    print(f"Number of rows: {len(result1)}")
    assert not result1.empty
    assert len(result1) > 0

    # Test 2: non-cv
    exclude_types = ["cv_"]
    result2 = rate_dataset._select_without(exclude_types=exclude_types)
    print("\nResult 2 (exclude charge):")
    print(f"Number of rows: {len(result2)}")
    assert not result2.empty
    assert len(result2) > 0

    # Test 3: only-cv
    exclude_types = ["charge", "discharge"]
    result2 = rate_dataset._select_without(exclude_types=exclude_types)
    print("\nResult 3 (exclude charge):")
    print(f"Number of rows: {len(result2)}")
    assert not result2.empty
    assert len(result2) > 0

    # Test 3: Exclude specific steps
    result3 = rate_dataset._select_without(exclude_steps=[1, 2])
    assert not result3.empty
    assert len(result3) > 0

    # Test 4: Exclude both types and steps
    result4 = rate_dataset._select_without(exclude_types="charge", exclude_steps=[1, 2])
    assert not result4.empty
    assert len(result4) > 0

    # Test 5: Verify data adjustments
    # Get original data for a cycle
    cycle = 1
    original_data = rate_dataset.data.raw[rate_dataset.data.raw.cycle_index == cycle]

    # Get data with exclusions
    excluded_data = rate_dataset._select_without(exclude_types="charge")
    excluded_cycle_data = excluded_data[excluded_data.cycle_index == cycle]

    # Verify that the data has been adjusted
    assert not original_data.equals(excluded_cycle_data)

    # Test 6: NaN handling
    result6 = rate_dataset._select_without(replace_nan=True)
    assert result6.isna().sum().sum() == 0  # No NaN values when replace_nan=True

    result7 = rate_dataset._select_without(replace_nan=False)
    # We don't assert anything about NaN values here as they might or might not exist
    # depending on the data


def test_summary_from_cellpyfile(parameters):
    c_cellpy = cellpy.get(testing=True)
    c_cellpy.load(parameters.cellpy_file_path)
    s1 = c_cellpy.data.summary
    mass = c_cellpy.get_mass()
    c_cellpy.mass = mass
    c_cellpy.make_summary(find_ir=True, find_end_voltage=True)
    s2 = c_cellpy.data.summary

    # TODO: this might break when updating cellpy format (should probably remove it):
    # assert sorted(s1.columns.tolist()) == sorted(s2.columns.tolist())
    assert s2.iloc[:, 3].size == 18


def test_load_cellpyfile(cellpy_data_instance, parameters):
    cellpy_data_instance.load(parameters.cellpy_file_path)
    cycle_number = 1
    data_point = 1457
    step_time = 1500.05
    sum_test_time = 9301719.457
    my_test = cellpy_data_instance.data
    unique_cycles = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18]
    unique_cycles_read = my_test.steps.loc[:, "cycle"].unique()
    assert any(map(lambda v: v in unique_cycles_read, unique_cycles))
    assert my_test.summary.loc[cycle_number, "data_point"] == data_point
    assert step_time == pytest.approx(my_test.raw.loc[5, "step_time"], 0.1)
    assert sum_test_time == pytest.approx(
        my_test.summary.loc[:, "test_time"].sum(), 0.1
    )


def test_get_current_voltage(dataset):
    v = dataset.get_voltage(cycle=5)
    assert len(v) == 498
    c = dataset.get_current(cycle=5)
    assert len(c) == 498
    c_all = dataset.get_current()  # pd.DataFrame
    c_all2 = dataset.get_current(as_frame=False)  # list of numpy arrays


def test_get_capacity(dataset):
    cc, vcc = dataset.get_ccap(cycle=5, as_frame=False)
    assert len(cc) == len(vcc)
    assert len(cc) == 214
    dc, vdc = dataset.get_dcap(cycle=5, as_frame=False)
    assert len(dc) == len(vdc)
    assert len(dc) == 224
    df = dataset.get_cap(cycle=5)  # new: returns dataframe as default
    assert len(df) == 438


def test_save_cellpyfile_with_extension(cellpy_data_instance, parameters):
    cellpy_data_instance.from_raw(parameters.res_file_path)
    cellpy_data_instance.make_summary(find_ir=True)
    cellpy_data_instance.make_step_table()
    tmp_file = next(tempfile._get_candidate_names()) + ".h5"
    cellpy_data_instance.save(tmp_file)
    assert os.path.isfile(tmp_file)
    os.remove(tmp_file)
    assert not os.path.isfile(tmp_file)


def test_save_cellpyfile_auto_extension(cellpy_data_instance, parameters):
    cellpy_data_instance.from_raw(parameters.res_file_path)
    cellpy_data_instance.make_summary(find_ir=True)
    cellpy_data_instance.make_step_table()
    tmp_file = next(tempfile._get_candidate_names())
    cellpy_data_instance.save(tmp_file)
    assert os.path.isfile(tmp_file + ".h5")
    os.remove(tmp_file + ".h5")
    assert not os.path.isfile(tmp_file + ".h5")


def test_save_cellpyfile_auto_extension_pathlib(cellpy_data_instance, parameters):
    cellpy_data_instance.from_raw(parameters.res_file_path)
    cellpy_data_instance.make_summary(find_ir=True)
    cellpy_data_instance.make_step_table()
    tmp_file = pathlib.Path(next(tempfile._get_candidate_names()))
    cellpy_data_instance.save(tmp_file)
    tmp_file = tmp_file.with_suffix(".h5")
    assert tmp_file.is_file()
    os.remove(tmp_file)
    assert not tmp_file.is_file()


def test_save_cvs(cellpy_data_instance, parameters):
    cellpy_data_instance.from_raw(parameters.res_file_path)
    cellpy_data_instance.make_summary(find_ir=True)
    cellpy_data_instance.make_step_table()
    temp_dir = tempfile.mkdtemp()
    cellpy_data_instance.to_csv(datadir=temp_dir)
    shutil.rmtree(temp_dir)
    # cellpy_data_instance.save(tmp_file)
    # assert os.path.isfile(tmp_file)
    # os.remove(tmp_file)
    # assert not os.path.isfile(tmp_file)


def test_save_excel(cellpy_data_instance, parameters):
    cellpy_data_instance.from_raw(parameters.res_file_path)
    cellpy_data_instance.make_summary(find_ir=True)
    cellpy_data_instance.make_step_table()
    temp_dir = pathlib.Path(tempfile.mkdtemp())
    filename = temp_dir / "test.xlsx"
    cellpy_data_instance.to_excel(
        filename=filename,
        cycles=None,
        raw=False,
        steps=True,
        nice=True,
        get_cap_kwargs=None,
        to_excel_kwargs=None,
    )
    shutil.rmtree(temp_dir)
    # cellpy_data_instance.save(tmp_file)
    # assert os.path.isfile(tmp_file)
    # os.remove(tmp_file)
    # assert not os.path.isfile(tmp_file)


def test_str_cellpy_data_object(dataset):
    assert str(dataset.data).find("silicon") >= 0
    assert str(dataset.data).find("rosenborg") < 0


def test_check_cellpy_file(cellpy_data_instance, parameters):
    file_name = parameters.cellpy_file_path
    ids = cellpy_data_instance._check_cellpy_file(file_name)


def test_cellpyfile_roundtrip(tmp_path, parameters):
    from cellpy import cellreader

    cellpy_file_name = (
        pathlib.Path(tmp_path) / pathlib.Path(parameters.cellpy_file_path).name
    )
    cdi = cellreader.CellpyCell()

    # create a cellpy file from the res-file
    cdi.from_raw(parameters.res_file_path)
    cdi.mass = 1.0
    cdi.make_summary(find_ir=True, find_end_voltage=True)
    cdi.save(cellpy_file_name)

    # load the cellpy file
    cdi = cellreader.CellpyCell()
    cdi.load(cellpy_file_name)
    cdi.make_step_table()
    cdi.make_summary(find_ir=True, find_end_voltage=True)


def test_load_custom_default(cellpy_data_instance, parameters):
    # uses custom.py loader
    from cellpy import prms

    s_headers = get_headers_summary()
    file_name = parameters.custom_file_paths
    instrument_file = parameters.custom_instrument_definitions_file
    # implement this also:
    # prms.Instruments.custom_instrument_definitions_file = instrument_file
    cellpy_data_instance.set_instrument("custom", instrument_file=instrument_file)
    cellpy_data_instance.from_raw(file_name)
    cellpy_data_instance.make_step_table()
    cellpy_data_instance.make_summary()
    summary = cellpy_data_instance.data.summary
    val = summary.loc[2, s_headers.shifted_discharge_capacity]
    # TODO: this breaks (gives 711 instead of 593)
    # assert 593.031 == pytest.approx(val, 0.1)


def test_get_custom_default(parameters):
    # uses custom.py loader
    from cellpy import prms
    import cellpy

    s_headers = get_headers_summary()
    file_name = parameters.custom_file_paths
    instrument_file = parameters.custom_instrument_definitions_file

    c = cellpy.get(file_name, instrument="custom", instrument_file=instrument_file)

    summary = c.data.summary
    val = summary.loc[2, s_headers.shifted_discharge_capacity]
    # TODO: this breaks (gives 711 instead of 593)
    # assert 593.031 == pytest.approx(val, 0.1)


def test_interpolate_y_on_x_per_monotonic_segments_preserves_taper_steps():
    """Interpolation with multiple steps (e.g. CC + taper) preserves segments (issue 307)."""
    import pandas as pd

    # CC-like segment (V increasing) then taper (V constant, capacity increasing)
    df = pd.DataFrame({
        "voltage": [3.0, 3.5, 4.0, 4.0, 4.0, 4.2],
        "capacity": [0.0, 50.0, 100.0, 120.0, 140.0, 150.0],
    })
    out = cellpy.readers.core.interpolate_y_on_x_per_monotonic_segments(
        df, x="voltage", y="capacity", number_of_points=5, direction=1
    )
    assert not out.empty
    # Should have segment 1 (3.0-4.0) interpolated + segment 2 (constant 4.0) kept
    assert out["voltage"].min() == 3.0
    assert out["voltage"].max() == 4.2
    # Constant-voltage segment should be present (4.0, 120-140)
    at_4 = out[out["voltage"] == 4.0]
    assert len(at_4) >= 2
    assert out["capacity"].min() <= 0.0
    assert out["capacity"].max() >= 150.0


def test_interpolate_y_on_x_per_monotonic_segments_max_segments_fallback():
    """When segment count exceeds max_segments, return df unchanged (avoid slow/noisy path)."""
    import pandas as pd

    # Noisy x: many small reversals -> many segments
    df = pd.DataFrame({
        "voltage": [3.0, 3.1, 3.05, 3.15, 3.1, 3.2] * 20,  # 120 points, many segments
        "capacity": range(120),
    })
    out = cellpy.readers.core.interpolate_y_on_x_per_monotonic_segments(
        df, x="voltage", y="capacity", number_of_points=5, direction=1, max_segments=10
    )
    # Should return unchanged (same length as input)
    assert out is df or (out.shape == df.shape and (out.values == df.values).all())


def test_group_by_interpolate(dataset):
    data = dataset.data.raw
    interpolated_data1 = cellpy.readers.core.group_by_interpolate(data)
    interpolated_data2 = cellpy.readers.core.group_by_interpolate(data, tidy=True)
    interpolated_data3 = cellpy.readers.core.group_by_interpolate(
        data, individual_x_cols=True
    )


def test_get(parameters):
    c_h5 = cellpy.get(parameters.cellpy_file_path, testing=True)
    c_res = cellpy.get(
        parameters.res_file_path, instrument="arbin_res", mass=0.045, testing=True
    )


def test_get_advanced(parameters):
    c_many = cellpy.get(
        [parameters.res_file_path, parameters.res_file_path2],
        logging_mode="DEBUG",
        mass=0.035,
        testing=True,
    )


@pytest.mark.skip(reason="only run locally")
def test_get_arbin_res_mdbtools(parameters):
    from cellpy import prms

    prms.Instruments.Arbin.use_subprocess = True
    prms.Instruments.Arbin.sub_process_path = (
        r"C:\scripting\cellpy_utilities\cellpy_utils\mdbtools-win\mdb-export.exe"
    )
    c = cellpy.get(
        parameters.res_file_path, instrument="arbin_res", testing=True, mass=0.035
    )
    prms.Instruments.Arbin.use_subprocess = False


@pytest.mark.skip(reason="only run locally")
def test_get_arbin_res_mdbtools_short_cut(parameters):
    from cellpy import prms

    sub_process_path = (
        r"C:\scripting\cellpy_utilities\cellpy_utils\mdbtools-win\mdb-export.exe"
    )
    prms._set_arbin_res_subprocess_exporter(sub_process_path=sub_process_path)
    c = cellpy.get(
        parameters.res_file_path, instrument="arbin_res", testing=True, mass=0.035
    )
    prms.Instruments.Arbin.use_subprocess = False
    assert c.data.summary.shape == (18, 61)


def test_get_empty():
    c_empty = cellpy.get(testing=True)


@pytest.mark.parametrize("val,validated", [(2.3, None), (2.3, True)])
def test_set_total_mass(dataset, val, validated):
    if validated is not False:
        dataset.tot_mass = val
    assert dataset.data.tot_mass == 2.3


@pytest.mark.parametrize(
    "val,validated",
    [
        (372.3, None),
        (372.3, True),
        pytest.param(372.5, None, marks=pytest.mark.xfail),
    ],
)
def test_set_nominal_capacity(dataset, val, validated):
    if validated is not False:
        dataset.nom_cap = val
    assert dataset.data.nom_cap == 372.3


@pytest.mark.xfail
@pytest.mark.filterwarnings("error")
def test_deprecations(dataset):
    dataset._check_file_type("my_file.res")


@pytest.mark.parametrize(
    "raw_file,cellpy_file",
    [
        ("raw", None),
        ("cellpy", None),
        ("raw", "cellpy"),
        (None, "cellpy"),
    ],
)
def test_loadcell_to_get_post(parameters, cellpy_file, raw_file):
    _raw_file = parameters.res_file_path
    _cellpy_file = parameters.cellpy_file_path

    if raw_file == "raw":
        raw_file = _raw_file
    if raw_file == "cellpy":
        raw_file = _cellpy_file

    if cellpy_file == "raw":
        raw_file = _raw_file
    if cellpy_file == "cellpy":
        raw_file = _cellpy_file

    cellpy.get(
        raw_file,
        cellpy_file=cellpy_file,
        # mass=1.2,
        logging_mode="DEBUG",
        testing=True,
    )


# TODO: fix this so that it does not globally alter the units
#   for other tests:
def test_cellpy_get_update_units(parameters):
    units = {"charge": "Ah"}
    raw_file = parameters.res_file_path
    c1 = cellpy.get(raw_file, logging_mode="DEBUG", testing=True)
    cellpy_unit_charge = c1.cellpy_units.charge
    units_old = {"charge": cellpy_unit_charge}
    c2 = cellpy.get(raw_file, units=units, logging_mode="DEBUG", testing=True)
    sc1 = c1.data.summary.charge_capacity_gravimetric
    sc2 = c2.data.summary.charge_capacity_gravimetric
    # Remark! This will break if we in the future decide to change
    #    the default cellpy_unit for charge to something else than mAh:
    assert sc1.iloc[0] == pytest.approx(1000 * sc2.iloc[0], rel=1e-3)
    c3 = cellpy.get(raw_file, units=units_old, logging_mode="DEBUG", testing=True)
    sc3 = c3.data.summary.charge_capacity_gravimetric
    assert sc1.iloc[0] == pytest.approx(sc3.iloc[0], rel=1e-3)


@pytest.mark.parametrize(
    "instrument_str, expected_instrument, expected_inst_file, expected_model, instrument_file, model",
    [
        ("arbin_res", "arbin_res", None, None, None, None),
        ("maccor_txt::some_file", "maccor_txt", "some_file", None, None, None),
        ("maccor_txt::model=some_model", "maccor_txt", None, "some_model", None, None),
        (
            "maccor_txt::model=some_model",
            "maccor_txt",
            "some_file.yml",
            "some_model",
            "some_file.yml",
            None,
        ),
        (
            "maccor_txt",
            "maccor_txt",
            "some_file.yml",
            "some_model",
            "some_file.yml",
            "some_model",
        ),
    ],
)
def test_instrument_str_splitter(
    instrument_str,
    expected_instrument,
    expected_inst_file,
    expected_model,
    instrument_file,
    model,
):
    from cellpy.readers import cellreader

    c = cellreader.CellpyCell()
    instrument2, inst_file2, model2, kwargs = c.set_instrument(
        instrument_str, instrument_file=instrument_file, model=model, unit_test=True
    )
    assert instrument2 == expected_instrument
    assert inst_file2 == expected_inst_file
    assert model2 == expected_model
