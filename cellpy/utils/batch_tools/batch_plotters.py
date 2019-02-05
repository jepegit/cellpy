import logging
import warnings
import sys

import itertools
import pandas as pd

from cellpy.utils.batch_tools.batch_core import BasePlotter
from cellpy.utils.batch_tools.batch_experiments import CyclingExperiment
from cellpy.exceptions import UnderDefined
from cellpy import prms


# print(prms.Batch.backend)

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
        logging.warning("could not import bokeh -> using matplotlib instead")

    except ModuleNotFoundError:
        prms.Batch.backend = "matplotlib"
        logging.warning("could not import bokeh -> using matplotlib instead")


def create_legend(info, c, option="clean", use_index=False):
    """creating more informative legends"""

    logging.debug("    - creating legends")
    mass, loading, label = info.loc[c, ["masses", "loadings", "labels"]]

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
    g, sg = info.loc[c, ["groups", "sub_groups"]]
    return int(g), int(sg)


def create_plot_option_dicts(info, marker_types=None, colors=None,
                             line_dash=None, size=None):
    """Create two dictionaries with plot-options.

    The first iterates colors (based on group-number), the second iterates
    through marker types.

    Returns: group_styles (dict), sub_group_styles (dict)
    """

    logging.debug("    - creating plot-options-dict (for bokeh)")

    # Current only works for bokeh

    if marker_types is None:
        marker_types = ["circle", "square", "triangle", "invertedtriangle",
                        "diamond", "cross", "asterix"]

    if line_dash is None:
        line_dash = [0, 0]

    if size is None:
        size = 10

    groups = info.groups.unique()
    number_of_groups = len(groups)
    if colors is None:
        if number_of_groups < 4:
            # print("using 3")
            colors = bokeh.palettes.brewer['YlGnBu'][3]
        else:
            # print(f"using {min(9, number_of_groups)}")
            colors = bokeh.palettes.brewer['YlGnBu'][min(9, number_of_groups)]

    sub_groups = info.sub_groups.unique()

    marker_it = itertools.cycle(marker_types)
    colors_it = itertools.cycle(colors)

    group_styles = dict()
    sub_group_styles = dict()

    for j in groups:
        color = next(colors_it)
        marker_options = {
            "line_color": color,
            "fill_color": color,
        }

        line_options = {
            "line_color": color,
        }
        group_styles[j] = {
            "marker": marker_options,
            "line": line_options,
        }

    for j in sub_groups:
        marker_type = next(marker_it)
        marker_options = {
            "marker": marker_type,
            "size": size,
        }

        line_options = {
            "line_dash": line_dash,
        }
        sub_group_styles[j] = {
            "marker": marker_options,
            "line": line_options,
        }
    return group_styles, sub_group_styles


def create_summary_plot(data, info, group_styles, sub_group_styles,
                        label = None,
                        title="Capacity", x_axis_label="Cycle number",
                        y_axis_label="Capacity (mAh/g)",
                        width=900, height=400,
                        legend_option="clean",
                        legend_location="bottom_right",
                        x_range=None,
                        y_range=None,
                        tools=["hover", ]
                        ):

    # Currently only works for Bokeh
    # from bokeh.plotting import figure, output_notebook, show
    # from bokeh.models import ColumnDataSource, Range1d, HoverTool
    # from bokeh.layouts import column
    # from bokeh.models.annotations import Legend

    logging.debug(f"    - creating summary (bokeh) plot for {label}")

    discharge_capacity = None
    if isinstance(data, (list, tuple)):
        charge_capacity = data[0]
        if len(data) == 2:
            discharge_capacity = data[1]
    else:
        charge_capacity = data

    charge_source = bokeh.models.ColumnDataSource(charge_capacity)
    if discharge_capacity is not None:
        discharge_source = bokeh.models.ColumnDataSource(discharge_capacity)

    p = bokeh.plotting.figure(
        title=title, width=width, height=height,
        # tools = tools,
        x_range=x_range,
        y_range=y_range,
        x_axis_label=x_axis_label,
        y_axis_label=y_axis_label
    )

    cols = charge_capacity.columns.get_level_values(0)
    if legend_option is not None:
        legend_collection = []

    for c in cols:
        g, sg = look_up_group(info, c)

        if legend_option is not None:
            legend_items = []
            l = create_legend(info, c, option=legend_option)
            # legend_option_dict = {"legend": f"{l}"}

        group_props = group_styles[g]
        sub_group_props = sub_group_styles[sg]

        ch_m = p.scatter(
            source=charge_source,
            x="Cycle_Index", y=c,
            # **legend_option_dict,
            #  Remark! cannot use the same legend name as
            #  column name (defaults to a lookup)
            **group_props["marker"],  # color
            **sub_group_props["marker"],  # marker
        )

        ch_l = p.line(
            source=charge_source,
            x="Cycle_Index", y=c,
            **group_props["line"],
            **sub_group_props["line"],
        )

        if legend_option is not None:
            legend_items.extend([ch_m, ch_l])

        if discharge_capacity is not None:
            # creating a local copy so that I can do local changes
            group_props_marker_charge = group_props["marker"].copy()
            group_props_marker_charge["fill_color"] = None
            dch_m = p.scatter(
                source=discharge_source,
                x="Cycle_Index", y=c,
                **group_props_marker_charge,
                **sub_group_props["marker"],
            )

            dch_l = p.line(
                source=discharge_source,
                x="Cycle_Index", y=c,
                **group_props["line"],
                **sub_group_props["line"],
            )

            if legend_option is not None:
                legend_items.extend([dch_m, dch_l])

        if legend_option is not None:
            legend_collection.append((l, legend_items))

    if discharge_capacity is not None:
        print("(filled:charge) (open:discharge)")

    if legend_option is not None:
        legend = bokeh.models.annotations.Legend(
            items=legend_collection,
            location=(10, 0)
        )
        p.add_layout(legend)
        p.legend.location = legend_location
        p.legend.click_policy = "hide"
    return p


def plot_cycle_life_summary(info, summaries, width=900, height=800,
                            height_fractions=[0.2, 0.5, 0.3]):
    # Currently only works for Bokeh
    # from bokeh.plotting import figure, output_notebook, show
    # from bokeh.models import ColumnDataSource, Range1d, HoverTool
    # from bokeh.layouts import column
    # from bokeh.models.annotations import Legend

    logging.debug(f"   * stacking and plotting")
    logging.debug(f"      backend: {prms.Batch.backend}")

    discharge_capacity = summaries.discharge_capacity
    charge_capacity = summaries.charge_capacity
    coulombic_efficiency = summaries.coulombic_efficiency
    ir_charge = summaries.ir_charge

    h_eff = int(height_fractions[0] * height)
    h_cap = int(height_fractions[1] * height)
    h_ir = int(height_fractions[2] * height)

    group_styles, sub_group_styles = create_plot_option_dicts(info)

    p_eff = create_summary_plot(
        coulombic_efficiency, info, group_styles, sub_group_styles,
        label="c.e.",
        legend_option=None, title=None, x_axis_label=None,
        y_axis_label="Coulombic efficiency (%)",
        width=width, height=h_eff,
    )

    p_cap = create_summary_plot(
        (charge_capacity, discharge_capacity), info, group_styles,
        sub_group_styles,
        label="charge and discharge cap.",
        title=None, x_axis_label=None, height=h_cap, width=width,
        x_range=p_eff.x_range,
    )

    p_ir = create_summary_plot(
        ir_charge, info, group_styles, sub_group_styles,
        label="ir charge",
        legend_option=None, title=None, x_axis_label="Cycle number",
        y_axis_label="IR Charge (Ohm)",
        width=width, height=h_ir,
        x_range=p_eff.x_range,
    )

    p_eff.y_range.start, p_eff.y_range.end = 20, 120
    p_eff.xaxis.visible = False
    p_cap.xaxis.visible = False

    hover = bokeh.models.HoverTool(tooltips=[
        ("cycle", "@Cycle_Index"),
        ("value", "$y"),
    ])

    p_eff.add_tools(hover)
    p_cap.add_tools(hover)
    p_ir.add_tools(hover)

    return bokeh.plotting.show(
        bokeh.layouts.column(p_eff, p_cap, p_ir)
    )


def summary_plotting_engine(**kwargs):
    """creates plots of summary data."""

    logging.debug(f"Using {prms.Batch.backend} for plotting")
    experiments = kwargs["experiments"]
    farms = kwargs["farms"]
    barn = None

    logging.debug("    - summary_plot_engine")
    farms = _preparing_data_and_plotting(
        experiments=experiments,
        farms=farms
    )

    return farms, barn


def _plotting_data(pages, summaries, width, height, height_fractions):
    # sub-sub-engine
    canvas = None
    if prms.Batch.backend == "bokeh":
        canvas = plot_cycle_life_summary(  # move this to sub-engine
            pages, summaries, width,
            height,
            height_fractions
        )
    else:
        logging.info(
            f"the {prms.Batch.backend} "
            f"back-end is not implemented yet"
        )

    return canvas


def _preparing_data_and_plotting(**kwargs):
    # sub-engine
    logging.debug("    - _preparing_data_and_plotting")
    experiments = kwargs["experiments"]
    farms = kwargs["farms"]

    width = prms.Batch.summary_plot_width
    height = prms.Batch.summary_plot_height
    height_fractions = prms.Batch.summary_plot_height_fractions

    for experiment in experiments:
        if not isinstance(experiment, CyclingExperiment):
            print(
                "No! This engine is only really good at"
                "processing CyclingExperiments"
            )
            print(experiment)
        else:
            pages = experiment.journal.pages
            try:
                keys = [df.name for df in
                        experiment.memory_dumped["summary_engine"]]

                summaries = pd.concat(
                    experiment.memory_dumped["summary_engine"],
                    keys=keys, axis=1
                )
                canvas = _plotting_data(
                    pages, summaries, width,
                    height,
                    height_fractions
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
    def __init__(self, *args):
        """
        Attributes (inherited):
            experiments: list of experiments.
            farms: list of farms (containing pandas DataFrames or figs).
            barn (str): identifier for where to place the output-files.
        """

        super().__init__(*args)
        self.engines = list()
        self.dumpers = list()
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

        self.farms, self.barn = engine(
            experiments=self.experiments,
            farms=self.farms
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

    def do(self):
        if not self.experiments:
            raise UnderDefined("cannot run until "
                               "you have assigned an experiment")

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


if __name__ == '__main__':
    print("batch_plotters".center(80, "="))
    csp = CyclingSummaryPlotter()
    eisp = EISPlotter()
    print("\n --> OK")

