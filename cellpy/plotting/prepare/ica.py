"""ICA/DVA prepare path: long frames from ``cellpy.ica`` + FigureSpec (#648).

Public ``ica_plot`` / ``dva_plot`` call :func:`prepare` then hand
``(frame, FigureSpec)`` to a backend renderer (``spec.extras['kind']`` is
``'ica'`` or ``'dva'``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

import pandas as pd

from cellpy.exceptions import UnitsError
from cellpy.ica import BOTH, ICA_COLS, dqdv, dvdq
from cellpy.plotting.labels import quantity_label
from cellpy.plotting.spec import AxisSpec, FigureSpec, PanelSpec
from cellpy.units import units_label, with_cellpy_unit

Derivative = Literal["dqdv", "dvdq"]


@dataclass
class IcaPrepareConfig:
    """Input knobs for :func:`prepare` (mirrors public ``ica_plot`` / ``dva_plot``)."""

    derivative: Derivative = "dqdv"
    cycles: Optional[Any] = None
    direction: str = BOTH
    options: Any = None
    strict: bool = False
    cycle_mode: Optional[str] = None
    number_of_points: Optional[int] = None
    title: Optional[str] = None
    colormap: str = "viridis"
    width: int = 800
    height: int = 600
    figsize: tuple = (6, 4)
    x_range: Optional[list] = None
    y_range: Optional[list] = None
    marker_size: int = 5
    plotly_template: Optional[str] = None
    backend: str = "plotly"
    option_overrides: dict = field(default_factory=dict)
    additional_kwargs: dict = field(default_factory=dict)


def _range_tuple(value: Any) -> Optional[tuple[float, float]]:
    if value is None:
        return None
    return (float(value[0]), float(value[1]))


def _capacity_unit(c: Any) -> str:
    try:
        return units_label("charge", "gravimetric", units=c.cellpy_units)
    except UnitsError:
        return "-"


def _default_title(c: Any, *, kind: str, backend: str) -> str:
    use_plotly = backend == "plotly"
    bold_o = "<b>" if use_plotly else "'"
    bold_c = "</b>" if use_plotly else "'"
    label = "Incremental capacity (dQ/dV)" if kind == "ica" else "Differential voltage (dV/dQ)"
    return f"{label} for {bold_o}{c.cell_name}{bold_c}"


def prepare(
    ctx: Any,
    family: Any,
    config: IcaPrepareConfig,
) -> tuple[pd.DataFrame, FigureSpec]:
    """Prepare an ICA or DVA frame and :class:`FigureSpec`.

    Args:
        ctx: :class:`~cellpy.plotting.context.CellContext` (or compatible).
        family: registered :class:`~cellpy.plotting.registry.PlotFamily`
            (``ica`` or ``dva``).
        config: :class:`IcaPrepareConfig` built by the public entry point.

    Returns:
        ``(frame, spec)`` where ``spec.extras['kind']`` is ``'ica'`` or ``'dva'``.
    """
    c = ctx.cell
    family_name = getattr(family, "name", config.derivative)
    kind = "dva" if config.derivative == "dvdq" else "ica"

    transform = dvdq if config.derivative == "dvdq" else dqdv
    frame = transform(
        c,
        cycles=config.cycles,
        direction=config.direction,
        options=config.options,
        strict=config.strict,
        cycle_mode=config.cycle_mode,
        number_of_points=config.number_of_points,
        **dict(config.option_overrides or {}),
    )
    frame = frame.copy()
    if ICA_COLS.legacy_dqdv in frame.columns:
        frame = frame.drop(columns=[ICA_COLS.legacy_dqdv])

    if config.derivative == "dvdq":
        x_col = ICA_COLS.capacity
        y_col = ICA_COLS.dvdq
        capacity_unit = _capacity_unit(c)
        x_label = quantity_label("Capacity", capacity_unit)
        y_label = quantity_label("dV/dQ", f"V/({capacity_unit})")
    else:
        x_col = ICA_COLS.voltage
        y_col = ICA_COLS.dqdv
        x_label = with_cellpy_unit("Voltage", "voltage", units=c.cellpy_units)
        capacity_unit = _capacity_unit(c)
        y_label = quantity_label("dQ/dV", f"{capacity_unit}/V")

    title = config.title
    if title is None:
        title = _default_title(c, kind=kind, backend=config.backend)

    x_range = _range_tuple(config.x_range)
    y_range = _range_tuple(config.y_range)

    spec = FigureSpec(
        panels=(
            PanelSpec(
                columns=(x_col, y_col),
                kind="line",
                y_axis=AxisSpec(label=y_label, range=y_range),
            ),
        ),
        x_axis=AxisSpec(label=x_label, range=x_range),
        title=title,
        supports_formation=False,
        extras={
            "kind": kind,
            "family": family_name,
            "derivative": config.derivative,
            "x": x_col,
            "y": y_col,
            "x_label": x_label,
            "y_label": y_label,
            "color": ICA_COLS.cycle,
            "hover": [ICA_COLS.cycle, ICA_COLS.direction],
            "colormap": config.colormap,
            "width": config.width,
            "height": config.height,
            "figsize": config.figsize,
            "marker_size": config.marker_size,
            "plotly_template": config.plotly_template,
            "x_range": list(config.x_range) if config.x_range is not None else None,
            "y_range": list(config.y_range) if config.y_range is not None else None,
            "additional_kwargs": dict(config.additional_kwargs or {}),
            "cell": c,
        },
    )
    return frame, spec
