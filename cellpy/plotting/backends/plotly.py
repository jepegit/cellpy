"""Plotly backend: formation/facet layout + summary ``render`` (#637 / #638).

Formation axis grids live in :func:`configure_formation_layout`. Public
``summary_plot`` draws through :class:`PlotlyBackend.render` from a tidy
frame + :class:`~cellpy.plotting.spec.FigureSpec` (#638).
"""

from __future__ import annotations

import logging
import warnings
from copy import deepcopy
from typing import Any, Optional, Sequence

import numpy as np

from cellpy.plotting.spec import FigureSpec

logger = logging.getLogger(__name__)

PLOTLY_BLANK_LABEL = {
    "font": {},
    "showarrow": False,
    "text": "",
    "x": 1.1,
    "xanchor": "center",
    "xref": "paper",
    "y": 1.0,
    "yanchor": "bottom",
    "yref": "paper",
}

DEFAULT_FORMATIONION_LABEL = '<span style="color:red">Formation</span>'
MAX_FORMATIONATION_ROWS = 4


def _label_dict(text: str, x: float, y: float) -> dict[str, Any]:
    d = PLOTLY_BLANK_LABEL.copy()
    d["text"] = text
    d["x"] = x
    d["y"] = y
    return d


def _xaxis_key(index: int) -> str:
    return "xaxis" if index == 1 else f"xaxis{index}"


def _yaxis_key(index: int) -> str:
    return "yaxis" if index == 1 else f"yaxis{index}"


def _y_ref(index: int) -> str:
    return "y" if index == 1 else f"y{index}"


def auto_range(fig: Any, axis_name_1: str, axis_name_2: str) -> list[float]:
    """Calculate a padded auto range covering two y-axes (plotly only)."""
    min_y = np.inf
    max_y = -np.inf
    full_axis_name_1 = axis_name_1.replace("y", "yaxis")
    full_axis_name_2 = axis_name_2.replace("y", "yaxis")

    _range_1 = getattr(fig.layout, f"{full_axis_name_1}_range", None)
    _range_2 = getattr(fig.layout, f"{full_axis_name_2}_range", None)
    if _range_1 is None:
        _range_1 = [np.inf, -np.inf]
    if _range_2 is None:
        _range_2 = [np.inf, -np.inf]
    _range = [min(_range_1[0], _range_2[0]), max(_range_1[1], _range_2[1])]

    for i, t in enumerate(deepcopy(fig.data)):
        if t.yaxis in [axis_name_1, axis_name_2]:
            y = deepcopy(t.y)
            try:
                y = np.array(y, dtype=float)
                min_y = np.ma.masked_invalid(y).min()
                max_y = np.ma.masked_invalid(y).max()
            except Exception as e:
                warnings.warn(
                    f"Could not calculate min and max for y-axis (data set {i}): {e}"
                )
            _range = [min(_range[0], min_y), max(_range[1], max_y)]
    return [0.95 * _range[0], 1.05 * _range[1]]


def configure_formation_layout(
    fig: Any,
    *,
    n_rows: int,
    x_axis_domain_formation: Sequence[float],
    x_axis_domain_rest: Sequence[float],
    x_axis_range_formation: Sequence[float],
    x_axis_range_rest: Sequence[float],
    show_y_labels_on_right_pane: bool = False,
    formation_header: str = DEFAULT_FORMATIONION_LABEL,
    row_y_ranges: Optional[Sequence[Optional[Sequence[float]]]] = None,
    top_row_label: Optional[str] = None,
) -> None:
    """Apply the formation × panel axis grid for *n_rows* rows (1–4).

    Replaces the old per-row-count ``_configure_formation_*_rows`` methods.
    """
    if n_rows < 1:
        raise ValueError(f"n_rows must be >= 1, got {n_rows}")
    if n_rows > MAX_FORMATIONATION_ROWS:
        raise NotImplementedError("Not implemented for more than four rows")

    header_y = 1.02 if n_rows == 1 else 1.0
    blank_count = 2 * n_rows - 1
    annotations = [_label_dict(formation_header, 0.08, header_y)] + blank_count * [
        PLOTLY_BLANK_LABEL
    ]

    if n_rows == 1:
        # Single-row formation: plotly's facet annotation count differs, and
        # the first x-axis range is set explicitly (matches the pre-#637 path).
        fig.update_layout(
            xaxis_domain=list(x_axis_domain_formation),
            scene_domain_x=list(x_axis_domain_formation),
            xaxis=dict(range=list(x_axis_range_formation)),
            xaxis2=dict(
                range=list(x_axis_range_rest),
                domain=list(x_axis_domain_rest),
                matches=None,
            ),
        )
        fig.layout["annotations"] = annotations
        fig.update_layout(
            yaxis2=dict(matches="y", showticklabels=show_y_labels_on_right_pane),
        )
        return

    fig.update_yaxes(matches="y")
    fig.update_yaxes(autorange=False)

    if top_row_label is not None:
        # Efficiency / C-rate families: top facet row gets a different quantity.
        fig.update_layout(
            yaxis3={
                "title": dict(text=top_row_label),
                "domain": [0.7, 1.0],
            },
            yaxis1=dict(domain=[0.0, 0.65]),
            yaxis2=dict(domain=[0.0, 0.65]),
            yaxis4=dict(domain=[0.70, 1.0]),
        )

    fig.update_layout(
        xaxis_domain=list(x_axis_domain_formation),
        scene_domain_x=list(x_axis_domain_formation),
    )

    resolved_ranges: list[list[float]] = []
    for row_index in range(n_rows):
        left = 2 * row_index + 1
        right = 2 * row_index + 2
        provided = None if row_y_ranges is None else row_y_ranges[row_index]
        if provided is not None:
            resolved_ranges.append(list(provided))
        else:
            resolved_ranges.append(
                auto_range(fig, _y_ref(left), _y_ref(right))
            )

    layout_updates: dict[str, Any] = {}
    for row_index in range(n_rows):
        left = 2 * row_index + 1
        right = 2 * row_index + 2
        y_range = resolved_ranges[row_index]

        if row_index == 0:
            layout_updates[_xaxis_key(right)] = dict(
                range=list(x_axis_range_rest),
                domain=list(x_axis_domain_rest),
                matches=None,
            )
        else:
            layout_updates[_xaxis_key(left)] = dict(
                range=list(x_axis_range_formation),
                domain=list(x_axis_domain_formation),
                matches="x",
            )
            layout_updates[_xaxis_key(right)] = dict(
                range=list(x_axis_range_rest),
                domain=list(x_axis_domain_rest),
                matches="x2",
            )

        layout_updates[_yaxis_key(left)] = dict(
            matches=_y_ref(right),
            range=y_range,
        )
        layout_updates[_yaxis_key(right)] = dict(
            matches=_y_ref(left),
            showticklabels=show_y_labels_on_right_pane,
            range=y_range,
        )

    fig.update_layout(**layout_updates)
    fig.layout["annotations"] = annotations


def configure_fullcell_standard_domains(
    fig: Any,
    *,
    plotly_row_ratios: Sequence[float],
    plotly_row_space: float,
    capacity_unit: str,
    y: str,
    show_formation: bool,
    x_axis_domain_formation_fraction: float,
    link_capacity_scales: bool,
    normalization_type: Any,
    normalization_factor: Optional[float],
    normalization_scaler: float,
) -> None:
    """Y-domain titles/ratios for fullcell_standard formation figures."""
    ce_domain_start, ce_domain_end = plotly_row_ratios[2], 1.0
    capacity_domain_start, capacity_domain_end = (
        plotly_row_ratios[1],
        plotly_row_ratios[2] - plotly_row_space,
    )
    loss_domain_start, loss_domain_end = (
        plotly_row_ratios[0],
        plotly_row_ratios[1] - plotly_row_space,
    )
    cv_domain_start, cv_domain_end = (
        0.0,
        plotly_row_ratios[0] - plotly_row_space,
    )

    ce_label = "Coulombic<br>Efficiency (%)"
    capacity_label = f"Capacity<br>({capacity_unit})"
    if normalization_type and normalization_factor is not None:
        _norm_label = (
            f"[{normalization_scaler:.1f}/{normalization_factor:.1f} {capacity_unit}]"
        )
        loss_label = f"Capacity<br>Retention (norm.)<br>{_norm_label}"
    else:
        loss_label = f"Capacity<br>Retention ({capacity_unit})"
    cv_label = f"CV Capacity<br>({capacity_unit})"

    fig.update_layout(
        yaxis8={"domain": [ce_domain_start, ce_domain_end]},
        yaxis7={
            "title": dict(text=ce_label),
            "domain": [ce_domain_start, ce_domain_end],
        },
        yaxis6={"domain": [capacity_domain_start, capacity_domain_end]},
        yaxis5={
            "title": dict(text=capacity_label),
            "domain": [capacity_domain_start, capacity_domain_end],
        },
        yaxis4={"domain": [loss_domain_start, loss_domain_end]},
        yaxis3={
            "title": dict(text=loss_label),
            "domain": [loss_domain_start, loss_domain_end],
        },
        yaxis2={"domain": [cv_domain_start, cv_domain_end]},
        yaxis1={
            "title": dict(text=cv_label),
            "domain": [cv_domain_start, cv_domain_end],
        },
    )
    if show_formation:
        fig.update_layout(xaxis1={"title": dict(text="")})
        if x_axis_domain_formation_fraction < 0.1:
            fig.update_layout(xaxis1={"showticklabels": False})

    if link_capacity_scales:
        fig.update_layout(
            yaxis={"matches": "y2"},
            yaxis2={"matches": "y3"},
            yaxis3={"matches": "y4"},
            yaxis4={"matches": "y5"},
            yaxis5={"matches": "y6"},
        )


class PlotlyBackend:
    """Plotly implementation of the :class:`~cellpy.plotting.backends.base.Backend` protocol.

    ``render(frame, spec)`` is the interactive path for public ``summary_plot``
    (#638). Layout knobs are expected on ``spec.extras['render']`` as produced
    by :mod:`cellpy.plotting.prepare.summary`.
    """

    name = "plotly"

    def __init__(self) -> None:
        self.y_header = "value"
        self.color = "variable"
        self.row = "row"
        self.col_id = "cycle_type"

    def render(self, frame: Any, spec: FigureSpec) -> Any:
        extras = dict(spec.extras or {})
        kind = extras.get("kind")
        if kind == "cycles":
            return self._render_cycles(frame, spec)
        if kind == "raw":
            return self._render_raw(frame, spec)
        if kind == "cycle_info":
            return self._render_cycle_info(frame, spec)
        if kind in ("ica", "dva"):
            return self._render_ica_dva(frame, spec)

        import plotly.express as px

        render = dict(extras.get("render") or {})
        prepared = dict(extras.get("prepared_data_info") or {})

        x = extras.get("x")
        if x is None:
            raise ValueError("FigureSpec.extras['x'] is required for PlotlyBackend.render")

        y_header = extras.get("y_header", self.y_header)
        color = extras.get("color", self.color)
        row = extras.get("row", self.row)
        col_id = extras.get("col_id", self.col_id)
        y = extras.get("y") or ""
        y_label = extras.get("y_label", y_header)
        x_label = prepared.get("x_label") or (spec.x_axis.label or x)
        number_of_rows = extras.get("number_of_rows") or prepared.get(
            "number_of_rows"
        ) or len(spec.panels) or 1

        additional_kwargs = dict(render.get("additional_kwargs") or {})
        smart_link = additional_kwargs.pop("smart_link", True)
        # Already consumed when building formation extras in prepare; drop so
        # they are not forwarded into px.line.
        additional_kwargs.pop("show_y_labels_on_right_pane", None)
        additional_kwargs.pop("fullcell_standard_row_height_ratios", None)
        additional_kwargs.pop("fullcell_standard_row_space", None)

        plotly_update_traces = {}
        for k in list(additional_kwargs.keys()):
            if k.startswith("plotly_"):
                plotly_update_traces[k.replace("plotly_", "")] = additional_kwargs.pop(k)

        title = render.get("title")
        if title is None:
            title = spec.title
        if title is None:
            cell_name = extras.get("cell_name") or ""
            title = f"Summary <b>{cell_name}</b>"

        plotly_kwargs: dict[str, Any] = {
            "color": color,
            "height": render.get("height"),
            "markers": render.get("markers", True),
            "title": title,
            "width": render.get("width", 900),
        }

        split = bool(render.get("split", True))
        if split and row in frame.columns:
            plotly_kwargs["facet_row"] = row

        hover_columns = render.get("hover_columns") or []
        if hover_columns:
            present = [h for h in hover_columns if h in frame.columns]
            if present:
                plotly_kwargs["hover_data"] = present

        if plotly_kwargs.get("height") is None:
            if y.startswith("fullcell_standard_"):
                plotly_kwargs["height"] = 800
            elif split and number_of_rows > 1:
                plotly_kwargs["height"] = 800
            else:
                plotly_kwargs["height"] = 200 + 200 * number_of_rows

        # Lazy import avoids a circular import with plotutils at module load.
        from cellpy.utils.plotutils import set_plotly_template

        set_plotly_template(render.get("plotly_template"))

        show_formation = bool(render.get("show_formation"))
        if show_formation and col_id in frame.columns:
            plotly_kwargs["facet_col"] = col_id

        fig = px.line(
            frame,
            x=x,
            y=y_header,
            **plotly_kwargs,
            labels={x: x_label, y_header: y_label},
            **additional_kwargs,
        )

        if plotly_update_traces:
            fig.update_traces(**plotly_update_traces)

        if not render.get("show_legend", True):
            fig.update_layout(showlegend=False)

        y_range = render.get("y_range")
        if y_range is not None:
            fig.update_layout(yaxis=dict(range=y_range))

        if show_formation:
            formation = dict(render.get("formation_layout") or {})
            if not formation:
                raise ValueError(
                    "FigureSpec.extras['render']['formation_layout'] is required "
                    "when show_formation is True"
                )
            configure_formation_layout(
                fig,
                n_rows=formation.get("n_rows") or number_of_rows,
                x_axis_domain_formation=formation["x_axis_domain_formation"],
                x_axis_domain_rest=formation["x_axis_domain_rest"],
                x_axis_range_formation=formation["x_axis_range_formation"],
                x_axis_range_rest=formation["x_axis_range_rest"],
                show_y_labels_on_right_pane=formation.get(
                    "show_y_labels_on_right_pane", False
                ),
                formation_header=DEFAULT_FORMATIONION_LABEL,
                row_y_ranges=formation.get("row_y_ranges"),
                top_row_label=formation.get("top_row_label"),
            )
            fullcell = formation.get("fullcell_standard_domains")
            if fullcell:
                configure_fullcell_standard_domains(fig, **fullcell)
        else:
            self._configure_no_formation_axes(
                fig, render.get("no_formation_layout") or {}
            )

        x_range = render.get("x_range")
        if x_range is not None and not show_formation:
            fig.update_layout(xaxis=dict(range=x_range))

        if split:
            if show_formation:
                if not render.get("share_y") and not smart_link:
                    fig.update_yaxes(matches=None)
            elif not render.get("share_y"):
                fig.update_yaxes(matches=None)

        if render.get("rangeslider"):
            if show_formation:
                logging.critical(
                    "Can not add rangeslider when showing formation cycles"
                )
            else:
                fig.update_layout(xaxis_rangeslider_visible=True)

        if render.get("auto_convert_legend_labels", True) and render.get(
            "show_legend", True
        ):
            self._convert_legend_labels(fig)

        return fig

    def _configure_no_formation_axes(self, fig: Any, layout: dict[str, Any]) -> None:
        """Configure axes when not showing formation cycles."""
        y = layout.get("y") or ""
        top_label = layout.get("top_row_label")
        if top_label is not None:
            fig.update_layout(
                yaxis=dict(domain=[0.0, 0.65]),
                yaxis2={
                    "title": dict(text=top_label),
                    "domain": [0.7, 1.0],
                },
            )
        if not y.startswith("fullcell_standard_"):
            return

        plotly_row_ratios = layout.get("plotly_row_ratios") or [0.3, 0.6, 0.9]
        plotly_row_space = layout.get("plotly_row_space", 0.02)
        max_val_normalized_col = layout.get("max_val_normalized_col") or 0.0
        eff_lim = layout.get("ce_range")

        range_1 = eff_lim or auto_range(fig, "y4", "y4")
        range_2 = layout.get("y_range") or auto_range(fig, "y3", "y3")
        range_3 = auto_range(fig, "y2", "y2")
        if layout.get("fullcell_standard_normalization_type") is not False:
            range_3 = [
                0.0,
                max(
                    max_val_normalized_col,
                    layout.get("fullcell_standard_normalization_scaler") or 1.0,
                ),
            ]
        range_3 = layout.get("norm_range") or range_3
        range_4 = layout.get("cv_share_range") or auto_range(fig, "y", "y")
        fig.layout["annotations"] = 4 * [PLOTLY_BLANK_LABEL]

        ce_domain_start, ce_domain_end = plotly_row_ratios[2], 1.0
        capacity_domain_start, capacity_domain_end = (
            plotly_row_ratios[1],
            plotly_row_ratios[2] - plotly_row_space,
        )
        loss_domain_start, loss_domain_end = (
            plotly_row_ratios[0],
            plotly_row_ratios[1] - plotly_row_space,
        )
        cv_domain_start, cv_domain_end = (
            0.0,
            plotly_row_ratios[0] - plotly_row_space,
        )

        capacity_unit = layout.get("capacity_unit") or "-"
        ce_label = "Coulombic<br>Efficiency (%)"
        capacity_label = f"Capacity<br>({capacity_unit})"
        if (
            layout.get("fullcell_standard_normalization_type")
            and layout.get("fullcell_standard_normalization_factor") is not None
        ):
            _norm_label = (
                f"[{layout['fullcell_standard_normalization_scaler']:.1f}/"
                f"{layout['fullcell_standard_normalization_factor']:.1f} "
                f"{capacity_unit}]"
            )
            loss_label = f"Capacity<br>Retention (norm.)<br>{_norm_label}"
        else:
            loss_label = f"Capacity<br>Retention ({capacity_unit})"
        cv_label = f"CV Capacity<br>({capacity_unit})"

        fig.update_layout(
            yaxis4={
                "title": dict(text=ce_label),
                "domain": [ce_domain_start, ce_domain_end],
                "matches": None,
                "range": range_1,
            },
            yaxis3={
                "title": dict(text=capacity_label),
                "domain": [capacity_domain_start, capacity_domain_end],
                "matches": None,
                "range": range_2,
            },
            yaxis2={
                "title": dict(text=loss_label),
                "domain": [loss_domain_start, loss_domain_end],
                "matches": None,
                "range": range_3,
            },
            yaxis={
                "title": dict(text=cv_label),
                "domain": [cv_domain_start, cv_domain_end],
                "matches": None,
                "range": range_4,
            },
        )

    @staticmethod
    def _convert_legend_labels(fig: Any) -> None:
        """Convert legend labels to nicer format."""
        for trace in fig.data:
            name = trace.name
            name = name.replace("_", " ").title()
            name = name.replace("Gravimetric", "Grav.")
            name = name.replace("Cv", "(CV)")
            name = name.replace("Non (CV)", "(without CV)")
            hover_template = trace.hovertemplate
            if hover_template:
                statements = []
                for statement in hover_template.split("<br>"):
                    if "=" in statement:
                        variable, value = statement.split("=", 1)
                        if value.startswith("%{y}"):
                            variable = name
                        statement = "=".join((variable, value))
                    statements.append(statement)
                hover_template = "<br>".join(statements)
            trace.update(name=name, hovertemplate=hover_template)

    def _render_cycles(self, frame: Any, spec: FigureSpec) -> Any:
        """Render voltage–capacity cycles figures (#646).

        Mechanical port of ``plotutils._cycles_plotter_plotly``.
        """
        from cellpycore.config import CurveCols

        import plotly.express as px
        import plotly.graph_objects as go

        from cellpy.units import with_cellpy_unit
        from cellpy.utils.plotutils import set_plotly_template

        ccols = CurveCols()
        extras = dict(spec.extras or {})
        c = extras.get("cell")
        if c is None:
            raise ValueError(
                "FigureSpec.extras['cell'] is required for cycles PlotlyBackend.render"
            )

        form_cycles = extras.get("form_cycles")
        rest_cycles = extras.get("rest_cycles")
        if form_cycles is None or rest_cycles is None:
            raise ValueError(
                "FigureSpec.extras must include 'form_cycles' and 'rest_cycles'"
            )

        set_plotly_template(extras.get("plotly_template"))
        kwargs = dict(extras.get("additional_kwargs") or {})
        plotly_max_individual_traces_for_lines = kwargs.pop(
            "plotly_max_individual_traces_for_lines", 8
        )

        colormap = extras.get("colormap") or "Blues_r"
        color_scales = px.colors.named_colorscales()
        if colormap not in color_scales:
            colormap = "Blues_r"

        capacity_unit = extras.get("capacity_unit") or "-"
        capacity_label = extras.get("capacity_label") or f"Capacity ({capacity_unit})"
        voltage_label = extras.get("voltage_label") or with_cellpy_unit(
            "Voltage", "voltage", units=c.cellpy_units
        )
        fig_title = spec.title
        n_rest_cycles = extras.get("n_rest_cycles")
        cut_colorbar = bool(extras.get("cut_colorbar", True))
        force_colorbar = bool(extras.get("force_colorbar", False))
        force_nonbar = bool(extras.get("force_nonbar", False))
        show_formation = bool(extras.get("show_formation", True))
        marker_size = extras.get("marker_size", 5)
        formation_line_color = extras.get(
            "formation_line_color", "rgba(152, 0, 0, .8)"
        )
        width = extras.get("width", 800)
        height = extras.get("height", 600)
        x_range = extras.get("x_range")
        y_range = extras.get("y_range")

        if cut_colorbar:
            range_color = [
                frame[ccols.cycle_num].min(),
                1.2 * frame[ccols.cycle_num].max(),
            ]
        else:
            range_color = [
                frame[ccols.cycle_num].min(),
                frame[ccols.cycle_num].max(),
            ]

        if (
            n_rest_cycles is not None
            and n_rest_cycles < plotly_max_individual_traces_for_lines
            and not force_colorbar
        ) or force_nonbar:
            logger.info("using px.line for non-formation cycles")
            show_formation_legend = True
            cmap = px.colors.sample_colorscale(
                colorscale=colormap,
                samplepoints=n_rest_cycles,
                low=0.0,
                high=0.8,
                colortype="rgb",
            )
            fig = px.line(
                rest_cycles,
                x="capacity",
                y=ccols.potential,
                color=ccols.cycle_num,
                title=fig_title,
                labels={
                    "capacity": capacity_label,
                    ccols.potential: voltage_label,
                },
                color_discrete_sequence=cmap,
            )
        else:
            logger.info("using px.scatter for non-formation cycles")
            show_formation_legend = False
            fig = px.scatter(
                rest_cycles,
                x="capacity",
                y=ccols.potential,
                title=fig_title,
                color=ccols.cycle_num,
                labels={
                    "capacity": capacity_label,
                    ccols.potential: voltage_label,
                },
                color_continuous_scale=colormap,
                range_color=range_color,
            )
            fig.update_traces(mode="lines+markers", line_color="white", line_width=1)

        if not form_cycles.empty and show_formation:
            for name, group in form_cycles.groupby(ccols.cycle_num):
                logger.info("using go.Scatter for formation cycle(s) %s", name)
                fig.add_trace(
                    go.Scatter(
                        x=group["capacity"],
                        y=group[ccols.potential],
                        name=f"{name} (f.c.)",
                        hovertemplate=(
                            f"Formation Cycle {name}<br>Capacity: %{{x}}<br>Voltage: %{{y}}"
                        ),
                        mode="lines",
                        marker=dict(color=formation_line_color),
                        showlegend=show_formation_legend,
                        legendrank=1,
                        legendgroup="formation",
                    )
                )

        fig.update_traces(marker=dict(size=marker_size))
        if x_range:
            fig.update_xaxes(range=x_range)
        if y_range:
            fig.update_yaxes(range=y_range)

        plotly_xaxes_kwargs = kwargs.pop("plotly_xaxes_kwargs", {})
        plotly_yaxes_kwargs = kwargs.pop("plotly_yaxes_kwargs", {})
        if plotly_xaxes_kwargs:
            fig.update_xaxes(**plotly_xaxes_kwargs)
        if plotly_yaxes_kwargs:
            fig.update_yaxes(**plotly_yaxes_kwargs)
        plotly_layout_kwargs = kwargs.pop("plotly_layout_kwargs", {})
        fig.update_layout(height=height, width=width, **plotly_layout_kwargs)
        return fig

    def _render_raw(self, frame: Any, spec: FigureSpec) -> Any:
        """Render raw time-series figures (#647)."""
        import plotly.express as px
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        extras = dict(spec.extras or {})
        if extras.get("unsupported_plot_type"):
            return None

        kwargs = dict(extras.get("additional_kwargs") or {})
        x = extras["x"]
        x_label = extras.get("x_label") or (spec.x_axis.label or x)
        y = list(extras["y"])
        y_label = list(extras["y_label"])
        title = spec.title or ""
        if not title.startswith("<b>"):
            title = f"<b>{title}</b>"
        special_height = extras.get("special_height")
        number_of_rows = len(y)

        if number_of_rows == 1:
            labels = {}
            if x_label:
                labels[x] = x_label
            if y_label:
                labels[y[0]] = y_label[0]
            return px.line(
                frame,
                x=x,
                y=y[0],
                title=title,
                labels=labels or None,
                **kwargs,
            )

        width = kwargs.pop("width", 1000)
        height = kwargs.pop("height", None)
        if height is None:
            height = special_height if special_height is not None else number_of_rows * 300
        vertical_spacing = kwargs.pop("vertical_spacing", 0.02)
        fig = make_subplots(
            rows=number_of_rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=vertical_spacing,
            x_title=x_label,
        )
        x_values = frame[x]
        for i in range(number_of_rows):
            fig.add_trace(
                go.Scatter(x=x_values, y=frame[y[i]], name=y_label[i]),
                row=i + 1,
                col=1,
                **kwargs,
            )
        fig.update_layout(height=height, width=width, title_text=title)
        return fig

    def _render_cycle_info(self, frame: Any, spec: FigureSpec) -> Any:
        """Render cycle-info overlay figures (#647)."""
        import numpy as np
        import plotly.graph_objects as go

        extras = dict(spec.extras or {})
        kwargs = dict(extras.get("additional_kwargs") or {})
        cycle_hdr = extras["cycle_hdr"]
        time_hdr = extras["time_hdr"]
        voltage_hdr = extras["voltage_hdr"]
        step_number_hdr = extras["step_number_hdr"]
        current_hdr = extras["current_hdr"]
        type_ = extras["type_hdr"]
        v_delta = extras["v_delta"]
        i_delta = extras["i_delta"]
        c_delta = extras["c_delta"]
        dc_delta = extras["dc_delta"]
        t_unit = extras["t_unit"]
        v_unit = extras["v_unit"]
        i_unit = extras["i_unit"]

        if kwargs.get("xlim"):
            logging.info("xlim is not supported for plotly yet")

        fig = go.Figure()
        for cycle_number, group in frame.groupby(cycle_hdr):
            fig.add_trace(
                go.Scatter(
                    x=group[time_hdr],
                    y=group[voltage_hdr],
                    mode="lines",
                    name=f"cycle {cycle_number}",
                    customdata=np.stack(
                        (
                            group[current_hdr],
                            group[step_number_hdr],
                            group[type_],
                            group[v_delta],
                            group[i_delta],
                            group[c_delta],
                            group[dc_delta],
                        ),
                        axis=-1,
                    ),
                    hovertemplate="<br>".join(
                        [
                            "<b>Time: %{x:.2f}" + f" {t_unit}" + "</b>",
                            "  <b>Voltage:</b> %{y:.4f}" + f" {v_unit}",
                            "  <b>Current:</b> %{customdata[0]:.4f}" + f" {i_unit}",
                            "<b>Step: %{customdata[1]} (%{customdata[2]})</b>",
                            "  <b>ΔV:</b> %{customdata[3]:.2f}",
                            "  <b>ΔI:</b> %{customdata[4]:.2f}",
                            "  <b>ΔCh:</b> %{customdata[5]:.2f}",
                            "  <b>ΔDCh:</b> %{customdata[6]:.2f}",
                        ]
                    ),
                ),
            )

        height = kwargs.get("height", 600)
        width = kwargs.get("width", 1000)
        y_title = (
            spec.panels[0].y_axis.label
            if spec.panels
            else f"Voltage ({v_unit})"
        )
        fig.update_layout(
            title=spec.title,
            xaxis_title=spec.x_axis.label or f"Time ({t_unit})",
            yaxis_title=y_title,
            width=width,
            height=height,
        )
        return fig

    def _render_ica_dva(self, frame: Any, spec: FigureSpec) -> Any:
        """Render ICA (dQ/dV) or DVA (dV/dQ) figures (#648).

        One trace per ``(cycle, direction)`` so half-cycles are not connected;
        color is keyed by cycle. Hover includes direction. Line style is shared
        across charge and discharge. Cycle legend vs colorbar via
        :mod:`cellpy.plotting.cycle_legend`.
        """
        import plotly.express as px
        import plotly.graph_objects as go

        from cellpy.ica import ICA_COLS
        from cellpy.plotting.cycle_legend import (
            add_plotly_cycle_colorbar,
            pop_cycle_legend_options,
            resolve_cycle_legend_mode,
        )
        from cellpy.utils.plotutils import set_plotly_template

        extras = dict(spec.extras or {})
        kwargs = dict(extras.get("additional_kwargs") or {})
        set_plotly_template(extras.get("plotly_template"))
        legend_opts = pop_cycle_legend_options(extras, kwargs)

        x_col = extras.get("x") or ICA_COLS.voltage
        y_col = extras.get("y") or ICA_COLS.dqdv
        x_label = extras.get("x_label") or (spec.x_axis.label or x_col)
        y_label = extras.get("y_label") or y_col
        colormap = extras.get("colormap") or "viridis"
        color_scales = px.colors.named_colorscales()
        if colormap not in color_scales:
            colormap = "viridis"

        marker_size = extras.get("marker_size", 5)
        width = extras.get("width", 800)
        height = extras.get("height", 600)
        x_range = extras.get("x_range")
        y_range = extras.get("y_range")

        cycles = sorted(frame[ICA_COLS.cycle].unique())
        n_cycles = len(cycles)
        mode = resolve_cycle_legend_mode(n_cycles, **legend_opts)
        use_legend = mode == "legend"

        sample_n = max(n_cycles, 1)
        samplepoints = [
            0.0 if sample_n == 1 else i / (sample_n - 1) for i in range(sample_n)
        ]
        colors = px.colors.sample_colorscale(colormap, samplepoints=samplepoints)
        cycle_to_color = {cycle: colors[i] for i, cycle in enumerate(cycles)}

        fig = go.Figure()
        shown_cycles: set[Any] = set()
        group_cols = [ICA_COLS.cycle, ICA_COLS.direction]
        for (cycle, direction), group in frame.groupby(group_cols, sort=True):
            color = cycle_to_color[cycle]
            show_legend = use_legend and cycle not in shown_cycles
            if show_legend:
                shown_cycles.add(cycle)
            fig.add_trace(
                go.Scatter(
                    x=group[x_col],
                    y=group[y_col],
                    mode="lines",
                    name=str(cycle),
                    legendgroup=str(cycle),
                    showlegend=show_legend,
                    line=dict(color=color, width=1.5),
                    customdata=group[[ICA_COLS.cycle, ICA_COLS.direction]],
                    hovertemplate=(
                        f"{x_label}: %{{x}}<br>"
                        f"{y_label}: %{{y}}<br>"
                        "cycle: %{customdata[0]}<br>"
                        "direction: %{customdata[1]}<extra></extra>"
                    ),
                )
            )

        if not use_legend and cycles:
            add_plotly_cycle_colorbar(fig, cycles=list(cycles), colormap=colormap)

        layout_kwargs: dict[str, Any] = {
            "title": spec.title,
            "width": width,
            "height": height,
        }
        if use_legend:
            layout_kwargs["legend_title_text"] = "cycle"
        else:
            layout_kwargs["showlegend"] = False
        fig.update_layout(**layout_kwargs)
        fig.update_xaxes(title_text=x_label, range=x_range)
        fig.update_yaxes(title_text=y_label, range=y_range)
        _ = marker_size
        return fig
