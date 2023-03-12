"""Collectors are used for simplifying plotting and exporting batch objects."""

import functools
import inspect
import logging
import math
from pprint import pprint
from pathlib import Path
import textwrap
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go

import cellpy
from cellpy.readers.core import group_by_interpolate
from cellpy.utils.batch import Batch
from cellpy.utils.helpers import concatenate_summaries
from cellpy.utils.plotutils import plot_concatenated
from cellpy.utils import ica

CELLPY_MINIMUM_VERSION = "1.0.0"
PLOTLY_BASE_TEMPLATE = "seaborn"
MAX_WIDTH = 1200

fig_pr_cell_template = go.layout.Template(
    layout=dict(
        xaxis=dict(
            linecolor='rgb(36,36,36)', mirror=True, showline=True, zeroline=False,
            title={'standoff': 15},
        ),
        yaxis=dict(
            linecolor='rgb(36,36,36)', mirror=True, showline=True, zeroline=False,
            title={'standoff': 15},
        ),
    )
)

fig_pr_cycle_template = go.layout.Template(
    layout=dict(
        xaxis=dict(
            linecolor='rgb(36,36,36)', mirror=True, showline=True, zeroline=False,
            title={'standoff': 15},
        ),
        yaxis=dict(
            linecolor='rgb(36,36,36)', mirror=True, showline=True, zeroline=False,
            title={'standoff': 15},
        ),
    )
)


def _setup():
    _welcome_message()


def _welcome_message():
    cellpy_version = cellpy.__version__
    logging.info(f"cellpy version: {cellpy_version}")
    logging.info(f"collectors need at least: {CELLPY_MINIMUM_VERSION}")


_setup()


class BatchCollector:
    collector_name: str = None
    data: pd.DataFrame = None
    figure: Any = None
    name: str = None
    nick: str = None
    autorun: bool = True
    figure_directory: Path = Path("out")
    data_directory: Path = Path("data/processed/")
    renderer: Any = None

    # override default arguments:
    elevated_data_collector_arguments: dict = None
    elevated_plotter_arguments: dict = None

    # defaults (and used also when resetting):
    _default_data_collector_arguments = {}
    _default_plotter_arguments = {}

    # templates override everything when using autorun:
    _templates = {
        "bokeh": [],
        "matplotlib": [],
        "plotly": [],
    }

    def __init__(
        self,
        b,
        data_collector,
        plotter,
        collector_name=None,
        name=None,
        nick=None,
        autorun=True,
        backend="plotly",
        elevated_data_collector_arguments=None,
        elevated_plotter_arguments=None,
        data_collector_arguments: dict = None,
        plotter_arguments: dict = None,
        **kwargs,
    ):
        """Update both the collected data and the plot(s).
        Args:
            b (cellpy.utils.Batch): the batch object.
            data_collector (callable): method that collects the data.
            plotter (callable): method that crates the plots.
            collector_name (str): name of collector.
            name (str or bool): name used for auto-generating filenames etc.
            autorun (bool): run collector and plotter immediately if True.
            use_templates (bool): also apply template(s) in autorun mode if True.
            backend (str): name of plotting backend to use ("plotly" or "matplotlib").
            elevated_data_collector_arguments (dict): arguments picked up by the child class' initializer.
            elevated_plotter_arguments (dict): arguments picked up by the child class' initializer.
            data_collector_arguments (dict): keyword arguments sent to the data collector.
            plotter_arguments (dict): keyword arguments sent to the plotter.
            update_name (bool): update the name (using automatic name generation) based on new settings.
            **kwargs: set Collector attributes.
        """
        self.b = b
        self.data_collector = data_collector
        self.plotter = plotter
        self.nick = nick
        self.backend = backend
        self.collector_name = collector_name or "base"

        # Arguments given as default arguments in the subclass have "low" priority (below elevated arguments at least):
        self._data_collector_arguments = self._default_data_collector_arguments.copy()
        self._plotter_arguments = self._default_plotter_arguments.copy()
        self._update_arguments(data_collector_arguments, plotter_arguments)

        # Elevated arguments have preference above the data_collector and plotter argument dicts:
        self._parse_elevated_arguments(
            elevated_data_collector_arguments, elevated_plotter_arguments
        )

        self._set_attributes(**kwargs)

        self._set_plotly_templates()

        if nick is None:
            self.nick = b.name

        if name is None:
            name = self.generate_name()
        self.name = name

        if autorun:
            self.update(update_name=False)

    @staticmethod
    def _set_plotly_templates():
        pio.templates.default = PLOTLY_BASE_TEMPLATE
        pio.templates["fig_pr_cell"] = fig_pr_cell_template
        pio.templates["fig_pr_cycle"] = fig_pr_cycle_template

    @property
    def data_collector_arguments(self):
        return self._data_collector_arguments

    @data_collector_arguments.setter
    def data_collector_arguments(self, argument_dict: dict):
        if argument_dict is not None:
            self._data_collector_arguments = {
                **self._data_collector_arguments,
                **argument_dict,
            }

    @property
    def plotter_arguments(self):
        return self._plotter_arguments

    @plotter_arguments.setter
    def plotter_arguments(self, argument_dict: dict):
        if argument_dict is not None:
            self._plotter_arguments = {**self._plotter_arguments, **argument_dict}

    def __str__(self):
        class_name = self.__class__.__name__

        txt = f"{class_name}\n{len(class_name) * '='}\n\n"
        txt += "Attributes:\n"
        txt += "-----------\n"
        txt += f" -collector_name: {self.collector_name}\n"
        txt += f" -autorun: {self.autorun}\n"
        txt += f" -name: {self.name}\n"
        txt += f" -nick: {self.nick}\n"
        txt += f" -csv_include_index: {self.csv_include_index}\n"
        txt += f" -csv_layout: {self.csv_layout}\n"
        txt += f" -sep: {self.sep}\n"
        txt += f" -toolbar: {self.toolbar}\n"
        txt += f" -figure_directory: {self.figure_directory}\n"
        txt += f" -data_directory: {self.data_directory}\n"
        txt += f" -batch-instance: {self.b.name}\n"
        txt += f" -data_collector_arguments: {self.data_collector_arguments}\n"
        txt += f" -plotter_arguments: {self.plotter_arguments}\n"

        txt += "\nfigure:\n"
        txt += ".......\n"
        txt += f"{self.figure}\n"

        txt += "\ndata:\n"
        txt += ".....\n"
        txt += f"{self.data}\n"

        txt += "\nData collector:\n"
        txt += "---------------\n"
        data_name = self.data_collector.__name__
        data_sig = inspect.signature(self.data_collector)
        data_doc = inspect.getdoc(self.data_collector)
        txt = f"{txt}{data_name}"
        txt = f"{txt}{data_sig}\n"
        txt = f"{txt}\n{data_doc}\n"

        txt += "\nPlotter:\n"
        txt += "--------\n"
        plotter_name = self.plotter.__name__
        plotter_sig = inspect.signature(self.plotter)
        plotter_doc = inspect.getdoc(self.plotter)
        txt = f"{txt}{plotter_name}"
        txt = f"{txt}{plotter_sig}\n"
        txt = f"{txt}\n{plotter_doc}\n"

        return txt

    def _repr_html_(self):
        class_name = self.__class__.__name__
        txt = f"<h2>{class_name}</h2> id={hex(id(self))}"
        _txt = self.__str__().replace("\n", "<br>")
        txt += f"<blockquote><code>{_txt}</></blockquote>"

        return txt

    def _set_attributes(self, **kwargs):
        self.sep = kwargs.get("sep", ";")
        self.csv_include_index = kwargs.get("csv_include_index", True)
        self.csv_layout = kwargs.get("csv_layout", "long")
        self.dpi = kwargs.get("dpi", 200)
        self.toolbar = kwargs.get("toolbar", True)

    def generate_name(self):
        names = ["collector", self.collector_name]
        if self.nick:
            names.insert(0, self.nick)
        name = "_".join(names)
        return name

    def _parse_elevated_arguments(
        self, data_collector_arguments: dict = None, plotter_arguments: dict = None
    ):
        if data_collector_arguments is not None:

            logging.info(f"Updating elevated arguments")
            elevated_data_collector_arguments = {}
            for k, v in data_collector_arguments.items():
                if v is not None:
                    elevated_data_collector_arguments[k] = v
            self._update_arguments(
                elevated_data_collector_arguments, None, set_as_defaults=True
            )

        if plotter_arguments is not None:

            logging.info(f"Updating elevated arguments")
            elevated_plotter_arguments = {}
            for k, v in plotter_arguments.items():
                if v is not None:
                    elevated_plotter_arguments[k] = v

            self._update_arguments(
                None, elevated_plotter_arguments, set_as_defaults=True
            )

    def _update_arguments(
        self,
        data_collector_arguments: dict = None,
        plotter_arguments: dict = None,
        set_as_defaults=False,
    ):
        self.data_collector_arguments = data_collector_arguments
        self.plotter_arguments = plotter_arguments
        logging.info(f"**data_collector_arguments: {self.data_collector_arguments}")
        logging.info(f"**plotter_arguments: {self.plotter_arguments}")

        # setting defaults also (py3.6 compatible):
        if set_as_defaults:
            logging.info("updating defaults for current instance")
            if data_collector_arguments is not None:
                self._default_data_collector_arguments = {
                    **self._default_data_collector_arguments,
                    **data_collector_arguments,
                }
            if plotter_arguments is not None:
                self._default_plotter_arguments = {
                    **self._default_plotter_arguments,
                    **plotter_arguments,
                }

    def reset_arguments(
        self, data_collector_arguments: dict = None, plotter_arguments: dict = None
    ):
        """Reset the arguments to the defaults.
        Args:
            data_collector_arguments (dict): optional additional keyword arguments for the data collector.
            plotter_arguments (dict): optional additional keyword arguments for the plotter.
        """
        self._data_collector_arguments = self._default_data_collector_arguments.copy()
        self._plotter_arguments = self._default_plotter_arguments.copy()
        self._update_arguments(data_collector_arguments, plotter_arguments)

    def update(
        self,
        data_collector_arguments: dict = None,
        plotter_arguments: dict = None,
        reset: bool = False,
        update_data: bool = False,
        update_name: bool = False,
        update_plot: bool = True,
    ):
        """Update both the collected data and the plot(s).
        Args:
            data_collector_arguments (dict): keyword arguments sent to the data collector.
            plotter_arguments (dict): keyword arguments sent to the plotter.
            reset (bool): reset the arguments first.
            update_data (bool): update the data before updating the plot even if data has been collected before.
            update_name (bool): update the name (using automatic name generation) based on new settings.
            update_plot (bool): update the plot.
        """
        if reset:
            self.reset_arguments(data_collector_arguments, plotter_arguments)
        else:
            self._update_arguments(data_collector_arguments, plotter_arguments)
        if update_data or self.data is None:
            try:
                self.data = self.data_collector(self.b, **self.data_collector_arguments)
            except TypeError as e:
                print("Type error:", e)
                print("Registered data_collector_arguments:")
                pprint(self.data_collector_arguments)
                print("Hint: fix it and then re-run using reset=True")
                return
        if update_plot:
            try:
                self.figure = self.plotter(
                    self.data, journal=self.b.journal, **self.plotter_arguments
                )
            except TypeError as e:
                print("Type error:", e)
                print("Registered plotter_arguments:")
                pprint(self.plotter_arguments)
                print("Hint: fix it and then re-run using reset=True")
                return

        if update_name:
            self.name = self.generate_name()

    def _figure_valid(self):
        # TODO: create a decorator
        if self.figure is None:
            print("No figure to show!")
            return False
        return True

    def show(self, **kwargs):
        if not self._figure_valid():
            return

        print(f"figure name: {self.name}")
        if kwargs:
            self._update_arguments(plotter_arguments=kwargs)
            self.figure = self.plotter(
                self.data, journal=self.b.journal, **self.plotter_arguments
            )
        return self.figure

    def redraw(self, **kwargs):
        print("EXPERIMENTAL FEATURE! THIS MIGHT NOT WORK PROPERLY YET")
        if not self._figure_valid():
            return

        print(f"figure name: {self.name}")
        return self.figure

    def render(self):
        print("Not implemented yet!")

    def preprocess_data_for_csv(self):
        print(f"the data layout {self.csv_layout} is not supported yet!")
        return self.data

    def to_csv(self, serial_number=None):
        filename = self._output_path(serial_number)
        filename = filename.with_suffix(".csv")
        if self.csv_layout != "long":
            data = self.preprocess_data_for_csv()
        else:
            data = self.data

        data.to_csv(
            filename,
            sep=self.sep,
            index=self.csv_include_index,
        )
        print(f"saved csv file: {filename}")

    def to_image_files(self, serial_number=None):
        if not self._figure_valid():
            return
        filename_pre = self._output_path(serial_number)
        filename_png = filename_pre.with_suffix(".png")
        filename_svg = filename_pre.with_suffix(".svg")
        filename_json = filename_pre.with_suffix(".json")
        print(f"TODO: implement saving {filename_png}")
        print(f"TODO: implement saving {filename_svg}")
        print(f"TODO: implement saving {filename_json}")

    def save(self, serial_number=None):
        self.to_csv(serial_number=serial_number)

        if self._figure_valid():
            self.to_image_files(serial_number=serial_number)

    def _output_path(self, serial_number=None):
        d = Path(self.figure_directory)
        n = self.name
        if serial_number is not None:
            n = f"{n}_{serial_number:03}"
        f = d / n
        return f


class BatchSummaryCollector(BatchCollector):
    # Three main levels of arguments to the plotter and collector funcs is available:
    #  - through dictionaries (`data_collector_arguments`, `plotter_arguments`) to init
    #  - given as defaults in the subclass (`_default_data_collector_arguments`, `_default_plotter_arguments`)
    #  - as elevated arguments (i.e. arguments normally given in the dictionaries elevated
    #    to their own keyword parameters)

    _default_data_collector_arguments = {
        "columns": ["charge_capacity_gravimetric"],
    }

    def __init__(
        self,
        b,
        max_cycle: int = None,
        rate=None,
        on=None,
        columns=None,
        column_names=None,
        normalize_capacity_on=None,
        scale_by=None,
        nom_cap=None,
        normalize_cycles=None,
        group_it=None,
        rate_std=None,
        rate_column=None,
        inverse=None,
        inverted: bool = None,
        key_index_bounds=None,
        backend: str = None,
        title: str = None,
        points: bool = None,
        line: bool = None,
        width: int = None,
        height: int = None,
        legend_title: str = None,
        marker_size: int = None,
        cmap=None,
        spread: bool = None,
        *args,
        **kwargs,
    ):
        """Collects and shows summaries.

        Elevated data collector args:
            max_cycle (int): drop all cycles above this value.
            rate (float): filter on rate (C-rate)
            on (str or list of str): only select cycles if based on the rate of this step-type (e.g. on="charge").
            columns (list): selected column(s) (using cellpy attribute name)
                [defaults to "charge_capacity_gravimetric"]
            column_names (list): selected column(s) (using exact column name)
            normalize_capacity_on (list): list of cycle numbers that will be used for setting the basis of the
                normalization (typically the first few cycles after formation)
            scale_by (float or str): scale the normalized data with nominal capacity if "nom_cap",
                or given value (defaults to one).
            nom_cap (float): nominal capacity of the cell
            normalize_cycles (bool): perform a normalization of the cycle numbers (also called equivalent cycle index)
            group_it (bool): if True, average pr group.
            rate_std (float): allow for this inaccuracy when selecting cycles based on rate
            rate_column (str): name of the column containing the C-rates.
            inverse (bool): select steps that do not have the given C-rate.
            inverted (bool): select cycles that do not have the steps filtered by given C-rate.
            key_index_bounds (list): used when creating a common label for the cells by splitting and combining from
                key_index_bound[0] to key_index_bound[1].

        Elevated plotter args:
            backend (str): backend used (defaults to Bokeh)
            points (bool): plot points if True
            line (bool): plot line if True
            width: width of plot
            height: height of plot
            legend_title: title to put over the legend
            marker_size: size of the markers used
            cmap: color-map to use
            spread (bool): plot error-bands instead of error-bars if True
        """

        elevated_data_collector_arguments = dict(
            max_cycle=max_cycle,
            rate=rate,
            on=on,
            columns=columns,
            column_names=column_names,
            normalize_capacity_on=normalize_capacity_on,
            scale_by=scale_by,
            nom_cap=nom_cap,
            normalize_cycles=normalize_cycles,
            group_it=group_it,
            rate_std=rate_std,
            rate_column=rate_column,
            inverse=inverse,
            inverted=inverted,
            key_index_bounds=key_index_bounds,
        )

        elevated_plotter_arguments = {
            "backend": backend,
            "title": title,
            "points": points,
            "line": line,
            "width": width,
            "height": height,
            "legend_title": legend_title,
            "marker_size": marker_size,
            "cmap": cmap,
            "spread": spread,
        }

        super().__init__(
            b,
            plotter=plot_concatenated,
            data_collector=concatenate_summaries,
            collector_name="summary",
            elevated_data_collector_arguments=elevated_data_collector_arguments,
            elevated_plotter_arguments=elevated_plotter_arguments,
            *args,
            **kwargs,
        )

    def generate_name(self):
        names = ["collected_summaries"]
        cols = self.data_collector_arguments.get("columns")
        grouped = self.data_collector_arguments.get("group_it")
        equivalent_cycles = self.data_collector_arguments.get("normalize_cycles")
        normalized_cap = self.data_collector_arguments.get("normalize_capacity_on", [])
        if self.nick:
            names.insert(0, self.nick)
        if cols:
            names.extend(cols)
        if grouped:
            names.append("average")
        if equivalent_cycles:
            names.append("equivalents")
        if len(normalized_cap):
            names.append("norm")

        name = "_".join(names)
        return name


class BatchICACollector(BatchCollector):

    def __init__(self, b, plot_type="fig_pr_cell", *args, **kwargs):
        """Create a collection of ica (dQ/dV) plots."""

        self.plot_type = plot_type
        self._default_plotter_arguments["method"] = plot_type
        super().__init__(
            b,
            plotter=ica_plotter,
            data_collector=ica_collector,
            collector_name="ica",
            *args,
            **kwargs,
        )

    def generate_name(self):
        names = ["collected_ica"]

        pm = self.plotter_arguments.get("method")
        if pm == "fig_pr_cell":
            names.append("pr_cell")
        elif pm == "fig_pr_cycle":
            names.append("pr_cyc")
        elif pm == "film":
            names.append("film")

        if self.nick:
            names.insert(0, self.nick)

        name = "_".join(names)
        return name


class BatchCyclesCollector(BatchCollector):
    _default_data_collector_arguments = {
        "interpolated": True,
        "number_of_points": 100,
        "max_cycle": 50,
        "abort_on_missing": False,
        "method": "back-and-forth",
    }

    def __init__(
        self,
        b,
        plot_type="fig_pr_cell",
        collector_type="back-and-forth",
        cycles=None,
        max_cycle=None,
        label_mapper=None,
        backend=None,
        cycles_to_plot=None,
        width=None,
        palette=None,
        show_legend=None,
        legend_position=None,
        fig_title=None,
        cols=None,
        *args,
        **kwargs,
    ):
        """Create a collection of capacity plots.

        Args:
            b:
            plot_type (str): either 'fig_pr_cell' or 'fig_pr_cycle'
            collector_type (str): how the curves are given
                "back-and-forth" - standard back and forth; discharge
                    (or charge) reversed from where charge (or discharge) ends.
                "forth" - discharge (or charge) continues along x-axis.
                "forth-and-forth" - discharge (or charge) also starts at 0
            data_collector_arguments (dict) - arguments transferred to the plotter
            plotter_arguments (dict) - arguments transferred to the plotter

        Elevated data collector args:
            cycles (int): drop all cycles above this value.
            max_cycle (float): filter on rate (C-rate)
            label_mapper (str or list of str): only select cycles if based on the rate of this step-type (e.g. on="charge").

        Elevated plotter args:
            backend (str): backend used (defaults to Bokeh)
            cycles_to_plot (int): plot points if True
            width (float): width of plot
            legend_position (str): position of the legend
            show_legend (bool): set to False if you don't want to show legend
            fig_title (str): title (will be put above the figure)
            palette (str): color-map to use
            cols (int): number of columns
        """

        elevated_data_collector_arguments = dict(
            cycles=cycles,
            max_cycle=max_cycle,
            label_mapper=label_mapper,
        )
        elevated_plotter_arguments = dict(
            backend=backend,
            cycles_to_plot=cycles_to_plot,
            width=width,
            palette=palette,
            legend_position=legend_position,
            show_legend=show_legend,
            fig_title=fig_title,
            cols=cols,
        )

        # internal attribute to keep track of plot type:
        self.plot_type = plot_type
        self._max_letters_in_cell_names = max(len(x) for x in b.cell_names)
        self._default_data_collector_arguments["method"] = collector_type
        self._default_plotter_arguments["method"] = plot_type

        super().__init__(
            b,
            plotter=cycles_plotter,
            data_collector=cycles_collector,
            collector_name="cycles",
            elevated_data_collector_arguments=elevated_data_collector_arguments,
            elevated_plotter_arguments=elevated_plotter_arguments,
            *args,
            **kwargs,
        )

    def _dynamic_update_template_parameter(self, hv_opt, backend, *args, **kwargs):
        k = hv_opt.key
        if k == "NdLayout" and backend == "matplotlib":
            if self.plot_type != "fig_pr_cycle":
                hv_opt.kwargs["fig_inches"] = self._max_letters_in_cell_names * 0.14
        return hv_opt

    def generate_name(self):
        names = ["collected_cycles"]

        if self.data_collector_arguments.get("interpolated"):
            names.append("intp")
            if n := self.data_collector_arguments.get("number_of_points"):
                names.append(f"p{n}")
        cm = self.data_collector_arguments.get("method")
        if cm.startswith("b"):
            names.append("bf")
        else:
            names.append("ff")

        pm = self.plotter_arguments.get("method")
        if pm == "fig_pr_cell":
            names.append("pr_cell")
        elif pm == "fig_pr_cycle":
            names.append("pr_cyc")

        if self.nick:
            names.insert(0, self.nick)

        name = "_".join(names)
        return name


def pick_named_cell(b, label_mapper=None):
    """generator that picks a cell from the batch object, yields its label and the cell itself.

    Args:
        b (cellpy.batch object): your batch object
        label_mapper (callable or dict): function (or dict) that changes the cell names.
            The dictionary must have the cell labels as given in the `journal.pages` index and new label as values.
            Similarly, if it is a function it takes the cell label as input and returns the new label.
            Remark! No check are performed to ensure that the new cell labels are unique.

    Yields:
        label, group, subgroup, cell

    Example:
        def my_mapper(n):
            return "_".join(n.split("_")[1:-1])

        # outputs "nnn_x" etc., if cell-names are of the form "date_nnn_x_y":
        for label, group, subgroup, cell in pick_named_cell(b, label_mapper=my_mapper):
            print(label)
    """

    cell_names = b.cell_names
    for n in cell_names:
        group = b.pages.loc[n, "group"]
        sub_group = b.pages.loc[n, "sub_group"]

        if label_mapper is not None:
            try:
                if isinstance(label_mapper, dict):
                    label = label_mapper[n]
                else:
                    label = label_mapper(n)
            except Exception as e:
                logging.info(f"label_mapper-error: could not rename cell {n}")
                logging.debug(f"caught exception: {e}")
                label = n
        else:
            try:
                label = b.pages.loc[n, "label"]
            except Exception as e:
                logging.info(f"lookup in pages failed: could not rename cell {n}")
                logging.debug(f"caught exception: {e}")
                label = n

        logging.info(f"renaming {n} -> {label} (group={group}, subgroup={sub_group})")
        yield label, group, sub_group, b.experiment.data[n]


def cycles_collector(
    b,
    cycles=None,
    interpolated=True,
    number_of_points=100,
    max_cycle=50,
    abort_on_missing=False,
    method="back-and-forth",
    label_mapper=None,
):
    if cycles is None:
        cycles = list(range(1, max_cycle + 1))
    all_curves = []
    keys = []
    for n, g, sg, c in pick_named_cell(b, label_mapper):
        curves = c.get_cap(
            cycle=cycles,
            label_cycle_number=True,
            interpolated=interpolated,
            number_of_points=number_of_points,
            method=method,
        )
        logging.debug(f"processing {n} (session name: {c.session_name})")
        if not curves.empty:
            curves = curves.assign(group=g, sub_group=sg)
            all_curves.append(curves)
            keys.append(n)
        else:
            if abort_on_missing:
                raise ValueError(f"{n} is empty - aborting!")
            logging.critical(f"[{n} (session name: {c.session_name}) empty]")
    collected_curves = pd.concat(
        all_curves, keys=keys, axis=0, names=["cell", "point"]
    ).reset_index(level="cell")
    return collected_curves


def ica_collector(
    b,
    cycles=None,
    voltage_resolution=0.005,
    max_cycle=50,
    abort_on_missing=False,
    label_direction=True,
    number_of_points=None,
    label_mapper=None,
    **kwargs,
):
    if cycles is None:
        cycles = list(range(1, max_cycle + 1))
    all_curves = []
    keys = []
    for n, g, sg, c in pick_named_cell(b, label_mapper):
        curves = ica.dqdv_frames(
            c,
            cycle=cycles,
            voltage_resolution=voltage_resolution,
            label_direction=label_direction,
            number_of_points=number_of_points,
            **kwargs,
        )
        logging.debug(f"processing {n} (session name: {c.session_name})")
        if not curves.empty:
            curves = curves.assign(group=g, sub_group=sg)
            all_curves.append(curves)
            keys.append(n)
        else:
            if abort_on_missing:
                raise ValueError(f"{n} is empty - aborting!")
            logging.critical(f"[{n} (session name: {c.session_name}) empty]")
    collected_curves = pd.concat(
        all_curves, keys=keys, axis=0, names=["cell", "point"]
    ).reset_index(level="cell")
    return collected_curves


def cycles_plotter(collected_curves, backend="plotly", method="fig_pr_cell", set_sub_fig_size=True, **kwargs):
    """Plot charge-discharge curves.

    Args:
        collected_curves(pd.DataFrame): collected data in long format.
        backend (str): what backend to use.
        method (str): 'fig_pr_cell' or 'fig_pr_cycle'.
        set_sub_fig_size (bool): width and height given for sub-plots and not the whole layout.

        **kwargs: consumed first in current function, rest sent to backend in sequence_plotter.

    Returns:
        styled figure object
    """

    logging.debug("picking kwargs for current level - rest goes to sequence_plotter")
    title = kwargs.pop("title", "Charge-Discharge Curves")
    width = kwargs.pop("width", 300)
    height = kwargs.pop("height", 300)
    palette = kwargs.pop("palette", None)
    palette_range = kwargs.pop("palette_range", None)
    legend_position = kwargs.pop("legend_position", None)
    legend_title = kwargs.pop("legend_title", None)
    show_legend = kwargs.pop("show_legend", None)
    cols = kwargs.pop("cols", 3)

    journal = kwargs.pop("journal", None)  # not used yet

    if legend_title is None:
        if method == "fig_pr_cell":
            legend_title = "Cell"
        else:
            legend_title = "Cycle"

    fig = sequence_plotter(
        collected_curves,
        x="capacity",
        y="voltage",
        z="cycle",
        g="cell",
        backend=backend,
        method=method,
        cols=cols,
        **kwargs,
    )

    no_cols = cols
    if method == "fig_pr_cell":
        number_of_figs = len(collected_curves["cell"].unique())
    else:
        number_of_figs = len(collected_curves["cycle"].unique())

    no_rows = math.ceil(number_of_figs / no_cols)

    # move this to separate function(s):
    if backend == "plotly":
        template = f"{PLOTLY_BASE_TEMPLATE}+{method}"

        if set_sub_fig_size:
            legend_size = 200
            title_size = 10
            height = no_rows * height + title_size
            width = no_cols * width
            if show_legend is not False:
                width += legend_size

            width = min(width, MAX_WIDTH)

        fig.update_layout(legend=dict(title=legend_title))

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

    return fig


def remove_markers(trace):
    trace.update(marker=None, mode="lines")
    return trace


def legend_replacer(trace, df, group_legends=True):
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
        trace.update(name=cell_label, legendgroup=cell_label,
                     hovertemplate=trace.hovertemplate.replace("subgroup", "cell"))
    else:
        trace.update(name=cell_label, hovertemplate=trace.hovertemplate.replace("subgroup", "cell"))


def sequence_plotter(
    collected_curves: pd.DataFrame,
    x: str = "capacity",
    y: str = "voltage",
    z: str = "cycle",
    g: str = "cell",
    group: str = "group",
    subgroup: str = "sub_group",
    x_label: str = "Capacity",
    x_unit: str = "mAh/g",
    y_label: str = "Voltage",
    y_unit: str = "V",
    method: str = "fig_pr_cell",
    markers: bool = True,
    group_cells: bool = True,
    group_legend_muting: bool = True,
    backend: str = "ploty",
    cycles: list = None,
    cols: int = 3,
    palette_discrete: str = None,
    palette_continuous: str = "Viridis",

    **kwargs,
) -> Any:
    """create a plot made up of sequences of data (voltage curves, dQ/dV, etc).

    This method contains the "common" operations done for all the sequence plots,
    currently supporting filtering out the specific cycles, selecting either
    dividing into subplots by cell or by cycle, and creating the (most basic) figure object.

    Args:
        collected_curves (pd.DataFrame): collected data in long format.
        x: column name for x-values.
        y: column name for y-values.
        z: if method is 'fig_pr_cell', column name for color (legend), else for subplot.
        g: if method is 'fig_pr_cell', column name for subplot, else for color.
        group: str = "group",
        subgroup: str = "sub_group",
        x_label: str = "",
        x_unit:
        y_label:
        y_unit:
        method: 'fig_pr_cell' or 'fig_pr_cycle'.
        markers: set to False if you don't want markers.
        group_cells:
        group_legend_muting:
        backend: what backend to use.
        cycles: what cycles to include in the plot.
        palette_discrete:
        palette_continuous:
        cols: number of columns for layout.

        **kwargs: sent to backend (if `backend == "plotly"`, it will be
            sent to `plotly.express` etc.)

    Returns:
        figure object
    """
    logging.debug("running sequence plotter")

    for k in kwargs:
        logging.debug(f"keyword argument sent to the backend: {k}")

    curves = None
    labels = {
        f"{x}": f"{x_label} ({x_unit})",
        f"{y}": f"{y_label} ({y_unit})",
    }
    plotly_arguments = dict(x=x, y=y, labels=labels, facet_col_wrap=cols)
    matplotlib_arguments = dict()

    if method == "fig_pr_cell":
        group_cells = False
        plotly_arguments["markers"] = False  # refusing to use markers for this option in plotly
        plotly_arguments["color"] = z
        plotly_arguments["facet_col"] = g
        if cycles is not None:
            curves = collected_curves.loc[collected_curves.cycle.isin(cycles), :]
        else:
            curves = collected_curves
        logging.debug(f"filtered_curves:\n{curves}")

    elif method == "fig_pr_cycle":
        z, g = g, z
        plotly_arguments["facet_col"] = g

        if cycles is None:
            unique_cycles = list(collected_curves.cycle.unique())
            if len(unique_cycles) > 10:
                cycles = [1, 10, 20]

        if cycles is not None:
            curves = collected_curves.loc[collected_curves.cycle.isin(cycles), :]
        else:
            curves = collected_curves

        if group_cells:
            plotly_arguments["color"] = group
            plotly_arguments["symbol"] = subgroup
        else:
            plotly_arguments["markers"] = markers
            plotly_arguments["color"] = z

    if backend == "plotly":

        if method == "fig_pr_cell":
            kwargs["color_discrete_sequence"] = getattr(px.colors.sequential, palette_continuous)
        else:
            if palette_discrete is not None:
                logging.debug(f"palette_discrete is not implemented yet ({palette_discrete})")

        fig = px.line(
            curves,
            **plotly_arguments,
            **kwargs,
        )

        if group_cells:
            try:
                fig.for_each_trace(functools.partial(legend_replacer, df=curves, group_legends=group_legend_muting))
                if markers is not True:
                    fig.for_each_trace(remove_markers)
            except Exception as e:
                print("failed")
                print(e)

        return fig

    elif backend == "matplotlib":
        print(f"{backend} not implemented yet")

    elif backend == "bokeh":
        print(f"{backend} not implemented yet")


def ica_plotter(
    collected_curves,
    journal=None,
    palette="Blues",
    palette_range=(0.2, 1.0),
    method="fig_pr_cell",
    backend="plotly",
    cycles_to_plot=None,
    cols=1,
    width=None,
    height=None,
    xlim_charge=(None, None),
    xlim_discharge=(None, None),
    **kwargs,
):
    if method == "film":
        if backend == "matplotlib":
            print("SORRY, PLOTTING FILM WITH MATPLOTLIB IS NOT IMPLEMENTED YET")
            return

        return ica_plotter_film_bokeh(
            collected_curves,
            journal=journal,
            palette=palette,
            backend="bokeh",
            cycles=cycles_to_plot,
            xlim_charge=xlim_charge,
            xlim_discharge=xlim_discharge,
            width=width,
            height=height,
            **kwargs,
        )
    else:
        return sequence_plotter(
            collected_curves,
            x="voltage",
            y="dq",
            z="cycle",
            g="cell",
            journal=journal,
            palette=palette,
            palette_range=palette_range,
            method=method,
            backend=backend,
            cycles=cycles_to_plot,
            cols=cols,
            width=width,
        )


def ica_plotter_film_bokeh(*args, **kwargs):
    print("running ica_plotter_film_bokeh")
    print(f"args: {args}")
    print(f"kwargs: {kwargs}")
