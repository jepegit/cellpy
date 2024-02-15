# -*- coding: utf-8 -*-
"""
Utilities for helping to plot cellpy-data.
"""

import collections
import importlib
import itertools
import logging
import os
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

# logger = logging.getLogger(__name__)
logging.captureWarnings(True)

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

hdr_summary = get_headers_summary()
hdr_raw = get_headers_normal()
hdr_steps = get_headers_step_table()
hdr_journal = get_headers_journal()


def create_colormarkerlist_for_journal(
    journal, symbol_label="all", color_style_label="seaborn-colorblind"
):
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
    groups = journal.pages[hdr_journal.group].unique()
    sub_groups = journal.pages[hdr_journal.subgroup].unique()
    return create_colormarkerlist(groups, sub_groups, symbol_label, color_style_label)


def create_colormarkerlist(
    groups, sub_groups, symbol_label="all", color_style_label="seaborn-colorblind"
):
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
    """Create column information for summary plots."""

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
        _capacities_areal
        + [col + "_cv" for col in _capacities_areal]
        + [col + "_non_cv" for col in _capacities_areal]
    )

    x_columns = ([hdr.cycle_index, hdr.data_point, hdr.test_time, hdr.datetime],)
    y_cols = dict(
        voltages=[hdr.end_voltage_charge, hdr.end_voltage_discharge],
        capacities_gravimetric=_capacities_gravimetric,
        capacities_areal=_capacities_areal,
        capacities_gravimetric_split_constant_voltage=_capacities_gravimetric_split,
        capacities_areal_split_constant_voltage=_capacities_areal_split,
    )
    return x_columns, y_cols


def create_label_dict(c):
    hdr = c.headers_summary
    x_axis_labels = {
        hdr.cycle_index: "Cycle Number",
        hdr.data_point: "Point",
        hdr.test_time: f"Test Time ({c.cellpy_units.time})",
        hdr.datetime: "Date",
    }

    _cap_gravimetric_label = (
        f"Capacity ({c.cellpy_units.charge}/{c.cellpy_units.specific_gravimetric})"
    )
    _cap_areal_label = (
        f"Capacity ({c.cellpy_units.charge}/{c.cellpy_units.specific_areal})"
    )

    y_axis_label = {
        "voltages": f"Voltage ({c.cellpy_units.voltage})",
        "capacities_gravimetric": _cap_gravimetric_label,
        "capacities_areal": _cap_areal_label,
        "capacities_gravimetric_split_constant_voltage": _cap_gravimetric_label,
        "capacities_areal_split_constant_voltage": _cap_areal_label,
    }
    return x_axis_labels, y_axis_label


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
    **kwargs,
):
    """Create a summary plot. Currently only supports plotly.


    Args:
        c: cellpy object
        x: x-axis column (default: cycle_index)
        y: y-axis column or column set (predefined sets implemented are: "voltages",
          "capacities_gravimetric", "capacities_areal", "capacities_gravimetric_split_constant_voltage",
          "capacities_areal_split_constant_voltage")
        height: height of the plot
        markers: use markers
        title: title of the plot
        x_range: limits for x-axis
        y_range: limits for y-axis
        split: split the plot
        interactive: use interactive plotting
        rangeslider: add a range slider to the x-axis (only for plotly)
        share_y (bool): share y-axis
        **kwargs: additional parameters for the plotting backend

    Returns:
        plotly figure or None

    """

    if plotly_available and interactive:
        import plotly.express as px
    else:
        warnings.warn(
            "plotly not available, and it is currently the only supported backend"
        )
        return None

    if title is None:
        title = f"Summary <b>{c.cell_name}</b>"

    if x is None:
        x = "cycle_index"

    x_columns, y_cols = create_col_info(c)
    x_axis_labels, y_axis_label = create_label_dict(c)

    # ------------------- main --------------------------------------------
    y_header = "value"
    color = "variable"

    additional_kwargs = dict(
        color=color,
        height=height,
        markers=markers,
        title=title,
    )

    # filter on constant voltage vs constant current
    if y.endswith("_split_constant_voltage"):
        cap_type = (
            "capacities_gravimetric"
            if y.startswith("capacities_gravimetric")
            else "capacities_areal"
        )
        column_set = y_cols[cap_type]
        s = partition_summary_cv_steps(c, x, column_set, split, color, y_header)
        if split:
            additional_kwargs["facet_row"] = "row"

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
    y_label = y_axis_label.get(y, y)
    fig = px.line(
        s,
        x=x,
        y=y_header,
        **additional_kwargs,
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

    return fig


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
        pandas DataFrame (melted with columns x, var_name, value_name, and optionally "row" if split is True)
    """
    import pandas as pd

    summary = c.data.summary
    summary = summary[column_set]

    summary_no_cv = c.make_summary(
        selector_type="non-cv", create_copy=True
    ).data.summary[column_set]
    summary_no_cv.columns = [col + "_non_cv" for col in summary_no_cv.columns]

    summary_only_cv = c.make_summary(
        selector_type="only-cv", create_copy=True
    ).data.summary[column_set]
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

    summary_no_cv = summary_no_cv.melt(
        id_vars, var_name=var_name, value_name=value_name
    )
    summary_only_cv = summary_only_cv.melt(
        id_vars, var_name=var_name, value_name=value_name
    )
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
    **kwargs,
):
    # TODO: missing doc-string

    raw = cell.data.raw.copy()

    if y is None:
        y, y_label = ("voltage", f"Voltage ({cell.data.raw_units.voltage})")
    if x is None:
        x, x_label = ("test_time_hrs", "Time (hours)")

    if title is None:
        title = f"{cell.cell_name}"

    if x == "test_time_hrs":
        raw["test_time_hrs"] = raw[hdr_raw["test_time_txt"]] / 3600

    if plotly_available and interactive:
        import plotly.express as px

        title = f"<b>{title}</b>"
        if x_label or y_label:
            labels = {}
            if x_label:
                labels[x] = x_label
            if y_label:
                labels[y] = y_label
        else:
            labels = None
        fig = px.line(raw, x=x, y=y, title=title, labels=labels, **kwargs)

        return fig

    # default to a simple matplotlib figure
    fig, ax = plt.subplots()
    ax.plot(raw[x], raw[y])
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.set_title(title)

    return ax


def cycle_info_plot(
    cell,
    cycle,
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
    )

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
    d_voltage, d_current = table.loc[
        m_table, ["voltage_delta", "current_delta"]
    ].values[0]
    d_discharge, d_charge = table.loc[
        m_table, ["discharge_delta", "charge_delta"]
    ].values[0]
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
        step_type, rate, current_max, dv, dc, d_discharge, d_charge = _get_info(
            table, cycle, s
        )
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


if __name__ == "__main__":
    pass
