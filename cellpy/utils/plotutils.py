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
    get_headers_normal, get_headers_step_table
)

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

logger = logging.getLogger(__name__)
logging.captureWarnings(True)

SYMBOL_DICT = {"all": ['s', 'o', 'v', '^', '<', '>', 'D', 'p', '*', '1', '2', '.', ',',
                       '3', '4', '8', 'p', 'd', 'h', 'H', '+', 'x', 'X', '|', '_'],
               "simple": ['s', 'o', 'v', '^', '<', '>', '*', 'd'],
               }

COLOR_DICT = {'classic': [u'b', u'g', u'r', u'c', u'm', u'y', u'k'],
              'grayscale': [u'0.00', u'0.40', u'0.60', u'0.70'],
              'bmh': [u'#348ABD', u'#A60628', u'#7A68A6', u'#467821', u'#D55E00', u'#CC79A7', u'#56B4E9',
                      u'#009E73', u'#F0E442', u'#0072B2'],
              'dark_background': [u'#8dd3c7', u'#feffb3', u'#bfbbd9', u'#fa8174', u'#81b1d2', u'#fdb462',
                                  u'#b3de69', u'#bc82bd', u'#ccebc4', u'#ffed6f'],
              'ggplot': [u'#E24A33', u'#348ABD', u'#988ED5', u'#777777', u'#FBC15E', u'#8EBA42', u'#FFB5B8'],
              'fivethirtyeight': [u'#30a2da', u'#fc4f30', u'#e5ae38', u'#6d904f', u'#8b8b8b'],
              'seaborn-colorblind': [u'#0072B2', u'#009E73', u'#D55E00', u'#CC79A7', u'#F0E442', u'#56B4E9'],
              'seaborn-deep': [u'#4C72B0', u'#55A868', u'#C44E52', u'#8172B2', u'#CCB974', u'#64B5CD'],
              'seaborn-bright': [u'#003FFF', u'#03ED3A', u'#E8000B', u'#8A2BE2', u'#FFC400', u'#00D7FF'],
              'seaborn-muted': [u'#4878CF', u'#6ACC65', u'#D65F5F', u'#B47CC7', u'#C4AD66', u'#77BEDB'],
              'seaborn-pastel': [u'#92C6FF', u'#97F0AA', u'#FF9F9A', u'#D0BBFF', u'#FFFEA3', u'#B0E0E6'],
              'seaborn-dark-palette': [u'#001C7F', u'#017517', u'#8C0900', u'#7600A1', u'#B8860B', u'#006374'],
              }

headers_summary = get_headers_summary()
headers_data = get_headers_normal()
headers_steps = get_headers_step_table()


def _hv_bokeh_available():
    if not hv_available:
        print("You need holoviews. But I cannot load it. Aborting...")
        return False
    if not bokeh_available:
        print("You need Bokeh. But I cannot find it. Aborting...")
        return False
    return True


def create_colormarkerlist_for_info_df(info_df, symbol_label="all", color_style_label="seaborn-colorblind"):
    logger.debug("symbol_label: " + symbol_label)
    logger.debug("color_style_label: " + color_style_label)
    groups = info_df.groups.unique()
    sub_groups = info_df.sub_groups.unique()
    return create_colormarkerlist(groups, sub_groups, symbol_label, color_style_label)


def create_colormarkerlist(groups, sub_groups, symbol_label="all", color_style_label="seaborn-colorblind"):
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
        width=800, height=300, labelled=['y'],
        #tools=["pan","box_zoom", "reset"],
        active_tools=['pan'],
    )
    src = raw_curve.opts(width=800, height=100, yaxis=None, default_tools=[])

    RangeToolLink(src, tgt)

    layout = (tgt + src).cols(1)
    layout.opts(opts.Layout(shared_axes=False, merge_tools=False))
    return layout


def raw_plot(cell, y=("Voltage", "Voltage (V vs Li/Li+)"), title=None,
             **kwargs):
    # TODO: missing doc-string

    if title is None:
        if isinstance(y, (list, tuple)):
            pre_title = str(y[0])
        else:
            pre_title = str(y)
        title = " ".join([pre_title, "versus", "time"])

    if not _hv_bokeh_available():
        return

    hv.extension('bokeh', logo=False)

    # obs! col-names hard-coded. fix me.
    raw = cell.dataset.dfdata
    raw["Test_Time_Hrs"] = raw["Test_Time"]/3600
    x = ("Test_Time_Hrs", "Time (hours)")
    raw_curve = hv.Curve(raw, x, y)
    layout = _raw_plot(raw_curve, title=title, **kwargs)
    return layout


def concatenated_summary_curve_factory(cdf, kdims="Cycle_Index",
                                       vdims="Charge_Capacity(mAh/g)",
                                       title="Summary Curves",
                                       fill_alpha=0.8, size=12,
                                       width=800, legend_position="right",
                                       colors=None, markers=None):
    # TODO: missing doc-string

    if not hv_available:
        print("This function uses holoviews. But could not import it."
              "So I am aborting...")
        return

    if colors is None:
        colors = hv.Cycle('Category10')

    if markers is None:
        markers = hv.Cycle(['circle', 'square', 'triangle', 'diamond'])

    groups = []
    curves_opts = []
    curves = {}

    for indx, new_df in cdf.groupby(level=0, axis=1):
        g = indx.split("_")[1]
        groups.append(g)

        n = hv.Scatter(
            data=new_df[indx], kdims=kdims, vdims=vdims, group=g, label=indx,
        ).opts(fill_alpha=fill_alpha, size=size)
        curves[indx] = n

    ugroups = set(groups)
    max_sub_group = max([groups.count(x) for x in ugroups])
    markers = markers[max_sub_group]

    colors = colors[len(ugroups)]
    for g, c in zip(ugroups, colors.values):
        curves_opts.append(opts.Scatter(g, color=c, marker=markers))

    curves_overlay = hv.NdOverlay(curves, kdims='cell id').opts(
        opts.NdOverlay(width=800, legend_position=legend_position, title=title),
        *curves_opts
    )

    return curves_overlay


def _plot_step(ax, x, y, color):
    ax.plot(x, y, color=color, linewidth=3)


def _get_info(table, cycle, step):
    # obs! hard-coded col-names. Please fix me.
    m_table = (table.cycle==cycle) & (table.step==step)
    p1, p2 = table.loc[m_table, ['point_min', 'point_max']].values[0]
    c1, c2 = table.loc[m_table, ['current_min', 'current_max']].abs().values[0]
    d_voltage, d_current  = table.loc[m_table, ['voltage_delta', 'current_delta']].values[0]
    d_discharge, d_charge  = table.loc[m_table, ['discharge_delta', 'charge_delta']].values[0]
    current_max = (c1 + c2)/2
    rate = table.loc[m_table, "rate_avr"].values[0]
    step_type = table.loc[m_table, 'type'].values[0]
    return [step_type, rate, current_max, d_voltage, d_current, d_discharge, d_charge]


def _add_step_info_cols(df, table, cycles=None, steps=None, h_cycle=None,
                        h_step=None):
    if h_cycle is None:
        h_cycle = "Cycle_Index"  # edit
    if h_step is None:
        h_step = "Step_Index"  # edit

    col_name_mapper = {
        "cycle": h_cycle,
        "step": h_step,
    }

    df = df.merge(
        table.rename(columns=col_name_mapper),
        on=('Cycle_Index', 'Step_Index'),
        how='left'
    )

    return df


def _cycle_info_plot_bokeh(cell, cycle=None, step=None, title=None, points=False, x=None,
                           y=None,
                           info_level=0,
                           h_cycle=None, h_step=None,
                           show_it=False, label_cycles=True, label_steps=False, **kwargs):
    """Plot raw data with annotations.

    This function uses Bokeh for plotting and is intended for use in
    Jupyter Notebooks.
    """

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
            print(
                "Plotting points only allowed when plotting one single cycle.")
            print("Turning points off.")
            points = False

    if h_cycle is None:
        h_cycle = "Cycle_Index"  # edit
    if h_step is None:
        h_step = "Step_Index"  # edit

    if x is None:
        x = "Test_Time"  # edit
    if y is None:
        y = "Voltage"  # edit

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

    df = cell.dataset.dfdata.loc[:, cols]

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
        table = cell.dataset.step_table
        df = _add_step_info_cols(df, table, cycle, step)

    source = ColumnDataSource(df)

    plot = figure(
        title=title,
        tools="pan,reset,save,wheel_zoom,box_zoom,undo,redo",
        x_range=[x_min, x_max], y_range=[y_min, y_max],
        **kwargs,
    )

    plot.line(
        x, y, source=source,
        line_width=3, line_alpha=0.6
    )

    # labelling cycles
    if label_cycles:
        cycle_line_positions = [df.loc[df[h_cycle] == c, x].min() for c in
                                cycle]
        cycle_line_positions.append(df.loc[df[h_cycle] == cycle[-1], x].max())
        for m in cycle_line_positions:
            _s = Span(location=m, dimension='height', line_color="red",
                      line_width=3,
                      line_alpha=0.5)
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

        c_labels = ColumnDataSource(data={
            x: s_x,
            y: s_y,
            'names': s_l

        })

        c_labels = LabelSet(x=x, y=y, text='names', level='glyph',
                            source=c_labels, render_mode='canvas',
                            text_color="red", text_alpha=0.7)

        plot.add_layout(c_labels)

        # labelling steps
    if label_steps:
        for c in cycle:
            step = df.loc[df[h_cycle] == c, h_step].unique()
            step_line_positions = [
                df.loc[(df[h_step] == s) & (df[h_cycle] == c), x].min() for s in
                step[0:]]
            for m in step_line_positions:
                _s = Span(location=m, dimension='height', line_color="olive",
                          line_width=3,
                          line_alpha=0.1)
                plot.add_layout(_s)

            # s_y_pos = y_min + 0.8 * (y_max - y_min)
            s_x = []
            s_y = []
            s_l = []

            for s in step:
                s_x_min = df.loc[
                    (df[h_step] == s) & (df[h_cycle] == c), x].min()
                s_x_max = df.loc[
                    (df[h_step] == s) & (df[h_cycle] == c), x].max()
                s_x_pos = s_x_min

                s_y_min = df.loc[
                    (df[h_step] == s) & (df[h_cycle] == c), y].min()
                s_y_max = df.loc[
                    (df[h_step] == s) & (df[h_cycle] == c), y].max()
                s_y_pos = (s_y_max + s_y_min) / 2

                s_x.append(s_x_pos)
                s_y.append(s_y_pos)
                s_l.append(f"s{s}")

            s_labels = ColumnDataSource(data={
                x: s_x,
                y: s_y,
                'names': s_l

            })

            s_labels = LabelSet(x=x, y=y, text='names', level='glyph',
                                source=s_labels, render_mode='canvas',
                                text_color="olive", text_alpha=0.3)

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
            ("rate", "@rate_avr{0.2f}")
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

    hover.mode = 'vline'
    plot.add_tools(hover)

    plot.xaxis.axis_label = x_label
    plot.yaxis.axis_label = y_label

    if points:
        plot.scatter(
            x, y, source=source,
            alpha=0.3
        )

    if show_it:
        show(plot)

    return plot


def _cycle_info_plot_matplotlib(cell, cycle, get_axes=False):

    # obs! hard-coded col-names. Please fix me.
    if not plt_available:
        print("This function uses matplotlib. But I could not import it. "
              "So I decided to abort...")
        return

    data = cell.dataset.dfdata
    table = cell.dataset.step_table

    span_colors = [
        "#4682B4",
        "#FFA07A"
    ]

    voltage_color = "#008B8B"
    current_color = "#CD5C5C"

    m_cycle_data = (data.Cycle_Index == cycle)
    all_steps = data[m_cycle_data]["Step_Index"].unique()

    color = itertools.cycle(span_colors)

    fig = plt.figure(figsize=(20, 8))
    fig.suptitle(f"Cycle: {cycle}")

    ax3 = plt.subplot2grid((8, 3), (0, 0), colspan=3, rowspan=1,
                           fig=fig)  # steps
    ax4 = plt.subplot2grid((8, 3), (1, 0), colspan=3, rowspan=2,
                           fig=fig)  # rate
    ax1 = plt.subplot2grid((8, 3), (3, 0), colspan=3, rowspan=5,
                           fig=fig)  # data

    ax2 = ax1.twinx()
    ax1.set_xlabel("time (minutes)")
    ax1.set_ylabel("voltage (V vs. Li/Li+)", color=voltage_color)
    ax2.set_ylabel("current (mA)", color=current_color)

    annotations_1 = []  # step number (IR)
    annotations_2 = []  # step number
    annotations_4 = []  # rate

    for i, s in enumerate(all_steps):
        m = m_cycle_data & (data.Step_Index == s)
        c = data.loc[m, "Current"] * 1000
        v = data.loc[m, "Voltage"]
        t = data.loc[m, "Test_Time"] / 60
        step_type, rate, current_max, dv, dc, d_discharge, d_charge = _get_info(
            table, cycle, s)
        if len(t) > 1:
            fcolor = next(color)

            info_txt = f"{step_type}\nc-rate = {rate}\ni = |{1000 * current_max:0.2f}| mA\n"
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
        ax3.annotate(f"{s[0]}", (s[1], 0.2), ha='center')

    for s in annotations_2:
        ax3.annotate(f"{s[0]}", (s[1], 0.6), ha='center')

    for s in annotations_4:
        ax4.annotate(f"{s[0]}", (s[1], 0.0), ha='center')

    for ax in [ax3, ax4]:
        ax.axes.get_yaxis().set_visible(False)
        ax.axes.get_xaxis().set_visible(False)

    if get_axes:
        return ax1, ax2, ax2, ax4


def cycle_info_plot(cell, cycle=None,
                    step=None, title=None,
                    points=False, x=None,y=None, info_level=0, h_cycle=None,
                    h_step=None, show_it=False, label_cycles=True,
                    label_steps=False,
                    get_axes=False, use_bokeh=True,
                    **kwargs):
    # TODO: missing doc-string
    if use_bokeh and not bokeh_available:
        print("OBS! bokeh is not available -"
              " using matplotlib instead")
        use_bokeh = False

    if use_bokeh:
        axes = _cycle_info_plot_bokeh(
            cell, cycle=cycle, step=step, title=title,
            points=points, x=x, y=y, info_level=info_level,
            h_cycle=h_cycle,
            h_step=h_step,
            show_it=show_it, label_cycles=label_cycles,
            label_steps=label_steps, **kwargs,
        )
    else:
        if isinstance(cycle, (list, tuple)):
            if len(cycle) > 1:
                print("OBS! The matplotlib-plotter only accepts single "
                      "cycles.")
                print(f"Selecting first cycle ({cycle[0]})")
            cycle = cycle[0]
        axes = _cycle_info_plot_matplotlib(cell, cycle, get_axes)
    if get_axes:
        return axes


if __name__ == "__main__":
    pass
