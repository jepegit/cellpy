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


def test_nominal_capacity(dataset):
    nom_cap = dataset.cell.nom_cap
    mass = dataset.cell.mass
    specifics = dataset.cell._nom_cap_specifics

    absolute_nom_cap = dataset._from_specific_nom_cap_to_absolute(
        nom_cap, mass, specifics
    )
    print(nom_cap)
    print(absolute_nom_cap)


def test_get_converter_to_specific_absolute_with_mode(dataset):
    c = dataset.get_converter_to_specific(mode="absolute")
    assert c == pytest.approx(1000, 0.0001)


def test_get_converter_to_specific_with_mode(dataset):
    area = 1.57  # cm2
    dataset.cell.active_electrode_area = area
    c = dataset.get_converter_to_specific(mode="areal")
    assert c == pytest.approx(1000 / area, 0.0001)


# This will only work when defaults are in place:
def test_get_converter_to_areal_specific(dataset):
    c = dataset.get_converter_to_specific(mode="areal")
    assert c == pytest.approx(1000 / dataset.cell.active_electrode_area, 0.0001)


def test_get_converter_to_specific_with_wrong_mode(dataset):
    with pytest.raises(ValueError):
        c = dataset.get_converter_to_specific(value=1.0, mode="plasma")


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
    h = f"{s_headers.discharge_capacity}_gravimetric"
    initial_value = dataset.cell.summary[h].values[10]

    dataset.cellpy_units["charge"] = 1000 * cellpy_unit_charge
    dataset.make_summary()
    new_value = dataset.cell.summary[h].values[10]

    assert new_value == pytest.approx(initial_value / 1000, 0.0001)

#
# @pytest.mark.parametrize(
#     "nom_cap_tuple,expected",
#     [
#         ((1.0, "mAh/g"), 5.0e-07),
#         ((1.0, "mAh/cm**2"), 0.0025),
#         ((1.0, "Ah"), 1.0),
#     ],
# )
# def test_pint_nom_cap_conversion(nom_cap_tuple, expected):
#     import pint
#     ureg = pint.UnitRegistry()
#     Q = ureg.Quantity
#     nom_cap = Q(*nom_cap_tuple)
#     mass = Q(0.5, "mg")
#     area = Q(2.5, "cm**2")
#     print()
#     print(80 * "-")
#     print(f"{nom_cap=}")
#
#     if nom_cap.check('[current]*[time]/[mass]'):
#         nom_cap_grav = nom_cap
#         nom_cap_abs = (nom_cap * mass).to_reduced_units().to("Ah")
#         nom_cap_areal = (nom_cap_abs / area).to_reduced_units().to("mAh/cm**2")
#
#     elif nom_cap.check('[current]*[time]/[area]'):
#         nom_cap_areal = nom_cap
#         nom_cap_abs = (nom_cap * area).to_reduced_units().to("Ah")
#         nom_cap_grav = (nom_cap_abs / mass).to_reduced_units().to("mAh/g")
#
#     else:
#         nom_cap_abs = nom_cap.to_reduced_units().to("Ah")
#         nom_cap_grav = (nom_cap_abs / mass).to_reduced_units().to("mAh/g")
#         nom_cap_areal = (nom_cap_abs / area).to_reduced_units().to("mAh/cm**2")
#
#     print(f"{nom_cap_abs=}")
#     print(f"{nom_cap_grav=}")
#     print(f"{nom_cap_areal=}")
#     print(80 * "-")
#     assert nom_cap_abs.m == pytest.approx(expected, 0.0001)
#
#
#
