# -*- coding: utf-8 -*-
"""
Utilities for helping to plot cellpy-data.
"""

import collections
import importlib
import itertools
import logging
from multiprocessing import Process
import os
import pickle as pkl
import sys
import warnings
from io import StringIO
from pathlib import Path

import matplotlib.pyplot as plt

from cellpy.parameters.internal_settings import (
    get_headers_journal,
    get_headers_normal,
    get_headers_step_table,
    get_headers_summary,
)
from cellpy.utils import helpers

plotly_available = importlib.util.find_spec("plotly") is not None
seaborn_available = importlib.util.find_spec("seaborn") is not None

# Refactoring work in progress:
# - homogenize plotting tools (plotutils, batchutils and collectors) to
#   remove the need to change code in many files when changing plotting settings and tools
# - utilize the prms system to set plotting settings
# - make standardized plot templates and looks

# including this to mimic the behaviour of collectors:
supported_backends = []
if plotly_available:
    supported_backends.append("plotly")
if seaborn_available:
    supported_backends.append("seaborn")


# logger = logging.getLogger(__name__)
logging.captureWarnings(True)


# from collectors - template:

PLOTLY_BASE_TEMPLATE = "plotly"
IMAGE_TO_FILE_TIMEOUT = 30


# from collectors - tools for loading and saving plots:
def load_figure(filename, backend=None):
    """Load figure from file."""

    filename = Path(filename)

    if backend is None:
        suffix = filename.suffix
        if suffix in [".pkl", ".pickle"]:
            backend = "matplotlib"
        elif suffix in [".json", ".plotly", ".jsn"]:
            backend = "plotly"
        else:
            backend = "plotly"

    if backend == "plotly":
        return load_plotly_figure(filename)
    elif backend == "seaborn":
        return load_matplotlib_figure(filename)
    elif backend == "matplotlib":
        return load_matplotlib_figure(filename)
    else:
        print(f"WARNING: {backend=} is not supported at the moment")
        return None


def save_matplotlib_figure(fig, filename):
    pkl.dump(fig, open(filename, "wb"))


def make_matplotlib_manager(fig):
    """Create a new manager for a matplotlib figure."""
    # create a dummy figure and use its
    # manager to display "fig"  ; based on https://stackoverflow.com/a/54579616/8508004
    dummy = plt.figure()
    new_manager = dummy.canvas.manager
    new_manager.canvas.figure = fig
    fig.set_canvas(new_manager.canvas)
    return fig


def load_matplotlib_figure(filename, create_new_manager=False):
    fig = pkl.load(open(filename, "rb"))
    if create_new_manager:
        fig = make_matplotlib_manager(fig)
    return fig


def load_plotly_figure(filename):
    """Load plotly figure from file."""

    # TODO: create a decorator for this:
    if not plotly_available:
        print("Plotly not available")
        return None
    import plotly.io as pio

    try:
        fig = pio.read_json(filename)
    except Exception as e:
        print("Could not load figure from json file")
        print(e)
        return None
    return fig


def _image_exporter_plotly(figure, filename, timeout=IMAGE_TO_FILE_TIMEOUT, **kwargs):
    p = Process(
        target=figure.write_image,
        args=(filename,),
        name="save_plotly_image_to_file",
        kwargs=kwargs,
    )
    p.start()
    p.join(timeout=timeout)
    p.terminate()
    if p.exitcode is None:
        print(f"Oops, {p} timeouts! Could not save {filename}")
    if p.exitcode == 0:
        print(f" - saved image file: {filename}")


def save_image_files(figure, name="my_figure", scale=3.0, dpi=300, backend="plotly", formats: list = None):
    """Save to image files (png, svg, json/pickle).

    Notes:
        This method requires ``kaleido`` for the plotly backend.

    Notes:
        Exporting to json is only applicable for the plotly backend.

    Args:
        figure (fig-object): The figure to save.
        name (pathlib.Path or str): The path of the file (without extension).
        scale (float): The scale of the image.
        dpi (int): The dpi of the image.
        backend (str): The backend to use (plotly or seaborn/matplotlib).
        formats (list): The formats to save (default: ["png", "svg", "json", "pickle"]).

    """
    filename = Path(name)
    filename_png = filename.with_suffix(".png")
    filename_svg = filename.with_suffix(".svg")
    filename_json = filename.with_suffix(".json")
    filename_pickle = filename.with_suffix(".pickle")

    if formats is None:
        formats = ["png", "svg", "json", "pickle"]

    if backend == "plotly":
        if "png" in formats:
            _image_exporter_plotly(figure, filename_png, scale=scale)
        if "svg" in formats:
            _image_exporter_plotly(figure, filename_svg)
        if "json" in formats:
            figure.write_json(filename_json)
            print(f" - saved plotly json file: {filename_json}")

    elif backend in ["seaborn", "matplotlib"]:
        if "png" in formats:
            figure.savefig(filename_png, dpi=dpi)
            print(f" - saved png file: {filename_png}")
        if "svg" in formats:
            figure.savefig(filename_svg)
            print(f" - saved svg file: {filename_svg}")
        if "pickle" in formats:
            save_matplotlib_figure(figure, filename_pickle)
            print(f" - pickled to file: {filename_pickle}")

    else:
        print(f"TODO: implement saving {filename_png}")
        print(f"TODO: implement saving {filename_svg}")
        print(f"TODO: implement saving {filename_json}")


# from batch_plotters:
def _plotly_remove_markers(trace):
    trace.update(marker=None, mode="lines")
    return trace


def _plotly_legend_replacer(trace, df, group_legends=True):
    name = trace.name
    parts = name.split(",")
    if len(parts) == 2:
        group = int(parts[0])
        subgroup = int(parts[1])
    else:
        print("Have not implemented replacing legend labels that are not on the form a,b yet.")
        print(f"legend label: {name}")
        return trace

    cell_label = df.loc[(df["group"] == group) & (df["sub_group"] == subgroup), "cell"].values[0]
    if group_legends:
        trace.update(
            name=cell_label,
            legendgroup=group,
            hovertemplate=f"{cell_label}<br>{trace.hovertemplate}",
        )
    else:
        trace.update(
            name=cell_label,
            legendgroup=cell_label,
            hovertemplate=f"{cell_label}<br>{trace.hovertemplate}",
        )


# original:
SYMBOL_DICT = {
    "all": [
        "s",
        "o",
        "v",
        "^",
        "<",
        ">",
        "D",
        "p",
        "*",
        "1",
        "2",
        ".",
        ",",
        "3",
        "4",
        "8",
        "p",
        "d",
        "h",
        "H",
        "+",
        "x",
        "X",
        "|",
        "_",
    ],
    "simple": ["s", "o", "v", "^", "<", ">", "*", "d"],
}

COLOR_DICT = {
    "classic": ["b", "g", "r", "c", "m", "y", "k"],
    "grayscale": ["0.00", "0.40", "0.60", "0.70"],
    "bmh": [
        "#348ABD",
        "#A60628",
        "#7A68A6",
        "#467821",
        "#D55E00",
        "#CC79A7",
        "#56B4E9",
        "#009E73",
        "#F0E442",
        "#0072B2",
    ],
    "dark_background": [
        "#8dd3c7",
        "#feffb3",
        "#bfbbd9",
        "#fa8174",
        "#81b1d2",
        "#fdb462",
        "#b3de69",
        "#bc82bd",
        "#ccebc4",
        "#ffed6f",
    ],
    "ggplot": [
        "#E24A33",
        "#348ABD",
        "#988ED5",
        "#777777",
        "#FBC15E",
        "#8EBA42",
        "#FFB5B8",
    ],
    "fivethirtyeight": ["#30a2da", "#fc4f30", "#e5ae38", "#6d904f", "#8b8b8b"],
    "seaborn-colorblind": [
        "#0072B2",
        "#009E73",
        "#D55E00",
        "#CC79A7",
        "#F0E442",
        "#56B4E9",
    ],
    "seaborn-deep": ["#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974", "#64B5CD"],
    "seaborn-bright": [
        "#003FFF",
        "#03ED3A",
        "#E8000B",
        "#8A2BE2",
        "#FFC400",
        "#00D7FF",
    ],
    "seaborn-muted": ["#4878CF", "#6ACC65", "#D65F5F", "#B47CC7", "#C4AD66", "#77BEDB"],
    "seaborn-pastel": [
        "#92C6FF",
        "#97F0AA",
        "#FF9F9A",
        "#D0BBFF",
        "#FFFEA3",
        "#B0E0E6",
    ],
    "seaborn-dark-palette": [
        "#001C7F",
        "#017517",
        "#8C0900",
        "#7600A1",
        "#B8860B",
        "#006374",
    ],
}

_hdr_summary = get_headers_summary()
_hdr_raw = get_headers_normal()
_hdr_steps = get_headers_step_table()
_hdr_journal = get_headers_journal()


def set_plotly_template(template_name=None, **kwargs):
    """Set the default plotly template."""
    if not plotly_available:
        return None
    import plotly.io as pio

    if template_name is None:
        name = create_plotly_default_template(**kwargs)
        pio.templates.default = f"{PLOTLY_BASE_TEMPLATE}+{name}"
    else:
        pio.templates.default = template_name


def create_plotly_default_template(
    name="all_axis",
    font_color="#455A64",
    marker_edge_on=False,
    marker_size=12,
    marker_edge_color="white",
    marker_width=None,
    opacity=0.8,
):
    if not plotly_available:
        return None
    import plotly.graph_objects as go
    import plotly.io as pio

    axis_color = "rgb(36,36,36)"
    grid_color = "white"
    axis_font = "Arial Black"
    axis_font_size = 16
    # axis_standoff = 15
    axis_standoff = None
    tick_label_width = 6

    title_font_size = 22
    title_font_family = "Arial Black, Helvetica, Sans-serif"
    title_font_color = font_color

    marker = dict(
        size=marker_size,
    )
    line = dict()

    if marker_edge_on:
        if marker_width is None:
            if marker_size is not None:
                marker_width = marker_size / 6
            else:
                marker_width = 0.5

        marker["line"] = dict(
            width=marker_width,
            color=marker_edge_color,
        )
    axis = dict(
        linecolor=axis_color,
        mirror=True,
        showline=True,
        gridcolor=grid_color,
        zeroline=False,
        tickformat=f"{tick_label_width}",
        titlefont_family=axis_font,
        title=dict(
            standoff=axis_standoff,
            font_size=axis_font_size,
            font_color=font_color,
        ),
    )
    title = dict(
        font_family=title_font_family,
        font_size=title_font_size,
        font_color=title_font_color,
        x=0,
        xref="paper",
    )
    data = dict(
        scatter=[go.Scatter(marker=marker, line=line, opacity=opacity)],
    )
    pio.templates[name] = go.layout.Template(layout=dict(title=title, xaxis=axis, yaxis=axis), data=data)
    return name


def create_colormarkerlist_for_journal(journal, symbol_label="all", color_style_label="seaborn-colorblind"):
    """Fetch lists with color names and marker types of correct length for a journal.

    Args:
        journal: cellpy journal
        symbol_label: sub-set of markers to use
        color_style_label: cmap to use for colors

    Returns:
        colors (list), markers (list)
    """
    logging.debug("symbol_label: " + symbol_label)
    logging.debug("color_style_label: " + color_style_label)
    groups = journal.pages[_hdr_journal.group].unique()
    sub_groups = journal.pages[_hdr_journal.subgroup].unique()
    return create_colormarkerlist(groups, sub_groups, symbol_label, color_style_label)


def create_colormarkerlist(groups, sub_groups, symbol_label="all", color_style_label="seaborn-colorblind"):
    """Fetch lists with color names and marker types of correct length.

    Args:
        groups: list of group numbers (used to generate the list of colors)
        sub_groups: list of sub-group numbers (used to generate the list of markers).
        symbol_label: sub-set of markers to use
        color_style_label: cmap to use for colors

    Returns:
        colors (list), markers (list)
    """
    symbol_list = SYMBOL_DICT[symbol_label]
    color_list = COLOR_DICT[color_style_label]

    # checking that we have enough colors and symbols (if not, then use cycler (e.g. reset))
    color_cycler = itertools.cycle(color_list)
    symbol_cycler = itertools.cycle(symbol_list)
    _color_list = []
    _symbol_list = []
    for i in groups:
        _color_list.append(next(color_cycler))
    for i in sub_groups:
        _symbol_list.append(next(symbol_cycler))
    return _color_list, _symbol_list


def create_col_info(c):
    """Create column information for summary plots.

    Args:
        c: cellpy object

    Returns:
        x_columns (tuple), y_cols (dict)

    """

    # TODO: add support for more column sets and individual columns
    hdr = c.headers_summary
    _cap_cols = [hdr.charge_capacity_raw, hdr.discharge_capacity_raw]
    _capacities_gravimetric = [col + "_gravimetric" for col in _cap_cols]
    _capacities_gravimetric_split = (
        _capacities_gravimetric
        + [col + "_cv" for col in _capacities_gravimetric]
        + [col + "_non_cv" for col in _capacities_gravimetric]
    )
    _capacities_areal = [col + "_areal" for col in _cap_cols]
    _capacities_areal_split = (
        _capacities_areal + [col + "_cv" for col in _capacities_areal] + [col + "_non_cv" for col in _capacities_areal]
    )

    x_columns = (
        [
            hdr.cycle_index,
            hdr.data_point,
            hdr.test_time,
            hdr.datetime,
            hdr.normalized_cycle_index,
        ],
    )
    y_cols = dict(
        voltages=[hdr.end_voltage_charge, hdr.end_voltage_discharge],
        capacities_gravimetric=_capacities_gravimetric,
        capacities_areal=_capacities_areal,
        capacities=_cap_cols,
        capacities_gravimetric_split_constant_voltage=_capacities_gravimetric_split,
        capacities_areal_split_constant_voltage=_capacities_areal_split,
    )
    return x_columns, y_cols


def create_label_dict(c):
    """Create label dictionary for summary plots.

    Args:
        c: cellpy object

    Returns:
        x_axis_labels (dict), y_axis_label (dict)

    """

    hdr = c.headers_summary
    x_axis_labels = {
        hdr.cycle_index: "Cycle Number",
        hdr.data_point: "Point",
        hdr.test_time: f"Test Time ({c.cellpy_units.time})",
        hdr.datetime: "Date",
        hdr.normalized_cycle_index: "Equivalent Full Cycle",
        # hdr.normalized_cycle_index: "Normalized Cycle Number",
    }

    _cap_gravimetric_label = f"Capacity ({c.cellpy_units.charge}/{c.cellpy_units.specific_gravimetric})"
    _cap_areal_label = f"Capacity ({c.cellpy_units.charge}/{c.cellpy_units.specific_areal})"

    _cap_label = f"Capacity ({c.cellpy_units.charge})"

    y_axis_label = {
        "voltages": f"Voltage ({c.cellpy_units.voltage})",
        "capacities_gravimetric": _cap_gravimetric_label,
        "capacities_areal": _cap_areal_label,
        "capacities": _cap_label,
        "capacities_gravimetric_split_constant_voltage": _cap_gravimetric_label,
        "capacities_areal_split_constant_voltage": _cap_areal_label,
    }
    return x_axis_labels, y_axis_label


def _get_capacity_unit(c, mode="gravimetric", seperator="/"):

    specific_selector = {
        "gravimetric": f"{c.cellpy_units.charge}{seperator}{c.cellpy_units.specific_gravimetric}",
        "areal": f"{c.cellpy_units.charge}{seperator}{c.cellpy_units.specific_areal}",
        "volumetric": f"{c.cellpy_units.charge}{seperator}{c.cellpy_units.specific_volumetric}",
        "absolute": f"{c.cellpy_units.charge}",
    }
    return specific_selector.get(mode, "-")


# TODO: add formation cycles handling
# TODO: consistent parameter names (e.g. y_range vs ylim) between summary_plot, plot_cycles, raw_plot, cycle_info_plot and batchutils
# TODO: consistent function names (raw_plot vs plot_raw etc)
def summary_plot(
    c,
    x: str = None,
    y: str = "capacities_gravimetric",
    height: int = 600,
    markers: bool = True,
    title=None,
    x_range: list = None,
    y_range: list = None,
    split: bool = False,
    interactive: bool = True,
    share_y: bool = False,
    rangeslider: bool = False,
    return_data: bool = False,
    verbose: bool = False,
    plotly_template: str = None,
    **kwargs,
):
    """Create a summary plot.


    Args:
        c: cellpy object
        x: x-axis column (default: 'cycle_index')
        y: y-axis column or column set. Currently, the following predefined sets exists:

            - "voltages", "capacities_gravimetric", "capacities_areal", "capacities",
              "capacities_gravimetric_split_constant_voltage", "capacities_areal_split_constant_voltage"

        height: height of the plot
        markers: use markers
        title: title of the plot
        x_range: limits for x-axis
        y_range: limits for y-axis
        split: split the plot
        interactive: use interactive plotting
        rangeslider: add a range slider to the x-axis (only for plotly)
        share_y: share y-axis
        return_data: return the data used for plotting
        verbose: print out some extra information to make it easier to find out what to plot next time
        plotly_template: name of the plotly template to use
        **kwargs: additional parameters for the plotting backend

    Returns:
        if ``return_data`` is True, returns a tuple with the figure and the data used for plotting.
        Otherwise, it returns only the figure. If ``interactive`` is True, the figure is a ``plotly`` figure,
        else it is a ``matplotlib`` figure.

    Hint:
        If you want to modify the non-interactive (matplotlib) plot, you can get the axes from the
        returned figure by ``axes = figure.get_axes()``.


    """

    if interactive and not plotly_available:
        warnings.warn("plotly not available, and it is currently the only supported interactive backend")
        return None

    if title is None:
        if interactive:
            title = f"Summary <b>{c.cell_name}</b>"
        else:
            title = f"Summary {c.cell_name}"

    if x is None:
        x = "cycle_index"

    x_cols, y_cols = create_col_info(c)
    x_axis_labels, y_axis_label = create_label_dict(c)

    # ------------------- main --------------------------------------------
    y_header = "value"
    color = "variable"
    row = "row"

    additional_kwargs_plotly = dict(
        color=color,
        height=height,
        markers=markers,
        title=title,
    )

    # filter on constant voltage vs constant current
    if y.endswith("_split_constant_voltage"):
        cap_type = "capacities_gravimetric" if y.startswith("capacities_gravimetric") else "capacities_areal"
        column_set = y_cols[cap_type]

        # turning off warnings when splitting the data
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            s = partition_summary_cv_steps(c, x, column_set, split, color, y_header)
        if split:
            additional_kwargs_plotly["facet_row"] = row

    # simple case
    else:
        column_set = y_cols.get(y, y)
        if isinstance(column_set, str):
            column_set = [column_set]
        summary = c.data.summary
        summary = summary.reset_index()
        s = summary.melt(x)
        s = s.loc[s.variable.isin(column_set)]
        s = s.reset_index(drop=True)

    x_label = x_axis_labels.get(x, x)
    if y in y_axis_label:
        y_label = y_axis_label.get(y, y)
    else:
        y_label = y.replace("_", " ").title()

    if verbose:
        _report_summary_plot_info(c, x, y, x_label, x_axis_labels, x_cols, y_label, y_axis_label, y_cols)

    if interactive:
        import plotly.express as px

        set_plotly_template(plotly_template)

        fig = px.line(
            s,
            x=x,
            y=y_header,
            **additional_kwargs_plotly,
            labels={
                x: x_label,
                y_header: y_label,
            },
            **kwargs,
        )

        if x_range is not None:
            fig.update_layout(xaxis=dict(range=x_range))
        if y_range is not None:
            fig.update_layout(yaxis=dict(range=y_range))
        elif split and not share_y:
            fig.update_yaxes(matches=None)

        if rangeslider:
            fig.update_layout(xaxis_rangeslider_visible=True)
        if return_data:
            return fig, s
        return fig

    else:
        # a very simple seaborn (matplotlib) plot...
        if not seaborn_available:
            warnings.warn("seaborn not available, returning only the data so that you can plot it yourself instead")
            return s

        import seaborn as sns

        sns.set_style(kwargs.pop("style", "darkgrid"))

        if split:
            sns_fig = sns.relplot(
                data=s,
                x=x,
                y=y_header,
                hue=color,
                row=row,
                height=2,
                aspect=4,
                kind="line",
                marker="o" if markers else None,
                **kwargs,
            )

            sns_fig.set_axis_labels(x_label, y_label)
            if x_range is not None:
                sns_fig.set(xlim=x_range)
            if y_range is not None:
                sns_fig.set(ylim=y_range)

            fig = sns_fig.figure
            fig.suptitle(title, y=1.05)

        else:
            fig, ax = plt.subplots()
            ax = sns.lineplot(
                data=s,
                x=x,
                y=y_header,
                hue=color,
                ax=ax,
                marker="o" if markers else None,
                **kwargs,
            )

            ax.set_xlabel(x_label)
            ax.set_ylabel(y_label)
            ax.set_title(title)

            if x_range is not None:
                ax.set_xlim(x_range)

            if y_range is not None:
                ax.set_ylim(y_range)

            sns.move_legend(
                ax,
                loc="upper left",
                bbox_to_anchor=(1, 1),
                title="Variable",
                frameon=False,
            )

        plt.close(fig)
        if return_data:
            return fig, s
        return fig


def _report_summary_plot_info(c, x, y, x_label, x_axis_labels, x_cols, y_label, y_axis_label, y_cols):
    from pprint import pprint, pformat
    import textwrap

    print("Running summary_plot in verbose mode\n")
    print("Selected columns:")
    print(60 * "-")
    print(f"x: {x}")
    print(f"y: {y}")
    print("\nSelected Labels:")
    print(60 * "-")
    print(f"x: {x_label}")
    print(f"y: {y_label}")
    print("\nAvailable x-columns:")
    print(60 * "-")
    for col in x_cols[0]:
        print(f"{col}")
    print("\nAvailable y-columns sets:")
    print(60 * "-")
    for key, cols in y_cols.items():
        print(f"{key}:")
        for line in textwrap.wrap(pformat(cols, width=60), width=60):
            print("  " + line)
    print("\nAvailable y-columns:")
    print(60 * "-")
    cols = list(c.data.summary.columns)
    for line in textwrap.wrap(pformat(cols, width=60), width=60):
        print("  " + line)
    print("\nAvailable pre-defined labels:")
    print(60 * "-")
    print("x_axis_labels")
    pprint(x_axis_labels)
    print("y_axis_label")
    pprint(y_axis_label)


def partition_summary_cv_steps(
    c,
    x: str,
    column_set: list,
    split: bool = False,
    var_name: str = "variable",
    value_name: str = "value",
):
    """Partition the summary data into CV and non-CV steps.

    Args:
        c: cellpy object
        x: x-axis column name
        column_set: names of columns to include
        split: add additional column that can be used to split the data when plotting.
        var_name: name of the variable column after melting
        value_name: name of the value column after melting

    Returns:
        ``pandas.DataFrame`` (melted with columns x, var_name, value_name, and optionally "row" if split is True)
    """
    import pandas as pd

    summary = c.data.summary
    summary = summary[column_set]

    summary_no_cv = c.make_summary(selector_type="non-cv", create_copy=True).data.summary[column_set]
    summary_no_cv.columns = [col + "_non_cv" for col in summary_no_cv.columns]

    summary_only_cv = c.make_summary(selector_type="only-cv", create_copy=True).data.summary[column_set]
    summary_only_cv.columns = [col + "_cv" for col in summary_only_cv.columns]

    if split:
        id_vars = [x, "row"]
        summary_no_cv["row"] = "without CV"
        summary_only_cv["row"] = "with CV"
        summary["row"] = "all"
    else:
        id_vars = x

    summary_no_cv = summary_no_cv.reset_index()
    summary_only_cv = summary_only_cv.reset_index()
    summary = summary.reset_index()

    summary_no_cv = summary_no_cv.melt(id_vars, var_name=var_name, value_name=value_name)
    summary_only_cv = summary_only_cv.melt(id_vars, var_name=var_name, value_name=value_name)
    summary = summary.melt(id_vars, var_name=var_name, value_name=value_name)

    s = pd.concat([summary, summary_no_cv, summary_only_cv], axis=0)
    s = s.reset_index(drop=True)

    return s


def raw_plot(
    cell,
    y=None,
    y_label=None,
    x=None,
    x_label=None,
    title=None,
    interactive=True,
    plot_type="voltage-current",
    double_y=True,
    **kwargs,
):
    """Plot raw data.

    Args:
        cell: cellpy object
        y (str or list): y-axis column
        y_label (str or list): label for y-axis
        x (str): x-axis column
        x_label (str): label for x-axis
        title (str): title of the plot
        interactive (bool): use interactive plotting
        plot_type (str): type of plot (defaults to "voltage-current") (overrides given y if y is not None),
          currently only "voltage-current", "raw", "capacity", "capacity-current", and "full" is supported.
        double_y (bool): use double y-axis (only for matplotlib and when plot_type with 2 rows is used)
        **kwargs: additional parameters for the plotting backend

    Returns:
        ``matplotlib`` figure or ``plotly`` figure

    """
    from cellpy.readers.core import Q

    _set_individual_y_labels = False
    _special_height = None

    raw = cell.data.raw.copy()
    if y is not None:
        if y_label is None:
            y_label = y
        y = [y]
        y_label = [y_label]

    elif plot_type is not None:
        # special pre-defined plot types
        if plot_type == "voltage-current":
            y1 = _hdr_raw["voltage_txt"]
            y1_label = f"Voltage ({cell.data.raw_units.voltage})"
            y2 = _hdr_raw["current_txt"]
            y2_label = f"Current ({cell.data.raw_units.current})"
            y = [y1, y2]
            y_label = [y1_label, y2_label]

        elif plot_type == "capacity":
            _y = [
                (
                    _hdr_raw["charge_capacity_txt"],
                    f"Charge capacity ({cell.data.raw_units.charge})",
                ),
                (
                    _hdr_raw["discharge_capacity_txt"],
                    f"Discharge capacity ({cell.data.raw_units.charge})",
                ),
            ]
            y, y_label = zip(*_y)

        elif plot_type == "raw":
            _y = [
                (
                    _hdr_raw["cycle_index_txt"],
                    f"Cycle index (#)",
                ),
                (
                    _hdr_raw["step_index_txt"],
                    f"Step index (#)",
                ),
                (_hdr_raw["voltage_txt"], f"Voltage ({cell.data.raw_units.voltage})"),
                (_hdr_raw["current_txt"], f"Current ({cell.data.raw_units.current})"),
            ]
            y, y_label = zip(*_y)
            _special_height = 600

        elif plot_type == "capacity-current":
            _y = [
                (
                    _hdr_raw["charge_capacity_txt"],
                    f"Charge capacity ({cell.data.raw_units.charge})",
                ),
                (
                    _hdr_raw["discharge_capacity_txt"],
                    f"Discharge capacity ({cell.data.raw_units.charge})",
                ),
                (_hdr_raw["current_txt"], f"Current ({cell.data.raw_units.current})"),
            ]
            y, y_label = zip(*_y)
            _special_height = 500

        elif plot_type == "full":
            _y = [
                (_hdr_raw["voltage_txt"], f"Voltage ({cell.data.raw_units.voltage})"),
                (_hdr_raw["current_txt"], f"Current ({cell.data.raw_units.current})"),
                (
                    _hdr_raw["charge_capacity_txt"],
                    f"Charge capacity ({cell.data.raw_units.charge})",
                ),
                (
                    _hdr_raw["discharge_capacity_txt"],
                    f"Discharge capacity ({cell.data.raw_units.charge})",
                ),
                (
                    _hdr_raw["cycle_index_txt"],
                    f"Cycle index (#)",
                ),
                (
                    _hdr_raw["step_index_txt"],
                    f"Step index (#)",
                ),
            ]
            y, y_label = zip(*_y)
            _special_height = 800

        else:
            warnings.warn(f"Plot type {plot_type} not supported")
            return None
    else:
        # default to voltage if y is not given
        y = [_hdr_raw["voltage_txt"]]
        y_label = [f"Voltage ({cell.data.raw_units.voltage})"]

    if x is None:
        x = "test_time_hrs"

    if x in ["test_time_hrs", "test_time_hours"]:
        raw_time_unit = cell.raw_units.time
        conv_factor = Q(raw_time_unit).to("hours").magnitude
        raw[x] = raw[_hdr_raw["test_time_txt"]] * conv_factor
        x_label = x_label or "Time (hours)"
    elif x == "test_time_days":
        raw_time_unit = cell.raw_units.time
        conv_factor = Q(raw_time_unit).to("days").magnitude
        raw[x] = raw[_hdr_raw["test_time_txt"]] * conv_factor
        x_label = x_label or "Time (days)"
    elif x == "test_time_years":
        raw_time_unit = cell.raw_units.time
        conv_factor = Q(raw_time_unit).to("years").magnitude
        raw[x] = raw[_hdr_raw["test_time_txt"]] * conv_factor
        x_label = x_label or "Time (years)"

    if title is None:
        title = f"{cell.cell_name}"

    number_of_rows = len(y)

    if plotly_available and interactive:
        title = f"<b>{title}</b>"
        if number_of_rows == 1:
            # single plot
            import plotly.express as px

            if x_label or y_label:
                labels = {}
                if x_label:
                    labels[x] = x_label
                if y_label:
                    labels[y[0]] = y_label[0]
            else:
                labels = None
            fig = px.line(raw, x=x, y=y[0], title=title, labels=labels, **kwargs)

        else:
            from plotly.subplots import make_subplots
            import plotly.graph_objects as go

            width = kwargs.pop("width", 1000)
            height = kwargs.pop("height", None)
            if height is None:
                if _special_height is not None:
                    height = _special_height
                else:
                    height = number_of_rows * 300

            vertical_spacing = kwargs.pop("vertical_spacing", 0.02)

            fig = make_subplots(
                rows=number_of_rows,
                cols=1,
                shared_xaxes=True,
                vertical_spacing=vertical_spacing,
                x_title=x_label,
                # hoversubplots="axis",  # only available in plotly 5.21
            )
            x_values = raw[x]

            rows = range(1, number_of_rows + 1)
            for i in range(number_of_rows):
                fig.add_trace(
                    go.Scatter(x=x_values, y=raw[y[i]], name=y_label[i]),
                    row=rows[i],
                    col=1,
                    **kwargs,
                )

            fig.update_layout(height=height, width=width, title_text=title)
            if _set_individual_y_labels:
                for i in range(number_of_rows):
                    fig.update_yaxes(title_text=y_label[i], row=rows[i], col=1)

        return fig

    # default to a simple matplotlib figure
    xlim = kwargs.get("xlim")
    figsize = kwargs.pop("figsize", (10, 2 * number_of_rows))
    if seaborn_available:
        import seaborn as sns

        if double_y:
            sns.set_style(kwargs.pop("style", "dark"))
        else:
            sns.set_style(kwargs.pop("style", "darkgrid"))

    if len(y) == 1:
        y = y[0]
        y_label = y_label[0]
        fig, ax = plt.subplots(figsize=figsize)
        ax.plot(raw[x], raw[y])
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.set_title(title)
        ax.set_xlim(xlim)
        plt.close(fig)
        return fig

    elif len(y) == 2 and double_y:
        fig, ax_v = plt.subplots(figsize=figsize)

        color = "tab:red"
        ax_v.set_xlabel(x_label)
        ax_v.set_ylabel(y_label[0], color=color)
        ax_v.plot(raw[x], raw[y[0]], label=y_label[0], color=color)
        ax_v.tick_params(axis="y", labelcolor=color)

        ax_c = ax_v.twinx()

        color = "tab:blue"
        ax_c.set_ylabel(y_label[1], color=color)
        ax_c.plot(raw[x], raw[y[1]], label=y_label[1], color=color)
        ax_c.tick_params(axis="y", labelcolor=color)
        ax_v.set_xlim(xlim)
    else:

        fig, axes = plt.subplots(nrows=number_of_rows, ncols=1, figsize=figsize, sharex=True)

        for i in range(number_of_rows):
            axes[i].plot(raw[x], raw[y[i]])
            axes[i].set_ylabel(y_label[i])

        axes[0].set_title(title)
        axes[0].set_xlim(xlim)
        axes[-1].set_xlabel(x_label)

        fig.align_ylabels()

    fig.tight_layout()
    plt.close(fig)
    return fig


def cycle_info_plot(
    cell,
    cycle=None,
    get_axes=False,
    interactive=True,
    t_unit="hours",
    v_unit="V",
    i_unit="mA",
    **kwargs,
):
    """Show raw data together with step and cycle information.

    Args:
        cell: cellpy object
        cycle (int or list or tuple): cycle(s) to select (must be int for matplotlib)
        get_axes (bool): return axes (for matplotlib) or figure (for plotly)
        interactive (bool): use interactive plotting (if available)
        t_unit (str): unit for x-axis (default: "hours")
        v_unit (str): unit for y-axis (default: "V")
        i_unit (str): unit for current (default: "mA")
        **kwargs: parameters specific to plotting backend.

    Returns:
        ``matplotlib.axes`` or None
    """
    t_scaler = cell.unit_scaler_from_raw(t_unit, "time")
    v_scaler = cell.unit_scaler_from_raw(v_unit, "voltage")
    i_scaler = cell.unit_scaler_from_raw(i_unit, "current")

    if plotly_available and interactive:
        fig = _cycle_info_plot_plotly(
            cell,
            cycle,
            get_axes,
            t_scaler,
            t_unit,
            v_scaler,
            v_unit,
            i_scaler,
            i_unit,
            **kwargs,
        )
        if get_axes:
            return fig
        return fig

    axes = _cycle_info_plot_matplotlib(
        cell,
        cycle,
        get_axes,
        t_scaler,
        t_unit,
        v_scaler,
        v_unit,
        i_scaler,
        i_unit,
        **kwargs,
    )

    if get_axes:
        return axes


def _cycle_info_plot_plotly(
    cell,
    cycle,
    get_axes,
    t_scaler,
    t_unit,
    v_scaler,
    v_unit,
    i_scaler,
    i_unit,
    **kwargs,
):
    import plotly.express as px
    import plotly.graph_objects as go
    import numpy as np

    if kwargs.get("xlim"):
        logging.info("xlim is not supported for plotly yet")

    raw_hdr = get_headers_normal()
    step_hdr = get_headers_step_table()

    data = cell.data.raw.copy()
    table = cell.data.steps.copy()

    if cycle is None:
        cycle = list(data["cycle_index"].unique())

    if not isinstance(cycle, (list, tuple)):
        cycle = [cycle]

    delta = "_delta"
    v_delta = step_hdr["voltage"] + delta
    i_delta = step_hdr["current"] + delta
    c_delta = step_hdr["charge"] + delta
    dc_delta = step_hdr["discharge"] + delta
    cycle_ = step_hdr["cycle"]
    step_ = step_hdr["step"]
    type_ = step_hdr["type"]

    time_hdr = raw_hdr["test_time_txt"]
    cycle_hdr = raw_hdr["cycle_index_txt"]
    step_number_hdr = raw_hdr["step_index_txt"]
    current_hdr = raw_hdr["current_txt"]
    voltage_hdr = raw_hdr["voltage_txt"]

    data = data[
        [
            time_hdr,
            cycle_hdr,
            step_number_hdr,
            current_hdr,
            voltage_hdr,
        ]
    ]

    table = table[
        [
            cycle_,
            step_,
            type_,
            v_delta,
            i_delta,
            c_delta,
            dc_delta,
        ]
    ]
    m_cycle_data = data[cycle_hdr].isin(cycle)
    data = data.loc[m_cycle_data, :]

    data[time_hdr] = data[time_hdr] * t_scaler
    data[voltage_hdr] = data[voltage_hdr] * v_scaler
    data[current_hdr] = data[current_hdr] * i_scaler
    data = data.merge(
        table,
        left_on=(cycle_hdr, step_number_hdr),
        right_on=(cycle_, step_),
    ).sort_values(by=[time_hdr])

    fig = go.Figure()

    grouped_data = data.groupby(cycle_hdr)
    for cycle_number, group in grouped_data:
        x = group[time_hdr]
        y = group[voltage_hdr]
        s = group[step_number_hdr]
        i = group[current_hdr]

        st = group[type_]
        dV = group[v_delta]
        dI = group[i_delta]
        dC = group[c_delta]
        dDC = group[dc_delta]

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                name=f"cycle {cycle_number}",
                customdata=np.stack((i, s, st, dV, dI, dC, dDC), axis=-1),
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

    cell_name = kwargs.get("title", cell.cell_name)
    title_start = f"<b>{cell_name}</b> Cycle"
    if len(cycle) > 2:
        if cycle[-1] - cycle[0] == len(cycle) - 1:
            title = f"{title_start}s {cycle[0]} - {cycle[-1]}"
        else:
            title = f"{title_start}s {cycle}"
    elif len(cycle) == 2:
        title = f"{title_start}s {cycle[0]} and {cycle[1]}"
    else:
        title = f"{title_start} {cycle[0]}"

    fig.update_layout(
        title=title,
        xaxis_title=f"Time ({t_unit})",
        yaxis_title=f"Voltage ({v_unit})",
    )

    if get_axes:
        return fig
    fig.show()


def _plot_step(ax, x, y, color):
    ax.plot(x, y, color=color, linewidth=3)


def _get_info(table, cycle, step):
    # obs! hard-coded col-names. Please fix me.
    m_table = (table.cycle == cycle) & (table.step == step)
    p1, p2 = table.loc[m_table, ["point_min", "point_max"]].values[0]
    c1, c2 = table.loc[m_table, ["current_min", "current_max"]].abs().values[0]
    d_voltage, d_current = table.loc[m_table, ["voltage_delta", "current_delta"]].values[0]
    d_discharge, d_charge = table.loc[m_table, ["discharge_delta", "charge_delta"]].values[0]
    current_max = (c1 + c2) / 2
    rate = table.loc[m_table, "rate_avr"].values[0]
    step_type = table.loc[m_table, "type"].values[0]
    return [step_type, rate, current_max, d_voltage, d_current, d_discharge, d_charge]


def _cycle_info_plot_matplotlib(
    cell,
    cycle,
    get_axes,
    t_scaler,
    t_unit,
    v_scaler,
    v_unit,
    i_scaler,
    i_unit,
    **kwargs,
):
    # obs! hard-coded col-names. Please fix me.
    if cycle is None:
        warnings.warn("Only one cycle at a time is supported for matplotlib")
        cycle = 1

    if isinstance(cycle, (list, tuple)):
        warnings.warn("Only one cycle at a time is supported for matplotlib")
        cycle = cycle[0]

    data = cell.data.raw
    table = cell.data.steps

    span_colors = ["#4682B4", "#FFA07A"]

    voltage_color = "#008B8B"
    current_color = "#CD5C5C"

    m_cycle_data = data.cycle_index == cycle
    all_steps = data[m_cycle_data]["step_index"].unique()

    color = itertools.cycle(span_colors)

    fig = plt.figure(figsize=(20, 8))
    fig.suptitle(f"Cycle: {cycle}")

    ax3 = plt.subplot2grid((8, 3), (0, 0), colspan=3, rowspan=1, fig=fig)  # steps
    ax4 = plt.subplot2grid((8, 3), (1, 0), colspan=3, rowspan=2, fig=fig)  # info
    ax1 = plt.subplot2grid((8, 3), (3, 0), colspan=3, rowspan=5, fig=fig)  # data

    ax2 = ax1.twinx()
    ax1.set_xlabel(f"time ({t_unit})")
    ax1.set_ylabel(f"voltage ({v_unit})", color=voltage_color)
    ax2.set_ylabel(f"current ({i_unit})", color=current_color)

    annotations_1 = []  # step number (IR)
    annotations_2 = []  # step number
    annotations_4 = []  # info

    for i, s in enumerate(all_steps):
        m = m_cycle_data & (data.step_index == s)
        c = data.loc[m, "current"] * i_scaler
        v = data.loc[m, "voltage"] * v_scaler
        t = data.loc[m, "test_time"] * t_scaler
        step_type, rate, current_max, dv, dc, d_discharge, d_charge = _get_info(table, cycle, s)
        if len(t) > 1:
            fcolor = next(color)

            info_txt = f"{step_type}\ni = |{i_scaler * current_max:0.2f}| {i_unit}\n"
            info_txt += f"delta V = {dv:0.2f} %\ndelta i = {dc:0.2f} %\n"
            info_txt += f"delta C = {d_charge:0.2} %\ndelta DC = {d_discharge:0.2} %\n"

            for ax in [ax2, ax3, ax4]:
                ax.axvspan(t.iloc[0], t.iloc[-1], facecolor=fcolor, alpha=0.2)
            _plot_step(ax1, t, v, voltage_color)
            _plot_step(ax2, t, c, current_color)
            annotations_1.append([f"{s}", t.mean()])
            annotations_4.append([info_txt, t.mean()])
        else:
            info_txt = f"{s}({step_type})"
            annotations_2.append([info_txt, t.mean()])
    ax3.set_ylim(0, 1)
    for s in annotations_1:
        ax3.annotate(f"{s[0]}", (s[1], 0.2), ha="center")

    for s in annotations_2:
        ax3.annotate(f"{s[0]}", (s[1], 0.6), ha="center")

    for s in annotations_4:
        ax4.annotate(f"{s[0]}", (s[1], 0.0), ha="center")

    for ax in [ax3, ax4]:
        ax.axes.get_yaxis().set_visible(False)
        ax.axes.get_xaxis().set_visible(False)

    if x := kwargs.get("xlim"):
        ax1.set_xlim(x)
        ax2.set_xlim(x)
        ax3.set_xlim(x)
        ax4.set_xlim(x)

    if get_axes:
        return ax1, ax2, ax2, ax4


def cycles_plot(
    c,
    cycles=None,
    formation_cycles=3,
    show_formation=True,
    mode="gravimetric",
    method="forth-and-forth",
    interpolated=True,
    number_of_points=200,
    colormap="Blues_r",
    formation_colormap="autumn",
    cut_colorbar=True,
    title=None,
    figsize=(6, 4),
    xlim=None,
    ylim=None,
    interactive=True,
    return_figure=None,
    width=600,
    height=400,
    marker_size=5,
    formation_line_color="rgba(152, 0, 0, .8)",
    force_colorbar=False,
    force_nonbar=False,
    plotly_template=None,
):
    """
    Plot the voltage vs. capacity for different cycles of a cell.

    This function is meant as an easy way of visualizing the voltage vs. capacity for different cycles of a cell. The
    cycles are plotted with different colors, and the formation cycles are highlighted with a different colormap.
    It is not intended to provide you with high quality plots, but rather to give you a quick overview of the data.

    Args:
        c: cellpy object containing the data to plot.
        cycles (list, optional): List of cycle numbers to plot. If None, all cycles are plotted.
        formation_cycles (int, optional): Number of formation cycles to highlight. Default is 3.
        show_formation (bool, optional): Whether to show formation cycles. Default is True.
        mode (str, optional): Mode for capacity ('gravimetric', 'areal', etc.). Default is 'gravimetric'.
        method (str, optional): Method for interpolation. Default is 'forth-and-forth'.
        interpolated (bool, optional): Whether to interpolate the data. Default is True.
        number_of_points (int, optional): Number of points for interpolation. Default is 200.
        colormap (str, optional): Colormap for the cycles. Default is 'Blues_r'.
        formation_colormap (str, optional): Colormap for the formation cycles. Default is 'autumn'.
        cut_colorbar (bool, optional): Whether to cut the colorbar. Default is True.
        title (str, optional): Title of the plot. If None, the cell name is used.
        figsize (tuple, optional): Size of the figure for matplotlib. Default is (6, 4).
        xlim (list, optional): Limits for the x-axis.
        ylim (list, optional): Limits for the y-axis.
        interactive (bool, optional): Whether to use interactive plotting (Plotly). Default is True.
        return_figure (bool, optional): Whether to return the figure object. Default is opposite of interactive.
        width (int, optional): Width of the figure for Plotly. Default is 600.
        height (int, optional): Height of the figure for Plotly. Default is 400.
        marker_size (int, optional): Size of the markers for Plotly. Default is 5.
        formation_line_color (str, optional): Color for the formation cycle lines in Plotly. Default is 'rgba(152, 0, 0, .8)'.
        force_colorbar (bool, optional): Whether to force the colorbar to be shown. Default is False.
        force_nonbar (bool, optional): Whether to force the colorbar to be hidden. Default is False.
        plotly_template (str, optional): Plotly template to use (uses default template if None).

    Returns:
        matplotlib.figure.Figure or plotly.graph_objects.Figure: The generated plot figure.
    """

    import numpy as np
    import matplotlib
    from matplotlib.colors import Normalize, ListedColormap

    if interactive and not plotly_available:
        warnings.warn("Can not perform interactive plotting. Plotly is not available.")
        interactive = False

    if return_figure is None:
        return_figure = not interactive

    if cycles is None:
        cycles = c.get_cycle_numbers()

    if interactive and title is None:
        fig_title = f"Capacity plots for <b>{c.cell_name}</b>"
        fig_title += f"<br>{mode} mode"
        if interpolated:
            fig_title += f", interpolated ({number_of_points} points)"

    else:
        fig_title = title or f"Capacity plots for {c.cell_name}"

    kw_arguments = dict(
        method=method,
        interpolated=interpolated,
        label_cycle_number=True,
        categorical_column=True,
        number_of_points=number_of_points,
        insert_nan=True,
        mode=mode,
    )
    df = c.get_cap(cycles=cycles, **kw_arguments)

    selector = df["cycle"] <= formation_cycles
    formation_cycles = df.loc[selector, :]
    rest_cycles = df.loc[~selector, :]

    n_formation_cycles = len(formation_cycles["cycle"].unique())
    n_rest_cycles = len(rest_cycles["cycle"].unique())

    capacity_unit = _get_capacity_unit(c, mode=mode)

    cbar_aspect = 30

    if not interactive:
        fig, ax = plt.subplots(1, 1, figsize=figsize)
        fig_width, fig_height = figsize

        if not formation_cycles.empty and show_formation:
            if fig_width < 6:
                print("Warning: try setting the figsize to (6, 4) or larger")
            if fig_width > 8:
                print("Warning: try setting the figsize to (8, 4) or smaller")
            min_cycle, max_cycle = (
                formation_cycles["cycle"].min(),
                formation_cycles["cycle"].max(),
            )
            norm_formation = Normalize(vmin=min_cycle, vmax=max_cycle)
            cycle_sequence = np.arange(min_cycle, max_cycle + 1, 1)

            shrink = min(1.0, (1 / 8) * n_formation_cycles)

            c_m_formation = ListedColormap(plt.get_cmap(formation_colormap, 2 * len(cycle_sequence))(cycle_sequence))
            s_m_formation = matplotlib.cm.ScalarMappable(cmap=c_m_formation, norm=norm_formation)
            for name, group in formation_cycles.groupby("cycle"):
                ax.plot(
                    group["capacity"],
                    group["voltage"],
                    lw=2,
                    # alpha=0.7,
                    color=s_m_formation.to_rgba(name),
                    label=f"Cycle {name}",
                )
            cbar_formation = fig.colorbar(
                s_m_formation,
                ax=ax,
                # label="Formation Cycle",
                ticks=np.arange(
                    formation_cycles["cycle"].min(),
                    formation_cycles["cycle"].max() + 1,
                    1,
                ),
                shrink=shrink,
                aspect=cbar_aspect * shrink,
                location="right",
                anchor=(0.0, 0.0),
            )
            cbar_formation.set_label(
                "Form. Cycle",
                rotation=270,
                labelpad=12,
            )

        norm = Normalize(vmin=rest_cycles["cycle"].min(), vmax=rest_cycles["cycle"].max())
        if cut_colorbar:
            cycle_sequence = np.arange(rest_cycles["cycle"].min(), rest_cycles["cycle"].max() + 1, 1)
            n = int(np.round(1.2 * rest_cycles["cycle"].max()))
            c_m = ListedColormap(plt.get_cmap(colormap, n)(cycle_sequence))
        else:
            c_m = plt.get_cmap(colormap)

        s_m = matplotlib.cm.ScalarMappable(cmap=c_m, norm=norm)
        for name, group in rest_cycles.groupby("cycle"):
            ax.plot(
                group["capacity"],
                group["voltage"],
                lw=1,
                color=s_m.to_rgba(name),
                label=f"Cycle {name}",
            )
        cbar = fig.colorbar(
            s_m,
            ax=ax,
            label="Cycle",
            aspect=cbar_aspect,
            location="right",
        )
        cbar.set_label(
            "Cycle",
            rotation=270,
            labelpad=12,
        )
        # cbar.ax.yaxis.set_ticks_position("left")

        ax.set_xlabel(f"Capacity ({capacity_unit})")
        ax.set_ylabel(f"Voltage ({c.cellpy_units.voltage})")

        ax.set_title(fig_title)

        if xlim:
            ax.set_xlim(xlim)
        if ylim:
            ax.set_ylim(ylim)

        if return_figure:
            plt.close(fig)
            return fig
    else:

        import plotly.express as px
        import plotly.graph_objects as go

        set_plotly_template(plotly_template)

        color_scales = px.colors.named_colorscales()
        if colormap not in color_scales:
            colormap = "Blues_r"

        if cut_colorbar:
            range_color = [df["cycle"].min(), 1.2 * df["cycle"].max()]
        else:
            range_color = [df["cycle"].min(), df["cycle"].max()]
        if (n_rest_cycles < 8 and not force_colorbar) or force_nonbar:
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
                y="voltage",
                color="cycle",
                title=fig_title,
                labels={
                    "capacity": f"Capacity ({capacity_unit})",
                    "voltage": f"Voltage ({c.cellpy_units.voltage})",
                },
                color_discrete_sequence=cmap,
            )

        else:
            show_formation_legend = False
            fig = px.scatter(
                rest_cycles,
                x="capacity",
                y="voltage",
                color="cycle",
                title=fig_title,
                labels={
                    "capacity": f"Capacity ({capacity_unit})",
                    "voltage": f"Voltage ({c.cellpy_units.voltage})",
                },
                color_continuous_scale=colormap,
                range_color=range_color,
            )
            fig.update_traces(mode="lines+markers", line_color="white", line_width=1)

        if not formation_cycles.empty and show_formation:
            for name, group in formation_cycles.groupby("cycle"):
                trace = go.Scatter(
                    x=group["capacity"],
                    y=group["voltage"],
                    name=f"{name} (f.c.)",
                    hovertemplate=f"Formation Cycle {name}<br>Capacity: %{{x}}<br>Voltage: %{{y}}",
                    mode="lines",
                    marker=dict(color=formation_line_color),
                    showlegend=show_formation_legend,
                    legendrank=1,
                    legendgroup="formation",
                )

                fig.add_trace(trace)

        fig.update_traces(marker=dict(size=marker_size))
        fig.update_layout(height=height, width=width)
        if xlim:
            fig.update_xaxes(range=xlim)
        if ylim:
            fig.update_yaxes(range=ylim)

        if return_figure:
            return fig
        fig.show()


def _check_plotter_plotly():
    import pathlib

    import cellpy

    p = pathlib.Path("../../testdata/hdf5/20160805_test001_45_cc.h5")
    out = pathlib.Path("../../tmp")
    assert out.exists()
    c = cellpy.get(p)
    fig = cycles_plot(
        c,
        ylim=[0.0, 1.0],
        show_formation=False,
        cut_colorbar=False,
        title="My nice plot",
        interactive=True,
        return_figure=True,
    )
    print("saving figure")
    print(f"{fig=}")
    print(f"{type(fig)=}")
    save_image_files(fig, out / "test_plot_plotly", backend="plotly")
    fig.show()


def _check_plotter_matplotlib():
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pathlib

    import cellpy

    p = pathlib.Path("../../testdata/hdf5/20160805_test001_45_cc.h5")
    out = pathlib.Path("../../tmp")
    assert out.exists()
    c = cellpy.get(p)
    fig = cycles_plot(
        c,
        ylim=[0.0, 1.0],
        show_formation=False,
        cut_colorbar=False,
        title="My nice plot",
        interactive=False,
        return_figure=True,
    )
    print("saving figure")
    print(f"{fig=}")
    print(f"{type(fig)=}")
    save_image_files(fig, out / "test_plot_matplotlib", backend="matplotlib")
    # need to create a new manager to show the figure since it is closed in
    # the plot_cycles function when issuing return_figure=True:
    make_matplotlib_manager(fig)
    plt.show()


def _check_summary_plotter_plotly():
    import pathlib

    import cellpy

    p = pathlib.Path("../../testdata/hdf5/20160805_test001_45_cc.h5")
    out = pathlib.Path("../../tmp")
    assert out.exists()
    c = cellpy.get(p)
    fig = summary_plot(
        c,
        # ylim=[0.0, 1.0],
        # show_formation=False,
        # cut_colorbar=False,
        title="My nice plot",
        interactive=True,
        # return_figure=True,
    )
    print("saving figure")
    print(f"{fig=}")
    print(f"{type(fig)=}")
    # save_image_files(fig, out / "test_plot_plotly", backend="plotly")
    fig.show()


if __name__ == "__main__":
    _check_plotter_plotly()
    # _check_plotter_matplotlib()
    # _check_summary_plotter_plotly()
