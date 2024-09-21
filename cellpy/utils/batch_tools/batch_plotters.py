import functools
import importlib
import itertools
import logging
import sys
import warnings
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from cellpy import prms
from cellpy.exceptions import UnderDefined
from cellpy.parameters.internal_settings import get_headers_journal, get_headers_summary
from cellpy.utils.batch_tools.batch_core import BasePlotter
from cellpy.utils.batch_tools.batch_experiments import CyclingExperiment


plotly_available = importlib.util.find_spec("plotly") is not None
bokeh_available = importlib.util.find_spec("bokeh") is not None
seaborn_available = importlib.util.find_spec("seaborn") is not None

available_plotting_backends = ["matplotlib"]

if bokeh_available:
    available_plotting_backends.append("bokeh")
    import bokeh

if plotly_available:
    import plotly.express as px
    import plotly
    import plotly.io as pio
    import plotly.graph_objects as go

    available_plotting_backends.append("plotly")

if seaborn_available:
    import seaborn as sns

    available_plotting_backends.append("seaborn")

hdr_journal = get_headers_journal()
hdr_summary = get_headers_summary()


def create_legend(info, c, option="clean", use_index=False):
    """creating more informative legends"""

    logging.debug("    - creating legends")
    mass, loading, label = info.loc[
        c, [hdr_journal["mass"], hdr_journal["loading"], hdr_journal["label"]]
    ]

    if use_index or not label:
        label = c.split("_")
        label = "_".join(label[1:])

    if option == "clean":
        logging.debug(f"label: {label}")
        return label

    if option == "mass":
        label = f"{label} ({mass:.2f} mg)"
    elif option == "loading":
        label = f"{label} ({loading:.2f} mg/cm2)"
    elif option == "all":
        label = f"{label} ({mass:.2f} mg) ({loading:.2f} mg/cm2)"
    logging.debug(f"advanced label: {label}")
    return label


def look_up_group(info, c):
    logging.debug("    - looking up groups")
    g, sg = info.loc[c, [hdr_journal["group"], hdr_journal["sub_group"]]]
    return int(g), int(sg)


def create_plot_option_dicts(
    info, marker_types=None, colors=None, line_dash=None, size=None, palette=None
):
    """Create two dictionaries with plot-options.

    The first iterates colors (based on group-number), the second iterates
    through marker types.

    Returns: group_styles (dict), sub_group_styles (dict)
    """

    logging.debug("    - creating plot-options-dict (for bokeh)")
    if palette is None:
        try:
            # palette = bokeh.palettes.brewer['YlGnBu']
            palette = bokeh.palettes.d3["Category20"]
            # palette = bokeh.palettes.brewer[prms.Batch.bokeh_palette']
        except (NameError, AttributeError) as e:
            logging.info(f"could not create the palette {e}")
            palette = {
                1: ["k"],
                3: ["k", "r"],
                4: ["k", "r", "b"],
                5: ["k", "r", "b", "g"],
                6: ["k", "r", "b", "g", "c"],
                7: ["k", "r", "b", "g", "c", "m"],
                8: ["k", "r", "b", "g", "c", "m", "y"],
            }

    max_palette_row = max(palette.keys())
    if marker_types is None:
        marker_types = [
            "circle",
            "square",
            "triangle",
            "inverted_triangle",
            "diamond",
            "asterisk",
            "cross",
        ]

    if line_dash is None:
        line_dash = [0, 0]

    if size is None:
        size = 10

    groups = info[hdr_journal.group].unique()
    number_of_groups = len(groups)
    if colors is None:
        if number_of_groups < 4:
            colors = palette[3]

        else:
            colors = palette[min(max_palette_row, number_of_groups)]

    sub_groups = info[hdr_journal.sub_group].unique()
    marker_it = itertools.cycle(marker_types)
    colors_it = itertools.cycle(colors)

    group_styles = dict()
    sub_group_styles = dict()

    for j in groups:
        color = next(colors_it)
        marker_options = {"line_color": color, "fill_color": color}

        line_options = {"line_color": color}
        group_styles[j] = {"marker": marker_options, "line": line_options}

    for j in sub_groups:
        marker_type = next(marker_it)
        marker_options = {"marker": marker_type, "size": size}

        line_options = {"line_dash": line_dash}
        sub_group_styles[j] = {"marker": marker_options, "line": line_options}
    return group_styles, sub_group_styles


def create_summary_plot_bokeh(
    data,
    info,
    group_styles,
    sub_group_styles,
    label=None,
    title="Capacity",
    x_axis_label="Cycle number",
    y_axis_label="Capacity (mAh/g)",
    width=900,
    height=400,
    legend_option="clean",
    legend_location="bottom_right",
    x_range=None,
    y_range=None,
    tools=None,
):
    # TODO: include max cycle (bokeh struggles when there is to much to plot)
    #   could also consider interpolating
    #   or defaulting to datashader for large files.

    warnings.warn(
        "This utility function is not maintained anymore.",
        category=DeprecationWarning,
    )

    if "bokeh" not in available_plotting_backends:
        raise ImportError("bokeh not available")

    if tools is None:
        tools = "pan,box_zoom,reset,save"

    logging.debug(f"    - creating summary (bokeh) plot for {label}")
    discharge_capacity = None
    if isinstance(data, (list, tuple)):
        charge_capacity = data[0]
        if len(data) == 2:
            discharge_capacity = data[1]
    else:
        charge_capacity = data

    figure_kwargs = dict(
        title=title,
        width=width,
        height=height,
        tools=tools,
        x_axis_label=x_axis_label,
        y_axis_label=y_axis_label,
    )
    if x_range is not None:
        figure_kwargs["x_range"] = x_range
    if y_range is not None:
        figure_kwargs["y_range"] = y_range

    p = bokeh.plotting.figure(**figure_kwargs)

    sub_cols_charge = None
    sub_cols_discharge = None
    legend_collection = []
    if isinstance(charge_capacity.columns, pd.MultiIndex):
        cols = charge_capacity.columns.get_level_values(1)
        sub_cols_charge = charge_capacity.columns.get_level_values(0).unique()

        charge_capacity.columns = [
            f"{col[0]}_{col[1]}" for col in charge_capacity.columns.values
        ]

        if discharge_capacity is not None:
            sub_cols_discharge = discharge_capacity.columns.get_level_values(0).unique()
            discharge_capacity.columns = [
                f"{col[0]}_{col[1]}" for col in discharge_capacity.columns.values
            ]
    else:
        cols = charge_capacity.columns
    logging.debug("iterate cols")
    for cc in cols:
        g, sg = look_up_group(info, cc)
        legend_items = []
        l = create_legend(info, cc, option=legend_option)
        group_props = group_styles[g]
        sub_group_props = sub_group_styles[sg]
        logging.debug(f"subgroups {sub_group_props}")

        if sub_cols_charge is not None:
            c = f"{sub_cols_charge[0]}_{cc}"
            r = f"{sub_cols_charge[1]}_{cc}"

            if c not in charge_capacity.columns:
                charge_capacity[c] = np.nan
            if r not in charge_capacity.columns:
                charge_capacity[r] = np.nan
            selector = [c, r]
            charge_capacity_sub = charge_capacity.loc[:, selector]

            charge_capacity_sub.columns = [c, "rate"]
            charge_source = bokeh.models.ColumnDataSource(charge_capacity_sub)

        else:
            c = cc
            if c not in charge_capacity.columns:
                charge_capacity[c] = np.nan
            charge_capacity_sub = charge_capacity.loc[:, [c]]
            charge_source = bokeh.models.ColumnDataSource(charge_capacity_sub)
        logging.debug(f"starting creating scatter")
        ch_m = p.scatter(
            source=charge_source,
            x=hdr_summary.cycle_index,
            y=c,
            # **legend_option_dict,
            #  Remark! cannot use the same legend name as
            #  column name (defaults to a lookup)
            **group_props["marker"],  # color
            **sub_group_props["marker"],  # marker
        )
        logging.debug(f"starting creating line")
        ch_l = p.line(
            source=charge_source,
            x=hdr_summary.cycle_index,
            y=c,
            **group_props["line"],
            **sub_group_props["line"],
        )

        legend_items.extend([ch_m, ch_l])
        logging.debug(f"fixing discharge cap")
        if discharge_capacity is not None:
            # creating a local copy so that I can do local changes
            group_props_marker_charge = group_props["marker"].copy()
            group_props_marker_charge["fill_color"] = None

            if sub_cols_discharge is not None:
                c = f"{sub_cols_discharge[0]}_{cc}"
                r = f"{sub_cols_discharge[1]}_{cc}"
                if c not in charge_capacity.columns:
                    charge_capacity[c] = np.nan
                if r not in charge_capacity.columns:
                    charge_capacity[r] = np.nan
                discharge_capacity_sub = discharge_capacity.loc[:, [c, r]]
                discharge_capacity_sub.columns = [c, "rate"]
                discharge_source = bokeh.models.ColumnDataSource(discharge_capacity_sub)

            else:
                c = cc
                if c not in charge_capacity.columns:
                    charge_capacity[c] = np.nan
                discharge_capacity_sub = discharge_capacity.loc[:, [c]]
                discharge_source = bokeh.models.ColumnDataSource(discharge_capacity_sub)

            dch_m = p.scatter(
                source=discharge_source,
                x=hdr_summary.cycle_index,
                y=c,
                **group_props_marker_charge,
                **sub_group_props["marker"],
            )

            dch_l = p.line(
                source=discharge_source,
                x=hdr_summary.cycle_index,
                y=c,
                **group_props["line"],
                **sub_group_props["line"],
            )

            legend_items.extend([dch_m, dch_l])
        legend_collection.append((l, legend_items))
    logging.debug("exiting summary plotter")
    return p, legend_collection


def plot_cycle_life_summary_bokeh(
    info,
    summaries,
    width=900,
    height=800,
    height_fractions=None,
    legend_option="all",
    add_rate=True,
    **kwargs,
):
    if "bokeh" not in available_plotting_backends:
        raise ImportError("bokeh not available")

    if height_fractions is None:
        height_fractions = [0.3, 0.4, 0.3]
    logging.debug(f"   * stacking and plotting")
    logging.debug(f"      backend: {prms.Batch.backend}")
    logging.debug(f"      received kwargs: {kwargs}")

    idx = pd.IndexSlice
    all_legend_items = []

    warnings.warn(
        "This utility function might be removed shortly", category=DeprecationWarning
    )
    if add_rate:
        try:
            discharge_capacity = summaries.loc[
                :,
                idx[
                    [
                        hdr_summary["discharge_capacity_gravimetric"],
                        hdr_summary["discharge_c_rate"],
                    ],
                    :,
                ],
            ]
        except AttributeError:
            warnings.warn(
                "No discharge rate columns available - consider re-creating summary!"
            )
            discharge_capacity = summaries[
                hdr_summary["discharge_capacity_gravimetric"]
            ]

        try:
            charge_capacity = summaries.loc[
                :,
                idx[
                    [
                        hdr_summary["charge_capacity_gravimetric"],
                        hdr_summary["charge_c_rate"],
                    ],
                    :,
                ],
            ]
        except AttributeError:
            warnings.warn(
                "No charge rate columns available - consider re-creating summary!"
            )
            charge_capacity = summaries[hdr_summary["charge_capacity_gravimetric"]]

        try:
            coulombic_efficiency = summaries.loc[
                :, idx[[hdr_summary.coulombic_efficiency, hdr_summary.charge_c_rate], :]
            ]
        except AttributeError:
            warnings.warn(
                "No charge rate columns available - consider re-creating summary!"
            )
            coulombic_efficiency = summaries.coulombic_efficiency

        if hdr_summary.ir_charge in summaries.columns:
            try:
                ir_charge = summaries.loc[
                    :, idx[[hdr_summary.ir_charge, hdr_summary.charge_c_rate], :]
                ]
            except AttributeError:
                warnings.warn(
                    "No charge rate columns available - consider re-creating summary!"
                )
                ir_charge = summaries.ir_charge
        else:
            ir_charge = pd.DataFrame()
    else:
        discharge_capacity = summaries[hdr_summary["discharge_capacity_gravimetric"]]
        charge_capacity = summaries[hdr_summary["charge_capacity_gravimetric"]]
        coulombic_efficiency = summaries[hdr_summary["coulombic_efficiency"]]
        ir_charge = summaries[hdr_summary["ir_charge"]]

    h_eff = int(height_fractions[0] * height)
    h_cap = int(height_fractions[1] * height)
    h_ir = int(height_fractions[2] * height)
    group_styles, sub_group_styles = create_plot_option_dicts(info)

    p_eff, legends_eff = create_summary_plot_bokeh(
        coulombic_efficiency,
        info,
        group_styles,
        sub_group_styles,
        label="c.e.",
        legend_option=legend_option,
        title="",
        x_axis_label="",
        y_axis_label="Coulombic efficiency (%)",
        width=width,
        height=h_eff,
    )

    all_legend_items.extend(legends_eff)

    if not ir_charge.empty:
        cap_x_axis = None
    else:
        cap_x_axis = "Cycle number"
    p_cap, legends_cap = create_summary_plot_bokeh(
        (charge_capacity, discharge_capacity),
        info,
        group_styles,
        sub_group_styles,
        legend_option=legend_option,
        label="charge and discharge cap.",
        title="",
        x_axis_label=cap_x_axis,
        height=h_cap,
        width=width,
        x_range=p_eff.x_range,
    )
    all_legend_items.extend(legends_cap)
    if not ir_charge.empty:
        p_ir, legends_ir = create_summary_plot_bokeh(
            ir_charge,
            info,
            group_styles,
            sub_group_styles,
            label="ir charge",
            legend_option=legend_option,
            title="",
            x_axis_label="Cycle number",
            y_axis_label="IR Charge (Ohm)",
            width=width,
            height=h_ir,
            x_range=p_eff.x_range,
        )

        all_legend_items.extend(legends_ir)

    p_eff.y_range.start, p_eff.y_range.end = 20, 120
    p_eff.xaxis.visible = False
    if not ir_charge.empty:
        p_cap.xaxis.visible = False

    tooltips = [("cycle", f"@{hdr_summary.cycle_index}"), ("value", "$y{0.}")]
    if add_rate:
        tooltips.append(("rate", "@rate{0.000}"))

    hover = bokeh.models.HoverTool(tooltips=tooltips)

    p_eff.add_tools(hover)
    p_cap.add_tools(hover)
    if not ir_charge.empty:
        p_ir.add_tools(hover)

    renderer_list = p_eff.renderers + p_cap.renderers
    if not ir_charge.empty:
        renderer_list += p_ir.renderers

    legend_items_dict = defaultdict(list)
    for label, r in all_legend_items:
        legend_items_dict[label].extend(r)

    legend_items = []
    renderer_list = []
    for legend in legend_items_dict:
        legend_items.append(
            bokeh.models.LegendItem(label=legend, renderers=legend_items_dict[legend])
        )
        renderer_list.extend(legend_items_dict[legend])

    legend_title = "Legends"

    legend_figure_kwargs = dict(
        outline_line_alpha=0,
        toolbar_location=None,
        width_policy="min",
        min_width=300,
        title=legend_title,
    )

    frame_width = 350

    if bokeh.__version__.split(".") >= ["3", "0", "0"]:
        legend_figure_kwargs["frame_width"] = frame_width
        legend_figure_kwargs["frame_height"] = height
        # legend_figure_kwargs["sizing_mode"] = "stretch_width"

    else:
        legend_figure_kwargs["plot_width"] = frame_width
        legend_figure_kwargs["plot_height"] = height
        # legend_figure_kwargs["sizing_mode"] = "scale_width"

    dummy_figure_for_legend = bokeh.plotting.figure(**legend_figure_kwargs)

    # set the components of the figure invisible
    for fig_component in [
        dummy_figure_for_legend.grid[0],
        dummy_figure_for_legend.ygrid[0],
        dummy_figure_for_legend.xaxis[0],
        dummy_figure_for_legend.yaxis[0],
    ]:
        fig_component.visible = False

    dummy_figure_for_legend.renderers += renderer_list

    # set the figure range outside the range of all
    # glyphs (assuming that negative cycle numbers never happen)
    dummy_figure_for_legend.x_range.start, dummy_figure_for_legend.x_range.end = (
        -10,
        -9,
    )
    dummy_figure_for_legend.add_layout(
        bokeh.models.Legend(
            click_policy="hide",
            location="top_left",
            border_line_alpha=0,
            items=legend_items,
        )
    )
    dummy_figure_for_legend.title.align = "center"

    grid_layout = [p_eff, p_cap]
    if not ir_charge.empty:
        grid_layout.append(p_ir)
    fig_grid = bokeh.layouts.gridplot(grid_layout, ncols=1, sizing_mode="stretch_width")

    info_text = "(filled:charge) (open:discharge)"
    if not ir_charge.empty:
        p_ir.add_layout(bokeh.models.Title(text=info_text, align="right"), "below")
    else:
        p_cap.add_layout(bokeh.models.Title(text=info_text, align="right"), "below")

    final_figure = bokeh.layouts.row(
        children=[fig_grid, dummy_figure_for_legend], sizing_mode="stretch_width"
    )
    return bokeh.plotting.show(final_figure)


def plot_cycle_life_summary_matplotlib(
    info,
    summaries,
    width=900,
    height=800,
    height_fractions=None,
    legend_option="all",
    **kwargs,
):
    warnings.warn(
        "This utility function is not maintained anymore",
        category=DeprecationWarning,
    )

    logging.debug(f"   * stacking and plotting")
    logging.debug(f"      backend: {prms.Batch.backend}")
    logging.debug(f"      received kwargs: {kwargs}")

    # Not used (yet?) - requires a more advanced generation of sub-plots
    if height_fractions is None:
        height_fractions = [0.3, 0.4, 0.3]

    # print(" running matplotlib plotter ".center(80,"="))
    # convert from bokeh to matplotlib - figsize - inch-ish
    width /= 80
    height /= 120
    discharge_capacity = summaries[hdr_summary["discharge_capacity_gravimetric"]]
    charge_capacity = summaries[hdr_summary["charge_capacity_gravimetric"]]
    coulombic_efficiency = summaries.coulombic_efficiency
    try:
        ir_charge = summaries.ir_charge
    except AttributeError:
        logging.debug("the data is missing ir charge")
        ir_charge = None

    plt.rcParams["figure.figsize"] = (10, 10)
    marker_types = [
        "o",
        "s",
        "v",
        "^",
        "<",
        ">",
        "8",
        "p",
        "P",
        "*",
        "h",
        "H",
        "+",
        "x",
        "X",
        "D",
        "d",
        ".",
        ",",
    ]

    marker_size = kwargs.pop("marker_size", None)
    group_styles, sub_group_styles = create_plot_option_dicts(
        info, marker_types=marker_types, size=marker_size
    )
    if ir_charge is None:
        canvas, (ax_ce, ax_cap) = plt.subplots(
            2,
            1,
            figsize=(width, height),
            sharex=True,
            gridspec_kw={"height_ratios": height_fractions[:-1]},
        )
    else:
        canvas, (ax_ce, ax_cap, ax_ir) = plt.subplots(
            3,
            1,
            figsize=(width, height),
            sharex=True,
            gridspec_kw={"height_ratios": height_fractions},
        )
    for label in charge_capacity.columns.get_level_values(0):
        name = create_legend(info, label, option=legend_option)
        g, sg = look_up_group(info, label)

        group_style = group_styles[g]
        sub_group_style = sub_group_styles[sg]

        marker = sub_group_style["marker"]
        line = group_style["line"]

        c = line["line_color"]
        m = marker["marker"]
        f = "white"

        try:
            ax_cap.plot(
                charge_capacity[label], label=name, color=c, marker=m, markerfacecolor=c
            )
        except Exception as e:
            logging.debug(f"Could not plot charge capacity for {label} ({e})")
        try:
            ax_cap.plot(
                discharge_capacity[label],
                label=name,
                color=c,
                marker=m,
                markerfacecolor=f,
            )
        except Exception as e:
            logging.debug(f"Could not plot discharge capacity for {label} ({e})")

        ax_ce.plot(
            coulombic_efficiency[label],
            label=name,
            color=c,
            marker=m,
            markerfacecolor=c,
        )

        if ir_charge is not None:
            try:
                ax_ir.plot(
                    ir_charge[label], color=c, label=name, marker=m, markerfacecolor=c
                )
            except Exception as e:
                logging.debug(f"Could not plot IR for {label} ({e})")

    ax_all = [ax_cap, ax_ce]
    ax_ce.set_ylabel("Coulombic\nEfficiency (%)")
    ax_ce.set_ylim((0, 110))
    ax_cap.set_ylabel("Capacity\n(mAh/g)")

    if ir_charge is not None:
        ax_ir.set_ylabel("IR\n(charge)")
        ax_ir.set_xlabel("Cycle")
        ax_all.append(ax_ir)
    else:
        ax_cap.set_xlabel("Cycle")

    for ax in ax_all:
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.6, box.height])

    # Put a legend to the right of the current axis
    legend = ax_cap.legend(loc="center left", bbox_to_anchor=(1, 0.5))
    legend.get_frame().set_facecolor("none")
    legend.get_frame().set_linewidth(0.0)

    return canvas


def summary_plotting_engine(**kwargs):
    """creates plots of summary data."""
    experiments = kwargs.pop("experiments")
    farms = kwargs.pop("farms")
    barn = None
    backend = prms.Batch.backend
    logging.debug(f"Using {prms.Batch.backend} for plotting summaries")
    if backend not in available_plotting_backends:
        warnings.warn(f"The back-end {backend} is not available.")
        warnings.warn(f"Available back-ends are: {available_plotting_backends}")
        warnings.warn("Consider installing the missing back-end.")
        return farms, barn

    if backend in ["bokeh", "matplotlib"]:
        farms = _preparing_data_and_plotting_legacy(
            experiments=experiments, farms=farms, **kwargs
        )

    elif backend in ["plotly", "seaborn"]:
        for experiment in experiments:
            if not isinstance(experiment, CyclingExperiment):
                logging.debug(f"skipping {experiment} - not a CyclingExperiment")
                logging.debug(f"({type(experiment)})")
                continue
            canvas = generate_summary_plots(
                experiment=experiment, farms=farms, **kwargs
            )
            farms.append(canvas)
            if backend == "plotly":
                canvas.show()

    return farms, barn


def generate_summary_plots(experiment, **kwargs):
    pages = experiment.journal.pages
    backend = prms.Batch.backend
    plotters = {
        "plotly": plot_cycle_life_summary_plotly,
        "seaborn": plot_cycle_life_summary_seaborn,
    }
    try:
        summaries = generate_summary_frame_for_plotting(pages, experiment)
    except KeyError as e:
        logging.info(f"could not process the summaries ({e})")
        return

    try:
        canvas = plotters[backend](summaries, **kwargs)
    except Exception as e:
        logging.info(f"could not generate summary plots ({e})")
        return

    return canvas


def generate_summary_frame_for_plotting(pages, experiment, **kwargs):
    trim_pages = kwargs.pop("trim_pages", False)
    keys = [df.name for df in experiment.memory_dumped["summary_engine"]]
    summaries = pd.concat(experiment.memory_dumped["summary_engine"], keys=keys, axis=1)
    summaries = summaries.reset_index()
    summaries.columns.names = ["variable", "cell"]

    hdr_cycle = hdr_summary["cycle_index"]
    hdr_charge = hdr_summary["charge_capacity_gravimetric"]
    hdr_discharge = hdr_summary["discharge_capacity_gravimetric"]
    hdr_ce = hdr_summary["coulombic_efficiency"]
    hdr_ir_charge = hdr_summary["ir_charge"]
    hdr_ir_discharge = hdr_summary["ir_discharge"]
    hdr_charge_rate = hdr_summary["charge_c_rate"]
    hdr_discharge_rate = hdr_summary["discharge_c_rate"]

    _required_summaries = [hdr_cycle, hdr_ce, hdr_charge, hdr_discharge]
    _optional_summaries = [
        hdr_ir_charge,
        hdr_ir_discharge,
        hdr_charge_rate,
        hdr_discharge_rate,
    ]
    for _optional_summary in _optional_summaries:
        if _optional_summary in summaries.columns:
            _required_summaries.append(_optional_summary)
    summaries = summaries.loc[:, _required_summaries]
    id_var = summaries.columns[0]
    summaries = summaries.melt(
        id_vars=[id_var],
        # prior to pandas 2.2.0, the following line was used
        #   id_vars=[hdr_cycle],
    )

    # due to pandas 2.2.0 change, the following line is needed:
    summaries = summaries.rename(columns={id_var: hdr_cycle})
    pages = pages.copy()
    pages.index.name = "cell"
    pages = pages.reset_index()

    if trim_pages:
        try:
            pages = pages.loc[
                :,
                [
                    "cell",
                    "mass",
                    "total_mass",
                    "loading",
                    "nom_cap",
                    "area",
                    "label",
                    "cell_type",
                    "instrument",
                    "group",
                    "sub_group",
                ],
            ]
        except KeyError as e:
            logging.debug(f"could not trim pages ({e})")
    try:
        summaries = summaries.merge(pages, on="cell")
    except Exception as e:
        logging.debug(f"could not merge summaries and pages ({e})")
    return summaries


# plotly helpers
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
        print(
            "Have not implemented replacing legend labels that are not on the form a,b yet."
        )
        print(f"legend label: {name}")
        return trace

    cell_label = df.loc[
        (df["group"] == group) & (df["sub_group"] == subgroup), "cell"
    ].values[0]
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


def _make_plotly_template(name="axis"):
    tick_label_width = 6
    title_font_size = 22
    title_font_family = "Arial"
    axis_font_size = 16
    axis_standoff = 15
    linecolor = "rgb(36,36,36)"

    t = go.layout.Template(
        layout=dict(
            font_family=title_font_family,
            title=dict(
                font_size=title_font_size,
                x=0,
                xref="paper",
            ),
            xaxis=dict(
                linecolor=linecolor,
                mirror=True,
                showline=True,
                zeroline=False,
                title=dict(
                    standoff=axis_standoff,
                    font_size=axis_font_size,
                ),
            ),
            yaxis=dict(
                linecolor=linecolor,
                mirror=True,
                showline=True,
                zeroline=False,
                tickformat=f"{tick_label_width}",
                title=dict(
                    standoff=axis_standoff,
                    font_size=axis_font_size,
                ),
            ),
        )
    )
    pio.templates[name] = t


def _make_labels():
    labels = {
        "cycle_index": "Cycle number",
        "charge_capacity_gravimetric": "Gravimetric Charge Capacity",
        "discharge_capacity_gravimetric": "Gravimetric Discharge Capacity",
        "charge_c_rate": "C-rate (charge)",
        "discharge_c_rate": "C-rate (discharge)",
        "coulombic_efficiency": "Coulombic Efficiency",
        "group": "Group",
        "sub_group": "Sub-group",
        "variable": "Variable",
        "value": "Value",
    }
    return labels


def plot_cycle_life_summary_plotly(summaries: pd.DataFrame, **kwargs):
    group_legends = kwargs.pop("group_legends", True)
    base_template = kwargs.pop("base_template", "plotly")
    color_map = kwargs.pop("color_map", px.colors.qualitative.Set1)

    if isinstance(color_map, str):
        if hasattr(px.colors.qualitative, color_map):
            color_map = getattr(px.colors.qualitative, color_map)
        else:
            logging.warning(f"could not find color map {color_map}")

    ce_range = kwargs.pop("ce_range", None)
    min_cycle = kwargs.pop("min_cycle", None)
    max_cycle = kwargs.pop("max_cycle", None)

    title = kwargs.pop("title", "Cycle Summary")
    x_label = kwargs.pop("x_label", "Cycle Number")
    direction = kwargs.pop("direction", "charge")
    rate = kwargs.pop("rate", False)
    ir = kwargs.pop("ir", True)
    filter_by_group = kwargs.pop("filter_by_group", None)
    filter_by_name = kwargs.pop("filter_by_name", None)

    individual_plot_height = 250
    header_height = 200
    individual_legend_height = 20
    legend_header_height = 20

    hdr_cycle = hdr_summary["cycle_index"]
    hdr_charge = hdr_summary["charge_capacity_gravimetric"]
    hdr_discharge = hdr_summary["discharge_capacity_gravimetric"]
    hdr_ce = hdr_summary["coulombic_efficiency"]
    hdr_ir_charge = hdr_summary["ir_charge"]
    hdr_ir_discharge = hdr_summary["ir_discharge"]
    hdr_charge_rate = hdr_summary["charge_c_rate"]
    hdr_discharge_rate = hdr_summary["discharge_c_rate"]
    hdr_group = "group"
    hdr_sub_group = "sub_group"

    legend_dict = {"title": "<b>Cell</b>", "orientation": "v"}

    additional_template = "axes_with_borders"
    _make_plotly_template(additional_template)

    available_summaries = summaries.variable.unique()

    if direction == "discharge":
        hdr_ir = hdr_ir_discharge
        hdr_rate = hdr_discharge_rate
        selected_summaries = [hdr_cycle, hdr_ce, hdr_discharge]
    else:
        selected_summaries = [hdr_cycle, hdr_ce, hdr_charge]
        hdr_ir = hdr_ir_charge
        hdr_rate = hdr_charge_rate

    if ir:
        if hdr_ir in available_summaries:
            selected_summaries.append(hdr_ir)
        else:
            logging.debug("no ir data available")
    if rate:
        if hdr_rate in available_summaries:
            selected_summaries.append(hdr_rate)
        else:
            logging.debug("no rate data available")

    plotted_summaries = selected_summaries[1:]

    summaries = summaries.loc[summaries.variable.isin(selected_summaries), :]
    if max_cycle:
        summaries = summaries.loc[summaries[hdr_cycle] <= max_cycle, :]

    if min_cycle:
        summaries = summaries.loc[summaries[hdr_cycle] >= min_cycle, :]

    labels = _make_labels()
    sub_titles = [labels.get(n, n.replace("_", " ").title()) for n in plotted_summaries]
    if max_cycle or min_cycle:
        sub_titles.append(f"[{min_cycle}, {max_cycle}]")
    sub_titles = ", ".join(sub_titles)

    number_of_cells = len(summaries.cell.unique())
    number_of_rows = len(plotted_summaries)
    legend_height = legend_header_height + individual_legend_height * number_of_cells
    plot_height = max(legend_height, individual_plot_height * number_of_rows)
    total_height = header_height + plot_height

    if filter_by_group is not None:
        if not isinstance(filter_by_group, (list, tuple)):
            filter_by_group = [filter_by_group]
        summaries = summaries.loc[summaries[hdr_group].isin([filter_by_group]), :]

    if filter_by_name is not None:
        summaries = summaries.loc[summaries.cell.str.contains(filter_by_name), :]

    canvas = px.line(
        summaries,
        x=hdr_cycle,
        y="value",
        facet_row="variable",
        color=hdr_group,
        symbol=hdr_sub_group,
        labels=labels,
        height=total_height,
        category_orders={"variable": plotted_summaries},
        template=f"{base_template}+{additional_template}",
        color_discrete_sequence=color_map,
        title=f"<b>{title}</b><br>{sub_titles}",
    )

    adjust_row_heights = True
    if number_of_rows == 1:
        domains = [[0.0, 1.00]]
    elif number_of_rows == 2:
        domains = [[0.0, 0.79], [0.8, 1.00]]
    elif number_of_rows == 3:
        domains = [[0.0, 0.39], [0.4, 0.79], [0.8, 1.00]]

    elif number_of_rows == 4:
        domains = [[0.0, 0.24], [0.25, 0.49], [0.5, 0.74], [0.75, 1.00]]

    else:
        adjust_row_heights = False
        domains = None

    canvas.for_each_trace(
        functools.partial(
            _plotly_legend_replacer,
            df=summaries,
            group_legends=group_legends,
        )
    )

    canvas.for_each_annotation(lambda a: a.update(text=""))
    canvas.update_traces(marker=dict(size=8))

    canvas.update_xaxes(row=1, title_text=f"<b>{x_label}</b>")

    for i, n in enumerate(reversed(plotted_summaries)):
        n = labels.get(n, n.replace("_", " ").title())
        update_kwargs = dict(
            row=i + 1,
            autorange=True,
            matches=None,
            title_text=f"<b>{n}</b>",
        )
        if adjust_row_heights:
            domain = domains[i]
            update_kwargs["domain"] = domain

        canvas.update_yaxes(**update_kwargs)

    if hdr_ce in plotted_summaries and ce_range is not None:
        canvas.update_yaxes(row=number_of_rows, autorange=False, range=ce_range)

    canvas.update_layout(
        legend=legend_dict,
        showlegend=True,
    )
    return canvas


def plot_cycle_life_summary_seaborn(summaries: pd.DataFrame, **kwargs):
    color_map = kwargs.pop("color_map", "Set1")

    ce_range = kwargs.pop("ce_range", None)
    min_cycle = kwargs.pop("min_cycle", None)
    max_cycle = kwargs.pop("max_cycle", None)

    title = kwargs.pop("title", "Cycle Summary")
    x_label = kwargs.pop("x_label", "Cycle Number")
    direction = kwargs.pop("direction", "charge")
    rate = kwargs.pop("rate", False)
    ir = kwargs.pop("ir", True)
    filter_by_group = kwargs.pop("filter_by_group", None)
    filter_by_name = kwargs.pop("filter_by_name", None)

    hdr_cycle = hdr_summary["cycle_index"]
    hdr_charge = hdr_summary["charge_capacity_gravimetric"]
    hdr_discharge = hdr_summary["discharge_capacity_gravimetric"]
    hdr_ce = hdr_summary["coulombic_efficiency"]
    hdr_ir_charge = hdr_summary["ir_charge"]
    hdr_ir_discharge = hdr_summary["ir_discharge"]
    hdr_charge_rate = hdr_summary["charge_c_rate"]
    hdr_discharge_rate = hdr_summary["discharge_c_rate"]
    hdr_group = "group"
    hdr_sub_group = "sub_group"

    legend_dict = {"title": "<b>Cell</b>", "orientation": "v"}

    available_summaries = summaries.variable.unique()

    if direction == "discharge":
        hdr_ir = hdr_ir_discharge
        hdr_rate = hdr_discharge_rate
        selected_summaries = [hdr_cycle, hdr_ce, hdr_discharge]
    else:
        selected_summaries = [hdr_cycle, hdr_ce, hdr_charge]
        hdr_ir = hdr_ir_charge
        hdr_rate = hdr_charge_rate

    if ir:
        if hdr_ir in available_summaries:
            selected_summaries.append(hdr_ir)
        else:
            logging.debug("no ir data available")
    if rate:
        if hdr_rate in available_summaries:
            selected_summaries.append(hdr_rate)
        else:
            logging.debug("no rate data available")

    plotted_summaries = selected_summaries[1:]

    summaries = summaries.loc[summaries.variable.isin(selected_summaries), :]
    if max_cycle:
        summaries = summaries.loc[_summaries[hdr_cycle] <= max_cycle, :]

    if min_cycle:
        summaries = summaries.loc[_summaries[hdr_cycle] >= min_cycle, :]

    labels = _make_labels()
    default_ranges = dict()
    if ce_range is not None:
        default_ranges[hdr_ce] = ce_range
    ranges = _get_ranges(summaries, plotted_summaries, default_ranges)

    sub_titles = [labels.get(n, n.replace("_", " ").title()) for n in plotted_summaries]
    if max_cycle or min_cycle:
        sub_titles.append(f"[{min_cycle}, {max_cycle}]")
    sub_titles = ", ".join(sub_titles)

    number_of_cells = len(summaries.cell.unique())
    number_of_rows = len(plotted_summaries)

    sns.set_theme(style="darkgrid")

    if filter_by_group is not None:
        if not isinstance(filter_by_group, (list, tuple)):
            filter_by_group = [filter_by_group]
        summaries = summaries.loc[summaries[hdr_group].isin([filter_by_group]), :]

    if filter_by_name is not None:
        summaries = summaries.loc[summaries.cell.str.contains(filter_by_name), :]

    canvas_grid = sns.relplot(
        data=summaries,
        kind="line",
        x=hdr_cycle,
        y="value",
        hue=hdr_group,
        style=hdr_sub_group,
        row="variable",
        markers=True,
        dashes=False,
        height=3,
        aspect=3,
        linewidth=2.0,
        legend="auto",
        palette=color_map,
        facet_kws={"sharex": True, "sharey": False, "legend_out": True},
    )

    canvas_grid.figure.suptitle(f"{title}\n{sub_titles}", y=1.05, fontsize=16)
    axes = canvas_grid.figure.get_axes()
    for ax in axes:
        hdr = ax.get_title().split(" = ")[-1]
        y_label = labels.get(hdr, hdr)
        _x_label = ax.get_xlabel()
        _x_label = labels.get(_x_label, _x_label)
        if _x_label:
            if x_label:
                ax.set_xlabel(x_label)
            else:
                ax.set_xlabel(_x_label)
        r = ranges.get(hdr, (None, None))
        legend_handles, legend_labels = ax.get_legend_handles_labels()
        # TODO: update legend
        if legend_handles:
            logging.debug("got legend handles")
            # ax.legend(legend_handles, legend_labels)
        ax.set_title("")
        ax.set_ylabel(y_label)
        ax.set_ylim(r)

    return canvas_grid.figure


def _get_ranges(summaries, plotted_summaries, defaults=None):
    ranges = dict()
    if defaults is None:
        defaults = dict()
    for hdr in plotted_summaries:
        if hdr in defaults:
            ranges[hdr] = defaults[hdr]
            continue
        start = summaries.loc[summaries.variable == hdr, "value"].min()
        if start in [np.nan, np.inf, -np.inf]:
            start = None

        end = summaries.loc[summaries.variable == hdr, "value"].max()
        if end in [np.nan, np.inf, -np.inf]:
            end = None
        if start is not None and end is not None:
            start -= 0.1 * abs(abs(end) - abs(start))
            end += 0.1 * abs(abs(end) - abs(start))
        elif end is not None:
            end += 0.1 * abs(end)
        elif start is not None:
            start -= 0.1 * abs(start)
        ranges[hdr] = (start, end)
    return ranges


def _plotting_data_legacy(pages, summaries, width, height, height_fractions, **kwargs):
    # sub-sub-engine
    canvas = None
    if prms.Batch.backend == "bokeh":
        canvas = plot_cycle_life_summary_bokeh(
            pages, summaries, width, height, height_fractions, **kwargs
        )
    elif prms.Batch.backend == "plotly":
        print("plotly not implemented yet")

    elif prms.Batch.backend == "matplotlib":
        logging.info("[obs! experimental]")
        canvas = plot_cycle_life_summary_matplotlib(
            pages, summaries, width, height, height_fractions, **kwargs
        )
    else:
        logging.info(f"the {prms.Batch.backend} " f"back-end is not implemented yet.")

    return canvas


def _preparing_data_and_plotting_legacy(**kwargs):
    # sub-engine
    logging.debug("    - _preparing_data_and_plotting_legacy")
    experiments = kwargs.pop("experiments")
    farms = kwargs.pop("farms")
    width = kwargs.pop("width", prms.Batch.summary_plot_width)
    height = kwargs.pop("height", prms.Batch.summary_plot_height)

    height_fractions = kwargs.pop(
        "height_fractions", prms.Batch.summary_plot_height_fractions
    )

    for experiment in experiments:
        if not isinstance(experiment, CyclingExperiment):
            logging.info(
                "No! This engine is only really good at processing CyclingExperiments"
            )
            logging.info(experiment)
        else:
            pages = experiment.journal.pages
            try:
                keys = [df.name for df in experiment.memory_dumped["summary_engine"]]
                summaries = pd.concat(
                    experiment.memory_dumped["summary_engine"], keys=keys, axis=1
                )
                canvas = _plotting_data_legacy(
                    pages, summaries, width, height, height_fractions, **kwargs
                )

                farms.append(canvas)

            except KeyError:
                logging.info("could not parse the summaries")
                logging.info(" - might be new a bug?")
                logging.info(
                    " - might be a known bug related to dropping cells (b.drop)"
                )
                logging.info(" - maybe try reloading the data helps?")

    return farms


def exporting_plots(**kwargs):
    # dumper
    experiments = kwargs["experiments"]
    farms = kwargs["farms"]
    barn = kwargs["barn"]
    engine = kwargs["engine"]
    return None


class CyclingSummaryPlotter(BasePlotter):
    def __init__(self, *args, reset_farms=True):
        """
        Attributes (inherited):
            experiments: list of experiments.
            farms: list of farms (containing pandas DataFrames or figs).
            barn (str): identifier for where to place the output-files.
            reset_farms (bool): empty the farms before running the engine.
        """

        super().__init__(*args)
        self.engines = list()
        self.dumpers = list()
        self.reset_farms = reset_farms
        self._use_dir = None
        self.current_engine = None
        self._assign_engine(summary_plotting_engine)
        self._assign_dumper(exporting_plots)

    @property
    def figure(self):
        """Get the (first) figure/canvas."""
        if len(self.farms) > 0:
            return self.farms[0]

    @property
    def fig(self):
        """Alias for figure."""
        return self.figure

    @property
    def figures(self):
        """Get all figures/canvases."""
        if len(self.farms) > 0:
            return self.farms

    @property
    def columns(self):
        if len(self.experiments > 0):
            return self.experiments[0].summaries.columns.get_level_values(0)

    def _assign_engine(self, engine):
        self.engines.append(engine)

    def _assign_dumper(self, dumper):
        self.dumpers.append(dumper)

    def run_engine(self, engine, **kwargs):
        """run engine (once pr. experiment).

        Args:
            engine: engine to run (function or method).

        The method issues the engine command (with experiments and farms
        as input) that returns an updated farms as well as the barn and
        assigns them both to self.

        The farms attribute is a list of farms, i.e. [farm1, farm2, ...], where
        each farm contains pandas DataFrames.

        The barns attribute is a pre-defined string used for picking what
        folder(s) the file(s) should be exported to.
        For example, if barn equals "batch_dir", the file(s) will be saved
        to the experiments batch directory.

        The engine(s) is given `self.experiments` and `self.farms` as input and
        returns farms to `self.farms` and barn to `self.barn`. Thus, one could
        in principle modify `self.experiments` within the engine without
        explicitly 'notifying' the poor soul who is writing a batch routine
        using that engine. However, it is strongly advised not to do such
        things. And if you, as engine designer, really need to, then at least
        notify it through a debug (logger) statement.
        """

        logging.debug("start engine::")

        self.current_engine = engine
        if self.reset_farms:
            self.farms = []
        self.farms, self.barn = engine(
            experiments=self.experiments, farms=self.farms, **kwargs
        )

        logging.debug("::engine ended")

    def run_dumper(self, dumper):
        """run dumber (once pr. engine)

        Args:
            dumper: dumper to run (function or method).

        The dumper takes the attributes experiments, farms, and barn as input.
        It does not return anything. But can, if the dumper designer feels in
        a bad and nasty mood, modify the input objects
        (for example experiments).
        """

        logging.debug("start dumper::")
        dumper(
            experiments=self.experiments,
            farms=self.farms,
            barn=self.barn,
            engine=self.current_engine,
        )
        logging.debug("::dumper ended")


class EISPlotter(BasePlotter):
    def __init__(self):
        super().__init__()

    def do(self):
        warnings.warn("not implemented yet")


if __name__ == "__main__":
    print("batch_plotters".center(80, "="))
    csp = CyclingSummaryPlotter()
    eisp = EISPlotter()
    print("\n --> OK")
