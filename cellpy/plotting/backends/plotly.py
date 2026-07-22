"""Plotly backend: generic formation/facet layout + render protocol (#637).

The four ``PlotlyPlotBuilder._configure_formation_{1,2,3,4}_rows`` methods are
collapsed into :func:`configure_formation_layout`. ``PlotlyPlotBuilder`` keeps
ownership of ``px.line`` construction and the no-formation path; this module
owns the formation axis grid.
"""

from __future__ import annotations

import logging
import os
import warnings
from copy import deepcopy
from typing import Any, Optional, Sequence

import numpy as np

from cellpy.plotting.spec import FigureSpec

logger = logging.getLogger(__name__)

#: Internal switch for the provisional ``PlotlyBackend.render`` path from
#: ``summary_plot``. Default off — public prepare→spec→render lands in #638.
SPEC_RENDER_ENV = "CELLPY_SUMMARY_PLOTLY_SPEC"

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

FORMATIONATION_HEADER = '<span style="color:red">Formation</span>'
MAX_FORMATIONATION_ROWS = 4


def use_spec_render() -> bool:
    """True when the provisional ``(frame, FigureSpec)`` render path is enabled."""
    value = os.environ.get(SPEC_RENDER_ENV, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


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
    formation_header: str = FORMATION_HEADER,
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

    Full prepare→spec→render ownership arrives in #638. Until then this class
    is available for the optional ``CELLPY_SUMMARY_PLOTLY_SPEC`` path and for
    layout helpers used by ``PlotlyPlotBuilder``.
    """

    name = "plotly"

    def render(self, frame: Any, spec: FigureSpec) -> Any:
        import plotly.express as px

        extras = dict(spec.extras or {})
        x = extras.get("x")
        y_header = extras.get("y_header", "value")
        if x is None:
            raise ValueError("FigureSpec.extras['x'] is required for PlotlyBackend.render")

        plotly_kwargs = dict(extras.get("plotly_kwargs") or {})
        labels = {
            x: (spec.x_axis.label or x),
            y_header: extras.get("y_label", y_header),
        }
        if spec.title is not None:
            plotly_kwargs.setdefault("title", spec.title)

        fig = px.line(frame, x=x, y=y_header, labels=labels, **plotly_kwargs)

        if extras.get("show_formation"):
            configure_formation_layout(
                fig,
                n_rows=extras.get("n_rows") or len(spec.panels) or 1,
                x_axis_domain_formation=extras["x_axis_domain_formation"],
                x_axis_domain_rest=extras["x_axis_domain_rest"],
                x_axis_range_formation=extras["x_axis_range_formation"],
                x_axis_range_rest=extras["x_axis_range_rest"],
                show_y_labels_on_right_pane=extras.get(
                    "show_y_labels_on_right_pane", False
                ),
                row_y_ranges=extras.get("row_y_ranges"),
                top_row_label=extras.get("top_row_label"),
            )
            fullcell = extras.get("fullcell_standard_domains")
            if fullcell:
                configure_fullcell_standard_domains(fig, **fullcell)

        return fig
