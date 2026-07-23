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
        import plotly.express as px

        extras = dict(spec.extras or {})
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
