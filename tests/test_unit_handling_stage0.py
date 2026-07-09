"""Stage 0.4 unit-handling characterization (issue #431).

Cross-boundary registry interop (strict xfail) and legacy↔cellpycore converter parity.
See architecture-plan/unit-handling-cellpy2-plan.md §6 and tests/README.md.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pint")

from cellpy.readers.data_structures import Q as cellpy_Q
from cellpycore import units as core_units
from cellpycore.units import CellpyUnits, Q as core_Q

from .unit_parity_support import (
    GOLDEN_CONVERTER_CASES,
    GOLDEN_NOM_CAP_CASES,
    apply_parity_units,
    make_core_stub,
    make_parity_cell,
)


@pytest.mark.xfail(
    strict=True,
    reason="Unit plan Phase 1: unify pint registries before cross-boundary Quantity math",
)
def test_cellpy_and_cellpycore_quantities_interoperate():
    """Multiply quantities from separate pint registries; passes after Phase 1."""
    # Two registries today: cellpy.readers.data_structures vs cellpycore.units.
    result = (cellpy_Q(1, "mAh") * core_Q(1, "h")).to("mAh")
    assert result.m == pytest.approx(1.0)


@pytest.mark.essential
@pytest.mark.parametrize("mode,expected", GOLDEN_CONVERTER_CASES)
def test_get_converter_to_specific_matches_cellpycore(
    cellpy_data_instance, mode, expected
):
    cell = make_parity_cell(cellpy_data_instance)
    legacy = cell.get_converter_to_specific(mode=mode)
    core = core_units.get_converter_to_specific(make_core_stub(), mode=mode)
    assert legacy == pytest.approx(expected)
    assert legacy == pytest.approx(core)


@pytest.mark.essential
def test_nominal_capacity_as_absolute_gravimetric_matches_cellpycore(cellpy_data_instance):
    cell = make_parity_cell(cellpy_data_instance)
    legacy = cell.nominal_capacity_as_absolute(nom_cap_specifics="gravimetric")
    core = core_units.nominal_capacity_as_absolute(
        make_core_stub(), nom_cap_specifics="gravimetric"
    )
    assert legacy == pytest.approx(0.006)
    assert legacy == pytest.approx(core)


@pytest.mark.parametrize("kwargs,expected", GOLDEN_NOM_CAP_CASES[1:])
def test_nominal_capacity_as_absolute_explicit_gravimetric_matches_cellpycore(
    cellpy_data_instance, kwargs, expected
):
    cell = make_parity_cell(cellpy_data_instance)
    legacy = cell.nominal_capacity_as_absolute(**kwargs)
    core = core_units.nominal_capacity_as_absolute(make_core_stub(), **kwargs)
    assert legacy == pytest.approx(expected)
    assert legacy == pytest.approx(core)


def test_get_converter_to_specific_charge_unit_mismatch_matches_cellpycore(
    cellpy_data_instance,
):
    raw = CellpyUnits()
    raw["charge"] = "A*h"
    cell = make_parity_cell(cellpy_data_instance)
    apply_parity_units(cell, raw_units=raw)
    legacy = cell.get_converter_to_specific(mode="gravimetric")
    core = core_units.get_converter_to_specific(
        make_core_stub(raw_units=raw), mode="gravimetric"
    )
    assert legacy == pytest.approx(500_000.0)
    assert legacy == pytest.approx(core)
