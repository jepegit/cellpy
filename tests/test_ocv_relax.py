import pytest
import logging
from cellpy import log
from cellpy.utils import ocv_rlx
from . import fdv

log.setup_logging(default_level=logging.DEBUG)


@pytest.fixture
def dataset():
    from cellpy import cellreader

    d = cellreader.CellpyData()
    d.load(fdv.cellpy_file_path)
    return d


@pytest.mark.parametrize(
    "variable,value",
    [
        ("r0", 12.15126),
        ("r1", 15.29991),
        ("ir", 19.36777),
        ("c1", 48.06680),
        ("c0", 7.41526),
        ("ocv", 0.096818),
    ],
)
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
    ocv_fit.run_fitting(direction="up")


def test_select_ocv_points(dataset):
    out = ocv_rlx.select_ocv_points(dataset)
    # print()
    # print(" ocv rlx points ".center(80, "="))
    # print(" all defaults ".center(80, "-"))
    # print(out.head())

    out = ocv_rlx.select_ocv_points(dataset, relative_voltage=True)
    # print(" relative voltage ".center(80, "-"))
    # print(out.head())

    out = ocv_rlx.select_ocv_points(dataset, number_of_points=1)
    # print(" seven points ".center(80, "-"))
    # print(out.head())

    out = ocv_rlx.select_ocv_points(dataset, report_times=True)
    # print(" report times ".center(80, "-"))
    # print(out.head())

    out = ocv_rlx.select_ocv_points(dataset, selection_method="fixed_times")
    # print(" fixed time method ".center(80, "-"))
    # print(out.head())
