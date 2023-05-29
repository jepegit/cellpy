"""Collectors are used for simplifying plotting and exporting batch objects."""

import functools
import inspect
import logging
import math
from pprint import pprint
from pathlib import Path
import textwrap
from typing import Any
import time
from itertools import count
from multiprocessing import Process

import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import numpy as np

import cellpy
from cellpy.readers.core import group_by_interpolate
from cellpy.utils.batch import Batch
from cellpy.utils.helpers import concatenate_summaries
from cellpy.utils.plotutils import plot_concatenated
from cellpy.utils import ica

DEFAULT_CYCLES = [1, 10, 20]

CELLPY_MINIMUM_VERSION = "1.0.0"
PLOTLY_BASE_TEMPLATE = "seaborn"
IMAGE_TO_FILE_TIMEOUT = 30

px_template_all_axis_shown = dict(
    xaxis=dict(
        linecolor="rgb(36,36,36)",
        mirror=True,
        showline=True,
        zeroline=False,
        title={"standoff": 15},
    ),
    yaxis=dict(
        linecolor="rgb(36,36,36)",
        mirror=True,
        showline=True,
        zeroline=False,
        title={"standoff": 15},
    ),
)

fig_pr_cell_template = go.layout.Template(
    # layout=px_template_all_axis_shown
)

fig_pr_cycle_template = go.layout.Template(
    # layout=px_template_all_axis_shown
)

film_template = go.layout.Template(
    # layout=px_template_all_axis_shown
)

summary_template = go.layout.Template(
    # layout=px_template_all_axis_shown
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
    units: dict = None

    # override default arguments:
    elevated_data_collector_arguments: dict = None
    elevated_plotter_arguments: dict = None

    # defaults (and used also when resetting):
    _default_data_collector_arguments = {}
    _default_plotter_arguments = {}

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

        self.parse_units()

        if autorun:
            self.update(update_name=False)

    @staticmethod
    def _set_plotly_templates():
        pio.templates.default = PLOTLY_BASE_TEMPLATE
        pio.templates["fig_pr_cell"] = fig_pr_cell_template
        pio.templates["fig_pr_cycle"] = fig_pr_cycle_template
        pio.templates["film"] = film_template
        pio.templates["summary"] = summary_template

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

    def _attr_text(self, bullet_start=" - ", sep="\n"):
        txt = f"{bullet_start}collector_name: {self.collector_name}" + sep
        txt += f"{bullet_start}autorun: {self.autorun}" + sep
        txt += f"{bullet_start}name: {self.name}" + sep
        txt += f"{bullet_start}nick: {self.nick}" + sep
        txt += f"{bullet_start}csv_include_index: {self.csv_include_index}" + sep
        txt += f"{bullet_start}csv_layout: {self.csv_layout}" + sep
        txt += f"{bullet_start}sep: {self.sep}" + sep
        txt += f"{bullet_start}backend: {self.backend}" + sep
        txt += f"{bullet_start}toolbar: {self.toolbar}" + sep
        txt += f"{bullet_start}figure_directory: {self.figure_directory}" + sep
        txt += f"{bullet_start}data_directory: {self.data_directory}" + sep
        txt += f"{bullet_start}batch-instance: {self.b.name}" + sep
        txt += (
            f"{bullet_start}data_collector_arguments: {self.data_collector_arguments}"
            + sep
        )
        txt += f"{bullet_start}plotter_arguments: {self.plotter_arguments}" + sep
        return txt

    def _attr_data_collector(self, h1="", h2="", sep="\n"):
        data_name = self.data_collector.__name__
        data_sig = inspect.signature(self.data_collector)
        data_doc = inspect.getdoc(self.data_collector)
        txt = f"{h1}{data_name}"
        txt = f"{txt}{data_sig}{h2}{sep}"
        txt = f"{txt}{sep}{data_doc}{sep}"
        return txt

    def _attr_plotter(self, h1="", h2="", sep="\n"):
        plotter_name = self.plotter.__name__
        plotter_sig = inspect.signature(self.plotter)
        plotter_doc = inspect.getdoc(self.plotter)
        txt = f"{h1}{plotter_name}"
        txt = f"{txt}{plotter_sig}{h2}{sep}"
        txt = f"{txt}{sep}{plotter_doc}{sep}"
        return txt

    def __str__(self):
        class_name = self.__class__.__name__
        txt = f"{class_name}\n{len(class_name) * '='}\n\n"
        txt += "Attributes:\n"
        txt += "-----------\n"
        txt += self._attr_text(sep="\n")

        txt += "\nfigure:\n"
        txt += ".......\n"
        fig_txt = f"{self.figure}"
        if isinstance(fig_txt, str) and len(fig_txt) > 500:
            fig_txt = fig_txt[0:500] + "\n ..."
        txt += f"{fig_txt}\n"

        txt += "\ndata:\n"
        txt += ".....\n"
        txt += f"{self.data}\n"

        txt += "\nData collector:\n"
        txt += "---------------\n"
        txt += self._attr_data_collector(sep="\n")

        txt += "\nPlotter:\n"
        txt += "--------\n"
        txt += self._attr_plotter(sep="\n")
        return txt

    def _repr_html_(self):
        class_name = self.__class__.__name__
        txt = f"<h2>{class_name}</h2> id={hex(id(self))}"
        txt += f"<h3>Attributes:</h3>"
        txt += "<ul>"
        txt += self._attr_text(bullet_start="<li><code>", sep="</code></li>")
        txt += "</ul>"
        txt += f"<h3>Figure:</h3><code>"

        fig_txt = f"{self.figure}"
        if isinstance(fig_txt, str) and len(fig_txt) > 500:
            fig_txt = fig_txt[0:500] + "<br>..."
        txt += f"{fig_txt}<br></code>"

        txt += f"<h3>Data:</h3>"
        if hasattr(self.data, "_repr_html_"):
            txt += self.data._repr_html_()
        else:
            txt += "NONE"
        txt += "<br>"
        txt += f"<h3>Data Collector:</h3><blockquote>"
        txt += self._attr_data_collector(h1="<b>", h2="</b>", sep="<br>")
        txt += f"</blockquote><h3>Plotter:</h3><blockquote>"
        txt += self._attr_plotter(h1="<b>", h2="</b>", sep="<br>")
        txt += "</blockquote>"
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

    def render(self):
        self.figure = self.plotter(
            self.data,
            journal=self.b.journal,
            units=self.units,
            **self.plotter_arguments,
        )

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
        self._check_plotter_arguments()

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

    def _check_plotter_arguments(self):
        if "plot_type" in self.plotter_arguments:
            print(
                "WARNING - using possible difficult option (future versions will fix this)"
            )
            print("*** 'plot_type' TRANSLATED TO 'method'")
            self.plotter_arguments["method"] = self.plotter_arguments.pop("plot_type")

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

    def parse_units(self, **kwargs):
        """Look through your cellpy objects and search for units."""
        b = self.b
        c_units = []
        r_units = []
        c_unit = None
        r_unit = None
        for c in b:
            cu = c.cellpy_units
            if cu != c_unit:
                c_unit = cu
                c_units.append(cu)

            ru = c.raw_units
            if ru != r_unit:
                r_unit = ru
                r_units.append(ru)
        if len(c_units) > 1:
            print("WARNING: non-homogenous units found: cellpy_units")
        if len(r_units) > 1:
            print("WARNING: non-homogenous units found: raw_units")
        raw_units = r_units[0]
        cellpy_units = c_units[0]
        self.units = dict(raw_units=raw_units, cellpy_units=cellpy_units)

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
                self.render()
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
        """Show the figure.

        Note that show returns the `figure` object and  if the `backend` used
        does not provide automatic rendering in the editor / running environment you
        are using, you might have to issue the rendering yourself. For example, if you
        are using `plotly` and running it as a script in a typical command shell,
        you will have to issue `.show()` on the returned `figure` object.

        Args:
            **kwargs: sent to the plotter.

        Returns:
            Figure object
        """
        if not self._figure_valid():
            return

        print(f"figure name: {self.name}")
        if kwargs:
            logging.info(f"updating figure with {kwargs}")
            self._update_arguments(plotter_arguments=kwargs)
            self.render()
        return self.figure

    def preprocess_data_for_csv(self):
        logging.debug(f"the data layout {self.csv_layout} is not supported yet!")
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

    def _image_exporter_plotly(self, filename, timeout=IMAGE_TO_FILE_TIMEOUT, **kwargs):
        p = Process(
            target=self.figure.write_image,
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
            print(f"saved image file: {filename}")

    def to_image_files(self, serial_number=None):
        if not self._figure_valid():
            return
        filename_pre = self._output_path(serial_number)
        filename_png = filename_pre.with_suffix(".png")
        filename_svg = filename_pre.with_suffix(".svg")
        filename_json = filename_pre.with_suffix(".json")

        if self.backend == "plotly":
            self._image_exporter_plotly(filename_png, scale=3.0)
            self._image_exporter_plotly(filename_svg)
            self.figure.write_json(filename_json)
            print(f"saved plotly json file: {filename_json}")
        elif self.backend == "matplotlib":
            print(f"TODO: implement saving {filename_png}")
            print(f"TODO: implement saving {filename_svg}")
            print(f"TODO: implement saving {filename_json}")
        else:
            print(f"TODO: implement saving {filename_png}")
            print(f"TODO: implement saving {filename_svg}")
            print(f"TODO: implement saving {filename_json}")

    def save(self, serial_number=None):
        self.to_csv(serial_number=serial_number)

        if self._figure_valid():
            self.to_image_files(serial_number=serial_number)

    def _output_path(self, serial_number=None):
        d = Path(self.figure_directory)
        if not d.is_dir():
            logging.debug(f"{d} does not exist")
            d = Path().cwd()
            logging.debug(f"using current directory ({d}) instead")
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

        csv_layout = kwargs.pop("csv_layout", "wide")

        super().__init__(
            b,
            plotter=summary_plotter,
            data_collector=summary_collector,
            collector_name="summary",
            elevated_data_collector_arguments=elevated_data_collector_arguments,
            elevated_plotter_arguments=elevated_plotter_arguments,
            csv_layout=csv_layout,
            *args,
            **kwargs,
        )

    def generate_name(self):
        names = ["collected_summaries"]
        cols = self.data_collector_arguments.get("columns")
        grouped = self.data_collector_arguments.get("group_it")
        equivalent_cycles = self.data_collector_arguments.get("normalize_cycles")
        normalized_cap = self.data_collector_arguments.get("normalize_capacity_on", [])

        if isinstance(cols, str):
            cols = [cols]
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

    def preprocess_data_for_csv(self):
        # TODO: check implementation long -> wide method here
        cols = self.data.columns.to_list()
        wide_cols = []
        value_cols = []
        sort_by = []
        if "cycle" in cols:
            index = "cycle"
            cols.remove("cycle")
        else:
            print("Could not find index")
            return self.data

        if "sub_group" in cols:
            cols.remove("sub_group")

        if "group" in cols:
            cols.remove("group")

        for _col in cols:
            if _col in ["cell", "variable"]:
                wide_cols.append(_col)
                if _col == "cell":
                    sort_by.append(_col)
            else:
                value_cols.append(_col)
                if _col == "variable":
                    sort_by.append(_col)
        try:
            logging.debug("pivoting data")
            logging.debug(f"index={index}")
            logging.debug(f"columns={wide_cols}")
            logging.debug(f"values={value_cols}")
            data = pd.pivot(
                self.data, index=index, columns=wide_cols, values=value_cols
            )
        except Exception as e:
            print("Could not make wide:")
            print(e)
            return self.data

        try:
            data = data.sort_index(axis=1, level=sort_by)
        except Exception as e:
            logging.debug("-could not sort columns:")
            logging.debug(e)
        try:
            if len(data.columns.names) == 3:
                data = data.reorder_levels([1, 2, 0], axis=1)
            else:
                data = data.reorder_levels([1, 0], axis=1)
        except Exception as e:
            logging.debug("-could not reorder levels:")
            logging.debug(e)
        return data


class BatchICACollector(BatchCollector):
    def __init__(
        self,
        b,
        plot_type="fig_pr_cell",
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
        group_legend_muting=True,
        *args,
        **kwargs,
    ):
        """Create a collection of ica (dQ/dV) plots."""

        self.plot_type = plot_type
        self._default_plotter_arguments["method"] = plot_type

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
            group_legend_muting=group_legend_muting,
        )

        super().__init__(
            b,
            plotter=ica_plotter,
            data_collector=ica_collector,
            collector_name="ica",
            elevated_data_collector_arguments=elevated_data_collector_arguments,
            elevated_plotter_arguments=elevated_plotter_arguments,
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
        group_legend_muting=True,
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
            group_legend_muting=group_legend_muting,
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


def summary_collector(*args, **kwargs):
    """See concatenate_summaries in helpers (summary_collector runs
    concatenate_summaries with melt=True and mode='collector')"""
    kwargs["melt"] = True
    kwargs["mode"] = "collector"
    return concatenate_summaries(*args, **kwargs)


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
        logging.debug(f"processing {n} (cell name: {c.cell_name})")
        if not curves.empty:
            curves = curves.assign(group=g, sub_group=sg)
            all_curves.append(curves)
            keys.append(n)
        else:
            if abort_on_missing:
                raise ValueError(f"{n} is empty - aborting!")
            logging.critical(f"[{n} (cell name: {c.cell_name}) empty]")
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
        logging.debug(f"processing {n} (cell name: {c.cell_name})")
        if not curves.empty:
            curves = curves.assign(group=g, sub_group=sg)
            all_curves.append(curves)
            keys.append(n)
        else:
            if abort_on_missing:
                raise ValueError(f"{n} is empty - aborting!")
            logging.critical(f"[{n} (cell name: {c.cell_name}) empty]")
    collected_curves = pd.concat(
        all_curves, keys=keys, axis=0, names=["cell", "point"]
    ).reset_index(level="cell")
    return collected_curves


def remove_markers(trace):
    trace.update(marker=None, mode="lines")
    return trace


def _hist_eq(trace):
    z = histogram_equalization(trace.z)
    trace.update(z=z)
    return trace


def y_axis_replacer(ax, label):
    ax.update(title_text=label)
    return ax


def legend_replacer(trace, df, group_legends=True):
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


def sequence_plotter(
    collected_curves: pd.DataFrame,
    x: str = "capacity",
    y: str = "voltage",
    z: str = "cycle",
    g: str = "cell",
    standard_deviation: str = None,
    group: str = "group",
    subgroup: str = "sub_group",
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
        standard_deviation: str = standard deviation column (skipped if None).
        group: str = "group",
        subgroup: str = "sub_group",
        x_label: str = "",
        x_unit:
        y_label:
        y_unit:
        z_label: str = "Cycle"
        z_unit: str = "n."
        y_label_mapper: dict
        nbinsx: int = 100
        histfunc: str = "avg"
        histscale (str) = "abs-log" used for scaling the z-values for 2D array plots (heatmaps and similar).
        direction (str) = "charge", "discharge", or "both".
        direction_col (str) = "direction",
        method: 'fig_pr_cell' or 'fig_pr_cycle'.
        markers: set to True if you want markers.
        group_cells (bool):
        group_legend_muting (bool):
        backend: what backend to use.
        cycles: what cycles to include in the plot.
        palette_discrete:
        palette_continuous:
        palette_range (tuple):
        facetplot (bool): square layout with group horizontally and subgroup vertically.
        cols: number of columns for layout.
        height:
        width:

        **kwargs: sent to backend (if `backend == "plotly"`, it will be
            sent to `plotly.express` etc.)

    Returns:
        figure object
    """
    logging.debug("running sequence plotter")

    for k in kwargs:
        logging.debug(f"keyword argument sent to the backend: {k}")

    curves = None
    seaborn_arguments = dict()

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

    elif method == "summary":
        labels = {
            f"{x}": f"{x_label} ({x_unit})",
        }
        plotly_arguments = dict(x=x, y=y, labels=labels, markers=markers)
        if g == "variable" and len(collected_curves[g].unique()) > 1:
            plotly_arguments["facet_row"] = g
        if standard_deviation:
            plotly_arguments["error_y"] = standard_deviation

    else:
        labels = {
            f"{x}": f"{x_label} ({x_unit})",
            f"{y}": f"{y_label} ({y_unit})",
        }
        plotly_arguments = dict(x=x, y=y, labels=labels, facet_col_wrap=cols)

    if method in ["fig_pr_cell", "film"]:
        group_cells = False
        if method == "fig_pr_cell":
            plotly_arguments["markers"] = markers
            plotly_arguments["color"] = z
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
            # selecting direction
            if direction == "charge":
                curves = curves.query(f"{direction_col} < 0")
            elif direction == "discharge":
                curves = curves.query(f"{direction_col} > 0")
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

    elif method == "summary":
        logging.info("sequence-plotter - summary")
        if cycles is not None:
            curves = collected_curves.loc[collected_curves.cycle.isin(cycles), :]
        else:
            curves = collected_curves

        if group_cells:
            plotly_arguments["color"] = group
            plotly_arguments["symbol"] = subgroup
        else:
            plotly_arguments["color"] = z

    if backend == "plotly":
        if method == "fig_pr_cell":
            start, end = 0.0, 1.0
            if palette_range is not None:
                start, end = palette_range
            unique_cycle_numbers = curves[z].unique()
            number_of_colors = len(unique_cycle_numbers)

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
                    print("failed")
                    print(e)

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
            # print("TRYING...")
            #
            # print(f"{plotly_arguments=}")
            # print(f"{kwargs=}")
            # print(f"{curves.columns}")
            fig = px.line(
                curves,
                **plotly_arguments,
                **kwargs,
            )
            if group_cells:
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
                    print("failed")
                    print(e)

            if y_label_mapper:
                annotations = fig.layout.annotations
                if annotations:
                    try:
                        # might consider a more robust method here - currently
                        # it assumes that the mapper is a list with same order
                        # and length as number of rows
                        for i, (a, la) in enumerate(zip(annotations, y_label_mapper)):
                            row = i + 1
                            fig.for_each_yaxis(
                                functools.partial(y_axis_replacer, label=la),
                                row=row,
                            )
                        fig.update_annotations(text="")
                    except Exception as e:
                        print("failed")
                        print(e)
                else:
                    try:
                        fig.for_each_yaxis(
                            functools.partial(y_axis_replacer, label=y_label_mapper[0]),
                        )
                    except Exception as e:
                        print("failed")
                        print(e)

        else:
            print(f"method '{method}' is not supported by plotly")

        return fig

    elif backend == "matplotlib":
        print(f"{backend} not implemented yet")

    elif backend == "bokeh":
        print(f"{backend} not implemented yet")


def _cycles_plotter(
    collected_curves,
    cycles=None,
    x="capacity",
    y="voltage",
    z="cycle",
    g="cell",
    standard_deviation=None,
    default_title="Charge-Discharge Curves",
    backend="plotly",
    method="fig_pr_cell",
    **kwargs,
):
    """Plot charge-discharge curves.

    Args:
        collected_curves(pd.DataFrame): collected data in long format.
        backend (str): what backend to use.
        method (str): 'fig_pr_cell' or 'fig_pr_cycle'.

        **kwargs: consumed first in current function, rest sent to backend in sequence_plotter.

    Returns:
        styled figure object
    """

    # --- pre-processing ---
    logging.debug("picking kwargs for current level - rest goes to sequence_plotter")
    title = kwargs.pop("title", default_title)
    width = kwargs.pop("width", None)
    height = kwargs.pop("height", None)
    palette = kwargs.pop("palette", None)
    legend_position = kwargs.pop("legend_position", None)
    legend_title = kwargs.pop("legend_title", None)
    show_legend = kwargs.pop("show_legend", None)
    cols = kwargs.pop("cols", 3)
    sub_fig_min_height = kwargs.pop("sub_fig_min_height", 200)

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
            number_of_figs = len(collected_curves["cycle"].unique())
    elif method == "summary":
        number_of_figs = len(collected_curves["variable"].unique())
        sub_fig_min_height = 300
    else:
        number_of_figs = 1

    no_rows = math.ceil(number_of_figs / no_cols)

    if not height:
        height = no_rows * sub_fig_min_height

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
        print("Could not create figure")
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

    return fig


def summary_plotter(collected_curves, cycles_to_plot=None, backend="plotly", **kwargs):
    """Plot summaries (value vs cycle number).

    Assuming data as pandas.DataFrame with either
    1) long format (where variables, for example charge capacity, are in the column "variable") or
    2) mixed long and wide format where the variables are own columns.
    """
    col_headers = collected_curves.columns.to_list()
    possible_id_vars = [
        "cell",
        "cycle",
        "equivalent_cycle",
        "value",
        "mean",
        "std",
        "group",
        "sub_group",
    ]

    id_vars = []
    for n in possible_id_vars:
        if n in col_headers:
            col_headers.remove(n)
            id_vars.append(n)

    if "variable" not in col_headers:
        collected_curves = collected_curves.melt(
            id_vars=id_vars, value_vars=col_headers
        )

    normalize_cycles = True if "equivalent_cycle" in id_vars else False
    group_it = False if "group" in id_vars else True

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
    if units:
        label_mapper[y] = []
        variables = list(collected_curves[g].unique())
        for v in variables:
            # extract units:
            u_sub = None
            if v.endswith("_areal"):
                u_sub = units["cellpy_units"].specific_areal
            elif v.endswith("_gravimetric"):
                u_sub = units["cellpy_units"].specific_gravimetric
            elif v.endswith("_volumetric"):
                u_sub = units["cellpy_units"].specific_volumetric
            u_top = None
            if "_capacity" in v:
                u_top = units["cellpy_units"].charge

            # creating label:
            u = u_top or "Value"
            v = v.split("_")
            if u_sub:
                u_sub = u_sub.replace("**", "")
                u = f"{u}/{u_sub}"
                v = v[:-1]
            v = " ".join(v).title()
            label_mapper[y].append(f"{v} ({u})")

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

    fig.update_yaxes(matches=None, showticklabels=True)
    return fig


def cycles_plotter(
    collected_curves,
    cycles_to_plot=None,
    backend="plotly",
    method="fig_pr_cell",
    **kwargs,
):
    """Plot charge-discharge curves.

    Args:
        collected_curves(pd.DataFrame): collected data in long format.
        cycles_to_plot (list): cycles to plot
        backend (str): what backend to use.
        method (str): 'fig_pr_cell' or 'fig_pr_cycle'.

        **kwargs: consumed first in current function, rest sent to backend in sequence_plotter.

    Returns:
        styled figure object
    """

    if cycles_to_plot is not None:
        unique_cycles = list(collected_curves.cycle.unique())
        if len(unique_cycles) > 50:
            cycles_to_plot = DEFAULT_CYCLES

    return _cycles_plotter(
        collected_curves,
        x="capacity",
        y="voltage",
        z="cycle",
        g="cell",
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
    if method in ["fig_pr_cell", "film"]:
        kwargs["range_y"] = kwargs.pop("range_y", None) or (1, max_cycle)

    return _cycles_plotter(
        collected_curves,
        x="voltage",
        y="dq",
        z="cycle",
        g="cell",
        x_label="Voltage",
        x_unit="V",
        y_label="dQ/dV",
        y_unit="mAh/g/V.",
        default_title=f"Incremental Analysis Plots ({direction.capitalize()})",
        direction=direction,
        backend=backend,
        method=method,
        cycles=cycles_to_plot,
        **kwargs,
    )


def histogram_equalization(image: np.array) -> np.array:
    """Perform histogram equalization on a numpy array.

    # from http://www.janeriksolem.net/histogram-equalization-with-python-and.html
    """
    number_bins = 256
    scale = 100
    image[np.isnan(image)] = 0.0
    image_histogram, bins = np.histogram(image.flatten(), number_bins, density=True)
    cdf = image_histogram.cumsum()  # cumulative distribution function
    cdf = (scale - 1) * cdf / cdf[-1]  # normalize
    # use linear interpolation of cdf to find new pixel values
    image_equalized = np.interp(image.flatten(), bins[:-1], cdf)

    return image_equalized.reshape(image.shape)


if __name__ == "__main__":
    from pathlib import Path
    import os

    import matplotlib.pyplot as plt
    import pandas as pd
    import numpy as np
    import seaborn as sns
    import plotly.express as px

    import cellpy
    from cellpy.utils import batch, helpers, plotutils

    project_dir = Path("../../testdata/batch_project")
    journal = project_dir / "test_project.json"
    assert project_dir.is_dir()
    assert journal.is_file()
    os.chdir(project_dir)
    print(f"cellpy version: {cellpy.__version__}")
    cellpy.log.setup_logging("INFO")

    b = batch.from_journal(journal)
    b.link()
    c = b.cells.first()

    summaries = BatchSummaryCollector(
        b,
        normalize_cycles=False,
        group_it=False,
        autorun=False,
        columns=["charge_capacity_areal", "charge_capacity_gravimetric"],
    )
    summaries.update(update_data=True, update_plot=True)

    # must use .figure.show() when not running in notebook:
    summaries.figure.show()
    summaries.save()

    dqdvs = BatchICACollector(b, plot_type="film")
    dqdvs.figure.show()

    print("Ended OK")
