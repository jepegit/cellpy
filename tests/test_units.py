import logging

import pytest

from cellpy import log, prms
from cellpy.exceptions import NoCellFound
from cellpy.parameters.internal_settings import get_headers_summary

log.setup_logging(default_level=logging.DEBUG, testing=True)


def test_that_raw_units_are_not_available_without_a_cell(cellpy_data_instance):
    with pytest.raises(NoCellFound):
        print(f"{cellpy_data_instance.raw_units=}")


def test_set_units(cellpy_data_instance):
    cellpy_data_instance.output_units["charge"] = 1.0
    cellpy_data_instance.cellpy_units["charge"] = 0.001

    assert cellpy_data_instance.output_units["charge"] == 1.0
    assert cellpy_data_instance.cellpy_units["charge"] == 0.001


def test_set_cellpy_unit_and_use(dataset):
    cellpy_unit_charge = dataset.cellpy_units["charge"]
    s_headers = get_headers_summary()
    initial_value = dataset.cell.summary[s_headers.discharge_capacity].values[10]

    dataset.cellpy_units["charge"] = 1000 * cellpy_unit_charge
    dataset.make_summary()
    new_value = dataset.cell.summary[s_headers.discharge_capacity].values[10]

    assert new_value == pytest.approx(initial_value / 1000, 0.0001)
