import logging
import warnings
import sys

import itertools
import pandas as pd

from cellpy.utils.batch_tools.batch_core import BasePlotter
from cellpy.utils.batch_tools.batch_experiments import CyclingExperiment
from cellpy.parameters.internal_settings import get_headers_journal, get_headers_summary
from cellpy.exceptions import UnderDefined
from cellpy import prms

hdr_journal = get_headers_journal()
hdr_summary = get_headers_summary()
# print(prms.Batch.backend)

# TODO: add palette to prms.Batch

if prms.Batch.backend == "bokeh":
    try:
        import bokeh
        import bokeh.plotting
        import bokeh.palettes
        import bokeh.models
        import bokeh.layouts
        import bokeh.models.annotations

    except ImportError:
        prms.Batch.backend = "matplotlib"
        logging.debug("could not import bokeh -> using matplotlib instead")

    except ModuleNotFoundError:
        prms.Batch.backend = "matplotlib"
        logging.debug("could not import bokeh -> using matplotlib instead")


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
        return label

    if option == "mass":
        label = f"{label} ({mass:.2f} mg)"
    elif option == "loading":
        label = f"{label} ({loading:.2f} mg/cm2)"
    elif option == "all":
        label = f"{label} ({mass:.2f} mg) ({loading:.2f} mg/cm2)"

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
            palette = bokeh.palettes.d3["Category10"]
            # palette = bokeh.palettes.brewer[prms.Batch.bokeh_palette']
        except NameError:
            palette = [
                ["k"],
                ["k", "r"],
                ["k", "r", "b"],
                ["k", "r", "b", "g"],
                ["k", "r", "b", "g", "c"],
                ["k", "r", "b", "g", "c", "m"],
                ["k", "r", "b", "g", "c", "m", "y"],
            ]

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
            colors = palette[min(6, number_of_groups)]

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
    tools=["hover"],
):

    logging.debug(f"    - creating summary (bokeh) plot for {label}")
    discharge_capacity = None
    if isinstance(data, (list, tuple)):
        charge_capacity = data[0]
        if len(data) == 2:
            discharge_capacity = data[1]
    else:
        charge_capacity = data

    p = bokeh.plotting.figure(
        title=title,
        width=width,
        height=height,
        # tools = tools,
        x_range=x_range,
        y_range=y_range,
        x_axis_label=x_axis_label,
        y_axis_label=y_axis_label,
    )

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

    for cc in cols:
        g, sg = look_up_group(info, cc)
        legend_items = []
        l = create_legend(info, cc, option=legend_option)
        group_props = group_styles[g]
        sub_group_props = sub_group_styles[sg]

        if sub_cols_charge is not None:
            c = f"{sub_cols_charge[0]}_{cc}"
            r = f"{sub_cols_charge[1]}_{cc}"
            charge_capacity_sub = charge_capacity.loc[:, [c, r]]
            charge_capacity_sub.columns = [c, "rate"]
            charge_source = bokeh.models.ColumnDataSource(charge_capacity_sub)

        else:
            c = cc
            charge_capacity_sub = charge_capacity.loc[:, [c]]
            charge_source = bokeh.models.ColumnDataSource(charge_capacity_sub)

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

        ch_l = p.line(
            source=charge_source,
            x=hdr_summary.cycle_index,
            y=c,
            **group_props["line"],
            **sub_group_props["line"],
        )

        legend_items.extend([ch_m, ch_l])

        if discharge_capacity is not None:
            # creating a local copy so that I can do local changes
            group_props_marker_charge = group_props["marker"].copy()
            group_props_marker_charge["fill_color"] = None

            if sub_cols_discharge is not None:
                c = f"{sub_cols_discharge[0]}_{cc}"
                r = f"{sub_cols_discharge[1]}_{cc}"
                discharge_capacity_sub = discharge_capacity.loc[:, [c, r]]
                discharge_capacity_sub.columns = [c, "rate"]
                discharge_source = bokeh.models.ColumnDataSource(discharge_capacity_sub)

            else:
                c = cc
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

    return p, legend_collection


def plot_cycle_life_summary_bokeh(
    info,
    summaries,
    width=900,
    height=800,
    height_fractions=[0.3, 0.4, 0.3],
    legend_option="all",
    add_rate=True,
):

    # reloading bokeh (in case we change backend during a session)
    import bokeh
    import bokeh.plotting
    import bokeh.palettes
    import bokeh.models
    import bokeh.layouts
    import bokeh.models.annotations
    from bokeh.models import LegendItem, Legend
    from collections import defaultdict

    logging.debug(f"   * stacking and plotting")
    logging.debug(f"      backend: {prms.Batch.backend}")

    idx = pd.IndexSlice
    all_legend_items = []

    if add_rate:

        try:
            discharge_capacity = summaries.loc[
                :, idx[["discharge_capacity", "discharge_c_rate"], :]
            ]
        except AttributeError:
            warnings.warn(
                "No discharge rate columns available - consider re-creating summary!"
            )
            discharge_capacity = summaries.discharge_capacity

        try:
            charge_capacity = summaries.loc[
                :, idx[["charge_capacity", "charge_c_rate"], :]
            ]
        except AttributeError:
            warnings.warn(
                "No charge rate columns available - consider re-creating summary!"
            )
            charge_capacity = summaries.charge_capacity

        try:
            coulombic_efficiency = summaries.loc[
                :, idx[["coulombic_efficiency", "charge_c_rate"], :]
            ]
        except AttributeError:
            warnings.warn(
                "No charge rate columns available - consider re-creating summary!"
            )
            coulombic_efficiency = summaries.coulombic_efficiency

        try:
            ir_charge = summaries.loc[:, idx[["ir_charge", "charge_c_rate"], :]]
        except AttributeError:
            warnings.warn(
                "No charge rate columns available - consider re-creating summary!"
            )
            ir_charge = summaries.ir_charge
    else:
        discharge_capacity = summaries.discharge_capacity
        charge_capacity = summaries.charge_capacity
        coulombic_efficiency = summaries.coulombic_efficiency
        ir_charge = summaries.ir_charge

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
        title=None,
        x_axis_label=None,
        y_axis_label="Coulombic efficiency (%)",
        width=width,
        height=h_eff,
    )

    all_legend_items.extend(legends_eff)

    p_cap, legends_cap = create_summary_plot_bokeh(
        (charge_capacity, discharge_capacity),
        info,
        group_styles,
        sub_group_styles,
        legend_option=legend_option,
        label="charge and discharge cap.",
        title=None,
        x_axis_label=None,
        height=h_cap,
        width=width,
        x_range=p_eff.x_range,
    )
    all_legend_items.extend(legends_cap)

    p_ir, legends_ir = create_summary_plot_bokeh(
        ir_charge,
        info,
        group_styles,
        sub_group_styles,
        label="ir charge",
        legend_option=legend_option,
        title=None,
        x_axis_label="Cycle number",
        y_axis_label="IR Charge (Ohm)",
        width=width,
        height=h_ir,
        x_range=p_eff.x_range,
    )
    all_legend_items.extend(legends_ir)

    p_eff.y_range.start, p_eff.y_range.end = 20, 120
    p_eff.xaxis.visible = False
    p_cap.xaxis.visible = False

    tooltips = [("cycle", f"@{hdr_summary.cycle_index}"), ("value", "$y{0.}")]
    if add_rate:
        tooltips.append(("rate", "@rate{0.000}"))

    hover = bokeh.models.HoverTool(tooltips=tooltips)

    p_eff.add_tools(hover)
    p_cap.add_tools(hover)
    p_ir.add_tools(hover)

    renderer_list = p_eff.renderers + p_cap.renderers + p_ir.renderers

    legend_items_dict = defaultdict(list)
    for label, r in all_legend_items:
        legend_items_dict[label].extend(r)

    legend_items = []
    renderer_list = []
    for legend in legend_items_dict:
        legend_items.append(
            LegendItem(label=legend, renderers=legend_items_dict[legend])
        )
        renderer_list.extend(legend_items_dict[legend])

    comment = "Legends"

    dum_fig = bokeh.plotting.figure(
        plot_width=300,
        plot_height=height,
        outline_line_alpha=0,
        toolbar_location=None,
        width_policy="min",
        min_width=300,
        title=comment,
    )
    # set the components of the figure invisible
    for fig_component in [
        dum_fig.grid[0],
        dum_fig.ygrid[0],
        dum_fig.xaxis[0],
        dum_fig.yaxis[0],
    ]:
        fig_component.visible = False

    dum_fig.renderers += renderer_list

    # set the figure range outside of the range of all
    # glyphs (need to double check this)
    dum_fig.x_range.end = width + 5
    dum_fig.x_range.start = width
    dum_fig.add_layout(
        Legend(
            click_policy="hide",
            location="top_left",
            border_line_alpha=0,
            items=legend_items,
        )
    )
    dum_fig.title.align = "center"

    fig_grid = bokeh.layouts.gridplot(
        [p_eff, p_cap, p_ir], ncols=1, sizing_mode="stretch_width"
    )

    info_text = "(filled:charge) (open:discharge)"
    p_ir.add_layout(bokeh.models.Title(text=info_text, align="right"), "below")

    final_figure = bokeh.layouts.row(
        children=[fig_grid, dum_fig], sizing_mode="stretch_width"
    )
    return bokeh.plotting.show(final_figure)


def plot_cycle_life_summary_matplotlib(
    info,
    summaries,
    width=900,
    height=800,
    height_fractions=[0.2, 0.5, 0.3],
    legend_option="all",
):

    import matplotlib.pyplot as plt

    # print(" running matplotlib plotter ".center(80,"="))

    discharge_capacity = summaries.discharge_capacity
    charge_capacity = summaries.charge_capacity
    coulombic_efficiency = summaries.coulombic_efficiency
    ir_charge = summaries.ir_charge

    h_eff = int(height_fractions[0] * height)
    h_cap = int(height_fractions[1] * height)
    h_ir = int(height_fractions[2] * height)

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

    group_styles, sub_group_styles = create_plot_option_dicts(
        info, marker_types=marker_types
    )

    canvas, (ax_cap, ax_ce, ax_ir) = plt.subplots(3, 1)
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

        ax_ce.plot(
            coulombic_efficiency[label],
            label=name,
            color=c,
            marker=m,
            markerfacecolor=c,
        )

        ax_cap.plot(
            charge_capacity[label], label=name, color=c, marker=m, markerfacecolor=c
        )

        ax_cap.plot(
            discharge_capacity[label], label=name, color=c, marker=m, markerfacecolor=f
        )
        ax_ir.plot(ir_charge[label], color=c, label=name, marker=m, markerfacecolor=c)

    ax_ce.set_ylabel("Coulombic Efficiency (%)")
    ax_ce.set_ylim((0, 110))
    ax_cap.set_ylabel("Capacity (mAh/g)")
    ax_ir.set_ylabel("IR (charge)")
    ax_ir.set_xlabel("Cycle")

    for ax in [ax_cap, ax_ce, ax_ir]:
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.6, box.height])

    # Put a legend to the right of the current axis
    ax_ce.legend(loc="center left", bbox_to_anchor=(1, 0.5))

    return canvas


def summary_plotting_engine(**kwargs):
    """creates plots of summary data."""

    logging.debug(f"Using {prms.Batch.backend} for plotting")
    experiments = kwargs.pop("experiments")
    farms = kwargs.pop("farms")
    barn = None

    logging.debug("    - summary_plot_engine")
    farms = _preparing_data_and_plotting(experiments=experiments, farms=farms, **kwargs)

    return farms, barn


def _plotting_data(pages, summaries, width, height, height_fractions, **kwargs):
    # sub-sub-engine

    canvas = None
    if prms.Batch.backend == "bokeh":
        canvas = plot_cycle_life_summary_bokeh(
            pages, summaries, width, height, height_fractions, **kwargs
        )
    elif prms.Batch.backend == "matplotlib":
        logging.info("[obs! experimental]")
        canvas = plot_cycle_life_summary_matplotlib(
            pages, summaries, width, height, height_fractions
        )
    else:
        logging.info(f"the {prms.Batch.backend} " f"back-end is not implemented yet.")

    return canvas


def _preparing_data_and_plotting(**kwargs):
    # sub-engine
    logging.debug("    - _preparing_data_and_plotting")
    experiments = kwargs.pop("experiments")
    farms = kwargs.pop("farms")

    width = prms.Batch.summary_plot_width
    height = prms.Batch.summary_plot_height
    height_fractions = prms.Batch.summary_plot_height_fractions

    for experiment in experiments:
        if not isinstance(experiment, CyclingExperiment):
            logging.info(
                "No! This engine is only really good at" "processing CyclingExperiments"
            )
            logging.info(experiment)
        else:
            pages = experiment.journal.pages
            try:
                keys = [df.name for df in experiment.memory_dumped["summary_engine"]]
                summaries = pd.concat(
                    experiment.memory_dumped["summary_engine"], keys=keys, axis=1
                )
                canvas = _plotting_data(
                    pages, summaries, width, height, height_fractions, **kwargs
                )
                farms.append(canvas)

            except KeyError:
                logging.info("no summary exists")
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
    def columns(self):
        if len(self.experiments > 0):
            return self.experiments[0].summaries.columns.get_level_values(0)

    def _assign_engine(self, engine):
        self.engines.append(engine)

    def _assign_dumper(self, dumper):
        self.dumpers.append(dumper)

    def run_engine(self, engine):
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
        For example, if barn equals "batch_dir", the the file(s) will be saved
        to the experiments batch directory.

        The engine(s) is given self.experiments and self.farms as input and
        returns farms to self.farms and barn to self.barn. Thus, one could
        in principle modify self.experiments within the engine without
        explicitly 'notifying' the poor soul who is writing a batch routine
        using that engine. However, it is strongly adviced not to do such
        things. And if you, as engine designer, really need to, then at least
        notify it through a debug (logger) statement.
        """

        logging.debug("start engine::")

        self.current_engine = engine
        if self.reset_farms:
            self.farms = []
        self.farms, self.barn = engine(experiments=self.experiments, farms=self.farms)
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

    def do(self):
        if not self.experiments:
            raise UnderDefined("cannot run until " "you have assigned an experiment")

        for engine in self.engines:
            self.empty_the_farms()
            logging.debug(f"running - {str(engine)}")
            self.run_engine(engine)

            for dumper in self.dumpers:
                logging.debug(f"exporting - {str(dumper)}")
                self.run_dumper(dumper)


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
