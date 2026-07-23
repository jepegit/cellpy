"""Cycles-plot prepare path: voltage–capacity frame + FigureSpec (#646).

Public ``cycles_plot`` calls :func:`prepare` then hands ``(frame, FigureSpec)``
to a backend renderer (``spec.extras['kind'] == 'cycles'``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

import pandas as pd
from cellpycore.config import CurveCols

from cellpy.exceptions import UnitsError
from cellpy.plotting.spec import AxisSpec, FigureSpec, PanelSpec
from cellpy.units import units_label, with_cellpy_unit

_CCOLS = CurveCols()


@dataclass
class CyclesPrepareConfig:
    """Input knobs for :func:`prepare` (mirrors public ``cycles_plot`` args)."""

    cycles: Optional[Any] = None
    inter_cycle_shift: bool = True
    cycle_mode: Optional[str] = None
    formation_cycles: int = 3
    show_formation: bool = True
    mode: str = "gravimetric"
    method: str = "forth-and-forth"
    interpolated: bool = True
    number_of_points: int = 200
    colormap: str = "Blues_r"
    formation_colormap: str = "autumn"
    cut_colorbar: bool = True
    title: Optional[str] = None
    figsize: tuple = (6, 4)
    x_range: Optional[list] = None
    y_range: Optional[list] = None
    width: int = 800
    height: int = 600
    marker_size: int = 5
    formation_line_color: str = "rgba(152, 0, 0, .8)"
    force_colorbar: bool = False
    force_nonbar: bool = False
    plotly_template: Optional[str] = None
    seaborn_palette: str = "deep"
    seaborn_style: str = "dark"
    seaborn_context: str = "notebook"
    seaborn_facecolor: str = "#EAEAF2"
    seaborn_edgecolor: str = "black"
    seaborn_style_dict: Optional[dict] = None
    cbar_aspect: int = 30
    backend: str = "plotly"
    additional_kwargs: dict = field(default_factory=dict)


def _capacity_unit(c: Any, mode: str = "gravimetric") -> str:
    try:
        return units_label("charge", mode, units=c.cellpy_units)
    except UnitsError:
        return "-"


def _range_tuple(value: Any) -> Optional[tuple[float, float]]:
    if value is None:
        return None
    return (float(value[0]), float(value[1]))


def _load_curve_frame(ctx: Any, cycles: Any, **get_cap_kwargs: Any) -> pd.DataFrame:
    """Load a tidy capacity–voltage frame.

    Seam for a future ``cellpycore.curves.get_cap_curve`` preferred path
    (architecture-plan risk table / epic #567). For #646 the working path is
    ``c.get_cap``, which already returns native ``CurveCols`` frames and
    matches the committed figure-spec oracle.
    """
    return ctx.cell.get_cap(cycles=cycles, **get_cap_kwargs)


def _default_title(
    c: Any,
    *,
    backend: str,
    mode: str,
    interpolated: bool,
    number_of_points: int,
) -> str:
    use_plotly_markup = backend == "plotly"
    _bold = "<b>" if use_plotly_markup else "'"
    _end_bold = "</b>" if use_plotly_markup else "'"
    _newline = "<br>" if use_plotly_markup else "\n"
    _small = '<span style="font-size: 14px;">' if use_plotly_markup else ""
    _end_small = "</span>" if use_plotly_markup else ""
    top_title_line = f"Capacity plots for {_bold}{c.cell_name}{_end_bold}"
    second_title_line = f"{_small} - {mode} mode"
    if interpolated:
        second_title_line = (
            f"{second_title_line}, interpolated ({number_of_points} points){_end_small}"
        )
    else:
        second_title_line = f"{second_title_line}{_end_small}"
    return _newline.join([top_title_line, second_title_line])


def prepare(
    ctx: Any,
    family: Any,
    config: CyclesPrepareConfig,
) -> tuple[pd.DataFrame, FigureSpec]:
    """Prepare a voltage–capacity frame and :class:`FigureSpec` for ``cycles_plot``.

    Args:
        ctx: :class:`~cellpy.plotting.context.CellContext` (or compatible).
        family: registered :class:`~cellpy.plotting.registry.PlotFamily` (``cycles``).
        config: :class:`CyclesPrepareConfig` built by the public entry point.

    Returns:
        ``(frame, spec)`` where ``spec.extras['kind'] == 'cycles'``.
    """
    c = ctx.cell
    cycles = config.cycles
    if cycles is None:
        cycles = c.get_cycle_numbers()

    title = config.title
    if title is None:
        title = _default_title(
            c,
            backend=config.backend,
            mode=config.mode,
            interpolated=config.interpolated,
            number_of_points=config.number_of_points,
        )

    get_cap_kwargs = dict(
        method=config.method,
        interpolated=config.interpolated,
        label_cycle_number=True,
        categorical_column=True,
        number_of_points=config.number_of_points,
        insert_nan=True,
        mode=config.mode,
        cycle_mode=config.cycle_mode,
        inter_cycle_shift=config.inter_cycle_shift,
    )
    df = _load_curve_frame(ctx, cycles, **get_cap_kwargs)
    df = df.sort_values(by=[_CCOLS.cycle_num, "direction"])

    selector = df[_CCOLS.cycle_num] <= config.formation_cycles
    form_cycles = df.loc[selector, :]
    rest_cycles = df.loc[~selector, :]
    n_form_cycles = len(form_cycles[_CCOLS.cycle_num].unique())
    n_rest_cycles = len(rest_cycles[_CCOLS.cycle_num].unique())

    capacity_unit = _capacity_unit(c, mode=config.mode)
    voltage_label = with_cellpy_unit("Voltage", "voltage", units=c.cellpy_units)
    capacity_label = f"Capacity ({capacity_unit})"

    x_range = _range_tuple(config.x_range)
    y_range = _range_tuple(config.y_range)

    family_name = getattr(family, "name", "cycles")
    spec = FigureSpec(
        panels=(
            PanelSpec(
                columns=("capacity", _CCOLS.potential),
                kind="line",
                y_axis=AxisSpec(label=voltage_label, range=y_range),
            ),
        ),
        x_axis=AxisSpec(label=capacity_label, range=x_range),
        title=title,
        supports_formation=bool(config.show_formation),
        extras={
            "kind": "cycles",
            "family": family_name,
            "form_cycles": form_cycles,
            "rest_cycles": rest_cycles,
            "capacity_unit": capacity_unit,
            "voltage_label": voltage_label,
            "capacity_label": capacity_label,
            "plotly_template": config.plotly_template,
            "colormap": config.colormap,
            "formation_colormap": config.formation_colormap,
            "cut_colorbar": config.cut_colorbar,
            "cbar_aspect": config.cbar_aspect,
            "figsize": config.figsize,
            "force_colorbar": config.force_colorbar,
            "force_nonbar": config.force_nonbar,
            "n_rest_cycles": n_rest_cycles,
            "n_form_cycles": n_form_cycles,
            "show_formation": config.show_formation,
            "width": config.width,
            "height": config.height,
            "marker_size": config.marker_size,
            "formation_line_color": config.formation_line_color,
            "x_range": list(config.x_range) if config.x_range is not None else None,
            "y_range": list(config.y_range) if config.y_range is not None else None,
            "seaborn_style": config.seaborn_style,
            "seaborn_palette": config.seaborn_palette,
            "seaborn_context": config.seaborn_context,
            "seaborn_facecolor": config.seaborn_facecolor,
            "seaborn_edgecolor": config.seaborn_edgecolor,
            "seaborn_style_dict": config.seaborn_style_dict,
            "additional_kwargs": dict(config.additional_kwargs or {}),
            "cell": c,
        },
    )
    return df, spec
