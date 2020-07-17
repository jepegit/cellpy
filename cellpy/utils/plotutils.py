# -*- coding: utf-8 -*-
"""
Utilities for helping to plot cellpy-data.
"""

import os
import warnings
import importlib
import logging
import itertools

from cellpy.parameters.internal_settings import (
    get_headers_summary,
    get_headers_normal,
    get_headers_step_table,
    get_headers_journal,
)

from cellpy.utils import helpers

try:
    import matplotlib.pyplot as plt

    plt_available = True
except ImportError:
    plt_available = False

try:
    from holoviews import opts
    import holoviews as hv
    from holoviews.plotting.links import RangeToolLink

    hv_available = True
except ImportError:
    hv_available = False

bokeh_available = importlib.util.find_spec("bokeh") is not None

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


def _hv_bokeh_available():
    if not hv_available:
        print("You need holoviews. But I cannot load it. Aborting...")
        return False
    if not bokeh_available:
        print("You need Bokeh. But I cannot find it. Aborting...")
        return False
    return True


def find_column(columns, label=None, end="cycle_index"):
    """find columns based on how the column-name ends.

    Args:
        columns: pandas columns
        label: if not provided, generate, if provided, return as is
        end: the string to use for searching

    Returns:
        column header, label
    """
    hdr = None
    lab = None
    for col in columns:
        if col.endswith(end):
            hdr = col
            if label is None:
                lab = col.replace("_", " ")
            else:
                lab = label
            break
    return hdr, lab


def plot_concatenated(
    dataframe,
    x=None,
    y=None,
    err=None,
    xlabel=None,
    ylabel=None,
    points=True,
    line=True,
    errors=True,
    hover=True,
    width=800,
    height=300,
    journal=None,
    file_id_level=0,
    hdr_level=None,
    axis=1,
    mean_end="_mean",
    std_end="_std",
    cycle_end="cycle_index",
    legend_title="cell-type",
    marker_size=None,
    cmap="default_colors",
    spread=False,
    extension="bokeh",
    edges=False,
    **kwargs,
):
    """Create a holoviews plot of the concatenated summary.

    This function is still under development. Feel free to contribute.

    Args:
        dataframe: the concatenated summary
        x: colum-name for the x variable (not implemented yet)
        y: colum-name for the y variable (not implemented yet)
        err: colum-name for the std variable (not implemented yet)
        xlabel: label for x-axis
        ylabel: label for y-axis
        points (bool): plot points if True
        line (bool): plot line if True
        errors (bool): plot errors if True
        hover (bool): add hover tool if True
        width: width of plot
        height: height of plot
        journal: batch.journal object
        file_id_level: the level (multiindex-level) where the cell-names are.
        hdr_level:  the level (multiindex-level) where the parameter names are.
        axis: what axis to use when looking in the data-frame (row-based or col-based).
        mean_end: used for searching for y-column names
        std_end: used for searching for e-column names
        cycle_end: used for searching for x-column name
        legend_title: title to put over the legends
        marker_size: size of the markers used
        cmap: color-map to use
        spread (bool): plot error-bands instead of error-bars if True
        extension (str): "matplotlib" or "bokeh". Note, this uses hv.extension) and will affect the
            state of your notebook
        edges (bool): show all axes
        **kwargs: key-word arguments sent to hv.NdOverlay

    Example:
        >>> my_mpl_plot = plot_concatenated(
        >>>     cap_cycle_norm_fast_1000, journal=b.experiment.journal,
        >>>     height=500, marker_size=5,
        >>>     extension="matplotlib",
        >>>     edges=True,
        >>> )

        >>> my_bokeh_plot = plot_concatenated(
        >>>     cap_cycle_norm_fast_1000, journal=b.experiment.journal,
        >>>     height=500, marker_size=5,
        >>>     edges=True,
        >>> )


    Example:
        >>> # Simple conversion from bokeh to matplotlib
        >>> # NB! make sure you have only used matplotlib-bokeh convertable key-words (not marker_size)

        >>> hv.extension("matplotlib")
        >>> my_plot.opts(aspect="auto", fig_inches=(12,7), fig_size=90, legend_position="top_right",
        >>>              legend_cols = 2,
        >>>              show_frame=True)

    """
    if not hv_available:
        print(
            "This function uses holoviews. But could not import it."
            "So I am aborting..."
        )
        return

    hv.extension(extension, logo=False)

    if hdr_level is None:
        hdr_level = 0 if file_id_level == 1 else 1

    averaged = True
    columns = list(set(dataframe.columns.get_level_values(hdr_level)))
    hdr_x, lab_x = find_column(columns, label=xlabel, end=cycle_end)
    hdr_y, lab_y = find_column(columns, label=ylabel, end=mean_end)

    if hdr_y is None:
        averaged = False
        errors = False
        if hdr_x is not None:
            columns.remove(hdr_x)
        hdr_y = columns[0]
        if ylabel is None:
            lab_y = hdr_y.replace("_", " ")
        else:
            lab_y = ylabel
    if errors:
        hdr_e, _ = find_column(columns, end=std_end)

    grouped = dataframe.groupby(axis=axis, level=file_id_level)
    curve_dict = dict()

    if not averaged and journal is not None:
        journal_pages = journal.pages[
            [hdr_journal["group"], hdr_journal["sub_group"]]
        ].copy()
        journal_pages["g"] = 0
        journal_pages["sg"] = 0
        markers = itertools.cycle(["s", "o", "<", "*", "+", "x"])
        colors = itertools.cycle(hv.Cycle(cmap).values)

        j = journal_pages.groupby(hdr_journal["group"])
        for i, (jn, jg) in enumerate(j):
            journal_pages.loc[journal_pages["group"] == jn, "g"] = i
            journal_pages.loc[journal_pages["group"] == jn, "sg"] = list(range(len(jg)))

        markers = [next(markers) for _ in range(journal_pages["sg"].max() + 1)]
        colors = [next(colors) for _ in range(journal_pages["g"].max() + 1)]
        journal_pages = journal_pages[["g", "sg"]]

    for i, (name, group) in enumerate(grouped):
        group.columns = group.columns.droplevel(file_id_level)
        if hdr_x is None:
            group = group.reset_index()
            hdr_x = group.columns[0]

        if lab_x is None:
            lab_x = hdr_x.replace("_", " ")

        if not averaged and journal is not None:
            g = journal_pages.loc[name, "g"]
            sg = journal_pages.loc[name, "sg"]
            color = colors[g]
            marker = markers[sg]
            curve = hv.Curve(group, (hdr_x, lab_x), (hdr_y, lab_y)).opts(color=color)

        else:
            curve = hv.Curve(group, (hdr_x, lab_x), (hdr_y, lab_y))

        if points:
            if not averaged and journal is not None:

                scatter = hv.Scatter(curve).opts(color=color, marker=marker)

                if edges and extension == "matplotlib":
                    scatter = scatter.opts(edgecolor="k")

                if edges and extension == "bokeh":
                    scatter = scatter.opts(line_color="k", line_width=1)

                if marker_size is not None and extension == "bokeh":
                    scatter = scatter.opts(size=marker_size)
            else:
                scatter = hv.Scatter(curve)

                if marker_size is not None and extension == "bokeh":
                    scatter = scatter.opts(size=marker_size)

        if points and line:
            curve *= scatter

        elif points:
            curve = scatter

        if errors:
            if spread:
                curve *= hv.Spread(group, hdr_x, [hdr_y, hdr_e])
            else:
                curve *= hv.ErrorBars(
                    group, hdr_x, [hdr_y, hdr_e]
                )  # should get the color from curve and set it here
        curve_dict[name] = curve

    if extension == "matplotlib":
        overlay_opts = {
            "aspect": "auto",
            "fig_inches": (width * 0.016, height * 0.012),
            "show_frame": True,
        }
    else:
        overlay_opts = {
            "width": width,
            "height": height,
        }

    final_plot = hv.NdOverlay(curve_dict, kdims=legend_title).opts(
        **overlay_opts, **kwargs
    )
    if hover:
        if points:
            final_plot.opts(opts.Scatter(tools=["hover"]))
        else:
            final_plot.opts(opts.Curve(tools=["hover"]))
    return final_plot


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


def _raw_plot(raw_curve, title="Voltage versus time", **kwargs):

    tgt = raw_curve.relabel(title).opts(
        width=800,
        height=300,
        labelled=["y"],
        # tools=["pan","box_zoom", "reset"],
        active_tools=["pan"],
    )
    src = raw_curve.opts(width=800, height=100, yaxis=None, default_tools=[])

    RangeToolLink(src, tgt)

    layout = (tgt + src).cols(1)
    layout.opts(opts.Layout(shared_axes=False, merge_tools=False))
    return layout


def raw_plot(cell, y=("voltage", "Voltage (V vs Li/Li+)"), title=None, **kwargs):
    # TODO: missing doc-string

    if title is None:
        if isinstance(y, (list, tuple)):
            pre_title = str(y[0])
        else:
            pre_title = str(y)
        title = " ".join([pre_title, "versus", "time"])

    if not _hv_bokeh_available():
        return

    hv.extension("bokeh", logo=False)

    raw = cell.cell.raw
    raw["test_time_hrs"] = raw[hdr_raw["test_time_txt"]] / 3600
    x = ("test_time_hrs", "Time (hours)")
    raw_curve = hv.Curve(raw, x, y)
    layout = _raw_plot(raw_curve, title=title, **kwargs)
    return layout


def cycle_info_plot(
    cell,
    cycle=None,
    step=None,
    title=None,
    points=False,
    x=None,
    y=None,
    info_level=1,
    h_cycle=None,
    h_step=None,
    show_it=True,
    label_cycles=True,
    label_steps=False,
    get_axes=False,
    use_bokeh=True,
    **kwargs,
):
    """Show raw data together with step and cycle information.

    Args:
        cell: cellpy object
        cycle: cycles to select (optional, default is all)
        step: steps to select (optional, defaults is all)
        title: a title to give the plot
        points: overlay a scatter plot
        x (str): column header for the x-value (defaults to "Test_Time")
        y (str): column header for the y-value (defaults to "Voltage")
        info_level (int): how much information to display (defaults to 1)
            0 - almost nothing
            1 - pretty much
            2 - something else
            3 - not implemented yet
        h_cycle: column header for the cycle number (defaults to "Cycle_Index")
        h_step: column header for the step number (defaults to "Step_Index")
        show_it (bool): show the figure (defaults to True). If not, return the figure.
        label_cycles (bool): add labels with cycle numbers.
        label_steps (bool): add labels with step numbers
        get_axes (bool): return axes (for matplotlib)
        use_bokeh (bool): use bokeh to plot (defaults to True). If not, use matplotlib.
        **kwargs: parameters specific to either matplotlib or bokeh.

    Returns:

    """
    # TODO: missing doc-string
    if use_bokeh and not bokeh_available:
        print("OBS! bokeh is not available - using matplotlib instead")
        use_bokeh = False

    if use_bokeh:
        axes = _cycle_info_plot_bokeh(
            cell,
            cycle=cycle,
            step=step,
            title=title,
            points=points,
            x=x,
            y=y,
            info_level=info_level,
            h_cycle=h_cycle,
            h_step=h_step,
            show_it=show_it,
            label_cycles=label_cycles,
            label_steps=label_steps,
            **kwargs,
        )
    else:
        if isinstance(cycle, (list, tuple)):
            if len(cycle) > 1:
                print("OBS! The matplotlib-plotter only accepts single cycles.")
                print(f"Selecting first cycle ({cycle[0]})")
            cycle = cycle[0]
        axes = _cycle_info_plot_matplotlib(cell, cycle, get_axes)
    if get_axes:
        return axes


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


def _add_step_info_cols(df, table, cycles=None, steps=None, h_cycle=None, h_step=None):
    if h_cycle is None:
        h_cycle = "cycle_index"  # edit
    if h_step is None:
        h_step = "step_index"  # edit

    col_name_mapper = {"cycle": h_cycle, "step": h_step}

    df = df.merge(
        table.rename(columns=col_name_mapper),
        on=("cycle_index", "step_index"),
        how="left",
    )

    return df


def _cycle_info_plot_bokeh(
    cell,
    cycle=None,
    step=None,
    title=None,
    points=False,
    x=None,
    y=None,
    info_level=0,
    h_cycle=None,
    h_step=None,
    show_it=False,
    label_cycles=True,
    label_steps=False,
    **kwargs,
):
    """Plot raw data with annotations.

    This function uses Bokeh for plotting and is intended for use in
    Jupyter Notebooks.
    """
    # TODO: check that correct new column-names are used
    # TODO: fix bokeh import
    from bokeh.io import output_notebook, show
    from bokeh.layouts import row, column
    from bokeh.models import ColumnDataSource, LabelSet
    from bokeh.models import HoverTool
    from bokeh.models.annotations import Span
    from bokeh.models.widgets import Slider, TextInput
    from bokeh.plotting import figure

    output_notebook(hide_banner=True)

    if points:
        if cycle is None or (len(cycle) > 1):
            print("Plotting points only allowed when plotting one single cycle.")
            print("Turning points off.")
            points = False

    if h_cycle is None:
        h_cycle = "cycle_index"  # edit
    if h_step is None:
        h_step = "step_index"  # edit

    if x is None:
        x = "test_time"  # edit
    if y is None:
        y = "voltage"  # edit

    if isinstance(x, tuple):
        x, x_label = x
    else:
        x_label = x

    if isinstance(y, tuple):
        y, y_label = y
    else:
        y_label = y

    t_x = x  # used in generating title - replace with a selector
    t_y = y  # used in generating title - replace with a selector

    if title is None:
        title = f"{t_y} vs. {t_x}"

    cols = [x, y]
    cols.extend([h_cycle, h_step])

    df = cell.cell.raw.loc[:, cols]

    if cycle is not None:
        if not isinstance(cycle, (list, tuple)):
            cycle = [cycle]

        _df = df.loc[df[h_cycle].isin(cycle), :]
        if len(cycle) < 5:
            title += f" [c:{cycle}]"
        else:
            title += f" [c:{cycle[0]}..{cycle[-1]}]"
        if _df.empty:
            print(f"EMPTY (available cycles: {df[h_step].unique()})")
            return
        else:
            df = _df

    cycle = df[h_cycle].unique()

    if step is not None:
        if not isinstance(step, (list, tuple)):
            step = [step]

        _df = df.loc[df[h_step].isin(step), :]
        if len(step) < 5:
            title += f" (s:{step})"
        else:
            title += f" [s:{step[0]}..{step[-1]}]"
        if _df.empty:
            print(f"EMPTY (available steps: {df[h_step].unique()})")
            return
        else:
            df = _df

    x_min, x_max = df[x].min(), df[x].max()
    y_min, y_max = df[y].min(), df[y].max()

    if info_level > 0:
        table = cell.cell.steps
        df = _add_step_info_cols(df, table, cycle, step)

    source = ColumnDataSource(df)

    plot = figure(
        title=title,
        tools="pan,reset,save,wheel_zoom,box_zoom,undo,redo",
        x_range=[x_min, x_max],
        y_range=[y_min, y_max],
        **kwargs,
    )

    plot.line(x, y, source=source, line_width=3, line_alpha=0.6)

    # labelling cycles
    if label_cycles:
        cycle_line_positions = [df.loc[df[h_cycle] == c, x].min() for c in cycle]
        cycle_line_positions.append(df.loc[df[h_cycle] == cycle[-1], x].max())
        for m in cycle_line_positions:
            _s = Span(
                location=m,
                dimension="height",
                line_color="red",
                line_width=3,
                line_alpha=0.5,
            )
            plot.add_layout(_s)

        s_y_pos = y_min + 0.9 * (y_max - y_min)
        s_x = []
        s_y = []
        s_l = []

        for s in cycle:
            s_x_min = df.loc[df[h_cycle] == s, x].min()
            s_x_max = df.loc[df[h_cycle] == s, x].max()
            s_x_pos = (s_x_min + s_x_max) / 2
            s_x.append(s_x_pos)
            s_y.append(s_y_pos)
            s_l.append(f"c{s}")

        c_labels = ColumnDataSource(data={x: s_x, y: s_y, "names": s_l})

        c_labels = LabelSet(
            x=x,
            y=y,
            text="names",
            level="glyph",
            source=c_labels,
            render_mode="canvas",
            text_color="red",
            text_alpha=0.7,
        )

        plot.add_layout(c_labels)

        # labelling steps
    if label_steps:
        for c in cycle:
            step = df.loc[df[h_cycle] == c, h_step].unique()
            step_line_positions = [
                df.loc[(df[h_step] == s) & (df[h_cycle] == c), x].min()
                for s in step[0:]
            ]
            for m in step_line_positions:
                _s = Span(
                    location=m,
                    dimension="height",
                    line_color="olive",
                    line_width=3,
                    line_alpha=0.1,
                )
                plot.add_layout(_s)

            # s_y_pos = y_min + 0.8 * (y_max - y_min)
            s_x = []
            s_y = []
            s_l = []

            for s in step:
                s_x_min = df.loc[(df[h_step] == s) & (df[h_cycle] == c), x].min()
                s_x_max = df.loc[(df[h_step] == s) & (df[h_cycle] == c), x].max()
                s_x_pos = s_x_min

                s_y_min = df.loc[(df[h_step] == s) & (df[h_cycle] == c), y].min()
                s_y_max = df.loc[(df[h_step] == s) & (df[h_cycle] == c), y].max()
                s_y_pos = (s_y_max + s_y_min) / 2

                s_x.append(s_x_pos)
                s_y.append(s_y_pos)
                s_l.append(f"s{s}")

            s_labels = ColumnDataSource(data={x: s_x, y: s_y, "names": s_l})

            s_labels = LabelSet(
                x=x,
                y=y,
                text="names",
                level="glyph",
                source=s_labels,
                render_mode="canvas",
                text_color="olive",
                text_alpha=0.3,
            )

            plot.add_layout(s_labels)

    hover = HoverTool()
    if info_level == 0:
        hover.tooltips = [
            (x, "$x{0.2f}"),
            (y, "$y"),
            ("cycle", f"@{h_cycle}"),
            ("step", f"@{h_step}"),
        ]
    elif info_level == 1:
        # insert C-rates etc here
        hover.tooltips = [
            (f"(x,y)", "($x{0.2f} $y"),
            ("cycle", f"@{h_cycle}"),
            ("step", f"@{h_step}"),
            ("step_type", "@type"),
            ("rate", "@rate_avr{0.2f}"),
        ]

    elif info_level == 2:
        hover.tooltips = [
            (x, "$x{0.2f}"),
            (y, "$y"),
            ("cycle", f"@{h_cycle}"),
            ("step", f"@{h_step}"),
            ("step_type", "@type"),
            ("rate (C)", "@rate_avr{0.2f}"),
            ("dv (%)", "@voltage_delta{0.2f}"),
            ("I-max (A)", "@current_max"),
            ("I-min (A)", "@current_min"),
            ("dCharge (%)", "@charge_delta{0.2f}"),
            ("dDischarge (%)", "@discharge_delta{0.2f}"),
        ]

    hover.mode = "vline"
    plot.add_tools(hover)

    plot.xaxis.axis_label = x_label
    plot.yaxis.axis_label = y_label

    if points:
        plot.scatter(x, y, source=source, alpha=0.3)

    if show_it:
        show(plot)

    return plot


def _cycle_info_plot_matplotlib(cell, cycle, get_axes=False):

    # obs! hard-coded col-names. Please fix me.
    if not plt_available:
        print(
            "This function uses matplotlib. But I could not import it. "
            "So I decided to abort..."
        )
        return

    data = cell.cell.raw
    table = cell.cell.steps

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


def bplot(b, **kwargs):
    """plot batch summaries.

    This is wrapper around the two functions concatenate_summaries and plot_concatenated.

    >>> p1 = bplot(b, columns=["charge_capacity"], journal=b.experiment.journal, group_it=True)

    is equivalent to:

    >>> cs = helpers.concatenate_summaries(b, columns=["charge_capacity"], group_it=True)
    >>> p1 = plot_concatenated(cs, journal=journal)

    Args:
        b (cellpy.batch object): the batch with the cells.
        rate (float): filter on rate (C-rate)
        on (str or list of str): only select cycles if based on the rate of this step-type (e.g. on="charge").
        columns (list): selected column(s) (using cellpy name) [defaults to "charge_capacity"]
        column_names (list): selected column(s) (using exact column name)
        normalize_capacity_on (list): list of cycle numbers that will be used for setting the basis of the normalization
            (typically the first few cycles after formation)
        nom_cap (float): nominal capacity of the cell
        normalize_cycles (bool): perform a normalisation of the cycle numbers (also called equivalent cycle index)
        add_areal (bool):  add areal capacity to the summary
        group_it (bool): if True, average pr group.
        rate_std (float): allow for this inaccuracy when selecting cycles based on rate
        rate_column (str): name of the column containing the C-rates.
        inverse (bool): select steps that does not have the given C-rate.
        inverted (bool): select cycles that does not have the steps filtered by given C-rate.
        journal (batch.journal object): the journal (will use the journal in b if not given).
        spread (bool): use error-spread instead of error-bars.

    Returns:
        holoviews plot
    """
    journal = kwargs.pop("journal", b.experiment.journal)
    spread = kwargs.pop("spread", True)
    columns = kwargs.pop("columns", ["charge_capacity"])
    p = []
    for col in columns:
        cs = helpers.concatenate_summaries(b, columns=[col], **kwargs)
        p.append(plot_concatenated(cs, journal=journal, spread=spread))

    return hv.Layout(p).cols(1)


if __name__ == "__main__":
    pass
