"""Raw-plot prepare path: raw frame + FigureSpec.

Public ``raw_plot`` calls :func:`prepare` then hands ``(frame, FigureSpec)``
to a backend renderer (``spec.extras['kind'] == 'raw'``).
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

import numpy as np
import pandas as pd

from cellpy.plotting.headers import LiveHeaders
from cellpy.plotting.labels import quantity_label, units_quantity_label
from cellpy.plotting.spec import AxisSpec, FigureSpec, PanelSpec


@dataclass
class RawPrepareConfig:
    """Input knobs for :func:`prepare` (mirrors public ``raw_plot`` args)."""

    y: Optional[Any] = None
    y_label: Optional[Any] = None
    x: Optional[str] = None
    x_label: Optional[str] = None
    title: Optional[str] = None
    plot_type: str = "voltage-current"
    double_y: bool = True
    backend: str = "plotly"
    cycles: Optional[Any] = None
    max_points: Optional[int] = None
    additional_kwargs: dict = field(default_factory=dict)


def _as_cycle_list(cycles: Any) -> list:
    """Normalise a cycle selector to a list of cycle numbers."""
    if isinstance(cycles, (int, np.integer)):
        return [int(cycles)]
    if isinstance(cycles, (Sequence, set, frozenset, range, np.ndarray, pd.Series)):
        return list(cycles)
    return [cycles]


def decimate(
    frame: pd.DataFrame,
    columns: Sequence[str],
    max_points: int,
) -> pd.DataFrame:
    """Thin *frame* to roughly *max_points* rows, keeping per-bucket extremes.

    The frame is split into positional buckets and, for every column in
    *columns*, the rows holding that bucket's minimum and maximum are kept. The
    union of those rows (plus the first and last row, so the x range is
    preserved) is the result — spikes survive, which is what separates this from
    plain striding. Because each trace contributes up to two rows per bucket,
    the bucket count is scaled by the number of columns to land near the budget
    instead of overshooting by a factor of the trace count.

    Args:
        frame (pandas.DataFrame): frame to thin, in plotting order.
        columns: the y columns whose extremes must survive.
        max_points (int): approximate row budget for the result.

    Returns:
        ``pandas.DataFrame``: the thinned frame, or *frame* itself when it is
        already within budget.
    """
    n_rows = len(frame)
    numeric = [
        col
        for col in columns
        if col in frame.columns and pd.api.types.is_numeric_dtype(frame[col])
    ]
    if max_points < 2 or n_rows <= max_points or not numeric:
        return frame

    n_buckets = max(1, max_points // (2 * len(numeric)))
    if n_buckets >= n_rows:
        return frame

    positions = np.arange(n_rows)
    bucket = pd.Series((positions * n_buckets) // n_rows)
    keep = {0, n_rows - 1}
    for col in numeric:
        values = pd.Series(frame[col].to_numpy(), copy=False).groupby(bucket)
        keep.update(int(i) for i in values.idxmin().dropna())
        keep.update(int(i) for i in values.idxmax().dropna())
    return frame.iloc[sorted(keep)]


def prepare(
    ctx: Any,
    family: Any,
    config: RawPrepareConfig,
) -> tuple[pd.DataFrame, FigureSpec]:
    """Prepare a raw frame and :class:`FigureSpec` for ``raw_plot``.

    Args:
        ctx: :class:`~cellpy.plotting.context.CellContext` (or compatible).
        family: registered :class:`~cellpy.plotting.registry.PlotFamily` (``raw``).
        config: :class:`RawPrepareConfig` built by the public entry point.

    Returns:
        ``(frame, spec)`` where ``spec.extras['kind'] == 'raw'``.
    """
    from cellpy.readers.data_structures import Q

    c = ctx.cell
    hdr_raw = LiveHeaders(c, "raw")
    raw = c.data.raw
    # Select before copying — a cycle subset should not pay for the full frame.
    if config.cycles is not None:
        cycle_col = hdr_raw["cycle_index_txt"]
        raw = raw.loc[raw[cycle_col].isin(_as_cycle_list(config.cycles))]
    raw = raw.copy()
    raw_units = c.data.raw_units

    y = config.y
    y_label = config.y_label
    x = config.x
    x_label = config.x_label
    title = config.title
    plot_type = config.plot_type
    special_height = None

    if y is not None:
        if y_label is None:
            y_label = y
        y = [y]
        y_label = [y_label]
    elif plot_type is not None:
        if plot_type == "voltage-current":
            y = [hdr_raw["voltage_txt"], hdr_raw["current_txt"]]
            y_label = [
                units_quantity_label("Voltage", "voltage", units=raw_units),
                units_quantity_label("Current", "current", units=raw_units),
            ]
        elif plot_type == "capacity":
            y = [
                hdr_raw["charge_capacity_txt"],
                hdr_raw["discharge_capacity_txt"],
            ]
            y_label = [
                units_quantity_label("Charge capacity", "charge", units=raw_units),
                units_quantity_label("Discharge capacity", "charge", units=raw_units),
            ]
        elif plot_type == "raw":
            y = [
                hdr_raw["cycle_index_txt"],
                hdr_raw["step_index_txt"],
                hdr_raw["voltage_txt"],
                hdr_raw["current_txt"],
            ]
            y_label = [
                quantity_label("Cycle index", "#"),
                quantity_label("Step index", "#"),
                units_quantity_label("Voltage", "voltage", units=raw_units),
                units_quantity_label("Current", "current", units=raw_units),
            ]
            special_height = 600
        elif plot_type == "capacity-current":
            y = [
                hdr_raw["charge_capacity_txt"],
                hdr_raw["discharge_capacity_txt"],
                hdr_raw["current_txt"],
            ]
            y_label = [
                units_quantity_label("Charge capacity", "charge", units=raw_units),
                units_quantity_label("Discharge capacity", "charge", units=raw_units),
                units_quantity_label("Current", "current", units=raw_units),
            ]
            special_height = 500
        elif plot_type == "full":
            y = [
                hdr_raw["voltage_txt"],
                hdr_raw["current_txt"],
                hdr_raw["charge_capacity_txt"],
                hdr_raw["discharge_capacity_txt"],
                hdr_raw["cycle_index_txt"],
                hdr_raw["step_index_txt"],
            ]
            y_label = [
                units_quantity_label("Voltage", "voltage", units=raw_units),
                units_quantity_label("Current", "current", units=raw_units),
                units_quantity_label("Charge capacity", "charge", units=raw_units),
                units_quantity_label("Discharge capacity", "charge", units=raw_units),
                quantity_label("Cycle index", "#"),
                quantity_label("Step index", "#"),
            ]
            special_height = 800
        else:
            warnings.warn(f"Plot type {plot_type} not supported")
            empty = pd.DataFrame()
            return empty, FigureSpec(
                title=title,
                extras={"kind": "raw", "unsupported_plot_type": plot_type},
            )
    else:
        y = [hdr_raw["voltage_txt"]]
        y_label = [units_quantity_label("Voltage", "voltage", units=raw_units)]

    if x is None:
        x = "test_time_hrs"

    if x in ["test_time_hrs", "test_time_hours"]:
        conv_factor = Q(c.raw_units.time).to("hours").magnitude
        raw[x] = raw[hdr_raw["test_time_txt"]] * conv_factor
        x_label = x_label or quantity_label("Time", "hours")
    elif x == "test_time_days":
        conv_factor = Q(c.raw_units.time).to("days").magnitude
        raw[x] = raw[hdr_raw["test_time_txt"]] * conv_factor
        x_label = x_label or quantity_label("Time", "days")
    elif x == "test_time_years":
        conv_factor = Q(c.raw_units.time).to("years").magnitude
        raw[x] = raw[hdr_raw["test_time_txt"]] * conv_factor
        x_label = x_label or quantity_label("Time", "years")

    if title is None:
        title = f"{c.cell_name}"

    y = list(y)
    y_label = list(y_label)

    if config.max_points is not None:
        raw = decimate(raw, y, config.max_points)
    panels = tuple(
        PanelSpec(
            columns=(col,),
            kind="line",
            y_axis=AxisSpec(label=lab),
        )
        for col, lab in zip(y, y_label)
    )
    family_name = getattr(family, "name", "raw")
    spec = FigureSpec(
        panels=panels,
        x_axis=AxisSpec(label=x_label),
        title=title,
        supports_formation=False,
        extras={
            "kind": "raw",
            "family": family_name,
            "x": x,
            "x_label": x_label,
            "y": y,
            "y_label": y_label,
            "double_y": config.double_y,
            "special_height": special_height,
            "backend": config.backend,
            "cell": c,
            "additional_kwargs": dict(config.additional_kwargs),
        },
    )
    return raw, spec
