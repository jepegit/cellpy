"""Shared cycle legend vs colorbar policy for multi-cycle plots (#648).

Several figure families colour traces by cycle number. A discrete legend
works for a handful of cycles and overflows once the list grows. This
module owns the **decision** (and small apply helpers) so matplotlib /
plotly backends — and future families — share one rule.

Default threshold matches ``cycles_plot``'s
``plotly_max_individual_traces_for_lines`` (8).

Override knobs (accepted from ``FigureSpec.extras`` or
``additional_kwargs``):

- ``legend_cycle_limit`` — max cycles that still get a discrete legend
- ``force_colorbar`` — always use a colorbar
- ``force_legend`` / ``force_nonbar`` — always use a discrete legend
"""

from __future__ import annotations

from typing import Any, Literal, Mapping, MutableMapping

CycleLegendMode = Literal["legend", "colorbar"]

#: Max number of cycles for which a discrete legend is preferred.
DEFAULT_LEGEND_CYCLE_LIMIT = 8


def resolve_cycle_legend_mode(
    n_cycles: int,
    *,
    legend_cycle_limit: int = DEFAULT_LEGEND_CYCLE_LIMIT,
    force_colorbar: bool = False,
    force_legend: bool = False,
) -> CycleLegendMode:
    """Choose discrete legend vs colorbar for a cycle-coloured figure.

    Args:
        n_cycles: Number of distinct cycle values being drawn.
        legend_cycle_limit: Prefer a legend when ``n_cycles`` is at most this.
        force_colorbar: Always return ``"colorbar"``.
        force_legend: Always return ``"legend"`` (wins over ``force_colorbar``,
            matching the ``force_nonbar`` escape hatch on ``cycles_plot``).

    Returns:
        ``"legend"`` or ``"colorbar"``.
    """
    if force_legend:
        return "legend"
    if force_colorbar:
        return "colorbar"
    if n_cycles <= legend_cycle_limit:
        return "legend"
    return "colorbar"


def pop_cycle_legend_options(
    extras: Mapping[str, Any] | None = None,
    kwargs: MutableMapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Pull shared cycle-legend knobs from extras / kwargs.

    Values in *kwargs* win over *extras*. Consumed keys are removed from
    *kwargs* when it is a mutable mapping.

    Returns:
        Dict with ``legend_cycle_limit``, ``force_colorbar``, ``force_legend``
        ready to splat into :func:`resolve_cycle_legend_mode`.
    """
    extras = dict(extras or {})
    source = dict(kwargs) if kwargs is not None else {}

    def _take(key: str, default: Any) -> Any:
        if kwargs is not None and key in kwargs:
            return kwargs.pop(key)
        if key in source:
            return source[key]
        return extras.get(key, default)

    force_legend = bool(_take("force_legend", False))
    if not force_legend:
        # Alias used by cycles_plot today.
        force_legend = bool(_take("force_nonbar", False))

    return {
        "legend_cycle_limit": int(
            _take("legend_cycle_limit", DEFAULT_LEGEND_CYCLE_LIMIT)
        ),
        "force_colorbar": bool(_take("force_colorbar", False)),
        "force_legend": force_legend,
    }


def add_matplotlib_cycle_colorbar(
    fig: Any,
    ax: Any,
    *,
    cmap: Any,
    norm: Any,
    label: str = "cycle",
    aspect: int = 30,
) -> Any:
    """Attach a cycle colorbar to a matplotlib axes.

    Args:
        fig: Matplotlib figure.
        ax: Axes that owns the cycle-coloured lines.
        cmap: Matplotlib colormap.
        norm: Normalize spanning the cycle range.
        label: Colorbar label.
        aspect: Colorbar aspect ratio.

    Returns:
        The colorbar instance.
    """
    from matplotlib.cm import ScalarMappable

    mappable = ScalarMappable(norm=norm, cmap=cmap)
    mappable.set_array([])
    cbar = fig.colorbar(mappable, ax=ax, aspect=aspect, location="right")
    cbar.set_label(label, rotation=270, labelpad=12)
    return cbar


def add_plotly_cycle_colorbar(
    fig: Any,
    *,
    cycles: list[Any],
    colormap: str = "viridis",
    title: str = "cycle",
) -> None:
    """Attach a cycle colorbar to a plotly figure via a hidden scale trace.

    Line traces keep explicit colours; this only adds the scale widget so the
    figure does not also need a long discrete legend.
    """
    import plotly.graph_objects as go

    if not cycles:
        return
    cmin = float(min(cycles))
    cmax = float(max(cycles))
    if cmin == cmax:
        cmin -= 0.5
        cmax += 0.5
    fig.add_trace(
        go.Scatter(
            x=[None],
            y=[None],
            mode="markers",
            marker=dict(
                size=0.1,
                color=[cmin],
                colorscale=colormap,
                cmin=cmin,
                cmax=cmax,
                showscale=True,
                colorbar=dict(title=title),
            ),
            hoverinfo="skip",
            showlegend=False,
        )
    )
