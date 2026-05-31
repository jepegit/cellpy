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
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Literal, Optional, Union

import pandas as pd

from cellpy.filters import filter_cycles
from cellpy.parameters.internal_settings import get_headers_normal
from cellpy.readers import core

if TYPE_CHECKING:
    from cellpy.parameters.internal_settings import CellpyUnits
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
    that holds the source unit (e.g. ``"charge"`` -> ``cellpy_units.charge``)
    and, when ``bdf_units`` override is used, the target unit.
    ``bdf_unit`` is the BDF spec target unit symbol that ``pint`` understands
    (e.g. ``"Ah"``). The special value :data:`DATETIME_KIND` for ``unit_kind``
    skips pint and routes the column through Unix-seconds conversion.
    Use ``None`` for both fields when no unit conversion is needed
    (e.g. dimensionless cycle / step indices).

    ``preferred`` and ``machine`` are the canonical BDF spec column names
    (used byte-for-byte when no override is in effect or the override is
    pint-equivalent to the spec default). ``base_preferred`` and
    ``base_machine`` are the unit-less stems used to synthesize column
    names when the override is to a non-spec unit (e.g. ``"Charging
    Capacity / mAh"`` / ``"charging_capacity_mah"``).
    """

    cellpy_field: str
    preferred: str
    machine: str
    base_preferred: str
    base_machine: str
    tier: Tier
    unit_kind: Optional[str] = None
    bdf_unit: Optional[str] = None


_COLUMN_MAP: tuple[_BdfColumn, ...] = (
    _BdfColumn(
        cellpy_field="test_time_txt",
        preferred="Test Time / s",
        machine="test_time_second",
        base_preferred="Test Time",
        base_machine="test_time",
        tier="required",
        unit_kind="time",
        bdf_unit="s",
    ),
    _BdfColumn(
        cellpy_field="voltage_txt",
        preferred="Voltage / V",
        machine="voltage_volt",
        base_preferred="Voltage",
        base_machine="voltage",
        tier="required",
        unit_kind="voltage",
        bdf_unit="V",
    ),
    _BdfColumn(
        cellpy_field="current_txt",
        preferred="Current / A",
        machine="current_ampere",
        base_preferred="Current",
        base_machine="current",
        tier="required",
        unit_kind="current",
        bdf_unit="A",
    ),
    _BdfColumn(
        cellpy_field="datetime_txt",
        preferred="Unix Time / s",
        machine="unix_time_second",
        base_preferred="Unix Time",
        base_machine="unix_time",
        tier="recommended",
        unit_kind=DATETIME_KIND,
        bdf_unit=None,
    ),
    _BdfColumn(
        cellpy_field="cycle_index_txt",
        preferred="Cycle Count / 1",
        machine="cycle_count",
        base_preferred="Cycle Count",
        base_machine="cycle_count",
        tier="recommended",
    ),
    _BdfColumn(
        cellpy_field="step_index_txt",
        preferred="Step Index / 1",
        machine="step_index",
        base_preferred="Step Index",
        base_machine="step_index",
        tier="optional",
    ),
    _BdfColumn(
        cellpy_field="charge_capacity_txt",
        preferred="Charging Capacity / Ah",
        machine="charging_capacity_ah",
        base_preferred="Charging Capacity",
        base_machine="charging_capacity",
        tier="optional",
        unit_kind="charge",
        bdf_unit="Ah",
    ),
    _BdfColumn(
        cellpy_field="discharge_capacity_txt",
        preferred="Discharging Capacity / Ah",
        machine="discharging_capacity_ah",
        base_preferred="Discharging Capacity",
        base_machine="discharging_capacity",
        tier="optional",
        unit_kind="charge",
        bdf_unit="Ah",
    ),
    _BdfColumn(
        cellpy_field="charge_energy_txt",
        preferred="Charging Energy / Wh",
        machine="charging_energy_wh",
        base_preferred="Charging Energy",
        base_machine="charging_energy",
        tier="optional",
        unit_kind="energy",
        bdf_unit="Wh",
    ),
    _BdfColumn(
        cellpy_field="discharge_energy_txt",
        preferred="Discharging Energy / Wh",
        machine="discharging_energy_wh",
        base_preferred="Discharging Energy",
        base_machine="discharging_energy",
        tier="optional",
        unit_kind="energy",
        bdf_unit="Wh",
    ),
    _BdfColumn(
        cellpy_field="power_txt",
        preferred="Power / W",
        machine="power_watt",
        base_preferred="Power",
        base_machine="power",
        tier="optional",
        unit_kind="power",
        bdf_unit="W",
    ),
    _BdfColumn(
        cellpy_field="internal_resistance_txt",
        preferred="Internal Resistance / Ohm",
        machine="internal_resistance_ohm",
        base_preferred="Internal Resistance",
        base_machine="internal_resistance",
        tier="optional",
        unit_kind="resistance",
        bdf_unit="ohm",
    ),
)


def _slug(unit: str) -> str:
    """Lowercase alphanumeric slug for a unit symbol.

    Used to synthesize machine column names when ``bdf_units`` overrides a
    BDF default (e.g. ``"mAh" -> "mah"``, ``"kWh" -> "kwh"``,
    ``"min" -> "min"``). Returns the lowercased input verbatim if it has
    no alphanumeric characters at all (extreme edge case; keeps the
    output non-empty).
    """
    slug = re.sub(r"[^A-Za-z0-9]+", "", unit)
    return slug.lower() if slug else unit.lower()


def _is_unit_equivalent(a: Optional[str], b: Optional[str]) -> bool:
    """Return ``True`` if ``a`` and ``b`` describe the same unit.

    Equivalent means either string-equal (``"A" == "A"``) or pint reports
    a unity ratio (``"sec"`` and ``"s"``, ``"V"`` and ``"volt"``). Unknown
    or empty values are treated as not equivalent unless both are empty.
    """
    if a == b:
        return True
    if not a or not b:
        return False
    try:
        ratio = core.Q(1.0, a) / core.Q(1.0, b)
        return float(ratio.to("dimensionless").magnitude) == 1.0
    except Exception:  # noqa: BLE001 - pint raises a few different types
        return False


def _conversion_factor(
    source_unit: Optional[str],
    target_unit: Optional[str],
    *,
    strict: bool = False,
) -> float:
    """Return the multiplier that turns ``source_unit`` into ``target_unit``.

    Delegates to :func:`cellpy.readers.core.Q` (pint) so that any unit
    spelling pint understands works automatically (``"mAh" -> "Ah"``,
    ``"sec" -> "s"``, ``"kWh" -> "Wh"``, ...). Returns ``1.0`` when no
    conversion is needed or the symbols are equal.

    When ``strict`` is true (i.e. the caller is acting on an explicit
    user ``bdf_units`` override), an incompatible / unknown unit raises
    :class:`ValueError` rather than silently leaving values unchanged.
    """
    if not source_unit or not target_unit or source_unit == target_unit:
        return 1.0
    try:
        ratio = core.Q(1.0, source_unit) / core.Q(1.0, target_unit)
        return float(ratio.to("dimensionless").magnitude)
    except Exception as exc:  # noqa: BLE001 - pint raises a few different types
        if strict:
            msg = (
                f"to_bdf: cannot convert {source_unit!r} to {target_unit!r} "
                f"(bdf_units override active): {exc}"
            )
            raise ValueError(msg) from exc
        logger.warning(
            "BDF export: could not convert %r to %r via pint (%s); "
            "leaving values unchanged.",
            source_unit,
            target_unit,
            exc,
        )
        return 1.0


def _resolve_column_name(
    spec: _BdfColumn,
    target_unit: Optional[str],
    header_style: HeaderStyle,
) -> str:
    """Pick the output column name for ``spec`` given the effective target unit.

    Returns the canonical BDF spec name (``spec.preferred`` /
    ``spec.machine``) when ``target_unit`` matches the BDF default, when
    it is pint-equivalent to the default (``"sec"`` vs ``"s"``), or when
    the column has no unit (cycle index, step index, datetime). Otherwise
    synthesizes a new name from the unit-less base (e.g.
    ``"Charging Capacity / mAh"`` / ``"charging_capacity_mah"``).
    """
    if (
        spec.bdf_unit is None
        or target_unit is None
        or _is_unit_equivalent(target_unit, spec.bdf_unit)
    ):
        return spec.preferred if header_style == "preferred" else spec.machine
    if header_style == "preferred":
        return f"{spec.base_preferred} / {target_unit}"
    return f"{spec.base_machine}_{_slug(target_unit)}"


def _resolve_target_units(bdf_units: Optional["CellpyUnits"]) -> dict[str, Optional[str]]:
    """Map each non-datetime ``unit_kind`` to the unit it should be written in.

    With ``bdf_units=None`` this is just the BDF spec defaults (the
    ``bdf_unit`` field on each ``_COLUMN_MAP`` row). With an override the
    corresponding attribute on the ``CellpyUnits`` object wins; unit
    kinds that the override does not define fall back to the BDF default.
    """
    targets: dict[str, Optional[str]] = {}
    for spec in _COLUMN_MAP:
        kind = spec.unit_kind
        if kind is None or kind == DATETIME_KIND:
            continue
        if bdf_units is None:
            targets[kind] = spec.bdf_unit
        else:
            targets[kind] = getattr(bdf_units, kind, spec.bdf_unit)
    return targets


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
    preprocess_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,
    bdf_units: Optional["CellpyUnits"] = None,
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
        bdf_units: Optional :class:`~cellpy.parameters.internal_settings.CellpyUnits`
            controlling the **units written into the BDF file**. ``None``
            (default) uses the BDF spec defaults (``A``, ``V``, ``Ah``,
            ``Wh``, ``s``, ``W``, ``ohm``); the file is then strictly
            BDF-compliant. When provided, each attribute on the
            ``CellpyUnits`` object overrides the spec target for the
            corresponding column kind: ``charge`` controls charge /
            discharge capacity, ``energy`` controls charge / discharge
            energy, etc. Column labels and machine names are rebuilt
            from the override (e.g. ``"Charging Capacity / mAh"`` /
            ``"charging_capacity_mah"``), and values are scaled
            accordingly via pint. Unit kinds that match the BDF default
            (string- or pint-equivalent, e.g. ``"sec"`` ≡ ``"s"``,
            ``"V"`` ≡ ``"volt"``) keep the canonical BDF spec spelling.
            *Caveat*: any override to a non-default unit makes the file
            no longer strictly BDF-compliant (parallel to ``extras=True``).
            An incompatible unit (e.g. ``charge="kg"``) raises
            :class:`ValueError` rather than emitting wrong-unit numbers.

            *Source units*: the conversion source is
            ``cell.data.raw_units`` (set by the instrument loader), **not**
            ``cell.cellpy_units``. The ``data.raw`` frame is always stored
            in the loader's raw units; ``cellpy_units`` describes the
            summary frame and user-facing meta-data only.

            Example::

                from cellpy.parameters.internal_settings import CellpyUnits

                # write charge in mAh and current in mA (everything else
                # stays BDF default)
                bdf_units = CellpyUnits(charge="mAh", current="mA")
                cell.to_bdf("out.bdf.csv", bdf_units=bdf_units)

    Returns:
        The path the file was written to.

    Raises:
        ValueError: If ``cell.data.raw`` is empty, any BDF *required*
            column is missing, or ``bdf_units`` specifies a unit that is
            not convertible from the cell's source unit (e.g.
            ``charge="kg"`` while ``cell.data.raw_units.charge == "Ah"``).
    """
    raw = cell.data.raw
    if raw is None or raw.empty:
        msg = "to_bdf: cell.data.raw is empty; nothing to export."
        raise ValueError(msg)

    headers = cell.headers_normal
    source_units = cell.data.raw_units
    target_units = _resolve_target_units(bdf_units)
    strict_units = bdf_units is not None

    cycle_col = headers.cycle_index_txt
    if cycle_col in raw.columns and (cycles is not None or last_cycle is not None):
        raw = filter_cycles(raw, cycles=cycles, last_cycle=last_cycle, column=cycle_col)
        if raw.empty:
            logger.warning("to_bdf: cycle filter produced an empty DataFrame.")

    if preprocess_fn:
        raw = preprocess_fn(raw)

    out_df, missing_recommended, extras_added, non_default_units = _build_bdf_frame(
        raw, headers, source_units, header_style, extras, target_units, strict_units
    )
    for col_name in missing_recommended:
        logger.warning("to_bdf: BDF-recommended column %r is not present in data.raw; skipped.", col_name)
    if extras_added:
        logger.info(
            "to_bdf: appended %d non-BDF column(s) verbatim: %s",
            len(extras_added),
            extras_added,
        )
    if non_default_units:
        logger.info(
            "to_bdf: bdf_units override active for %s; resulting file is not strictly BDF-compliant.",
            non_default_units,
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
    source_units,
    header_style: HeaderStyle,
    extras: ExtrasArg,
    target_units: dict[str, Optional[str]],
    strict_units: bool,
) -> tuple[pd.DataFrame, list[str], list[str], list[str]]:
    """Build the BDF output frame.

    Returns ``(frame, missing_recommended, extras_added, non_default_units)``.
    ``extras_added`` is the list of non-BDF cellpy column names appended
    verbatim (in the order they appear in the output frame).
    ``non_default_units`` is the list of unit kinds whose effective
    target unit differs from the BDF spec (i.e. the ``bdf_units``
    override is active for them); used to emit one human-readable
    non-strict-BDF log line in the caller.
    """
    out: dict[str, pd.Series] = {}
    missing_recommended: list[str] = []
    missing_required: list[str] = []
    consumed: set[str] = set()
    non_default_units: list[str] = []
    seen_non_default: set[str] = set()

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
        target_unit: Optional[str] = spec.bdf_unit

        if spec.unit_kind == DATETIME_KIND:
            converted = _datetime_to_unix_seconds(series)
        elif spec.unit_kind is None:
            converted = series
        else:
            source_unit = getattr(source_units, spec.unit_kind, None)
            target_unit = target_units.get(spec.unit_kind, spec.bdf_unit)
            factor = _conversion_factor(source_unit, target_unit, strict=strict_units)
            converted = series * factor if factor != 1.0 else series
            if (
                strict_units
                and spec.bdf_unit is not None
                and not _is_unit_equivalent(target_unit, spec.bdf_unit)
                and spec.unit_kind not in seen_non_default
            ):
                non_default_units.append(spec.unit_kind)
                seen_non_default.add(spec.unit_kind)

        out_name = _resolve_column_name(spec, target_unit, header_style)
        out[out_name] = converted.reset_index(drop=True)

    if missing_required:
        msg = (
            "to_bdf: BDF-required column(s) missing from data.raw: "
            f"{missing_required}. Cannot export a valid BDF file."
        )
        raise ValueError(msg)

    extras_added = _append_extras(raw, out, consumed, extras)

    return pd.DataFrame(out), missing_recommended, extras_added, non_default_units


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


if __name__ == "__main__":
    import cellpy
    import pathlib
    import pandas as pd
    from cellpy.parameters.internal_settings import CellpyUnits

    raw_data_path = pathlib.Path(r"local\data\combined_protocol_results_realistic.bdf.csv")
    out_path = pathlib.Path(r"local\out\batmo_bdf\out.bdf.csv")
    assert raw_data_path.exists()

    c = cellpy.get(
        raw_data_path,
        instrument="batmo_bdf",
        cycle_mode="full_cell",
        mass=1.0,
        nominal_capacity=120.0,
        nom_cap_specifics="absolute",
        refuse_copying=True,
    )
    bdf_units = CellpyUnits(
        charge="mAh"
    )
    c.to_bdf(out_path, bdf_units=bdf_units)

    print(f"Wrote BDF file to {out_path}")

    print("Now we should check the input and output files")
    print("--------------------------------")
    r_cha, r_dch = 'Charge Capacity / Ah', 'Discharge Capacity / Ah'
    c_cha, c_dch = 'charge_capacity', 'discharge_capacity'
    o_cha, o_dch =  f'Charging Capacity / {bdf_units.charge}', f'Discharging Capacity / {bdf_units.charge}'
    print("INPUT FILE:")
    df_raw = pd.read_csv(raw_data_path)
    # print(df_raw.head())
    print(df_raw[r_cha].max())
    print(df_raw[r_dch].max())


    print("CELLPY CELL:")
    # print(c.data.raw.head())
    print(c.data.raw[c_cha].max())
    print(c.data.raw[c_dch].max())

    print("OUTPUT FILE:")
    df_out = pd.read_csv(out_path)
    print(df_out.head())
    print(df_out[o_cha].max())
    print(df_out[o_dch].max())

    print("-------------raw-cellpy----------------")
    print("Checking if the values are the same")
    print(f"Input {r_cha}: {df_raw[r_cha].max()} vs Output {c_cha}: {c.data.raw[c_cha].max()}")
    print(f"Input {r_dch}: {df_raw[r_dch].max()} vs Output {c_dch}: {c.data.raw[c_dch].max()}")

    print("-------------raw-exported--------------")
    print("Checking if the values are the same")
    print(f"Input {r_cha}: {df_raw[r_cha].max()} vs Output {o_cha}: {df_out[o_cha].max()}")
    print(f"Input {r_dch}: {df_raw[r_dch].max()} vs Output {o_dch}: {df_out[o_dch].max()}")

    print(c.data.raw_units)