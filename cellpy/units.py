"""Unit presentation helpers (unit plan Phase 4, issue #564).

Plots and reports need to *say* what a number is measured in. Before this
module every caller composed that string by hand::

    f"Capacity ({c.cellpy_units.charge}/{c.cellpy_units.specific_gravimetric})"

which is where gravimetric/areal/absolute mix-ups live: the mode is encoded in
the choice of attribute, so picking the wrong one is a silent mislabel rather
than an error. These two helpers make the mode an argument instead:

    >>> units_label("charge", mode="gravimetric")          # doctest: +SKIP
    'mAh/g'
    >>> with_cellpy_unit("Capacity", "charge", "areal")    # doctest: +SKIP
    'Capacity (mAh/cm**2)'

``units`` defaults to the session's cellpy units. Pass a cell's own units
explicitly — ``units_label("charge", "gravimetric", units=c.cellpy_units)`` —
whenever the label describes that cell's frames rather than session policy.
Values cross the seam, never config objects (architecture plan §4).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from cellpy.exceptions import UnitsError
from cellpy.parameters.internal_settings import get_cellpy_units

if TYPE_CHECKING:
    from cellpycore.units import CellpyUnits

# Specific mode -> the CellpyUnits field holding that mode's denominator.
_SPECIFIC_FIELD = {
    "gravimetric": "specific_gravimetric",
    "areal": "specific_areal",
    "volumetric": "specific_volumetric",
}

# Modes that mean "no denominator".
_ABSOLUTE_MODES = (None, "absolute")

# Convenience spellings. The native schema calls it ``potential`` while the
# unit spec calls it ``voltage``; accept both so callers can use the column
# vocabulary they already have.
_PROPERTY_ALIASES = {
    "potential": "voltage",
    "capacity": "charge",
    "charge_capacity": "charge",
    "discharge_capacity": "charge",
}


def _resolve_units(units: Optional["CellpyUnits"]) -> "CellpyUnits":
    return get_cellpy_units() if units is None else units


def _unit_for(units: "CellpyUnits", physical_property: str) -> str:
    prop = _PROPERTY_ALIASES.get(physical_property, physical_property)
    try:
        unit = units[prop]
    except (KeyError, AttributeError):
        unit = getattr(units, prop, None)
    if not isinstance(unit, str):
        raise UnitsError(
            f"{physical_property!r} is not a known physical property "
            f"(no such field in the cellpy unit spec)"
        )
    return unit


def units_label(
    physical_property: str,
    mode: Optional[str] = None,
    *,
    units: Optional["CellpyUnits"] = None,
) -> str:
    """Return the unit string for a physical property, e.g. ``"mAh/g"``.

    Args:
        physical_property: what is being measured — a field of the cellpy unit
            spec (``"charge"``, ``"voltage"``, ``"time"``, ``"energy"``, …).
            ``"potential"`` and ``"capacity"`` are accepted spellings of
            ``"voltage"`` and ``"charge"``.
        mode: ``"gravimetric"``, ``"areal"``, ``"volumetric"``, or
            ``"absolute"``/``None`` for the bare unit. A specific mode
            appends that mode's denominator.
        units: the unit spec to read. Defaults to the session's cellpy units;
            pass ``c.cellpy_units`` when labelling a particular cell.

    Returns:
        The unit string — ``"mAh"``, ``"mAh/g"``, ``"mAh/cm**2"``, ``"V"``, …

    Raises:
        UnitsError: if the property or the mode is unknown. Mislabelled axes
            are worse than a traceback, so this fails loudly rather than
            returning a placeholder (conventions plan §4).
    """
    spec = _resolve_units(units)
    unit = _unit_for(spec, physical_property)

    if mode in _ABSOLUTE_MODES:
        return unit

    field = _SPECIFIC_FIELD.get(mode)
    if field is None:
        raise UnitsError(
            f"unknown unit mode {mode!r}; expected one of "
            f"{sorted(_SPECIFIC_FIELD)} or 'absolute'"
        )
    return f"{unit}/{getattr(spec, field)}"


def with_cellpy_unit(
    name: str,
    physical_property: str,
    mode: Optional[str] = None,
    *,
    units: Optional["CellpyUnits"] = None,
) -> str:
    """Return an axis label: ``name`` followed by its unit in parentheses.

    Args:
        name: the human-readable quantity name, e.g. ``"Capacity"``.
        physical_property: as :func:`units_label`.
        mode: as :func:`units_label`.
        units: as :func:`units_label`.

    Returns:
        e.g. ``"Capacity (mAh/g)"``, ``"Voltage (V)"``.
    """
    return f"{name} ({units_label(physical_property, mode, units=units)})"
