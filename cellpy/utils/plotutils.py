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

    if y is None:
        y, y_label = ("voltage", "Voltage (V)")
    if x is None:
        x, x_label = ("test_time_hrs", "Time (hours)")

    if title is None:
        title = f"{cell.cell_name}"

    raw = cell.data.raw
    if x == "test_time_hrs":
        raw["test_time_hrs"] = raw[hdr_raw["test_time_txt"]] / 3600

    if plotly_available and interactive:
        import plotly.express as px

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
    interactive=False,
    **kwargs,
):
    """Show raw data together with step and cycle information.

    Args:
        cell: cellpy object
        cycle (int or list or tuple): cycle(s) to select (must be int for matplotlib)
        get_axes (bool): return axes (for matplotlib) or figure (for plotly)
        interactive (bool): use interactive plotting (if available)
        **kwargs: parameters specific to plotting backend.

    Returns:
        ``matplotlib.axes`` or None
    """
    if plotly_available and interactive:
        fig = _cycle_info_plot_plotly(cell, cycle, get_axes, **kwargs)
        if get_axes:
            return fig
        return fig

    axes = _cycle_info_plot_matplotlib(cell, cycle, get_axes, **kwargs)
    if get_axes:
        return axes


def _cycle_info_plot_plotly(cell, cycle=None, get_axes=False, **kwargs):
    import plotly.express as px
    import plotly.graph_objects as go
    import numpy as np

    # TODO: implement options for units
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

    data = data.merge(
        table,
        left_on=(cycle_hdr, step_number_hdr),
        right_on=(cycle_, step_),
    )

    hover_template = (
        "<br>".join(
            [
                "Time: %{x:.2f}",
                "Voltage: %{y:.4f} V",
                "Current: %{customdata[0]:.4f} mA",
                "Step: %{customdata[1]}",
                "Type: %{customdata[2]}",
                "delta V: %{customdata[3]:.2f}",
                "delta I: %{customdata[4]:.2f}",
                "delta C: %{customdata[5]:.2f}",
                "delta DC: %{customdata[6]:.2f}",
            ]
        ),
    )

    fig = go.Figure()

    grouped_data = data.groupby(cycle_hdr)
    for cycle_number, group in grouped_data:
        x = group[time_hdr] / 3600
        y = group[voltage_hdr]
        s = group[step_number_hdr]
        i = group[current_hdr] * 1000

        st = group[step_]
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
                hovertemplate=hover_template,
            )
        )

    if len(cycle) > 2:
        if cycle[-1] - cycle[0] == len(cycle) - 1:
            title = f"{cell.cell_name} Cycles {cycle[0]} - {cycle[-1]}"
        else:
            title = f"{cell.cell_name} Cycles {cycle}"
    elif len(cycle) == 2:
        title = f"{cell.cell_name} Cycles {cycle[0]} and {cycle[1]}"
    else:
        title = f"{cell.cell_name} Cycle {cycle[0]}"

    fig.update_layout(
        title=title,
        xaxis_title="Time (hours)",
        yaxis_title="Voltage (V)",
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


def _cycle_info_plot_matplotlib(cell, cycle, get_axes=False, **kwargs):
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
    ax4 = plt.subplot2grid((8, 3), (1, 0), colspan=3, rowspan=2, fig=fig)  # rate
    ax1 = plt.subplot2grid((8, 3), (3, 0), colspan=3, rowspan=5, fig=fig)  # data

    ax2 = ax1.twinx()
    ax1.set_xlabel("time (minutes)")
    ax1.set_ylabel("voltage (V vs. Li/Li+)", color=voltage_color)
    ax2.set_ylabel("current (mA)", color=current_color)

    annotations_1 = []  # step number (IR)
    annotations_2 = []  # step number
    annotations_4 = []  # rate

    for i, s in enumerate(all_steps):
        m = m_cycle_data & (data.step_index == s)
        c = data.loc[m, "current"] * 1000
        v = data.loc[m, "voltage"]
        t = data.loc[m, "test_time"] / 60
        step_type, rate, current_max, dv, dc, d_discharge, d_charge = _get_info(
            table, cycle, s
        )
        if len(t) > 1:
            fcolor = next(color)

            info_txt = (
                f"{step_type}\nc-rate = {rate}\ni = |{1000 * current_max:0.2f}| mA\n"
            )
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

    if get_axes:
        return ax1, ax2, ax2, ax4


if __name__ == "__main__":
    pass
