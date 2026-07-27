import logging

import pytest

from cellpy import log
from cellpy.utils import ocv_rlx

log.setup_logging(default_level=logging.DEBUG, testing=True)


def test_get_ocv_rlx_for_fitting(dataset):
    import matplotlib.pyplot as plt

    raw = dataset.data.raw
    for h, v in dataset.headers_normal.items():
        print(f"{h}: {v}", end=" -> ")
        if v in raw.columns:
            print("Exists")
        else:
            print("MISSING")
    steps = dataset.data.steps
    hdr_s = dataset.headers_step_table
    n = steps.loc[steps[hdr_s.cycle].isin([1]), :]
    n = n.loc[n[hdr_s.type].str.startswith("ocvrlx_up"), :]
    print(n)
    rlx = dataset.get_ocv(direction="up", cycles=1)
    print(rlx)


@pytest.mark.parametrize(
    "variable,value",
    [
        ("r0", 12.15126),
        # ("r1", 15.29991),
        # ("ir", 19.36777),
        # ("c1", 48.06680),
        # ("c0", 7.41526),
        # ("ocv", 0.096818),
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


def test_multicycle_holds_cell_under_new_name(dataset):
    """#709: the held CellpyCell is ``.cell`` (was the ``self.data.data.steps`` trap)."""
    ocv_fit = ocv_rlx.MultiCycleOcvFit(dataset, [1], circuits=2)
    assert ocv_fit.cell is dataset


def test_multicycle_data_alias_is_deprecated(dataset):
    """`.data` / `set_data` stay as deprecated aliases for `.cell` / `set_cell`."""
    ocv_fit = ocv_rlx.MultiCycleOcvFit(dataset, [1], circuits=2)
    with pytest.warns(DeprecationWarning):
        assert ocv_fit.data is dataset
    ocv_fit.set_cell(dataset)
    assert ocv_fit.cell is dataset
    with pytest.warns(DeprecationWarning):
        ocv_fit.set_data(dataset)
    assert ocv_fit.cell is dataset


def test_select_ocv_points(dataset):
    # 2023-04-05: the test fails on GitHub actions py3.10 (AttributeError: DataFrame has no attribute 'append')
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
