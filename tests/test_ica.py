import logging

import pandas as pd
import pytest

from cellpy import log
from cellpy.exceptions import NullData
from cellpy.utils import ica

# import warnings
# warnings.simplefilter("ignore", FutureWarning)
# warnings.simplefilter("error", FutureWarning)

# note! FutureWarning in converter.pre_process_data()
#    scipy/signal/_savitzky_golay.py:175: in _fit_edge
#    FutureWarning: Using a non-tuple sequence for multidimensional
#      indexing is deprecated

log.setup_logging(default_level=logging.DEBUG, testing=True)


@pytest.fixture
def converter(dataset):
    q, v = dataset.get_ccap(1, as_frame=False)
    o = ica.Converter()
    o.set_data(q, v)
    return o


def test_ica_converter(dataset):
    # warnings.simplefilter("error", FutureWarning)
    list_of_cycles = dataset.get_cycle_numbers()
    number_of_cycles = len(list_of_cycles)
    logging.debug(f"you have {number_of_cycles} cycles")
    cycle = 5
    logging.debug(f"looking at cycle {cycle}")
    capacity, voltage = dataset.get_ccap(cycle, as_frame=False)
    converter = ica.Converter()
    converter.set_data(capacity, voltage)
    converter.inspect_data()
    converter.pre_process_data()
    converter.increment_data()
    converter.post_process_data()


@pytest.mark.xfail(raises=TypeError)
def test_none_data():
    ica.dqdv(None, None)


@pytest.mark.xfail(raises=NullData)
def test_short_data():
    ica.dqdv(pd.Series(), pd.Series())


@pytest.mark.parametrize("cycle", [1, 2, 3, 4, 5, 10])
def test_ica_dqdv(dataset, cycle):
    capacity, voltage = dataset.get_ccap(cycle, as_frame=False)
    ica.dqdv(voltage, capacity)


def test_ica_value_bounds_simple():
    x = [1, 2, 3, 4]
    m1, m2 = ica.value_bounds(x)
    assert m1 == 1
    assert m2 == 4


def test_ica_value_bounds(dataset):
    capacity, voltage = dataset.get_ccap(5, mode="gravimetric", as_frame=False)
    c = ica.value_bounds(capacity)
    v = ica.value_bounds(voltage)
    assert c == pytest.approx((0.001106868, 1535.303235807), 0.0001)
    assert v == pytest.approx((0.15119725465774536, 1.0001134872436523), 0.0001)


def test_ica_index_bounds(dataset):
    capacity, voltage = dataset.get_ccap(5, as_frame=False)
    c = ica.index_bounds(capacity)
    v = ica.index_bounds(voltage)
    assert c == pytest.approx((0.001106868, 1535.303235807), 0.0001)
    assert v == pytest.approx((0.15119725465774536, 1.0001134872436523), 0.0001)


def test_ica_dqdv_cycles(dataset):
    cycles = dataset.get_cap(
        method="forth-and-forth",
        categorical_column=True,
        label_cycle_number=True,
        insert_nan=False,
    )
    dQdV = ica.dqdv_cycles(cycles)


def test_ica_str(dataset):
    o = ica.Converter()
    print(o)


def test_set_data(dataset):
    q, v = dataset.get_ccap(1, as_frame=False)
    data = pd.concat([q, v], axis=1)
    o = ica.Converter()
    o.set_data(data, capacity_label="charge_capacity", voltage_label="voltage")


def test_inspect_data(converter):
    converter.inspect_data(err_est=True, diff_est=True)
    converter.pre_process_data()
    converter.increment_data()
    converter.post_process_data()
    v = converter.voltage_processed
    q = converter.incremental_capacity
    assert len(v) == len(q)
    assert len(v) > 1


def test_pre_process_data_smoothing(converter):
    converter.inspect_data()
    converter.pre_smoothing = True
    converter.pre_process_data()
    converter.increment_data()
    converter.post_process_data()
    v = converter.voltage_processed
    q = converter.incremental_capacity
    assert len(v) == len(q)
    assert len(v) > 1


def test_increment_hist_method(converter):
    converter.inspect_data()
    converter.pre_smoothing = True
    converter.increment_method = "hist"
    converter.pre_process_data()
    converter.increment_data()
    print(len(converter.incremental_capacity))
    print(len(converter.voltage_processed))

    # import matplotlib.pyplot as plt
    # plt.plot(converter.voltage_processed, converter.incremental_capacity)
    # plt.plot(converter.voltage_processed, converter.incremental_capacity)
    # plt.show()


def test_increment_data_smoothing(converter):
    converter.inspect_data()
    converter.pre_process_data()
    converter.smoothing = True
    converter.increment_data()
    converter.post_process_data()
    v = converter.voltage_processed
    q = converter.incremental_capacity
    assert len(v) == len(q)
    assert len(v) > 1


def test_dqdv_frames_split(dataset):
    df_ica_charge, df_ica_discharge = ica.dqdv_frames(dataset, split=True, cycle=2)
    assert df_ica_charge.size == 300
    assert df_ica_discharge.size == 300
    df_ica_charge, df_ica_discharge = ica.dqdv_frames(dataset, split=True)
    assert df_ica_charge.size == 5400
    assert df_ica_discharge.size == 5400
    assert "voltage" in df_ica_charge.columns
    assert "cycle" in df_ica_charge.columns
    assert "dq" in df_ica_charge.columns


def test_dqdv_frames_one_cycle_tidy(dataset):
    df_ica = ica.dqdv_frames(dataset, cycle=2)
    assert "voltage" in df_ica.columns
    assert "cycle" in df_ica.columns
    assert "dq" in df_ica.columns
    assert df_ica.size == 2280


def test_dqdv_frames_multi_cycles_tidy(dataset):
    df_ica = ica.dqdv_frames(dataset)
    assert "voltage" in df_ica.columns
    assert "cycle" in df_ica.columns
    assert "dq" in df_ica.columns
    assert df_ica.size == 26379


def test_dqdv_frames_multi_cycles_wide(dataset):
    df_ica = ica.dqdv_frames(dataset, tidy=False)
    cycles_available = set(dataset.get_cycle_numbers())
    cycles_processed = set(df_ica.columns.get_level_values(0))
    assert cycles_available.issuperset(cycles_processed)
    assert "voltage" in df_ica.columns.get_level_values(1)
    assert "dq" in df_ica.columns.get_level_values(1)
    assert df_ica.size == 37536


# TODO - aulv: this test should be un-commented when hist-method
#  is implemented
# def test_increment_data_hist(converter):
#     converter.inspect_data()
#     converter.pre_process_data()
#     converter.smoothing = True
#     converter.increment_method = "hist"
#     converter.increment_data()
#     converter.post_process_data()
#     v = converter.voltage_processed
#     q = converter.incremental_capacity
#     assert len(v) == len(q)
#     assert len(v) > 1


# missing test: fixed_range in post_process_data
