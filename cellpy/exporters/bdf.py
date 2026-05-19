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
from typing import TYPE_CHECKING, Literal, Optional, Union

import pandas as pd

from cellpy.filters import filter_cycles
from cellpy.parameters.internal_settings import get_headers_normal

if TYPE_CHECKING:
    from cellpy.readers.cellreader import CellpyCell

logger = logging.getLogger(__name__)

HeaderStyle = Literal["preferred", "machine"]
BdfFormat = Literal["csv", "parquet"]
Tier = Literal["required", "recommended", "optional"]

CyclesArg = Optional[Union[int, Iterable[int]]]


@dataclass(frozen=True)
class _BdfColumn:
    """One row of the cellpy <-> BDF column map."""

    cellpy_field: str
    preferred: str
    machine: str
    tier: Tier
    unit_kind: Optional[str] = None


_COLUMN_MAP: tuple[_BdfColumn, ...] = (
    _BdfColumn("test_time_txt", "Test Time / s", "test_time_second", "required", "time"),
    _BdfColumn("voltage_txt", "Voltage / V", "voltage_volt", "required", "voltage"),
    _BdfColumn("current_txt", "Current / A", "current_ampere", "required", "current"),
    _BdfColumn("datetime_txt", "Unix Time / s", "unix_time_second", "recommended", "datetime"),
    _BdfColumn("cycle_index_txt", "Cycle Count / 1", "cycle_count", "recommended", None),
    _BdfColumn("step_index_txt", "Step Index / 1", "step_index", "optional", None),
    _BdfColumn("charge_capacity_txt", "Charging Capacity / Ah", "charging_capacity_ah", "optional", "charge"),
    _BdfColumn("discharge_capacity_txt", "Discharging Capacity / Ah", "discharging_capacity_ah", "optional", "charge"),
    _BdfColumn("charge_energy_txt", "Charging Energy / Wh", "charging_energy_wh", "optional", "energy"),
    _BdfColumn("discharge_energy_txt", "Discharging Energy / Wh", "discharging_energy_wh", "optional", "energy"),
    _BdfColumn("power_txt", "Power / W", "power_watt", "optional", "power"),
    _BdfColumn("internal_resistance_txt", "Internal Resistance / Ohm", "internal_resistance_ohm", "optional", "resistance"),
)


_UNIT_FACTORS: dict[str, dict[str, float]] = {
    "current": {"A": 1.0, "mA": 1e-3},
    "charge": {"Ah": 1.0, "mAh": 1e-3},
    "energy": {"Wh": 1.0, "mWh": 1e-3, "kWh": 1e3},
    "power": {"W": 1.0, "mW": 1e-3, "kW": 1e3},
    "voltage": {"V": 1.0, "mV": 1e-3},
    "time": {"s": 1.0, "sec": 1.0, "second": 1.0, "min": 60.0, "h": 3600.0, "hour": 3600.0},
    "resistance": {"ohm": 1.0, "Ohm": 1.0, "mOhm": 1e-3, "mohm": 1e-3, "kOhm": 1e3, "kohm": 1e3},
}


def _unit_factor(unit_kind: Optional[str], cellpy_unit: Optional[str]) -> float:
    """Return the multiplier that converts ``cellpy_unit`` -> BDF unit."""
    if unit_kind is None or cellpy_unit is None:
        return 1.0
    table = _UNIT_FACTORS.get(unit_kind)
    if table is None:
        return 1.0
    factor = table.get(str(cellpy_unit))
    if factor is None:
        logger.warning(
            "BDF export: unknown %s unit %r; assuming identity factor (no conversion).",
            unit_kind,
            cellpy_unit,
        )
        return 1.0
    return factor


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

    out_df, missing_recommended = _build_bdf_frame(raw, headers, cellpy_units, header_style)
    for col_name in missing_recommended:
        logger.warning("to_bdf: BDF-recommended column %r is not present in data.raw; skipped.", col_name)

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
) -> tuple[pd.DataFrame, list[str]]:
    """Build the BDF output frame and report missing recommended columns."""
    out: dict[str, pd.Series] = {}
    missing_recommended: list[str] = []
    missing_required: list[str] = []

    for spec in _COLUMN_MAP:
        src_col = getattr(headers, spec.cellpy_field, None)
        if src_col is None or src_col not in raw.columns:
            if spec.tier == "required":
                missing_required.append(spec.preferred)
            elif spec.tier == "recommended":
                missing_recommended.append(spec.preferred)
            continue

        series = raw[src_col]

        if spec.unit_kind == "datetime":
            converted = _datetime_to_unix_seconds(series)
        else:
            cellpy_unit = getattr(cellpy_units, spec.unit_kind, None) if spec.unit_kind else None
            factor = _unit_factor(spec.unit_kind, cellpy_unit)
            converted = series * factor if factor != 1.0 else series

        out_name = spec.preferred if header_style == "preferred" else spec.machine
        out[out_name] = converted.reset_index(drop=True)

    if missing_required:
        msg = (
            "to_bdf: BDF-required column(s) missing from data.raw: "
            f"{missing_required}. Cannot export a valid BDF file."
        )
        raise ValueError(msg)

    return pd.DataFrame(out), missing_recommended
