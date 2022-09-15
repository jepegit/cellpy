import logging

import pytest

import cellpy.readers.core
from cellpy import log, prms
from cellpy.exceptions import NoCellFound
from cellpy.parameters.internal_settings import get_headers_summary

log.setup_logging(default_level=logging.DEBUG, testing=True)


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ((1.0, 1.0), 1.0),  # (to_unit, from_unit), conversion-factor
        ((1.0, 0.1), 0.1),
        ((0.1, 1.0), 10.0),
        pytest.param((1.0, 0.001), 1.0, marks=pytest.mark.xfail),
    ],
)
def test_get_converter_to_specific(dataset, test_input, expected):
    c = dataset.get_converter_to_specific(
        value=1.0, to_unit=test_input[0], from_unit=test_input[1], mode="gravimetric"
    )
    assert c == expected


def test_get_converter_to_specific_absolute_with_mode(dataset):
    c = dataset.get_converter_to_specific(
        mode="absolute"
    )
    assert c == pytest.approx(1000, 0.0001)


def test_get_converter_to_specific_with_mode(dataset):
    area = 1.57  # cm2
    dataset.cell.active_electrode_area = area
    c = dataset.get_converter_to_specific(
        mode="areal"
    )
    assert c == pytest.approx(1000/area, 0.0001)


# This will only work when defaults are in place:
# def test_get_converter_to_areal_specific(dataset):
#     c = dataset.get_converter_to_specific(
#         mode="areal"
#     )
#     assert c == pytest.approx(1000/dataset.cell.active_electrode_area, 0.0001)


def test_get_converter_to_specific_with_wrong_mode(dataset):
    with pytest.raises(ValueError):
        c = dataset.get_converter_to_specific(
            value=1.0, mode="plasma"
        )


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
