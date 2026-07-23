"""Collected-frame plotting: multi-cell layout/kind render (#657).

Collectors own collection; this module owns drawing for already-tidy frames
with ``cell`` / ``group`` / ``sub_group`` columns. Public entry:
:func:`collected_plot` → ``FigureSpec`` → backend.render.
"""

from __future__ import annotations

import functools
import logging
import math
import warnings
from typing import Any, Optional

import numpy as np
import pandas as pd

from cellpycore.config import CurveCols
from cellpy.parameters.internal_settings import get_headers_journal
from cellpy.plotting.labels import legend_replacer, remove_markers
from cellpy.plotting import theme
from cellpy.plotting.spec import FigureSpec

logger = logging.getLogger(__name__)

_CCOLS = CurveCols()
hdr_journal = get_headers_journal()

DEFAULT_CYCLES = [1, 10, 20]
PLOTLY_BASE_TEMPLATE = "plotly"
MAX_POINTS_SEABORN_FACET_GRID = 60_000

supported_backends: list[str] = []
px = None
go = None
pio = None
plt = None
sns = None

try:
    import plotly
    import plotly.express as px
    import plotly.graph_objects as go
    import plotly.io as pio

    supported_backends.append("plotly")
except ImportError:
    plotly = None  # type: ignore[assignment]

try:
    import matplotlib.pyplot as plt

    # matplotlib alone is not a collectors layout backend; seaborn owns that path.
except ImportError:
    plt = None

try:
    import seaborn as sns

    supported_backends.append("seaborn")
except ImportError:
    sns = None


# Internal plotter implementations (moved from collectors.py; #657)




def _hist_eq(trace):
    z = histogram_equalization(trace.z)
    trace.update(z=z)
    return trace


def y_axis_replacer(ax, label):
    """Replace y-axis label in matplotlib plots."""
    if isinstance(label, dict):
        _label = label.get(ax.title.text, None)
        if _label is None:
            _label = list(label.values())[0]
        ax.update(title_text=_label)
    else:
        ax.update(title_text=label)
    return ax




def _plotly_y_label_cleaner(y_label_mapper, split_at=20):
    """Clean up the y-label mapper for plotly.

    The y-label mapper is a dictionary that maps the variable name to the y-label. The y-labels are
    expected to be in the form of "Variable Name (unit)". If the y-label is too long, it is
    split into multiple lines.
    This is done to avoid the y-labels from being too long and wrapping around.

    Discharge Capacity Retention Gravimetric Norm (%) should become:
    Discharge Capacity<br>Retention Gravimetric Norm<br>(%)

    Args:
        y_label_mapper (dict): the y-label mapper.

    Returns:
        dict: the cleaned up y-label mapper.

    """

    new_y_label_mapper = {}
    for k, v in y_label_mapper.items():
        if len(v) > split_at:
            # First split on " (" pattern
            v = "<br>(".join(v.split(" ("))

            # Then check if any resulting line is still too long and split on spaces
            lines = v.split("<br>")
            final_lines = []
            for line in lines:
                if len(line) > split_at and " " in line:
                    # Split long lines on spaces
                    words = line.split(" ")
                    current_line = ""
                    for word in words:
                        if len(current_line + " " + word) > split_at and current_line:
                            final_lines.append(current_line)
                            current_line = word
                        else:
                            if current_line:
                                current_line += " " + word
                            else:
                                current_line = word
                    if current_line:
                        final_lines.append(current_line)
                else:
                    final_lines.append(line)
            v = "<br>".join(final_lines)
        new_y_label_mapper[k] = v
    return new_y_label_mapper


def spread_plot(curves, plotly_arguments=None, y_label_mapper=None, **kwargs):
    """Create a spread plot (error-bands instead of error-bars).

    This is an experimental feature that is not yet fully tested. It uses make_subplots to create the figure,
    and then adds the traces one by one. This methodology will eventually replace the use of plotly.express
    for all the summary plots.

    """
    from plotly.subplots import make_subplots

    if y_label_mapper is None:
        y_label_mapper = {}
    else:
        y_label_mapper = _plotly_y_label_cleaner(y_label_mapper)

    selected_variables = curves["variable"].unique()
    number_of_rows = len(selected_variables)
    # TODO: change this (only temporary fix to allow height fractions to be set by spread_plot)
    height_fractions = kwargs.get(
        "height_fractions_spread", [1 / number_of_rows] * number_of_rows
    )

    colors = plotly.colors.qualitative.Plotly
    opacity = 0.2
    color_list = []
    for color in colors:
        color_rgb = plotly.colors.hex_to_rgb(color)
        color_rgb_main = f"rgb({color_rgb[0]}, {color_rgb[1]}, {color_rgb[2]})"
        color_rgba_spread = (
            f"rgba({color_rgb[0]}, {color_rgb[1]}, {color_rgb[2]}, {opacity})"
        )
        color_list.append((color_rgb_main, color_rgba_spread))

    if plotly_arguments.get("markers"):
        mode = "lines+markers"
    else:
        mode = "lines"

    g = curves.groupby("cell")
    fig = make_subplots(
        rows=number_of_rows,
        cols=1,
        start_cell=plotly_arguments.get("plotly_start_cell", "top-left"),
        shared_xaxes=plotly_arguments.get("plotly_shared_xaxes", True),
        row_heights=height_fractions,
        vertical_spacing=plotly_arguments.get("plotly_vertical_spacing", 0.01),
    )
    y_labels = {}
    for i, (cell, data) in enumerate(g):
        color = color_list[i % len(color_list)]

        for row_number, variable in enumerate(selected_variables):
            y_label = y_label_mapper.get(variable, variable)
            y_labels[row_number] = y_label
            if row_number == 0:
                show_legend = True
            else:
                show_legend = False
            sub_data = data[data["variable"] == variable]
            fig.add_trace(
                go.Scatter(
                    name=cell,
                    x=sub_data["cycle"],
                    y=sub_data["mean"],
                    mode=mode,
                    line=dict(color=color[0]),
                    legendgroup=cell,
                    legendgrouptitle=None,
                    showlegend=show_legend,
                ),
                row=row_number + 1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    name=f"Upper Bound {cell}",
                    x=sub_data["cycle"],
                    y=sub_data["mean"] + sub_data["std"],
                    mode="lines",
                    marker=dict(
                        color=color[1],
                    ),
                    line=dict(width=0),
                    showlegend=False,
                    legendgroup=cell,
                ),
                row=row_number + 1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    name=f"Lower Bound {cell}",
                    x=sub_data["cycle"],
                    y=sub_data["mean"] - sub_data["std"],
                    mode="lines",
                    marker=dict(
                        color=color[1],
                    ),
                    line=dict(width=0),
                    fillcolor=color[1],
                    fill="tonexty",
                    showlegend=False,
                    legendgroup=cell,
                ),
                row=row_number + 1,
                col=1,
            )
    for row_number, y_label in y_labels.items():
        fig.update_yaxes(title_text=y_label, row=row_number + 1, col=1)

    fig.update_layout(legend_tracegroupgap=0)
    # fig.update_layout(hovermode="x")

    if labels := plotly_arguments.get("labels"):
        fig.update_xaxes(title=labels.get("cycle", None), row=number_of_rows)

    # Hack to remove the x-axis title that appears on the top of the plot:
    # if number_of_rows > 1:
    #     fig.update_layout(xaxis_title=None)

    if hover_mode := kwargs.pop("hovermode", None):
        fig.update_layout(hovermode=hover_mode)

    return fig


def _select_direction(curves, direction, direction_col="direction"):
    """Select one direction from a collected curve frame.

    Handles both direction encodings that reach the plotters:

    - The specced ICA frame (#566) spells direction out ("charge" /
      "discharge"), **cell-centric** per decision #591.
    - Frames straight from ``get_cap(categorical_column=True)`` still carry
      the raw ±1 half-cycle code. For those the historical mapping is kept
      (-1 selected as "charge") so non-ICA film plots are unchanged; the code
      is positional, and relabelling it needs the cell's cycle_mode, which a
      collected frame no longer knows.
    """
    if direction_col not in curves.columns:
        logging.debug(
            "no %r column in the collected frame - direction filter skipped",
            direction_col,
        )
        return curves

    column = curves[direction_col]
    if pd.api.types.is_numeric_dtype(column):
        if direction == "charge":
            return curves.loc[column < 0]
        if direction == "discharge":
            return curves.loc[column > 0]
        return curves

    return curves.loc[column == direction]


def sequence_plotter(
    collected_curves: pd.DataFrame,
    x: str = _CCOLS.capacity,
    y: str = _CCOLS.potential,
    z: str = _CCOLS.cycle_num,
    g: str = "cell",
    standard_deviation: str = None,
    group: str = hdr_journal.group,
    subgroup: str = hdr_journal.sub_group,
    x_label: str = "Capacity",
    x_unit: str = "mAh/g",
    y_label: str = "Voltage",
    y_unit: str = "V",
    z_label: str = "Cycle",
    z_unit: str = "n.",
    y_label_mapper: dict = None,
    nbinsx: int = 100,
    histfunc: str = "avg",
    histscale: str = "abs-log",
    direction: str = "charge",
    direction_col: str = "direction",
    method: str = "fig_pr_cell",
    markers: bool = False,
    group_cells: bool = True,
    group_legend_muting: bool = True,
    backend: str = "plotly",
    cycles: list = None,
    facetplot: bool = False,
    cols: int = 3,
    palette_discrete: str = None,
    palette_continuous: str = "Viridis",
    palette_range: tuple = None,
    height: float = None,
    width: float = None,
    spread: bool = False,
    **kwargs,
) -> Any:
    """Create a plot made up of sequences of data (voltage curves, dQ/dV, etc).

    This method contains the "common" operations done for all the sequence plots,
    currently supporting filtering out the specific cycles, selecting either
    dividing into subplots by cell or by cycle, and creating the (most basic) figure object.

    Args:
        collected_curves (pd.DataFrame): collected data in long format.
        x (str): column name for x-values.
        y (str): column name for y-values.
        z (str): if method is 'fig_pr_cell', column name for color (legend), else for subplot.
        g (str): if method is 'fig_pr_cell', column name for subplot, else for color.
        standard_deviation: str = standard deviation column (skipped if None).
        group (str): column name for group.
        subgroup (str): column name for subgroup.
        x_label (str): x-label.
        x_unit (str): x-unit (will be put in parentheses after the label).
        y_label (str): y-label.
        y_unit (str): y-unit (will be put in parentheses after the label).
        z_label (str): z-label.
        z_unit (str): z-unit (will be put in parentheses after the label).
        y_label_mapper (dict): map the y-labels to something else.
        nbinsx (int): number of bins to use in interpolations.
        histfunc (str): aggregation method.
        histscale (str): used for scaling the z-values for 2D array plots (heatmaps and similar).
        direction (str): "charge", "discharge", or "both".
        direction_col (str): name of columns containing information about direction ("charge" or "discharge").
        method: 'fig_pr_cell' or 'fig_pr_cycle'.
        markers: set to True if you want markers.
        group_cells (bool): give each cell within a group same color.
        group_legend_muting (bool): if True, you can click on the legend to mute the whole group (only for plotly).
        backend (str): what backend to use.
        cycles: what cycles to include in the plot.
        palette_discrete: palette to use for discrete color mapping.
        palette_continuous: palette to use for continuous color mapping.
        palette_range (tuple): range of palette to use for continuous color mapping (from 0 to 1).
        facetplot (bool): square layout with group horizontally and subgroup vertically.
        cols (int): number of columns for layout.
        height (int): plot height.
        width (int): plot width.
        spread (bool): plot error-bands instead of error-bars if True.

        **kwargs: sent to backend (if `backend == "plotly"`, it will be
            sent to `plotly.express` etc.)

    Returns:
        figure object
    """
    logging.debug("running sequence plotter")

    for k in kwargs:
        logging.debug(f"keyword argument sent to the backend: {k}")
    if backend not in supported_backends:
        print(f"Backend '{backend}' not supported", end="")
        print(f" - supported backends: {supported_backends}")
        return
    curves = None

    # ----------------- parsing arguments -----------------------------

    if method == "film":
        labels = {
            f"{x}": f"{x_label} ({x_unit})",
            f"{z}": f"{z_label} ({z_unit})",
        }
        plotly_arguments = dict(
            x=x,
            y=z,
            z=y,
            labels=labels,
            facet_col_wrap=cols,
            nbinsx=nbinsx,
            histfunc=histfunc,
        )

        seaborn_arguments = dict(x=x, y=z, z=y, labels=labels, row=g, col=subgroup)

    elif method == "summary":
        labels = {
            f"{x}": f"{x_label} ({x_unit})",
        }
        plotly_arguments = dict(x=x, y=y, labels=labels, markers=markers)
        seaborn_arguments = dict(x=x, y=y, markers=markers)
        seaborn_arguments["labels"] = labels

        if g == "variable" and len(collected_curves[g].unique()) > 1:
            plotly_arguments["facet_row"] = g
            seaborn_arguments["row"] = g
        if standard_deviation:
            plotly_arguments["error_y"] = standard_deviation
            seaborn_arguments["error_y"] = standard_deviation

    else:
        labels = {
            f"{x}": f"{x_label} ({x_unit})",
            f"{y}": f"{y_label} ({y_unit})",
        }
        plotly_arguments = dict(x=x, y=y, labels=labels, facet_col_wrap=cols)
        seaborn_arguments = dict(x=x, y=y, labels=labels, row=group, col=subgroup)

    if method in ["fig_pr_cell", "film"]:
        group_cells = False
        if method == "fig_pr_cell":
            plotly_arguments["markers"] = markers
            plotly_arguments["color"] = z
            seaborn_arguments["hue"] = z
        if facetplot:
            plotly_arguments["facet_col"] = group
            plotly_arguments["facet_row"] = subgroup
            plotly_arguments["hover_name"] = g
        else:
            plotly_arguments["facet_col"] = g

        if cycles is not None:
            curves = collected_curves.loc[collected_curves.cycle.isin(cycles), :]
        else:
            curves = collected_curves
        logging.debug(f"filtered_curves:\n{curves}")

        if method == "film":
            curves = _select_direction(curves, direction, direction_col)
            # scaling (assuming 'y' is the "value" axis):
            if histscale == "abs-log":
                curves[y] = curves[y].apply(np.abs).apply(np.log)
            elif histscale == "abs":
                curves[y] = curves[y].apply(np.abs)
            elif histscale == "norm":
                curves[y] = curves[y].apply(np.abs)

    elif method == "fig_pr_cycle":
        z, g = g, z
        plotly_arguments["facet_col"] = g
        seaborn_arguments["col"] = g

        if cycles is not None:
            curves = collected_curves.loc[collected_curves.cycle.isin(cycles), :]
        else:
            curves = collected_curves

        if group_cells:
            plotly_arguments["color"] = group
            plotly_arguments["symbol"] = subgroup
            seaborn_arguments["hue"] = group
            seaborn_arguments["style"] = subgroup
        else:
            plotly_arguments["markers"] = markers
            plotly_arguments["color"] = z
            seaborn_arguments["hue"] = z
            seaborn_arguments["style"] = z

    elif method == "summary":
        if cycles is not None:
            curves = collected_curves.loc[collected_curves.cycle.isin(cycles), :]
        else:
            curves = collected_curves

        if group_cells:
            plotly_arguments["color"] = group
            plotly_arguments["symbol"] = subgroup
            seaborn_arguments["hue"] = group
            seaborn_arguments["style"] = subgroup
        else:
            plotly_arguments["color"] = z
            seaborn_arguments["hue"] = z

    # ----------------- individual plotting calls  -----------------------------
    # TODO: move as much as possible up to the parsing of arguments
    #   (i.e. prepare for future refactoring)

    if backend == "plotly":
        if method == "fig_pr_cell":
            start, end = 0.0, 1.0
            if palette_range is not None:
                start, end = palette_range
            unique_cycle_numbers = curves[z].unique()
            number_of_colors = len(unique_cycle_numbers)
            if number_of_colors > 1:
                selected_colors = px.colors.sample_colorscale(
                    palette_continuous, number_of_colors, low=start, high=end
                )
                plotly_arguments["color_discrete_sequence"] = selected_colors
        elif method == "fig_pr_cycle":
            if palette_discrete is not None:
                # plotly_arguments["color_discrete_sequence"] = getattr(px.colors.sequential, palette_discrete)
                logging.debug(
                    f"palette_discrete is not implemented yet ({palette_discrete})"
                )

        elif method == "film":
            number_of_colors = 10
            start, end = 0.0, 1.0
            if palette_range is not None:
                start, end = palette_range
            plotly_arguments["color_continuous_scale"] = px.colors.sample_colorscale(
                palette_continuous, number_of_colors, low=start, high=end
            )

        elif method == "summary":
            logging.info("sequence-plotter - summary plotly")

        abs_facet_row_spacing = kwargs.pop("abs_facet_row_spacing", 20)
        abs_facet_col_spacing = kwargs.pop("abs_facet_col_spacing", 20)
        facet_row_spacing = kwargs.pop(
            "facet_row_spacing", abs_facet_row_spacing / height if height else 0.1
        )
        facet_col_spacing = kwargs.pop(
            "facet_col_spacing", abs_facet_col_spacing / (width or 1000)
        )

        plotly_arguments["facet_row_spacing"] = facet_row_spacing
        plotly_arguments["facet_col_spacing"] = facet_col_spacing

        logging.debug(f"{plotly_arguments=}")
        logging.debug(f"{kwargs=}")

        fig = None
        if method in ["fig_pr_cycle", "fig_pr_cell"]:
            fig = px.line(
                curves,
                **plotly_arguments,
                **kwargs,
            )

            if method == "fig_pr_cycle" and group_cells:
                try:
                    fig.for_each_trace(
                        functools.partial(
                            legend_replacer,
                            df=curves,
                            group_legends=group_legend_muting,
                        )
                    )
                    if markers is not True:
                        fig.for_each_trace(remove_markers)
                except Exception as e:
                    print(f"sequence_plotter - fig_pr_cycle - failed {e} [{z}]")

        elif method == "film":
            fig = px.density_heatmap(curves, **plotly_arguments, **kwargs)
            if histscale is None:
                color_bar_txt = f"{y_label} ({y_unit})"
            else:
                color_bar_txt = f"{y_label} ({histscale})"

            if histscale == "hist-eq":
                fig = fig.for_each_trace(lambda _x: _hist_eq(_x))

            fig.update_layout(coloraxis_colorbar_title_text=color_bar_txt)

        elif method == "summary":
            if spread:
                logging.info(
                    "using spread is an experimental feature and might not work as expected"
                )
                fig = spread_plot(
                    curves,
                    plotly_arguments=plotly_arguments,
                    y_label_mapper=y_label_mapper,
                    **kwargs,
                )
            else:
                # remove all kwargs that are only intended for spread_plot
                _ = kwargs.pop("height_fractions_spread", None)
                _ = plotly_arguments.pop("plotly_start_cell", None)
                _ = plotly_arguments.pop("plotly_shared_xaxes", None)
                _ = plotly_arguments.pop("plotly_vertical_spacing", None)
                _ = kwargs.pop("plotly_start_cell", None)
                _ = kwargs.pop("plotly_shared_xaxes", None)
                _ = kwargs.pop("plotly_vertical_spacing", None)

                fig = px.line(
                    curves,
                    **plotly_arguments,
                    **kwargs,
                )

            if group_cells:  # all cells in same group has same color
                try:
                    fig.for_each_trace(
                        functools.partial(
                            legend_replacer,
                            df=curves,
                            group_legends=group_legend_muting,
                        )
                    )
                    if markers is not True:
                        fig.for_each_trace(remove_markers)
                except Exception as e:
                    print(f"sequence_plotter - summary - failed {e} [{group}]")

            if y_label_mapper and not spread:
                y_label_mapper = _plotly_y_label_cleaner(y_label_mapper)
                annotations = fig.layout.annotations
                if annotations:
                    try:
                        for i in range(len(annotations)):
                            row = i + 1
                            if annotations[i].text.startswith("variable="):
                                variable = annotations[i].text.split("=")[1]
                                if variable in y_label_mapper:
                                    v = y_label_mapper[variable]
                                    fig.for_each_yaxis(
                                        functools.partial(y_axis_replacer, label=v),
                                        row=row,
                                    )
                            else:
                                for k, v in y_label_mapper.items():
                                    if annotations[i].text.endswith(k):
                                        fig.for_each_yaxis(
                                            functools.partial(y_axis_replacer, label=v),
                                            row=row,
                                        )
                                        break

                        fig.update_annotations(text="")

                    except Exception as e:
                        print(
                            f"sequence_plotter - summary - y-label mapper failed {e} [{group}]"
                        )
                else:
                    try:
                        fig.for_each_yaxis(
                            functools.partial(y_axis_replacer, label=y_label_mapper),
                        )
                    except Exception as e:
                        print(
                            f"sequence_plotter - summary - y-label mapper - no annotations - failed {e} [{group}]"
                        )
                        print(f"y_label_mapper: {y_label_mapper}")
                        print(f"annotations: {annotations}")

        else:
            print(f"method '{method}' is not supported by plotly")

        return fig

    if backend == "seaborn":
        number_of_data_points = len(curves)
        if number_of_data_points > MAX_POINTS_SEABORN_FACET_GRID:
            print(
                f"WARNING! Too many data points for seaborn to plot: "
                f"{number_of_data_points} > {MAX_POINTS_SEABORN_FACET_GRID}"
            )
            print(
                f"  - Try to reduce the number of data points "
                f"e.g. by selecting fewer cycles and interpolating "
                f"using the `number_of_points` and `max_cycle` or `cycles_to_plot` arguments."
            )
            return

        if method == "fig_pr_cell":
            seaborn_arguments["height"] = kwargs.pop("height", 3)
            seaborn_arguments["aspect"] = kwargs.pop("height", 1)
            sns.set_theme(style="darkgrid")
            x = seaborn_arguments.get("x", _CCOLS.capacity)
            y = seaborn_arguments.get("y", _CCOLS.potential)
            row = seaborn_arguments.get("row", hdr_journal.group)
            hue = seaborn_arguments.get("hue", _CCOLS.cycle_num)
            col = seaborn_arguments.get("col", hdr_journal.sub_group)
            height = seaborn_arguments.get("height", 3)
            aspect = seaborn_arguments.get("aspect", 1)

            if palette_discrete is not None:
                seaborn_arguments["palette"] = getattr(
                    sns.color_palette, palette_discrete
                )

            number_of_columns = len(curves[col].unique())
            if number_of_columns > 6:
                print(
                    f"WARNING! {number_of_columns} columns is a lot for seaborn to plot"
                )
                print(
                    f"  - consider making the plot manually (use the `.data` attribute to get the data)"
                )

            legend_items = curves[hue].unique()
            number_of_legends = len(legend_items)
            palette = (
                seaborn_arguments.get("palette", "viridis")
                if number_of_legends > 10
                else None
            )

            g = sns.FacetGrid(
                curves,
                hue=hue,
                row=row,
                col=col,
                height=height,
                aspect=aspect,
                palette=palette,
            )

            g.map(plt.plot, x, y)

            if number_of_legends > 10:
                vmin = legend_items.min()
                vmax = legend_items.max()

                sm = plt.cm.ScalarMappable(
                    cmap=palette, norm=plt.Normalize(vmin=vmin, vmax=vmax)
                )
                cbar = g.figure.colorbar(
                    sm,
                    ax=g.figure.axes,
                    location="right",
                    extend="max",
                    # pad=0.05/number_of_columns,
                )
                cbar.ax.set_title("Cycle")
            else:
                g.add_legend()

            fig = g.fig
            g.set_xlabels(labels[x])
            g.set_ylabels(labels[y])
            return fig

        if method == "fig_pr_cycle":
            sns.set_theme(style="darkgrid")
            seaborn_arguments["height"] = 4
            seaborn_arguments["aspect"] = 3
            seaborn_arguments["linewidth"] = 2.0
            g = sns.FacetGrid(
                curves,
                hue=z,
                height=seaborn_arguments["height"],
                aspect=seaborn_arguments["aspect"],
            )
            g.map(plt.plot, x, y)
            fig = g.fig
            g.set_xlabels(x_label)
            g.set_ylabels(y_label)
            g.add_legend()
            return fig

        if method == "film":
            sns.set_theme(style="darkgrid")
            seaborn_arguments["height"] = 4
            seaborn_arguments["aspect"] = 3
            seaborn_arguments["linewidth"] = 2.0
            g = sns.FacetGrid(
                curves,
                hue=z,
                height=seaborn_arguments["height"],
                aspect=seaborn_arguments["aspect"],
            )
            g.map(
                sns.kdeplot,
                y,
                x,
                fill=True,
                thresh=0,
                levels=100,
                cmap=palette_continuous,
            )
            fig = g.fig
            g.set_xlabels(x_label)
            g.set_ylabels(y_label)
            g.add_legend()
            return fig

        if method == "summary":
            sns.set_theme(style="darkgrid")
            seaborn_arguments["height"] = 4
            seaborn_arguments["aspect"] = 3
            seaborn_arguments["linewidth"] = 2.0

            x = seaborn_arguments.get("x", "cycle")
            y = seaborn_arguments.get("y", "mean")
            hue = seaborn_arguments.get("hue", None)

            labels = seaborn_arguments.get("labels", None)
            x_label = labels.get(x, x)

            std = seaborn_arguments.get("error_y", None)
            marker = "o" if seaborn_arguments.get("markers", False) else None
            row = seaborn_arguments.get("row", None)

            g = sns.FacetGrid(
                curves,
                hue=hue,
                height=seaborn_arguments["height"],
                aspect=seaborn_arguments["aspect"],
                row=row,
            )

            if std:
                g.map(plt.errorbar, x, y, std, marker=marker, elinewidth=0.5, capsize=2)
            else:
                g.map(plt.plot, x, y, marker=marker)

            fig = g.figure

            g.set_xlabels(x_label)
            if y_label_mapper:
                for i, ax in enumerate(g.axes.flat):
                    ax.set_ylabel(y_label_mapper[i])
            g.add_legend()
            return fig

    elif backend == "matplotlib":
        print(f"{backend} not implemented yet")

    elif backend == "bokeh":
        print(f"{backend} not implemented yet")

    else:
        print(f"{backend} not implemented yet")


def _cycles_plotter(
    collected_curves,
    cycles=None,
    x=_CCOLS.capacity,
    y=_CCOLS.potential,
    z=_CCOLS.cycle_num,
    g="cell",
    standard_deviation=None,
    default_title="Charge-Discharge Curves",
    backend="plotly",
    method="fig_pr_cell",
    match_axes=True,
    **kwargs,
):
    """Plot charge-discharge curves.

    Args:
        collected_curves(pd.DataFrame): collected data in long format.
        backend (str): what backend to use.
        match_axes (bool): if True, all subplots will have the same axes.
        method (str): 'fig_pr_cell' or 'fig_pr_cycle'.

        **kwargs: consumed first in current function, rest sent to backend in sequence_plotter.

    Returns:
        styled figure object
    """
    # --- pre-processing ---
    logging.debug("picking kwargs for current level - rest goes to sequence_plotter")
    title = kwargs.pop("fig_title", default_title)
    width = kwargs.pop("width", 900)
    height = kwargs.pop("height", None)
    palette = kwargs.pop("palette", None)
    legend_position = kwargs.pop("legend_position", None)
    legend_title = kwargs.pop("legend_title", None)
    show_legend = kwargs.pop("show_legend", None)
    cols = kwargs.pop("cols", 3)
    sub_fig_min_height = kwargs.pop("sub_fig_min_height", 200)
    figure_border_height = kwargs.pop("figure_border_height", 100)
    # kwargs from default `BatchCollector.render` method not used by `sequence_plotter`:
    journal = kwargs.pop("journal", None)
    units = kwargs.pop("units", None)

    if palette is not None:
        kwargs["palette_continuous"] = palette
        kwargs["palette_discrete"] = palette

    if legend_title is None:
        if method == "fig_pr_cell":
            legend_title = "Cycle"
        else:
            legend_title = "Cell"

    no_cols = cols

    if method in ["fig_pr_cell", "film"]:
        number_of_figs = len(collected_curves["cell"].unique())

    elif method == "fig_pr_cycle":
        if cycles is not None:
            number_of_figs = len(cycles)
        else:
            number_of_figs = len(collected_curves[_CCOLS.cycle_num].unique())
    elif method == "summary":
        number_of_figs = len(collected_curves["variable"].unique())
        sub_fig_min_height = 300
    else:
        number_of_figs = 1

    no_rows = math.ceil(number_of_figs / no_cols)

    if not height:
        height = figure_border_height + no_rows * sub_fig_min_height

    fig = sequence_plotter(
        collected_curves,
        x=x,
        y=y,
        z=z,
        g=g,
        standard_deviation=standard_deviation,
        backend=backend,
        method=method,
        cols=cols,
        cycles=cycles,
        width=width,
        height=height,
        **kwargs,
    )
    if fig is None:
        print("Could not create figure!")
        return

    # Rendering:
    if backend == "plotly":
        template = f"{PLOTLY_BASE_TEMPLATE}+{method}"

        legend_orientation = "v"
        if legend_position == "bottom":
            legend_orientation = "h"

        legend_dict = {
            "title": legend_title,
            "orientation": legend_orientation,
        }
        title_dict = {
            "text": title,
        }

        fig.update_layout(
            template=template,
            title=title_dict,
            legend=legend_dict,
            showlegend=show_legend,
            height=height,
            width=width,
        )
        if not match_axes:
            fig.update_yaxes(matches=None)
            fig.update_xaxes(matches=None)

    return fig


def summary_plotter(collected_curves, cycles_to_plot=None, backend="plotly", **kwargs):
    """Plot summaries (value vs cycle number).

    Assuming data as pandas.DataFrame with either
    1) long format (where variables, for example charge capacity, are in the column "variable") or
    2) mixed long and wide format where the variables are own columns.
    """

    # start_cell is used to determine the starting cell for the subplots (plotly)
    start_cell = kwargs.pop("start_cell", "bottom-left")

    col_headers = collected_curves.columns.to_list()

    # need to manually update this if new columns are added to collected_curves that should not be plotted:
    not_available_for_plotting = [hdr_journal.label, hdr_journal.group_label, hdr_journal.selected]

    possible_id_vars = [
        "cell",
        "cycle",
        "equivalent_cycle",
        "value",
        "mean",
        "std",
        hdr_journal.group,
        hdr_journal.sub_group,
    ]
    id_vars = []
    for n in possible_id_vars:
        if n in col_headers:
            col_headers.remove(n)
            id_vars.append(n)
    for n in not_available_for_plotting:
        if n in col_headers:
            col_headers.remove(n)

    if "variable" not in col_headers:
        collected_curves = collected_curves.melt(
            id_vars=id_vars, value_vars=col_headers
        )

    normalize_cycles = True if "equivalent_cycle" in id_vars else False
    group_it = False if hdr_journal.group in id_vars else True

    cols = kwargs.pop("cols", 1)

    z = "cell"
    g = "variable"

    if normalize_cycles:
        x = "equivalent_cycle"
        x_label = "Equivalent Cycle"
        x_unit = "cum/nom.cap."
    else:
        x = "cycle"
        x_label = "Cycle"
        x_unit = "n."

    if group_it:
        group_cells = False
        y = "mean"
        standard_deviation = "std"

    else:
        y = "value"
        standard_deviation = None
        group_cells = kwargs.pop("group_cells", True)

    units = kwargs.pop("units", None)
    label_mapper = {
        f"{y}": None,
    }
    # order the variables by a given order:
    order_variables = kwargs.pop("order_variables", None)
    if order_variables:
        collected_curves[g] = collected_curves[g].astype(
            pd.CategoricalDtype(categories=order_variables, ordered=True)
        )
        collected_curves = collected_curves.sort_values(by=[g, z, x])

    if units:
        label_mapper[y] = {}
        variables = list(collected_curves[g].unique())
        for v in variables:
            # unit label
            u_sub = None
            if v.endswith("_areal") or v.endswith("_areal_cv"):
                u_sub = units["cellpy_units"].specific_areal
            elif v.endswith("_gravimetric") or v.endswith("_gravimetric_cv"):
                u_sub = units["cellpy_units"].specific_gravimetric
            elif v.endswith("_volumetric") or v.endswith("_volumetric_cv"):
                u_sub = units["cellpy_units"].specific_volumetric

            u_top = None
            if "_capacity" in v:
                u_top = units["cellpy_units"].charge
            if "_norm" in v:
                u_top = "normalized"
            if v == "coulombic_efficiency":
                u_top = "%"

            u = u_top or "Value"

            # variable label
            v2 = v.split("_")
            if u_sub:
                u_sub = u_sub.replace("**", "")
                u = f"{u}/{u_sub}"
                if v2[-1] == "cv":
                    v2 = v2[:-2]
                    v2.append("cv")
                else:
                    v2 = v2[:-1]
            v2 = " ".join(v2).title()

            if v2.endswith("Cv"):
                v2 = v2.replace("Cv", "CV")

            label_mapper[y][v] = f"{v2} ({u})"

    # TODO: need to refactor and fix how the classes are created so that leftover kwargs are not sent to the backend
    #  (for example if another collector is used and registers a kwarg without popping it)

    _ = kwargs.pop("method", None)  # also set in BatchCyclesCollector
    height_fractions = kwargs.pop("height_fractions", [])

    fig = _cycles_plotter(
        collected_curves,
        x=x,
        y=y,
        z=z,
        g=g,
        standard_deviation=standard_deviation,
        x_label=x_label,
        x_unit=x_unit,
        y_label_mapper=label_mapper[y],
        group_cells=group_cells,
        default_title="Summary Plot",
        backend=backend,
        method="summary",
        cycles=cycles_to_plot,
        cols=cols,
        **kwargs,
    )

    if backend == "plotly":
        # TODO: implement having different heights of the subplots

        if len(height_fractions) > 0:
            # Determine number of rows in the original figure
            print("THIS IS EXPERIMENTAL")
            number_of_rows = len([key for key in fig.layout if key.startswith("yaxis")])
            if number_of_rows == 0:
                number_of_rows = 1  # Default to 1 if no y-axes found

            # Only proceed if height_fractions matches the number of rows
            if len(height_fractions) != number_of_rows:
                print(
                    f"Warning: height_fractions length ({len(height_fractions)}) does not match number of rows ({number_of_rows}). Ignoring height_fractions."
                )
            else:
                # Update subplot heights using make_subplots parameters
                from plotly.subplots import make_subplots

                # Get current figure data and layout properties
                current_data = fig.data
                current_layout = fig.layout

                # Create new figure with custom row heights
                new_fig = make_subplots(
                    rows=number_of_rows,
                    cols=1,
                    start_cell=start_cell,
                    shared_xaxes=True,
                    row_heights=height_fractions[::-1],
                    vertical_spacing=0.02,
                    subplot_titles=[ann.text for ann in current_layout.annotations]
                    if current_layout.annotations
                    else None,
                )

                new_height_fractions = {}
                for key in new_fig.layout:
                    if key.startswith("yaxis"):
                        new_height_fractions[key] = new_fig.layout[key].domain

                # Add traces from original figure
                for trace in current_data:
                    new_fig.add_trace(trace)

                # Update layout properties from original figure (including theme)
                new_fig.update_layout(current_layout)
                for key in new_height_fractions:
                    new_fig.layout[key].domain = new_height_fractions[key]

                fig = new_fig
                # Preserve x-axis linking and only show labels on bottom row with small gaps
                fig.update_xaxes(matches="x")
                fig.update_yaxes(matches=None, showticklabels=True)

                # Only show x-axis labels on the bottom subplot (not needed anymore?)
                # for i in range(1, len(height_fractions)):
                #     fig.update_xaxes(showticklabels=False, row=i, col=1)

        return fig
    if backend == "seaborn":
        print("using seaborn (experimental feature)")
        return fig
    if backend == "matplotlib":
        print("using matplotlib (experimental feature)")
        return fig
    if backend == "bokeh":
        print("using bokeh (experimental feature)")
        return fig


def cycles_plotter(
    collected_curves,
    cycles_to_plot=None,
    backend="plotly",
    method="fig_pr_cell",
    x_unit="mAh/g",
    y_unit="V",
    **kwargs,
):
    """Plot charge-discharge curves.

    Args:
        collected_curves(pd.DataFrame): collected data in long format.
        cycles_to_plot (list): cycles to plot
        backend (str): what backend to use.
        method (str): 'fig_pr_cell' or 'fig_pr_cycle'.
        x_unit (str): unit for x-axis.
        y_unit (str): unit for y-axis.

        **kwargs: consumed first in current function, rest sent to backend in sequence_plotter.

    Returns:
        styled figure object
    """

    if cycles_to_plot is not None:
        unique_cycles = list(collected_curves.cycle.unique())
        if len(unique_cycles) > 50:
            print(f"Too many cycles - setting it to default {DEFAULT_CYCLES}")
            cycles_to_plot = DEFAULT_CYCLES

    return _cycles_plotter(
        collected_curves,
        x=_CCOLS.capacity,
        y=_CCOLS.potential,
        z=_CCOLS.cycle_num,
        g="cell",
        x_unit=x_unit,
        y_unit=y_unit,
        default_title="Charge-Discharge Curves",
        backend=backend,
        method=method,
        cycles=cycles_to_plot,
        **kwargs,
    )


def ica_plotter(
    collected_curves,
    cycles_to_plot=None,
    backend="plotly",
    method="fig_pr_cell",
    direction="charge",
    **kwargs,
):
    """Plot charge-discharge curves.

    Args:
        collected_curves(pd.DataFrame): collected data in long format.
        cycles_to_plot (list): cycles to plot
        backend (str): what backend to use.
        method (str): 'fig_pr_cell' or 'fig_pr_cycle' or 'film'.
        direction (str): 'charge' or 'discharge'.

        **kwargs: consumed first in current function, rest sent to backend in sequence_plotter.

    Returns:
        styled figure object
    """

    if cycles_to_plot is None:
        unique_cycles = list(collected_curves.cycle.unique())
        max_cycle = max(unique_cycles)
        if len(unique_cycles) > 50:
            cycles_to_plot = DEFAULT_CYCLES
            max_cycle = max(cycles_to_plot)
    else:
        max_cycle = max(cycles_to_plot)

    if direction not in ["charge", "discharge"]:
        print(f"direction='{direction}' not allowed - setting it to 'charge'")
        direction = "charge"
    if method == "film":
        kwargs["range_y"] = kwargs.pop("range_y", None) or (1, max_cycle)

    return _cycles_plotter(
        collected_curves,
        x="voltage",
        y="dqdv",
        z="cycle",
        g="cell",
        x_label="Voltage",
        x_unit="V",
        y_label="dQ/dV",
        y_unit="mAh/g/V.",
        default_title=f"Incremental Analysis Plots",
        direction=direction,
        backend=backend,
        method=method,
        cycles=cycles_to_plot,
        **kwargs,
    )


def histogram_equalization(image: np.array) -> np.array:
    """Perform histogram equalization on a numpy array."""
    # from http://www.janeriksolem.net/histogram-equalization-with-python-and.html
    number_bins = 256
    scale = 100
    image[np.isnan(image)] = 0.0
    image_histogram, bins = np.histogram(image.flatten(), number_bins, density=True)
    cdf = image_histogram.cumsum()  # cumulative distribution function
    cdf = (scale - 1) * cdf / cdf[-1]  # normalize
    # use linear interpolation of cdf to find new pixel values
    image_equalized = np.interp(image.flatten(), bins[:-1], cdf)

    return image_equalized.reshape(image.shape)




# ---------------------------------------------------------------------------
# Public orchestrator (layout=/kind= → FigureSpec → backend)
# ---------------------------------------------------------------------------

_METHOD_TO_LAYOUT = {
    "fig_pr_cell": "per_cell",
    "fig_pr_cycle": "per_cycle",
    "film": "per_cell",
    "summary": "summary",
}

_LAYOUT_TO_METHOD = {
    "per_cell": "fig_pr_cell",
    "per_cycle": "fig_pr_cycle",
    "summary": "summary",
}


def resolve_collected_layout_kind(
    *,
    layout: Optional[str] = None,
    kind: Optional[str] = None,
    method: Optional[str] = None,
    plot_type: Optional[str] = None,
    spread: bool = False,
) -> tuple[str, str, str]:
    """Map legacy ``method``/``plot_type``/``spread`` to ``(layout, kind, method)``.

    Returns:
        layout: ``per_cell`` | ``per_cycle`` | ``summary``
        kind: ``line`` | ``film`` | ``spread``
        method: legacy template/method string still understood by renderers
    """
    if method is None and plot_type is not None:
        method = plot_type
    if kind is None:
        if spread:
            kind = "spread"
        elif method == "film":
            kind = "film"
        else:
            kind = "line"
    if layout is None:
        if method in _METHOD_TO_LAYOUT:
            layout = _METHOD_TO_LAYOUT[method]
        elif kind == "film":
            layout = "per_cell"
        else:
            layout = "per_cell"
    if method is None:
        if kind == "film":
            method = "film"
        else:
            method = _LAYOUT_TO_METHOD.get(layout, "fig_pr_cell")
    if kind == "spread":
        # spread is a summary rendering mode
        if layout not in ("summary", "per_cell"):
            layout = "summary"
        if method not in ("summary", "film", "fig_pr_cell", "fig_pr_cycle"):
            method = "summary"
    return layout, kind, method


def render_collected(frame: Any, spec: FigureSpec, *, backend_override: Optional[str] = None) -> Any:
    """Dispatch a collected-frame ``FigureSpec`` to the legacy layout engines."""
    extras = dict(spec.extras or {})
    family_kind = extras.get("family_kind") or "cycles"
    method = extras.get("method") or "fig_pr_cell"
    collected_kind = extras.get("collected_kind") or "line"
    opts = dict(extras.get("render_opts") or {})
    backend = backend_override or extras.get("backend") or "plotly"

    if collected_kind == "spread":
        opts["spread"] = True
    if collected_kind == "film":
        method = "film"

    # Do not let a resolved layout method override summary_plotter's forced
    # method="summary" via **kwargs.
    opts.pop("method", None)
    opts.pop("plot_type", None)

    if family_kind == "summary":
        return summary_plotter(frame, backend=backend, **opts)
    if family_kind == "ica":
        return ica_plotter(frame, backend=backend, method=method, **opts)
    if family_kind == "cycles":
        return cycles_plotter(frame, backend=backend, method=method, **opts)
    return sequence_plotter(frame, backend=backend, method=method, **opts)


def collected_plot(
    frame: Any,
    *,
    family_kind: str = "cycles",
    layout: Optional[str] = None,
    kind: Optional[str] = None,
    backend: str = "plotly",
    method: Optional[str] = None,
    plot_type: Optional[str] = None,
    spread: bool = False,
    **opts: Any,
) -> Any:
    """Plot an already-collected tidy multi-cell frame (#657).

    Args:
        frame: long/tidy frame with ``cell`` / ``group`` / ``sub_group`` as needed.
        family_kind: ``summary`` | ``cycles`` | ``ica`` (selects column defaults).
        layout: ``per_cell`` | ``per_cycle`` | ``summary``.
        kind: ``line`` | ``film`` | ``spread``.
        backend: ``plotly`` (primary) or ``seaborn`` / ``matplotlib`` (best-effort).
        method / plot_type: legacy collector knobs (mapped to layout/kind).
        spread: legacy flag → ``kind="spread"``.
        **opts: forwarded to the collected renderers (cycles, labels, sizes, …).

    Returns:
        Backend-native figure object.
    """
    from cellpy._deprecation import warn_once
    from cellpy.plotting.backends import get_backend

    layout, kind, method = resolve_collected_layout_kind(
        layout=layout,
        kind=kind,
        method=method,
        plot_type=plot_type,
        spread=spread or bool(opts.get("spread")),
    )
    opts = dict(opts)
    opts.pop("spread", None)
    if kind == "spread":
        opts["spread"] = True

    # Ensure collector templates exist before plotly render.
    if backend == "plotly" and pio is not None:
        pio.templates.default = PLOTLY_BASE_TEMPLATE
    theme.make_collector_templates()

    backend_key = (backend or "plotly").strip().lower()
    if backend_key == "matplotlib":
        warn_once(
            "collected_plot: backend='matplotlib' uses the collectors seaborn "
            "layout path (best-effort parity); prefer backend='plotly'.",
            stacklevel=2,
        )
        backend_key = "seaborn"

    spec = FigureSpec(
        title=opts.get("fig_title"),
        extras={
            "kind": "collected",
            "family_kind": family_kind,
            "layout": layout,
            "collected_kind": kind,
            "method": method,
            "backend": backend_key,
            "render_opts": opts,
        },
    )

    if backend_key == "seaborn":
        # Keep the historical seaborn branch without forcing get_backend("matplotlib")
        # into the single-cell summary path.
        return render_collected(frame, spec, backend_override="seaborn")

    return get_backend(backend_key).render(frame, spec)


