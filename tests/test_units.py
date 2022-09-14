import logging

import pytest

from cellpy import log, prms
from cellpy.exceptions import NoCellFound

log.setup_logging(default_level=logging.DEBUG, testing=True)


def test_that_raw_units_are_not_available_without_a_cell(cellpy_data_instance):
    with pytest.raises(NoCellFound):
        print(f"{cellpy_data_instance.raw_units=}")


def test_set_units(cellpy_data_instance):
    cellpy_data_instance.output_units["charge"] = 1.0
    cellpy_data_instance.cellpy_units["charge"] = 0.001

    assert cellpy_data_instance.output_units["charge"] == 1.0
    assert cellpy_data_instance.cellpy_units["charge"] == 0.001


# TODO: this might break when updating cellpy format - fix it using HeadersSummary etc.:
def test_set_cellpy_unit_and_use(dataset):
    cellpy_unit_charge = dataset.cellpy_units["charge"]
    initial_value = dataset.cell.summary["discharge_capacity_u_mAh_g"].values[10]

    dataset.cellpy_units["charge"] = 1000 * cellpy_unit_charge
    dataset.make_summary()
    new_value = dataset.cell.summary["discharge_capacity_u_mAh_g"].values[10]

    assert new_value == pytest.approx(initial_value / 1000, 0.0001)


def test_set_output_unit_and_use(dataset):
    cellpy_unit_charge = dataset.cellpy_units["charge"]
    initial_value = dataset.cell.summary["discharge_capacity_u_mAh_g"].values[10]

    dataset.output_units["charge"] = 1000 * cellpy_unit_charge

    # TODO: implement something like this when proper tweaking of output is implemented:

    # dataset.make_summary()
    # new_value = dataset.cell.summary["discharge_capacity_u_mAh_g"].values[10]
    #
    # assert new_value == pytest.approx(initial_value/1000, 0.0001)
