"""Shared golden inputs for legacy↔cellpycore unit converter parity (issue #431)."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from cellpy.parameters.internal_settings import get_cellpy_units
from cellpy.readers.cellreader import CellpyCell
from cellpy.readers.data_structures import Data
from cellpycore.units import CellpyUnits

# Mirrors cellpy-core/tests/test_units_converters.py defaults (mass=area=volume=2.0).
GOLDEN_CONVERTER_CASES: list[tuple[str, float]] = [
    ("gravimetric", 500.0),
    ("areal", 0.5),
    ("absolute", 1.0),
]

# Gravimetric nominal-capacity cases that agree today (areal/absolute legacy path broken;
# see issue431_status.md).
GOLDEN_NOM_CAP_CASES: list[tuple[dict[str, Any], float]] = [
    ({"nom_cap_specifics": "gravimetric"}, 0.006),
    (
        {
            "value": 1000.0,
            "specific": 0.5,
            "nom_cap_specifics": "gravimetric",
        },
        0.0005,
    ),
]


def make_core_stub(raw_units: CellpyUnits | None = None, **attrs: Any) -> SimpleNamespace:
    """Minimal stand-in for ``Data`` exposing only what the converters read."""
    base: dict[str, Any] = dict(
        raw_units=raw_units if raw_units is not None else CellpyUnits(),
        mass=2.0,
        active_electrode_area=2.0,
        volume=2.0,
        nom_cap=3000.0,
        nom_cap_specifics="gravimetric",
    )
    base.update(attrs)
    return SimpleNamespace(**base)


def apply_parity_units(cell: CellpyCell, *, raw_units: CellpyUnits | None = None) -> None:
    """Align legacy cell units and attrs with core ``_stub()`` defaults."""
    units = get_cellpy_units()
    cell.data.raw_units = raw_units if raw_units is not None else CellpyUnits()
    if raw_units is None:
        cell.data.raw_units.update(units)
    cell.cellpy_units = CellpyUnits()
    cell.cellpy_units.update(units)
    cell.data.mass = 2.0
    cell.data.active_electrode_area = 2.0
    cell.data.volume = 2.0
    cell.data.nom_cap = 3000.0
    cell.data.nom_cap_specifics = "gravimetric"


def make_parity_cell(cellpy_data_instance: CellpyCell) -> CellpyCell:
    """Return a ``CellpyCell`` whose data matches core converter goldens."""
    cell = cellpy_data_instance
    cell.data = Data()
    apply_parity_units(cell)
    return cell
