import pytest
import logging
import pandas as pd
from cellpy import log
from cellpy.utils import ica
from . import fdv
from cellpy.exceptions import NullData

# import warnings
# warnings.simplefilter("ignore", FutureWarning)
# warnings.simplefilter("error", FutureWarning)

# note! FutureWarning in converter.pre_process_data()
#    scipy/signal/_savitzky_golay.py:175: in _fit_edge
#    FutureWarning: Using a non-tuple sequence for multidimensional
#      indexing is deprecated

log.setup_logging(default_level=logging.DEBUG)


@pytest.fixture
def cellpy_data_instance():
    from cellpy import cellreader
    return cellreader.CellpyData()


@pytest.fixture
def dataset():
    from cellpy import cellreader
    d = cellreader.CellpyData()
    d.load(fdv.cellpy_file_path)
    return d


def test_ica_converter(dataset):
    # warnings.simplefilter("error", FutureWarning)
    list_of_cycles = dataset.get_cycle_numbers()
    number_of_cycles = len(list_of_cycles)
    logging.debug(f"you have {number_of_cycles} cycles")
    cycle = 5
    logging.debug(f"looking at cycle {cycle}")
    capacity, voltage = dataset.get_ccap(cycle)
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


def test_ica_value_bounds():
    x = [1, 2, 3, 4]
    m1, m2 = ica.value_bounds(x)
    assert m1 == 1
    assert m2 == 4


def test_ica_dqdv_cycles(dataset):
    cycles = dataset.get_cap(
        method="forth-and-forth",
        categorical_column=True,
        label_cycle_number=True,
    )
    dQdV = ica.dqdv_cycles(cycles)

