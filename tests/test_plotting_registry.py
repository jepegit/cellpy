"""Unit tests for the PlotFamily registry (#636)."""

from __future__ import annotations

import pytest

from cellpy.plotting import AxisSpec, FigureSpec, PanelSpec, PlotFamily, families
from cellpy.plotting import _register_family, get_family
from cellpy.plotting import registry as plot_registry
from cellpy.parameters.internal_settings import get_headers_summary
from tests.figure_spec_support import SUMMARY_FAMILIES

# Contract menu from the pre-registry `_create_col_info` table / figure oracle.
# `SUMMARY_FAMILIES` is derived from the registry; this constant is the check
# that the registry still exposes exactly those names in that order.
EXPECTED_SUMMARY_FAMILIES = (
    "voltages",
    "capacities",
    "capacities_gravimetric",
    "capacities_areal",
    "capacities_absolute",
    "capacities_gravimetric_split_constant_voltage",
    "capacities_areal_split_constant_voltage",
    "capacities_gravimetric_coulombic_efficiency",
    "capacities_areal_coulombic_efficiency",
    "capacities_absolute_coulombic_efficiency",
    "capacities_gravimetric_with_rate",
    "capacities_areal_with_rate",
    "capacities_absolute_with_rate",
    "fullcell_standard_gravimetric",
    "fullcell_standard_areal",
    "fullcell_standard_absolute",
    "fullcell_standard_cumloss_gravimetric",
    "fullcell_standard_cumloss_areal",
    "fullcell_standard_cumloss_absolute",
    "fullcell_standard_dev",
)


@pytest.mark.essential
def test_builtin_families_match_oracle_menu():
    names = tuple(name for name, _ in families(entry_point="summary_plot"))
    assert names == EXPECTED_SUMMARY_FAMILIES
    assert SUMMARY_FAMILIES == EXPECTED_SUMMARY_FAMILIES
    # Stage 2 (#646): cycles is registered but is not a summary_plot(y=) name.
    assert ("cycles", "Voltage vs capacity by cycle") in families(
        entry_point="cycles_plot"
    )
    assert "cycles" not in SUMMARY_FAMILIES


@pytest.mark.essential
def test_get_returns_family_and_resolves_columns():
    family = get_family("capacities_gravimetric_coulombic_efficiency")
    assert family.name == "capacities_gravimetric_coulombic_efficiency"
    assert family.mode == "gravimetric"
    hdr = get_headers_summary()
    columns = family.columns(hdr)
    assert hdr.coulombic_efficiency in columns
    assert all(isinstance(col, str) for col in columns)


@pytest.mark.essential
def test_unknown_family_lists_known_names():
    with pytest.raises(ValueError, match="unknown plot family") as caught:
        get_family("not_a_real_family")
    message = str(caught.value)
    assert "voltages" in message
    assert "capacities_gravimetric" in message


@pytest.mark.essential
def test_register_family_round_trip():
    name = "_test_only_family_636"
    assert name not in dict(families())

    family = PlotFamily(
        name=name,
        description="temporary test family",
        column_builder=lambda hdr: ["charge_capacity"],
        mode="gravimetric",
    )
    _register_family(family)
    try:
        assert get_family(name) is family
        assert (name, "temporary test family") in families()
    finally:
        plot_registry._FAMILIES.pop(name, None)


@pytest.mark.essential
def test_spec_dataclasses_are_frozen():
    axis = AxisSpec(label="Cycle")
    panel = PanelSpec(columns=("a", "b"), y_axis=axis)
    figure = FigureSpec(panels=(panel,), title="demo")
    assert figure.panels[0].columns == ("a", "b")
    with pytest.raises(Exception):
        figure.title = "nope"  # type: ignore[misc]
