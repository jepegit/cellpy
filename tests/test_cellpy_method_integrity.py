import logging
import shutil
import tempfile

import pytest

from cellpy import get, log, prms

log.setup_logging(default_level=logging.DEBUG, testing=True)


@pytest.fixture
def cellpy_cell(cellpy_data_instance, parameters):
    return cellpy_data_instance.load(parameters.cellpy_file_path)


@pytest.fixture
def neware_cellpy_cell(cellpy_data_instance, parameters):
    return cellpy_data_instance.load(parameters.nw_cellpy_file_path)


# TODO: this cellpy file is not found - fix it!
# @pytest.fixture
# def maccor_cellpy_cell(cellpy_data_instance, parameters):
#     return cellpy_data_instance.load(parameters.mcc_cellpy_file_path)

# TODO: This one is not supported anymore - make method for converting it to v>=5:
# @pytest.fixture
# def cellpy_cell_v4(cellpy_data_instance, parameters):
#     return cellpy_data_instance.load(parameters.cellpy_file_path_v4)


@pytest.fixture
def cellpy_cell_v5(cellpy_data_instance, parameters):
    return cellpy_data_instance.load(parameters.cellpy_file_path_v5)


@pytest.fixture
def cellpy_cell_v6(cellpy_data_instance, parameters):
    return cellpy_data_instance.load(parameters.cellpy_file_path_v6)


@pytest.fixture
def arbin_res_cell(parameters):
    return get(parameters.res_file_path)


@pytest.fixture
def arbin_res_cell2(parameters):
    return get(parameters.res_file_path2)


@pytest.fixture
def arbin_res_cell3(parameters):
    return get(parameters.res_file_path3)


@pytest.fixture
def arbin_res_cell4(parameters):
    return get(parameters.res_file_path4)


@pytest.fixture
def arbin_sql_h5_cell(parameters):
    return get(
        filename=parameters.arbin_sql_h5_path, instrument="arbin_sql_h5", testing=True
    )


@pytest.fixture
def neware_csv_cell(parameters):
    return get(
        filename=parameters.nw_file_path,
        instrument="neware_txt",
        model="UIO",
        mass=2.08,
        testing=True,
    )


@pytest.fixture
def maccor_txt_cell(parameters):
    return get(
        filename=parameters.mcc_file_path, instrument="maccor_txt", testing=True
    )


@pytest.fixture
def pec_txt_cell(parameters):
    return get(
        filename=parameters.pec_file_path, instrument="pec_csv", testing=True
    )


@pytest.fixture
def custom_cell(parameters):
    file_name = parameters.custom_file_paths
    instrument_file = parameters.custom_instrument_definitions_file
    return get(
        filename=file_name, instrument="custom", instrument_file=instrument_file, testing=True
    )


@pytest.mark.skip(reason="only run locally")
def test_cellpy_cells(
    cellpy_cell,
    cellpy_cell_v5,
    cellpy_cell_v6,
    neware_cellpy_cell,
):
    pass


@pytest.mark.skip(reason="only run locally")
def test_main_raw_cells(
    maccor_txt_cell,
    neware_csv_cell,
    arbin_sql_h5_cell,
    arbin_res_cell,
    arbin_res_cell2,
    arbin_res_cell3,
    arbin_res_cell4,
    custom_cell,
):
    pass


@pytest.mark.skip(reason="only run locally")
def test_other_raw_cells(
    pec_txt_cell,
):
    pass


@pytest.mark.parametrize(
    "_c",
    [
        "cellpy_cell_v5",
        "cellpy_cell_v6",
        "neware_cellpy_cell",

    ]
)
def test_total_time_at_low_voltage_from_cellpy_cells(_c, request):
    c = request.getfixturevalue(_c)
    t = c.total_time_at_voltage_level()
    print(f"total time at low voltage: {t} seconds")


@pytest.mark.parametrize(
    "_c",
    [
        "maccor_txt_cell",
        "neware_csv_cell",
        "arbin_sql_h5_cell",
        "arbin_res_cell",
        "arbin_res_cell2",
        "arbin_res_cell3",
        "arbin_res_cell4",
    ]
)
def test_total_time_at_low_voltage_from_raw(_c, request):
    c = request.getfixturevalue(_c)
    t = c.total_time_at_voltage_level()
    print(f"total time at low voltage: {t} seconds")


# TODO: fails! fix it!
# @pytest.mark.parametrize(
#     "_c",
#     [
#         "custom_cell",
#     ]
# )
# def test_total_time_at_low_voltage_from_custom_raw(_c, request):
#     c = request.getfixturevalue(_c)
#     t = c.total_time_at_voltage_level()
#     print(f"total time at low voltage: {t} seconds")


@pytest.mark.parametrize(
    "_c",
    [
        "pec_txt_cell",
    ]
)
def test_total_time_at_low_voltage_from_other_raw(_c, request):
    c = request.getfixturevalue(_c)
    t = c.total_time_at_voltage_level()
    print(f"total time at low voltage: {t} seconds")
