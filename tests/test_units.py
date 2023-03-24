import logging

import pytest

import cellpy.readers.core
from cellpy import log, prms, Q
from cellpy.exceptions import NoDataFound
from cellpy.parameters.internal_settings import get_headers_summary

log.setup_logging(default_level=logging.DEBUG, testing=True)


def test_with_cellpy_unit(dataset):
    n = dataset.with_cellpy_unit("nom_cap")


def test_to_cellpy_unit_from_cellpy_instance(cellpy_data_instance):
    value = Q(12.2, cellpy_data_instance.cellpy_units["length"])
    expected_new_value = Q(12.2, cellpy_data_instance.cellpy_units["length"]).m
    new_value = cellpy_data_instance.to_cellpy_unit(value, physical_property="length")
    assert new_value == expected_new_value


def test_to_cellpy_unit_from_cellpy_instance_with_cell(dataset):
    value = 12.2
    new_value = dataset.to_cellpy_unit(value, physical_property="length")
    assert (
        new_value
        == Q(12.2, dataset.data.raw_units["length"])
        .to(dataset.cellpy_units["length"])
        .m
    )

    new_value = dataset.to_cellpy_unit(
        f"12.2 {dataset.cellpy_units['length']}", physical_property="length"
    )
    assert new_value == 12.2

    new_value = dataset.to_cellpy_unit(
        (12.2, dataset.data.raw_units["length"]), physical_property="length"
    )
    assert (
        new_value
        == Q(12.2, dataset.data.raw_units["length"])
        .to(dataset.cellpy_units["length"])
        .m
    )


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ((1.0, "gravimetric"), 1),  # (to_unit, from_unit), conversion-factor
        ((1.0, "areal"), 1),
        ((1.0, "absolute"), 1),
        pytest.param((1.0, "other"), 2.0, marks=pytest.mark.xfail),
    ],
)
def test_get_converter_to_specific(dataset, test_input, expected):
    # This test is basically a reimplementation of what it is going to test.
    # Dont think that is a too good and idea.
    raw_unit_charge = dataset.data.raw_units["charge"]
    cellpy_unit_charge = dataset.cellpy_units["charge"]
    value_unit = {
        "gravimetric": dataset.cellpy_units["mass"],
        "areal": dataset.cellpy_units["area"],
        "absolute": None,
    }
    specific_unit = f"specific_{test_input[1]}"
    physical_unit = value_unit[test_input[1]]

    specific_conv = {
        "gravimetric": lambda x: Q(x, physical_unit)
        .to(dataset.cellpy_units[specific_unit])
        .to_reduced_units()
        .m,
        "areal": lambda x: Q(x, physical_unit)
        .to(dataset.cellpy_units[specific_unit])
        .to_reduced_units()
        .m,
        "absolute": lambda x: x,
    }

    conv = (Q(1, raw_unit_charge) / Q(1, cellpy_unit_charge)).to_reduced_units()

    conv = conv.m / specific_conv[test_input[1]](1)

    c = dataset.get_converter_to_specific(
        value=test_input[0],
        mode=test_input[1],
    )
    assert c == conv * expected


def test_nominal_capacity(dataset):
    nom_cap = dataset.data.nom_cap
    mass = 0.47
    nom_cap_specifics = None  # dataset.data._nom_cap_specifics

    absolute_nom_cap = dataset.nominal_capacity_as_absolute(
        nom_cap, mass, nom_cap_specifics
    )
    print(nom_cap)
    print(absolute_nom_cap)


def test_get_converter_to_specific_absolute_with_mode(dataset):
    c = dataset.get_converter_to_specific(mode="absolute")
    assert c == pytest.approx(1000, 0.0001)


def test_get_converter_to_specific_with_mode(dataset):
    area = 1.57  # cm2
    dataset.data.active_electrode_area = area
    c = dataset.get_converter_to_specific(mode="areal")
    assert c == pytest.approx(1000 / area, 0.0001)


# This will only work when defaults are in place:
def test_get_converter_to_areal_specific(dataset):
    area = dataset.data.active_electrode_area
    print(f"{area=}")
    print(f"{dataset.cellpy_units['area']=}")
    print(f"{dataset.data.raw_units['area']=}")
    print(f"{dataset.cellpy_units['specific_areal']=}")
    print(f"{dataset.data.raw_units['specific_areal']=}")

    c = dataset.get_converter_to_specific(mode="areal")
    assert c == pytest.approx(1000 / dataset.data.active_electrode_area, 0.0001)


def test_that_raw_units_are_not_available_without_a_cell(cellpy_data_instance):
    with pytest.raises(NoDataFound):
        print(f"{cellpy_data_instance.raw_units=}")


def test_set_units(cellpy_data_instance):
    cellpy_data_instance.output_units["charge"] = 1.0
    cellpy_data_instance.cellpy_units["charge"] = 0.001

    assert cellpy_data_instance.output_units["charge"] == 1.0
    assert cellpy_data_instance.cellpy_units["charge"] == 0.001


def test_set_cellpy_unit_and_use(dataset):
    s_headers = get_headers_summary()
    h = f"{s_headers.discharge_capacity}_gravimetric"

    dataset.cellpy_units["charge"] = "Ah"
    dataset.make_summary()
    initial_value = dataset.data.summary[h].values[10]

    dataset.cellpy_units["charge"] = "mAh"
    dataset.make_summary()
    new_value = dataset.data.summary[h].values[10]

    assert new_value == pytest.approx(initial_value * 1000, 0.0001)


def test_using_internal_pint_methods():
    from cellpy import ureg, Q

    mass = Q(0.5, "mg")
    area = Q(2.5, "cm**2")
    print(f"mass: {mass}")
    print(f"area: {area}")
    print(ureg.g)
    print(ureg.ohms)
    print(ureg.mAh)


@pytest.mark.parametrize(
    "nom_cap_tuple,expected",
    [
        ((1.0, "mAh/g"), 5.0e-07),
        ((1.0, "mAh/cm**2"), 0.0025),
        ((1.0, "Ah"), 1.0),
    ],
)
def test_pint_nom_cap_conversion(nom_cap_tuple, expected):
    import pint

    ureg = pint.UnitRegistry()
    Q = ureg.Quantity
    nom_cap = Q(*nom_cap_tuple)
    mass = Q(0.5, "mg")
    area = Q(2.5, "cm**2")
    print()
    print(80 * "-")
    print(f"{nom_cap=}")

    if nom_cap.check("[current]*[time]/[mass]"):
        nom_cap_grav = nom_cap
        nom_cap_abs = (nom_cap * mass).to_reduced_units().to("Ah")
        nom_cap_areal = (nom_cap_abs / area).to_reduced_units().to("mAh/cm**2")

    elif nom_cap.check("[current]*[time]/[area]"):
        nom_cap_areal = nom_cap
        nom_cap_abs = (nom_cap * area).to_reduced_units().to("Ah")
        nom_cap_grav = (nom_cap_abs / mass).to_reduced_units().to("mAh/g")

    else:
        nom_cap_abs = nom_cap.to_reduced_units().to("Ah")
        nom_cap_grav = (nom_cap_abs / mass).to_reduced_units().to("mAh/g")
        nom_cap_areal = (nom_cap_abs / area).to_reduced_units().to("mAh/cm**2")

    print(f"{nom_cap_abs=}")
    print(f"{nom_cap_grav=}")
    print(f"{nom_cap_areal=}")
    print(80 * "-")
    assert nom_cap_abs.m == pytest.approx(expected, 0.0001)
