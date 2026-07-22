"""Map legacy/vendor auxiliary column names onto the harmonized aux scheme.

The native scheme is ``aux_<quantity>_<name>`` with quantity one of
temperature / potential / pressure / resistance (see
``LoaderDeclarations.aux_map``). Arbin's wide-aux path still emits the older
``aux_<nick>_u_<unit>`` (and ``aux_d_<nick>_dt_u_d<unit>_dt``) names on the
vendor frame — those must be declared or ``harmonize()`` warn-and-drops them
(#560 Phase C / #621).
"""

from __future__ import annotations

import re
from typing import Iterable

#: Arbin unit token → harmonized quantity.
_UNIT_TO_QUANTITY = {
    "C": "temperature",
    "V": "potential",
    "Pa": "pressure",
    "psi": "pressure",
    "ohm": "resistance",
    "Ohm": "resistance",
    "Ω": "resistance",
}

#: ``aux_<nick>_u_<unit>`` — the wide-aux name ``arbin_res`` builds.
_AUX_VALUE = re.compile(r"^aux_(?P<nick>.+)_u_(?P<unit>[^_]+)$")

#: ``aux_d_<nick>_dt_u_d<unit>_dt`` — the dx/dt companion.
_AUX_DERIV = re.compile(r"^aux_d_(?P<nick>.+)_dt_u_d(?P<unit>[^_]+)_dt$")

#: ``Aux_Voltage_1`` / ``Aux_Temperature_2`` style SQL-export columns.
_AUX_SQL = re.compile(
    r"^Aux_(?P<quantity>Voltage|Temperature|Pressure|Resistance)_(?P<nick>\w+)",
    re.IGNORECASE,
)

_SQL_QUANTITY = {
    "voltage": "potential",
    "temperature": "temperature",
    "pressure": "pressure",
    "resistance": "resistance",
}


def _sanitize_nick(nick: object) -> str:
    """Make a nick safe for ``aux_<quantity>_<name>`` (``\\w+``)."""
    text = str(nick).strip()
    text = re.sub(r"\W+", "_", text)
    return text or "x"


def map_one_aux_column(column: str) -> str | None:
    """Return the harmonized aux target for one vendor column, or ``None``."""
    match = _AUX_DERIV.match(column)
    if match:
        quantity = _UNIT_TO_QUANTITY.get(match["unit"])
        if quantity is None:
            return None
        return f"aux_{quantity}_d{_sanitize_nick(match['nick'])}_dt"

    match = _AUX_VALUE.match(column)
    if match:
        # Derivative names also match the value pattern if we are not careful
        # about order — the deriv regex runs first for that reason.
        quantity = _UNIT_TO_QUANTITY.get(match["unit"])
        if quantity is None:
            return None
        return f"aux_{quantity}_{_sanitize_nick(match['nick'])}"

    match = _AUX_SQL.match(column)
    if match:
        quantity = _SQL_QUANTITY.get(match["quantity"].lower())
        if quantity is None:
            return None
        return f"aux_{quantity}_{_sanitize_nick(match['nick'])}"

    return None


def aux_map_from_columns(
    columns: Iterable[str],
    *,
    already_declared: Iterable[str] = (),
) -> dict[str, str]:
    """Build ``aux_map`` for every recognisable aux column in ``columns``.

    Columns already claimed by ``column_map`` / ``passthrough`` / ``dropped``
    are skipped so a later call cannot double-declare them (e.g. Arbin SQL's
    ``Aux_Voltage_1`` already riding as ``reference_voltage`` passthrough).
    """
    claimed = set(already_declared)
    aux_map: dict[str, str] = {}
    for column in columns:
        if column in claimed or column in aux_map:
            continue
        target = map_one_aux_column(column)
        if target is None:
            continue
        aux_map[column] = target
    return aux_map
