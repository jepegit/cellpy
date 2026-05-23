"""Export a :class:`cellpy.readers.cellreader.CellpyCell` raw time-series
in `Battery Data Format (BDF) <https://github.com/battery-data-alliance/battery-data-format>`_.

The BDF specifies a fixed column schema and unit set for cycler
time-series. This module:

1. Maps cellpy ``HeadersNormal`` column names to BDF preferred labels and
   machine-readable names.
2. Converts unit-bearing columns (capacity in ``mAh`` -> ``Ah``,
   ``date_time`` -> Unix seconds, etc.) using the cell's
   ``CellpyUnits``.
3. Filters by cycle (delegated to :func:`cellpy.filters.filter_cycles`).
4. Writes the result as ``.bdf.csv`` (default) or ``.bdf.parquet``.

Design rules (recorded in ``.issueflows/04-designs-and-guides/bdf-export.md``):

- The ``CellpyCell`` class layer (``cellpy/readers/cellreader.py``)
  imports BDF export logic only via ``cellpy.exporters``, never via
  ``cellpy.utils``.
- BDF *required* columns missing from ``data.raw`` raise; recommended
  and optional ones warn-and-skip.
- Default header style is the BDF "Preferred Label" form
  (``Test Time / s``); ``header_style="machine"`` switches to
  ``test_time_second``.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Literal, Optional, Union

import pandas as pd

from cellpy.filters import filter_cycles
from cellpy.parameters.internal_settings import get_headers_normal
from cellpy.readers import core

if TYPE_CHECKING:
    from cellpy.readers.cellreader import CellpyCell

logger = logging.getLogger(__name__)

HeaderStyle = Literal["preferred", "machine"]
BdfFormat = Literal["csv", "parquet"]
Tier = Literal["required", "recommended", "optional"]

CyclesArg = Optional[Union[int, Iterable[int]]]
ExtrasArg = Union[bool, str, Iterable[str]]

DATETIME_KIND = "datetime"


@dataclass(frozen=True)
class _BdfColumn:
    """One row of the cellpy <-> BDF column map.

    ``unit_kind`` is the attribute name on :class:`cellpy.parameters.internal_settings.CellpyUnits`
    that holds the source unit (e.g. ``"charge"`` -> ``cellpy_units.charge``).
    ``bdf_unit`` is the BDF target unit symbol that ``pint`` understands
    (e.g. ``"Ah"``). The special value :data:`DATETIME_KIND` for ``unit_kind``
    skips pint and routes the column through Unix-seconds conversion.
    Use ``None`` for both fields when no unit conversion is needed
    (e.g. dimensionless cycle / step indices).
    """

    cellpy_field: str
    preferred: str
    machine: str
    tier: Tier
    unit_kind: Optional[str] = None
    bdf_unit: Optional[str] = None


_COLUMN_MAP: tuple[_BdfColumn, ...] = (
    _BdfColumn("test_time_txt", "Test Time / s", "test_time_second", "required", "time", "s"),
    _BdfColumn("voltage_txt", "Voltage / V", "voltage_volt", "required", "voltage", "V"),
    _BdfColumn("current_txt", "Current / A", "current_ampere", "required", "current", "A"),
    _BdfColumn("datetime_txt", "Unix Time / s", "unix_time_second", "recommended", DATETIME_KIND, None),
    _BdfColumn("cycle_index_txt", "Cycle Count / 1", "cycle_count", "recommended"),
    _BdfColumn("step_index_txt", "Step Index / 1", "step_index", "optional"),
    _BdfColumn("charge_capacity_txt", "Charging Capacity / Ah", "charging_capacity_ah", "optional", "charge", "Ah"),
    _BdfColumn("discharge_capacity_txt", "Discharging Capacity / Ah", "discharging_capacity_ah", "optional", "charge", "Ah"),
    _BdfColumn("charge_energy_txt", "Charging Energy / Wh", "charging_energy_wh", "optional", "energy", "Wh"),
    _BdfColumn("discharge_energy_txt", "Discharging Energy / Wh", "discharging_energy_wh", "optional", "energy", "Wh"),
    _BdfColumn("power_txt", "Power / W", "power_watt", "optional", "power", "W"),
    _BdfColumn("internal_resistance_txt", "Internal Resistance / Ohm", "internal_resistance_ohm", "optional", "resistance", "ohm"),
)


def _conversion_factor(cellpy_unit: Optional[str], bdf_unit: Optional[str]) -> float:
    """Return the multiplier that turns ``cellpy_unit`` into ``bdf_unit``.

    Delegates to :func:`cellpy.readers.core.Q` (pint) so that any unit
    spelling pint understands works automatically (``"mAh" -> "Ah"``,
    ``"sec" -> "s"``, ``"kWh" -> "Wh"``, ...). Returns ``1.0`` when no
    conversion is needed or the symbols are equal.
    """
    if not cellpy_unit or not bdf_unit or cellpy_unit == bdf_unit:
        return 1.0
    try:
        ratio = core.Q(1.0, cellpy_unit) / core.Q(1.0, bdf_unit)
        return float(ratio.to("dimensionless").magnitude)
    except Exception as exc:  # noqa: BLE001 - pint raises a few different types
        logger.warning(
            "BDF export: could not convert %r to %r via pint (%s); "
            "leaving values unchanged.",
            cellpy_unit,
            bdf_unit,
            exc,
        )
        return 1.0


def _datetime_to_unix_seconds(series: pd.Series) -> pd.Series:
    """Convert a datetime-ish series to floating-point Unix seconds."""
    if pd.api.types.is_datetime64_any_dtype(series):
        ts = series
    else:
        ts = pd.to_datetime(series, errors="coerce", utc=False)
    if getattr(ts.dt, "tz", None) is None:
        ts = ts.dt.tz_localize("UTC", nonexistent="NaT", ambiguous="NaT")
    else:
        ts = ts.dt.tz_convert("UTC")
    return ts.view("int64") / 1e9


def _resolve_filename(filename: Union[str, Path, None], cell: "CellpyCell", fmt: BdfFormat) -> Path:
    """Apply the BDF default-extension rules to ``filename``."""
    if filename is None:
        base = cell.cell_name or "cell"
        filename = f"{base}.bdf.{fmt}"
    p = Path(filename)
    if not p.suffix:
        p = p.with_suffix(f".bdf.{fmt}")
    return p


def to_bdf(
    cell: "CellpyCell",
    filename: Union[str, Path, None] = None,
    *,
    cycles: CyclesArg = None,
    last_cycle: Optional[int] = None,
    header_style: HeaderStyle = "preferred",
    format: BdfFormat = "csv",
    extras: ExtrasArg = False,
    preprocess_fn: Callable[[pd.DataFrame], pd.DataFrame] = None,
) -> Path:
    """Export ``cell.data.raw`` as a BDF file.

    Args:
        cell: The ``CellpyCell`` whose raw time-series will be exported.
        filename: Output path. If ``None`` or extensionless, a default
            ``<cell_name>.bdf.<format>`` (or ``<filename>.bdf.<format>``)
            is used. An explicit suffix is honoured as-is.
        cycles: Optional cycle filter. ``None`` exports all cycles; a
            scalar exports that single cycle; an iterable exports the
            listed cycles. Combines with ``last_cycle``.
        last_cycle: If given, drop rows whose cycle index exceeds
            ``last_cycle``.
        header_style: ``"preferred"`` (default, BDF spec) writes headers
            like ``"Test Time / s"``. ``"machine"`` writes machine-
            readable names like ``"test_time_second"``.
        format: ``"csv"`` or ``"parquet"``. Determines both the writer
            used and the default extension.
        extras: Append columns from ``data.raw`` that are not part of the
            BDF column map. ``False`` (default) exports the BDF columns
            only. ``True`` appends every unmapped raw column verbatim
            (no unit conversion, original cellpy column name kept). A
            string or iterable of strings appends only the listed
            columns. The resulting file is no longer strictly BDF-
            compliant; useful when you need to preserve cycler-specific
            auxiliary channels alongside the BDF payload.
        preprocess_fn: A function that takes the raw DataFrame and returns
            a new DataFrame. This function is applied to the raw DataFrame
            after the cycle filter and before the BDF export.

    Returns:
        The path the file was written to.

    Raises:
        ValueError: If ``cell.data.raw`` is empty or any BDF *required*
            column is missing.
    """
    raw = cell.data.raw
    if raw is None or raw.empty:
        msg = "to_bdf: cell.data.raw is empty; nothing to export."
        raise ValueError(msg)

    headers = cell.headers_normal
    cellpy_units = cell.cellpy_units

    cycle_col = headers.cycle_index_txt
    if cycle_col in raw.columns and (cycles is not None or last_cycle is not None):
        raw = filter_cycles(raw, cycles=cycles, last_cycle=last_cycle, column=cycle_col)
        if raw.empty:
            logger.warning("to_bdf: cycle filter produced an empty DataFrame.")

    if preprocess_fn:
        raw = preprocess_fn(raw)

    out_df, missing_recommended, extras_added = _build_bdf_frame(
        raw, headers, cellpy_units, header_style, extras
    )
    for col_name in missing_recommended:
        logger.warning("to_bdf: BDF-recommended column %r is not present in data.raw; skipped.", col_name)
    if extras_added:
        logger.info(
            "to_bdf: appended %d non-BDF column(s) verbatim: %s",
            len(extras_added),
            extras_added,
        )

    out_path = _resolve_filename(filename, cell, format)
    if format == "csv":
        out_df.to_csv(out_path, index=False)
    elif format == "parquet":
        out_df.to_parquet(out_path, index=False)
    else:  # pragma: no cover - exhaustively typed
        msg = f"to_bdf: unsupported format {format!r}; expected 'csv' or 'parquet'."
        raise ValueError(msg)

    logger.info("to_bdf: wrote %d rows to %s", len(out_df), out_path)
    return out_path


def _build_bdf_frame(
    raw: pd.DataFrame,
    headers,
    cellpy_units,
    header_style: HeaderStyle,
    extras: ExtrasArg = False,
) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Build the BDF output frame.

    Returns ``(frame, missing_recommended, extras_added)``. ``extras_added``
    is the list of non-BDF cellpy column names appended verbatim (in the
    order they appear in the output frame).
    """
    out: dict[str, pd.Series] = {}
    missing_recommended: list[str] = []
    missing_required: list[str] = []
    consumed: set[str] = set()

    for spec in _COLUMN_MAP:
        src_col = getattr(headers, spec.cellpy_field, None)
        if src_col is None or src_col not in raw.columns:
            if spec.tier == "required":
                missing_required.append(spec.preferred)
            elif spec.tier == "recommended":
                missing_recommended.append(spec.preferred)
            continue

        consumed.add(src_col)
        series = raw[src_col]

        if spec.unit_kind == DATETIME_KIND:
            converted = _datetime_to_unix_seconds(series)
        else:
            cellpy_unit = getattr(cellpy_units, spec.unit_kind, None) if spec.unit_kind else None
            factor = _conversion_factor(cellpy_unit, spec.bdf_unit)
            converted = series * factor if factor != 1.0 else series

        out_name = spec.preferred if header_style == "preferred" else spec.machine
        out[out_name] = converted.reset_index(drop=True)

    if missing_required:
        msg = (
            "to_bdf: BDF-required column(s) missing from data.raw: "
            f"{missing_required}. Cannot export a valid BDF file."
        )
        raise ValueError(msg)

    extras_added = _append_extras(raw, out, consumed, extras)

    return pd.DataFrame(out), missing_recommended, extras_added


def _append_extras(
    raw: pd.DataFrame,
    out: dict[str, pd.Series],
    consumed: set[str],
    extras: ExtrasArg,
) -> list[str]:
    """Append unmapped raw columns to ``out`` per the ``extras`` policy.

    Extras are written verbatim: the cellpy column name is preserved and
    no unit conversion is performed. Returns the list of column names
    that were actually appended (in insertion order).
    """
    if not extras:
        return []

    if extras is True:
        requested: list[str] = [c for c in raw.columns if c not in consumed]
    elif isinstance(extras, str):
        requested = [extras]
    else:
        requested = list(extras)

    added: list[str] = []
    for col in requested:
        if col not in raw.columns:
            logger.warning(
                "to_bdf: requested extra column %r not in data.raw; skipped.", col
            )
            continue
        if col in consumed:
            logger.debug(
                "to_bdf: extra column %r is already part of the BDF column map; skipped.",
                col,
            )
            continue
        if col in out:
            continue
        out[col] = raw[col].reset_index(drop=True)
        added.append(col)
    return added
