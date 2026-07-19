"""Tests for the unit presentation helpers (#564, unit plan Phase 4).

The expectation table below is the committed contract for the label helpers:
if a label changes, this table changes with it, deliberately.
"""

from __future__ import annotations

import logging

import pytest
from cellpycore.units import CellpyUnits

from cellpy import log
from cellpy.exceptions import UnitsError
from cellpy.units import units_label, with_cellpy_unit

log.setup_logging(default_level=logging.DEBUG, testing=True)


# (physical_property, mode) -> expected label, against the default unit spec.
EXPECTED = {
    ("charge", None): "mAh",
    ("charge", "absolute"): "mAh",
    ("charge", "gravimetric"): "mAh/g",
    ("charge", "areal"): "mAh/cm**2",
    ("charge", "volumetric"): "mAh/cm**3",
    ("voltage", None): "V",
    ("current", None): "A",
    ("time", None): "sec",
    ("mass", None): "mg",
    ("energy", None): "Wh",
    ("energy", "gravimetric"): "Wh/g",
    ("power", None): "W",
    ("area", None): "cm**2",
    ("resistance", None): "ohm",
}


@pytest.mark.essential
@pytest.mark.parametrize("key, expected", sorted(EXPECTED.items(), key=str))
def test_units_label_expectation_table(key, expected):
    physical_property, mode = key
    assert units_label(physical_property, mode) == expected


@pytest.mark.essential
@pytest.mark.parametrize(
    "alias, canonical",
    [
        ("potential", "voltage"),
        ("capacity", "charge"),
        ("charge_capacity", "charge"),
        ("discharge_capacity", "charge"),
    ],
)
def test_property_aliases(alias, canonical):
    # The native schema says "potential" while the unit spec says "voltage";
    # callers should be able to use the vocabulary they already have.
    assert units_label(alias) == units_label(canonical)
    assert units_label(alias, "gravimetric") == units_label(canonical, "gravimetric")


@pytest.mark.essential
def test_units_argument_overrides_the_session_spec():
    custom = CellpyUnits(charge="Ah", specific_gravimetric="kg")
    assert units_label("charge", "gravimetric", units=custom) == "Ah/kg"
    # ... and the session default is untouched by that call.
    assert units_label("charge", "gravimetric") == "mAh/g"


@pytest.mark.essential
def test_with_cellpy_unit_composes_an_axis_label():
    assert with_cellpy_unit("Capacity", "charge", "gravimetric") == "Capacity (mAh/g)"
    assert with_cellpy_unit("Voltage", "voltage") == "Voltage (V)"
    assert with_cellpy_unit("Test Time", "time") == "Test Time (sec)"


@pytest.mark.essential
def test_unknown_property_raises():
    # Fail loudly: a mislabelled axis is worse than a traceback.
    with pytest.raises(UnitsError):
        units_label("not_a_property")


@pytest.mark.essential
def test_unknown_mode_raises():
    with pytest.raises(UnitsError):
        units_label("charge", "sideways")


@pytest.mark.essential
def test_error_names_the_valid_modes():
    with pytest.raises(UnitsError, match="gravimetric"):
        units_label("charge", "sideways")


@pytest.mark.essential
def test_plotutils_capacity_unit_matches_the_helper(dataset):
    """The plotutils wrapper must agree with the helper it now delegates to."""
    from cellpy.utils.plotutils import _get_capacity_unit

    for mode in ("gravimetric", "areal", "absolute", "volumetric"):
        assert _get_capacity_unit(dataset, mode=mode) == units_label(
            "charge", mode, units=dataset.cellpy_units
        )


@pytest.mark.essential
def test_plotutils_capacity_unit_keeps_its_placeholder(dataset):
    """Callers pass a y-spec suffix as the mode, so non-modes must not raise."""
    from cellpy.utils.plotutils import _get_capacity_unit

    assert _get_capacity_unit(dataset, mode="not_a_mode") == "-"
