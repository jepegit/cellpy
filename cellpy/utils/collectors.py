"""Collectors are used for simplifying plotting and exporting batch objects."""

import functools
import inspect
import logging
import math
import pickle as pkl
from pprint import pprint
from pathlib import Path
import textwrap
from typing import Any
import time
from itertools import count
from multiprocessing import Process
import warnings

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import cellpy
from cellpy.readers.core import group_by_interpolate
from cellpy.utils.batch import Batch
from cellpy.utils.helpers import concat_summaries
from cellpy.utils import ica

supported_backends = []

try:
    import plotly
    import plotly.express as px
    import plotly.io as pio
    import plotly.graph_objects as go

    supported_backends.append("plotly")
except ImportError:
    print("WARNING: plotly not installed")

try:
    import seaborn as sns

    supported_backends.append("seaborn")
except ImportError:
    print("WARNING: seaborn not installed")

DEFAULT_CYCLES = [1, 10, 20]
CELLPY_MINIMUM_VERSION = "1.0.0"
PLOTLY_BASE_TEMPLATE = "plotly"
IMAGE_TO_FILE_TIMEOUT = 30
HDF_KEY = "collected_data"
MAX_POINTS_SEABORN_FACET_GRID = 60_000


def load_data(filename):
    """Load data from hdf5 file."""
    try:
        data = pd.read_hdf(filename, key=HDF_KEY)
    except Exception as e:
        print("Could not load data from hdf5 file")
        print(e)
        return None
    return data


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
    try:
        fig = pio.read_json(filename)
    except Exception as e:
        print("Could not load figure from json file")
        print(e)
        return None
    return fig


def generate_output_path(name, directory, serial_number=None):
    d = Path(directory)
    if not d.is_dir():
        logging.debug(f"{d} does not exist")
        d = Path().cwd()
        logging.debug(f"using current directory ({d}) instead")
    if serial_number is not None:
        name = f"{name}_{serial_number:03}"
    f = d / name
    return f


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


def save_plotly_figure(figure, name=None, directory=".", serial_number=None):
    """Save to image files (png, svg, json).

    Notes:
        This method requires ``kaleido`` for the plotly backend.

    Notes:
        Exporting to json is only applicable for the plotly backend.

    Args:
        figure: the plotly figure object.
        name (str): name of the file (without extension).
        directory (str): directory to save the file in.
        serial_number (int): serial number to append to the filename.

    """
    if name is None:
        name = f"{time.strftime('%Y%m%d_%H%M%S')}_figure"
    filename_pre = generate_output_path(name, directory, serial_number)
    filename_png = filename_pre.with_suffix(".png")
    filename_svg = filename_pre.with_suffix(".svg")
    filename_json = filename_pre.with_suffix(".json")

    _image_exporter_plotly(figure, filename_png, scale=3.0)
    _image_exporter_plotly(figure, filename_svg)
    figure.write_json(filename_json)
    print(f" - saved plotly json file: {filename_json}")


if not supported_backends:
    print("WARNING: no supported backends found")
    print("WARNING: install plotly or seaborn to enable plotting")

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

fig_pr_cell_template = go.layout.Template(layout=px_template_all_axis_shown)

fig_pr_cycle_template = go.layout.Template(layout=px_template_all_axis_shown)

film_template = go.layout.Template(layout=px_template_all_axis_shown)

summary_template = go.layout.Template(layout=px_template_all_axis_shown)


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
        experimental: bool = False,
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
        self.experimental = experimental
        if backend != "plotly" and not self.experimental:
            print(f"{backend=}")
            print("WARNING: only plotly is supported at the moment")
            self.backend = "plotly"
        else:
            self.backend = backend
        self.collector_name = collector_name or "base"

        # Arguments given as default arguments in the subclass have "low" priority (below elevated arguments at least):
        self._data_collector_arguments = self._default_data_collector_arguments.copy()
        self._plotter_arguments = self._default_plotter_arguments.copy()
        self._update_arguments(data_collector_arguments, plotter_arguments)

        # Elevated arguments have preference above the data_collector and plotter argument dicts:
        self._parse_elevated_arguments(elevated_data_collector_arguments, elevated_plotter_arguments)

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
        txt += f"{bullet_start}data_collector_arguments: {self.data_collector_arguments}" + sep
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
        """Generate a name for the collection."""

        names = ["collector", self.collector_name]
        if self.nick:
            names.insert(0, self.nick)
        name = "_".join(names)
        return name

    def render(self, **kwargs):
        """Render the figure."""

        kwargs = {**self.plotter_arguments, **kwargs}
        self.figure = self.plotter(
            self.data,
            backend=self.backend,
            journal=self.b.journal,
            units=self.units,
            **kwargs,
        )

    def _parse_elevated_arguments(self, data_collector_arguments: dict = None, plotter_arguments: dict = None):
        if data_collector_arguments is not None:
            logging.info(f"Updating elevated arguments")
            elevated_data_collector_arguments = {}
            for k, v in data_collector_arguments.items():
                if v is not None:
                    elevated_data_collector_arguments[k] = v
            self._update_arguments(elevated_data_collector_arguments, None, set_as_defaults=True)

        if plotter_arguments is not None:
            logging.info(f"Updating elevated arguments")
            elevated_plotter_arguments = {}
            for k, v in plotter_arguments.items():
                if v is not None:
                    elevated_plotter_arguments[k] = v
            self._update_arguments(None, elevated_plotter_arguments, set_as_defaults=True)

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
            print("WARNING - using possible difficult option (future versions will fix this)")
            print("*** 'plot_type' TRANSLATED TO 'method'")
            self.plotter_arguments["method"] = self.plotter_arguments.pop("plot_type")

    def reset_arguments(self, data_collector_arguments: dict = None, plotter_arguments: dict = None):
        """Reset the arguments to the defaults.

        Args:
            data_collector_arguments (dict): optional additional keyword arguments for the data collector.
            plotter_arguments (dict): optional additional keyword arguments for the plotter.

        """
        # warnings.warn("reset_arguments is deprecated", DeprecationWarning)
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

    def collect(self, *args, **kwargs):
        """Collect data."""
        self.data = self.data_collector(self.b, **self.data_collector_arguments, **kwargs)
        self.post_collect(*args, **kwargs)

    def post_collect(self, *args, **kwargs):
        """Perform post-operation after collecting the data"""
        ...

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
                self.collect()
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

        Note:
            If you are working in a Jupyter notebook and using a "matplotlib"-type backend,
            the figure will most likely be shown automatically when the figure is rendered.
            You should not need to use this method in that case, unless you want to
            show the figure one extra time.

        Note:
            The ``show`` method returns the ``figure`` object and  if the ``backend`` used
            does not provide automatic rendering in the editor / running environment you
            are using, you might have to issue the rendering yourself. For example, if you
            are using `plotly` and running it as a script in a typical command shell,
            you will have to issue ``.show()`` on the returned ``figure`` object.

        Args:
            **kwargs: sent to the plotter.

        Returns:
            Figure object
        """

        if not self._figure_valid():
            return

        skip_render_for_seaborn = kwargs.pop("skip_render_for_seaborn", False)

        print(f"figure name: {self.name}")
        if kwargs:
            logging.info(f"updating figure with {kwargs}")
            self._update_arguments(plotter_arguments=kwargs)
            self.render()

        if self.backend == "seaborn":
            if not skip_render_for_seaborn:
                return self.figure.figure
            print("WARNING: skipping rendering for seaborn, assuming it is already rendered during the plotter call")
            print(
                "WARNING: if you want to show the figure, provide `skip_render_for_seaborn=False` as keyword argument"
            )
        else:
            return self.figure

    def preprocess_data_for_csv(self):
        logging.debug(f"the data layout {self.csv_layout} is not supported yet!")
        not_needed_columns = ["group", "sub_group", "group_label", "label", "selected"]
        wide_data = self.data.copy()
        if "mean" in wide_data.columns:
            values = ["mean", "std"]
            columns = ["cell", "variable"]
            wide_data = wide_data.pivot(index=["cycle"], columns=columns, values=values)
            wide_data = wide_data.reorder_levels([2, 1, 0], axis=1)
            wide_data = wide_data.sort_index(axis=1)
        else:
            columns = ["cell"]
            values = [col for col in wide_data.columns if col not in not_needed_columns]
            wide_data = wide_data.pivot(index=["cycle"], columns=columns, values=values)

        return wide_data

    def to_csv(self, serial_number=None):
        """Save to csv file.

        Args:
            serial_number (int): serial number to append to the filename.

        """

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
        print(f" - saved csv file: {filename}")

    def to_hdf5(self, serial_number=None):
        """Save to hdf5 file.

        Args:
            serial_number (int): serial number to append to the filename.

        """

        filename = self._output_path(serial_number)
        filename = filename.with_suffix(".h5")
        data = self.data

        data.to_hdf(filename, key=HDF_KEY, mode="w")
        print(f" - saved hdf5 file: {filename}")

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
            print(f" - saved image file: {filename}")

    def to_image_files(self, serial_number=None):
        """Save to image files (png, svg, json).

        Notes:
            This method requires ``kaleido`` for the plotly backend.

        Notes:
            Exporting to json is only applicable for the plotly backend.

        Args:
            serial_number (int): serial number to append to the filename.

        """

        if not self._figure_valid():
            return
        filename_pre = self._output_path(serial_number)
        filename_png = filename_pre.with_suffix(".png")
        filename_svg = filename_pre.with_suffix(".svg")
        filename_json = filename_pre.with_suffix(".json")
        filename_pickle = filename_pre.with_suffix(".pickle")

        if self.backend == "plotly":
            self._image_exporter_plotly(filename_png, scale=3.0)
            self._image_exporter_plotly(filename_svg)
            self.figure.write_json(filename_json)
            print(f" - saved plotly json file: {filename_json}")
        elif self.backend == "seaborn":
            self.figure.savefig(filename_png, dpi=self.dpi)
            print(f" - saved png file: {filename_png}")
            self.figure.savefig(filename_svg)
            print(f" - saved svg file: {filename_svg}")
            save_matplotlib_figure(self.figure, filename_pickle)
            print(f" - pickled to file: {filename_pickle}")

            # print(f"TODO: implement saving {filename_png}")
            # print(f"TODO: implement saving {filename_svg}")
            # print(f"TODO: implement saving {filename_json}")
        else:
            print(f"TODO: implement saving {filename_png}")
            print(f"TODO: implement saving {filename_svg}")
            print(f"TODO: implement saving {filename_json}")

    def save(self, serial_number=None):
        """Save to csv, hdf5 and image files.

        Args:
            serial_number (int): serial number to append to the filename.

        """

        self.to_csv(serial_number=serial_number)
        self.to_hdf5(serial_number=serial_number)

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
        backend: str = "plotly",
        title: str = None,
        markers: bool = None,
        line: bool = None,
        width: int = None,
        height: int = None,
        legend_title: str = None,
        marker_size: int = None,
        cmap=None,
        spread: bool = None,
        fig_title: str = None,
        only_selected: bool = None,
        *args,
        **kwargs,
    ):
        """Collects and shows summaries.

        Arguments:
            b (cellpy.utils.Batch): the batch object.
            name (str or bool): name used for auto-generating filenames etc.
            autorun (bool): run collector and plotter immediately if True.
            use_templates (bool): also apply template(s) in autorun mode if True.
            backend (str): name of plotting backend to use ("plotly" or "matplotlib").
            data_collector_arguments (dict): keyword arguments sent to the data collector.
            plotter_arguments (dict): keyword arguments sent to the plotter.
            update_name (bool): update the name (using automatic name generation) based on new settings.
            backend (str): what plotting backend to use (currently only 'plotly' is supported)
            max_cycle (int): drop all cycles above this value (elevated data collector argument).
            rate (float): filter on rate (C-rate) (elevated data collector argument).
            on (str or list of str): only select cycles if based on the rate of this step-type (e.g. on="charge").
                (elevated data collector argument).
            columns (list): selected column(s) (using cellpy attribute name). Defaults to "charge_capacity_gravimetric".
                (elevated data collector argument).
            column_names (list): selected column(s) (using exact column name) (elevated data collector argument)
            normalize_capacity_on (list): list of cycle numbers that will be used for setting the basis of the
                normalization (typically the first few cycles after formation) (elevated data collector argument)
            scale_by (float or str): scale the normalized data with nominal capacity if "nom_cap",
                or given value (defaults to one) (elevated data collector argument).
            nom_cap (float): nominal capacity of the cell (elevated data collector argument)
            normalize_cycles (bool): perform a normalization of the cycle numbers (also called equivalent cycle index)
                (elevated data collector argument).
            group_it (bool): if True, average pr group (elevated data collector argument).
            rate_std (float): allow for this inaccuracy when selecting cycles based on rate
                (elevated data collector argument)
            rate_column (str): name of the column containing the C-rates (elevated data collector argument).
            inverse (bool): select steps that do not have the given C-rate (elevated data collector argument).
            inverted (bool): select cycles that do not have the steps filtered by given C-rate
                (elevated data collector argument).
            key_index_bounds (list): used when creating a common label for the cells in a group
                (when group_it is set to True) by splitting and combining from key_index_bound[0] to key_index_bound[1].
                For example, if your cells are called "cell_01_01" and "cell_01_02" and you set
                key_index_bounds=[0, 2], the common label will be "cell_01". Or if they are called
                "20230101_cell_01_01_01" and "20230101_cell_01_01_02" and you set key_index_bounds=[1, 3],
                the common label will be "cell_01_01" (elevated data collector argument).
            only_selected (bool): only process selected cells (elevated data collector argument).
            markers (bool): plot points if True (elevated plotter argument).
            line (bool): plot line if True (elevated plotter argument).
            width: width of plot (elevated plotter argument).
            height: height of plot (elevated plotter argument).
            legend_title: title to put over the legend (elevated plotter argument).
            marker_size: size of the markers used (elevated plotter argument).
            cmap: color-map to use (elevated plotter argument).
            spread (bool): plot error-bands instead of error-bars if True (elevated plotter argument).
            fig_title (str): title of the figure (elevated plotter argument).
        """

        # TODO: include option for error-bands (spread) (https://plotly.com/python/continuous-error-bars/)

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
            only_selected=only_selected,
        )

        elevated_plotter_arguments = {
            "fig_title": fig_title,
            "title": title,
            "markers": markers,
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
            backend=backend,
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
            data = pd.pivot(self.data, index=index, columns=wide_cols, values=value_cols)
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
        rate=None,
        rate_on=None,
        rate_std=None,
        rate_agg=None,
        inverse=False,
        label_mapper=None,
        backend="plotly",
        cycles_to_plot=None,
        width=None,
        palette=None,
        show_legend=None,
        legend_position=None,
        fig_title=None,
        cols=None,
        group_legend_muting=True,
        only_selected: bool = False,
        *args,
        **kwargs,
    ):
        """Create a collection of ica (dQ/dV) plots.

        Args:
            b: cellpy batch object
            plot_type (str): either 'fig_pr_cell' or 'fig_pr_cycle'
            backend (str): what plotting backend to use (currently only 'plotly' is supported)
            cycles (list): select these cycles (elevated data collector argument).
            max_cycle (int): drop all cycles above this value (elevated data collector argument).
            rate (float): filter on rate (C-rate) (elevated data collector argument).
            rate_on (str or list of str): only select cycles if based on the rate of this step-type (e.g. on="charge")
                (elevated data collector argument).
            rate_std (float): allow for this inaccuracy when selecting cycles based on rate
                (elevated data collector argument).
            rate_agg (str): how to aggregate the rate (e.g. "mean", "max", "min", "first", "last")
                (elevated data collector argument).
            inverse (bool): select steps that do not have the given C-rate (elevated data collector argument).
            label_mapper (callable or dict): function (or dict) that changes the cell names
                (elevated data collector argument).
                The dictionary must have the cell labels as given in the `journal.pages` index and new label as values.
                Similarly, if it is a function it takes the cell label as input and returns the new label.
                Remark! No check are performed to ensure that the new cell labels are unique.
            cycles_to_plot (int): plot points if True (elevated plotter argument).
            width (float): width of plot (elevated plotter argument).
            palette (str): color-map to use (elevated plotter argument).
            legend_position (str): position of the legend (elevated plotter argument).
            show_legend (bool): set to False if you don't want to show legend (elevated plotter argument).
            fig_title (str): title (will be put above the figure) (elevated plotter argument).
            cols (int): number of columns (elevated plotter argument).
            group_legend_muting (bool): if True, the legend will be interactive (elevated plotter argument).
            only_selected (bool): only process selected cells (elevated data collector argument).

        """

        self.plot_type = plot_type
        self._default_plotter_arguments["method"] = plot_type

        elevated_data_collector_arguments = dict(
            cycles=cycles,
            max_cycle=max_cycle,
            rate=rate,
            rate_on=rate_on,
            rate_std=rate_std,
            rate_agg=rate_agg,
            inverse=inverse,
            label_mapper=label_mapper,
            only_selected=only_selected,
        )
        elevated_plotter_arguments = dict(
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
            backend=backend,
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
        number_of_points=100,
        rate=None,
        rate_on=None,
        rate_std=None,
        rate_agg=None,
        inverse=False,
        label_mapper=None,
        backend="plotly",
        cycles_to_plot=None,
        width=None,
        palette=None,
        show_legend=None,
        legend_position=None,
        fig_title=None,
        cols=None,
        group_legend_muting=True,
        only_selected: bool = False,
        *args,
        **kwargs,
    ):
        """Create a collection of capacity plots.

        Args:
            b: cellpy batch object
            plot_type (str): either 'fig_pr_cell' or 'fig_pr_cycle'
            backend (str): what plotting backend to use (currently only 'plotly' is supported)
            collector_type (str): how the curves are given

                - "back-and-forth" - standard back and forth; discharge
                  (or charge) reversed from where charge (or discharge) ends.
                - "forth" - discharge (or charge) continues along x-axis.
                - "forth-and-forth" - discharge (or charge) also starts at 0.

            data_collector_arguments (dict) - arguments transferred to the to `CellpyCell.get_cap`.
            plotter_arguments (dict) - arguments transferred to `cycles_plotter`.
            cycles (list): select these cycles (elevated data collector argument).
            max_cycle (int): drop all cycles above this value (elevated data collector argument).
            rate (float): filter on rate (C-rate) (elevated data collector argument).
            rate_on (str or list of str): only select cycles if based on the rate of this step-type (e.g. on="charge")
                (elevated data collector argument).
            rate_std (float): allow for this inaccuracy when selecting cycles based on rate
                (elevated data collector argument).
            rate_agg (str): how to aggregate the rate (e.g. "mean", "max", "min", "first", "last")
                (elevated data collector argument).
            inverse (bool): select steps that do not have the given C-rate (elevated data collector argument).
            label_mapper (callable or dict): function (or dict) that changes the cell names
                (elevated data collector argument).
                The dictionary must have the cell labels as given in the `journal.pages` index and new label as values.
                Similarly, if it is a function it takes the cell label as input and returns the new label.
                Remark! No check are performed to ensure that the new cell labels are unique.
            cycles_to_plot (int): plot only these cycles (elevated plotter argument).
            width (float): width of plot (elevated plotter argument).
            legend_position (str): position of the legend (elevated plotter argument).
            show_legend (bool): set to False if you don't want to show legend (elevated plotter argument).
            fig_title (str): title (will be put above the figure) (elevated plotter argument).
            palette (str): color-map to use (elevated plotter argument).
            cols (int): number of columns (elevated plotter argument).
            only_selected (bool): only process selected cells (elevated data collector argument).
        """

        elevated_data_collector_arguments = dict(
            cycles=cycles,
            max_cycle=max_cycle,
            number_of_points=number_of_points,
            label_mapper=label_mapper,
            rate=rate,
            rate_on=rate_on,
            rate_std=rate_std,
            rate_agg=rate_agg,
            inverse=inverse,
            only_selected=only_selected,
        )
        elevated_plotter_arguments = dict(
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
            backend=backend,
            collector_name="cycles",
            elevated_data_collector_arguments=elevated_data_collector_arguments,
            elevated_plotter_arguments=elevated_plotter_arguments,
            *args,
            **kwargs,
        )

    def post_collect(self, *args, **kwargs):
        """Update the x-unit after collecting the data in case the mode has been set."""

        logging.debug("updating the x-unit")
        if m := self.data_collector_arguments.get("mode"):
            if m == "gravimetric":
                self.plotter_arguments["x_unit"] = (
                    f'{self.units["cellpy_units"].charge}/{self.units["cellpy_units"].gravimetric}'
                )
            elif m == "areal":
                self.plotter_arguments["x_unit"] = (
                    f'{self.units["cellpy_units"].charge}/{self.units["cellpy_units"].areal}'
                )
            elif m == "volumetric":
                self.plotter_arguments["x_unit"] = (
                    f'{self.units["cellpy_units"].charge}/{self.units["cellpy_units"].volumetric}'
                )
            elif m == "absolute":
                self.plotter_arguments["x_unit"] = self.units["cellpy_units"].charge

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
    """Generator that picks a cell from the batch object, yields its label and the cell itself.

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
        logging.debug(f"processing {n} (group={group}, sub_group={sub_group})")
        # putting this check here for backwards compatibility:
        if "selected" in b.pages.columns:
            selected = b.pages.loc[n, "selected"]
        else:
            selected = True

        if label_mapper is not None:
            logging.info(f"renaming {n} using label_mapper")
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

                if label is None:
                    logging.info(f"label from journal.pages: {label} -> using original name ({n})")
                    label = n
            except Exception as e:
                logging.info(f"lookup in pages failed: could not rename cell {n}")
                logging.debug(f"caught exception: {e}")
                label = n

        logging.info(f"renaming {n} -> {label} (group={group}, sub_group={sub_group})")
        yield selected, label, group, sub_group, b.experiment.data[n]


def summary_collector(*args, **kwargs):
    """Collects summaries using cellpy.utils.helpers.concat_summaries."""
    return concat_summaries(*args, **kwargs)


def cycles_collector(
    b,
    cycles=None,
    rate=None,
    rate_on=None,
    rate_std=None,
    rate_agg="first",
    inverse=False,
    interpolated=True,
    number_of_points=100,
    max_cycle=50,
    abort_on_missing=False,
    method="back-and-forth",
    label_mapper=None,
    mode="gravimetric",
    only_selected=False,
):
    """
    Collects cycles from all the cells in the batch object.

    Args:
        b: cellpy batch object
        cycles: list of cycle numbers to collect
        rate: filter on rate (C-rate)
        rate_on: only select cycles if based on the rate of this step-type (e.g. on="charge").
        rate_std: allow for this inaccuracy when selecting cycles based on rate
        rate_agg: how to aggregate the rate (e.g. "mean", "max", "min", "first", "last")
        inverse: select steps that do not have the given C-rate.
        interpolated: if True, interpolate the data
        number_of_points: number of points to interpolate to
        max_cycle: drop all cycles above this value
        abort_on_missing: if True, abort if a cell is empty
        method: how the voltage curves are given (back-and-forth, forth, forth-and-forth)
        label_mapper: function (or dict) that changes the cell names.
        mode (string): 'gravimetric', 'areal', 'volumetric' or 'absolute'.
        only_selected (bool): only process selected cells.

    Returns:
        pd.DataFrame: collected data
    """
    if cycles is None:
        cycles = list(range(1, max_cycle + 1))
    all_curves = []
    keys = []
    for selected, n, g, sg, c in pick_named_cell(b, label_mapper):
        if only_selected and not selected:
            logging.debug(f"skipping {n} (cell name: {c.cell_name})")
            continue
        if rate is not None:
            filtered_cycles = c.get_cycle_numbers(
                rate=rate,
                rate_on=rate_on,
                rate_std=rate_std,
                rate_agg=rate_agg,
                inverse=inverse,
            )
            cycles = list(set(filtered_cycles).intersection(set(cycles)))
        curves = c.get_cap(
            cycle=cycles,
            label_cycle_number=True,
            interpolated=interpolated,
            number_of_points=number_of_points,
            method=method,
            mode=mode,
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
    collected_curves = pd.concat(all_curves, keys=keys, axis=0, names=["cell", "point"]).reset_index(level="cell")
    return collected_curves


def ica_collector(
    b,
    cycles=None,
    rate=None,
    rate_on=None,
    rate_std=None,
    rate_agg="first",
    inverse=False,
    voltage_resolution=0.005,
    max_cycle=50,
    abort_on_missing=False,
    label_direction=True,
    number_of_points=None,
    label_mapper=None,
    only_selected=False,
    **kwargs,
):
    """
    Collects ica (dQ/dV) curves from all the cells in the batch object.

    Args:
        b: cellpy batch object
        cycles: list of cycle numbers to collect
        rate: filter on rate (C-rate)
        rate_on: only select cycles if based on the rate of this step-type (e.g. on="charge").
        rate_std: allow for this inaccuracy when selecting cycles based on rate
        rate_agg: how to aggregate the rate (e.g. "mean", "max", "min", "first", "last")
        inverse: select steps that do not have the given C-rate.
        voltage_resolution: smoothing of the voltage curve
        number_of_points: number of points to interpolate to
        max_cycle: drop all cycles above this value
        abort_on_missing: if True, abort if a cell is empty
        label_direction: how the voltage curves are given (back-and-forth, forth, forth-and-forth)
        label_mapper: function (or dict) that changes the cell names.
        only_selected (bool): only process selected cells.
        **kwargs: passed on to ica.dqdv

    Returns:
        pd.DataFrame: collected data
    """

    if cycles is None:
        cycles = list(range(1, max_cycle + 1))
    all_curves = []
    keys = []
    for selected, n, g, sg, c in pick_named_cell(b, label_mapper):
        if only_selected and not selected:
            logging.debug(f"skipping {n} (cell name: {c.cell_name})")
            continue
        if rate is not None:
            filtered_cycles = c.get_cycle_numbers(
                rate=rate,
                rate_on=rate_on,
                rate_std=rate_std,
                rate_agg=rate_agg,
                inverse=inverse,
            )
            cycles = list(set(filtered_cycles).intersection(set(cycles)))
        curves = ica.dqdv(
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
    collected_curves = pd.concat(all_curves, keys=keys, axis=0, names=["cell", "point"]).reset_index(level="cell")
    return collected_curves


# plotter functions (consider moving to plotutils)


def remove_markers(trace):
    """Remove markers from a plotly trace."""

    trace.update(marker=None, mode="lines")
    return trace


def _hist_eq(trace):
    z = histogram_equalization(trace.z)
    trace.update(z=z)
    return trace


def y_axis_replacer(ax, label):
    """Replace y-axis label in matplotlib plots."""
    ax.update(title_text=label)
    return ax


def legend_replacer(trace, df, group_legends=True):
    """Replace legend labels with cell names in plotly plots."""

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


def spread_plot(curves, plotly_arguments, **kwargs):
    """Create a spread plot (error-bands instead of error-bars)."""
    from plotly.subplots import make_subplots

    selected_variables = curves["variable"].unique()
    number_of_rows = len(selected_variables)

    colors = plotly.colors.qualitative.Plotly
    opacity = 0.2
    color_list = []
    for color in colors:
        color_rgb = plotly.colors.hex_to_rgb(color)
        color_rgb_main = f"rgb({color_rgb[0]}, {color_rgb[1]}, {color_rgb[2]})"
        color_rgba_spread = f"rgba({color_rgb[0]}, {color_rgb[1]}, {color_rgb[2]}, {opacity})"
        color_list.append((color_rgb_main, color_rgba_spread))

    if plotly_arguments.get("markers"):
        mode = "lines+markers"
    else:
        mode = "lines"

    g = curves.groupby("cell")
    fig = make_subplots(
        rows=number_of_rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
    )
    for i, (cell, data) in enumerate(g):
        color = color_list[i % len(color_list)]

        for row_number, variable in enumerate(selected_variables):
            if row_number == 0:
                show_legend = True
            else:
                show_legend = False
            sub_data = data[data["variable"] == variable]
            fig.add_trace(
                go.Scatter(
                    name=cell,
                    x=sub_data["cycle"],
                    y=sub_data["mean"],
                    mode=mode,
                    line=dict(color=color[0]),
                    legendgroup=cell,
                    legendgrouptitle=None,
                    showlegend=show_legend,
                ),
                row=row_number + 1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    name=f"Upper Bound {cell}",
                    x=sub_data["cycle"],
                    y=sub_data["mean"] + sub_data["std"],
                    mode="lines",
                    marker=dict(
                        color=color[1],
                    ),
                    line=dict(width=0),
                    showlegend=False,
                    legendgroup=cell,
                ),
                row=row_number + 1,
                col=1,
            )
            fig.add_trace(
                go.Scatter(
                    name=f"Lower Bound {cell}",
                    x=sub_data["cycle"],
                    y=sub_data["mean"] - sub_data["std"],
                    mode="lines",
                    marker=dict(
                        color=color[1],
                    ),
                    line=dict(width=0),
                    fillcolor=color[1],
                    fill="tonexty",
                    showlegend=False,
                    legendgroup=cell,
                ),
                row=row_number + 1,
                col=1,
            )

    fig.update_layout(legend_tracegroupgap=0)

    if labels := plotly_arguments.get("labels"):
        fig.update_xaxes(title=labels.get("cycle", None))

    # Hack to remove the x-axis title that appears on the top of the plot:
    if number_of_rows > 1:
        fig.update_layout(xaxis_title=None)

    if hover_mode := kwargs.pop("hovermode", None):
        fig.update_layout(hovermode=hover_mode)

    return fig


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
    spread: bool = False,
    **kwargs,
) -> Any:
    """Create a plot made up of sequences of data (voltage curves, dQ/dV, etc).

    This method contains the "common" operations done for all the sequence plots,
    currently supporting filtering out the specific cycles, selecting either
    dividing into subplots by cell or by cycle, and creating the (most basic) figure object.

    Args:
        collected_curves (pd.DataFrame): collected data in long format.
        x (str): column name for x-values.
        y (str): column name for y-values.
        z (str): if method is 'fig_pr_cell', column name for color (legend), else for subplot.
        g (str): if method is 'fig_pr_cell', column name for subplot, else for color.
        standard_deviation: str = standard deviation column (skipped if None).
        group (str): column name for group.
        subgroup (str): column name for subgroup.
        x_label (str): x-label.
        x_unit (str): x-unit (will be put in parentheses after the label).
        y_label (str): y-label.
        y_unit (str): y-unit (will be put in parentheses after the label).
        z_label (str): z-label.
        z_unit (str): z-unit (will be put in parentheses after the label).
        y_label_mapper (dict): map the y-labels to something else.
        nbinsx (int): number of bins to use in interpolations.
        histfunc (str): aggregation method.
        histscale (str): used for scaling the z-values for 2D array plots (heatmaps and similar).
        direction (str): "charge", "discharge", or "both".
        direction_col (str): name of columns containing information about direction ("charge" or "discharge").
        method: 'fig_pr_cell' or 'fig_pr_cycle'.
        markers: set to True if you want markers.
        group_cells (bool): give each cell within a group same color.
        group_legend_muting (bool): if True, you can click on the legend to mute the whole group (only for plotly).
        backend (str): what backend to use.
        cycles: what cycles to include in the plot.
        palette_discrete: palette to use for discrete color mapping.
        palette_continuous: palette to use for continuous color mapping.
        palette_range (tuple): range of palette to use for continuous color mapping (from 0 to 1).
        facetplot (bool): square layout with group horizontally and subgroup vertically.
        cols (int): number of columns for layout.
        height (int): plot height.
        width (int): plot width.
        spread (bool): plot error-bands instead of error-bars if True.

        **kwargs: sent to backend (if `backend == "plotly"`, it will be
            sent to `plotly.express` etc.)

    Returns:
        figure object
    """
    logging.debug("running sequence plotter")

    for k in kwargs:
        logging.debug(f"keyword argument sent to the backend: {k}")
    if backend not in supported_backends:
        print(f"Backend '{backend}' not supported", end="")
        print(f" - supported backends: {supported_backends}")
        return
    curves = None

    # ----------------- parsing arguments -----------------------------

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

        seaborn_arguments = dict(x=x, y=z, z=y, labels=labels, row=g, col=subgroup)

    elif method == "summary":
        labels = {
            f"{x}": f"{x_label} ({x_unit})",
        }
        plotly_arguments = dict(x=x, y=y, labels=labels, markers=markers)
        seaborn_arguments = dict(x=x, y=y, markers=markers)
        seaborn_arguments["labels"] = labels

        if g == "variable" and len(collected_curves[g].unique()) > 1:
            plotly_arguments["facet_row"] = g
            seaborn_arguments["row"] = g
        if standard_deviation:
            plotly_arguments["error_y"] = standard_deviation
            seaborn_arguments["error_y"] = standard_deviation

    else:
        labels = {
            f"{x}": f"{x_label} ({x_unit})",
            f"{y}": f"{y_label} ({y_unit})",
        }
        plotly_arguments = dict(x=x, y=y, labels=labels, facet_col_wrap=cols)
        seaborn_arguments = dict(x=x, y=y, labels=labels, row=group, col=subgroup)

    if method in ["fig_pr_cell", "film"]:
        group_cells = False
        if method == "fig_pr_cell":
            plotly_arguments["markers"] = markers
            plotly_arguments["color"] = z
            seaborn_arguments["hue"] = z
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
        seaborn_arguments["col"] = g

        if cycles is not None:
            curves = collected_curves.loc[collected_curves.cycle.isin(cycles), :]
        else:
            curves = collected_curves

        if group_cells:
            plotly_arguments["color"] = group
            plotly_arguments["symbol"] = subgroup
            seaborn_arguments["hue"] = group
            seaborn_arguments["style"] = subgroup
        else:
            plotly_arguments["markers"] = markers
            plotly_arguments["color"] = z
            seaborn_arguments["hue"] = z
            seaborn_arguments["style"] = z

    elif method == "summary":
        logging.info("sequence-plotter - summary")
        if cycles is not None:
            curves = collected_curves.loc[collected_curves.cycle.isin(cycles), :]
        else:
            curves = collected_curves

        if group_cells:
            plotly_arguments["color"] = group
            plotly_arguments["symbol"] = subgroup
            seaborn_arguments["hue"] = group
            seaborn_arguments["style"] = subgroup
        else:
            plotly_arguments["color"] = z
            seaborn_arguments["hue"] = z

    # ----------------- individual plotting calls  -----------------------------
    # TODO: move as much as possible up to the parsing of arguments
    #   (i.e. prepare for future refactoring)

    if backend == "plotly":
        if method == "fig_pr_cell":
            start, end = 0.0, 1.0
            if palette_range is not None:
                start, end = palette_range
            unique_cycle_numbers = curves[z].unique()
            number_of_colors = len(unique_cycle_numbers)
            if number_of_colors > 1:
                selected_colors = px.colors.sample_colorscale(palette_continuous, number_of_colors, low=start, high=end)
                plotly_arguments["color_discrete_sequence"] = selected_colors
        elif method == "fig_pr_cycle":
            if palette_discrete is not None:
                # plotly_arguments["color_discrete_sequence"] = getattr(px.colors.sequential, palette_discrete)
                logging.debug(f"palette_discrete is not implemented yet ({palette_discrete})")

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
        facet_row_spacing = kwargs.pop("facet_row_spacing", abs_facet_row_spacing / height if height else 0.1)
        facet_col_spacing = kwargs.pop("facet_col_spacing", abs_facet_col_spacing / (width or 1000))

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
            if spread:
                logging.critical("using spread is an experimental feature and might not work as expected")
                fig = spread_plot(curves, plotly_arguments, **kwargs)
            else:
                fig = px.line(
                    curves,
                    **plotly_arguments,
                    **kwargs,
                )

            if group_cells:  # all cells in same group has same color
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
                        if spread:
                            for i, la in enumerate(y_label_mapper):
                                row = i + 1
                                fig.for_each_yaxis(functools.partial(y_axis_replacer, label=la), row=row)

                        else:
                            fig.for_each_yaxis(
                                functools.partial(y_axis_replacer, label=y_label_mapper[0]),
                            )
                    except Exception as e:
                        print("failed")
                        print(e)

        else:
            print(f"method '{method}' is not supported by plotly")

        return fig

    if backend == "seaborn":
        number_of_data_points = len(curves)
        if number_of_data_points > MAX_POINTS_SEABORN_FACET_GRID:
            print(
                f"WARNING! Too many data points for seaborn to plot: "
                f"{number_of_data_points} > {MAX_POINTS_SEABORN_FACET_GRID}"
            )
            print(
                f"  - Try to reduce the number of data points "
                f"e.g. by selecting fewer cycles and interpolating "
                f"using the `number_of_points` and `max_cycle` or `cycles_to_plot` arguments."
            )
            return

        if method == "fig_pr_cell":
            seaborn_arguments["height"] = kwargs.pop("height", 3)
            seaborn_arguments["aspect"] = kwargs.pop("height", 1)
            sns.set_theme(style="darkgrid")
            x = seaborn_arguments.get("x", "capacity")
            y = seaborn_arguments.get("y", "voltage")
            row = seaborn_arguments.get("row", "group")
            hue = seaborn_arguments.get("hue", "cycle")
            col = seaborn_arguments.get("col", "sub_group")
            height = seaborn_arguments.get("height", 3)
            aspect = seaborn_arguments.get("aspect", 1)

            if palette_discrete is not None:
                seaborn_arguments["palette"] = getattr(sns.color_palette, palette_discrete)

            number_of_columns = len(curves[col].unique())
            if number_of_columns > 6:
                print(f"WARNING! {number_of_columns} columns is a lot for seaborn to plot")
                print(f"  - consider making the plot manually (use the `.data` attribute to get the data)")

            legend_items = curves[hue].unique()
            number_of_legends = len(legend_items)
            palette = seaborn_arguments.get("palette", "viridis") if number_of_legends > 10 else None

            g = sns.FacetGrid(
                curves,
                hue=hue,
                row=row,
                col=col,
                height=height,
                aspect=aspect,
                palette=palette,
            )

            g.map(plt.plot, x, y)

            if number_of_legends > 10:

                vmin = legend_items.min()
                vmax = legend_items.max()

                sm = plt.cm.ScalarMappable(cmap=palette, norm=plt.Normalize(vmin=vmin, vmax=vmax))
                cbar = g.figure.colorbar(
                    sm,
                    ax=g.figure.axes,
                    location="right",
                    extend="max",
                    # pad=0.05/number_of_columns,
                )
                cbar.ax.set_title("Cycle")
            else:
                g.add_legend()

            fig = g.fig
            g.set_xlabels(labels[x])
            g.set_ylabels(labels[y])
            return fig

        if method == "fig_pr_cycle":
            sns.set_theme(style="darkgrid")
            seaborn_arguments["height"] = 4
            seaborn_arguments["aspect"] = 3
            seaborn_arguments["linewidth"] = 2.0
            g = sns.FacetGrid(
                curves,
                hue=z,
                height=seaborn_arguments["height"],
                aspect=seaborn_arguments["aspect"],
            )
            g.map(plt.plot, x, y)
            fig = g.fig
            g.set_xlabels(x_label)
            g.set_ylabels(y_label)
            g.add_legend()
            return fig

        if method == "film":
            sns.set_theme(style="darkgrid")
            seaborn_arguments["height"] = 4
            seaborn_arguments["aspect"] = 3
            seaborn_arguments["linewidth"] = 2.0
            g = sns.FacetGrid(
                curves,
                hue=z,
                height=seaborn_arguments["height"],
                aspect=seaborn_arguments["aspect"],
            )
            g.map(
                sns.kdeplot,
                y,
                x,
                fill=True,
                thresh=0,
                levels=100,
                cmap=palette_continuous,
            )
            fig = g.fig
            g.set_xlabels(x_label)
            g.set_ylabels(y_label)
            g.add_legend()
            return fig

        if method == "summary":
            sns.set_theme(style="darkgrid")
            seaborn_arguments["height"] = 4
            seaborn_arguments["aspect"] = 3
            seaborn_arguments["linewidth"] = 2.0

            x = seaborn_arguments.get("x", "cycle")
            y = seaborn_arguments.get("y", "mean")
            hue = seaborn_arguments.get("hue", None)

            labels = seaborn_arguments.get("labels", None)
            x_label = labels.get(x, x)

            std = seaborn_arguments.get("error_y", None)
            marker = "o" if seaborn_arguments.get("markers", False) else None
            row = seaborn_arguments.get("row", None)

            g = sns.FacetGrid(
                curves,
                hue=hue,
                height=seaborn_arguments["height"],
                aspect=seaborn_arguments["aspect"],
                row=row,
            )

            if std:
                g.map(plt.errorbar, x, y, std, marker=marker, elinewidth=0.5, capsize=2)
            else:
                g.map(plt.plot, x, y, marker=marker)

            fig = g.figure

            g.set_xlabels(x_label)
            if y_label_mapper:
                for i, ax in enumerate(g.axes.flat):
                    ax.set_ylabel(y_label_mapper[i])
            g.add_legend()
            return fig

    elif backend == "matplotlib":
        print(f"{backend} not implemented yet")

    elif backend == "bokeh":
        print(f"{backend} not implemented yet")

    else:
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
    match_axes=True,
    **kwargs,
):
    """Plot charge-discharge curves.

    Args:
        collected_curves(pd.DataFrame): collected data in long format.
        backend (str): what backend to use.
        match_axes (bool): if True, all subplots will have the same axes.
        method (str): 'fig_pr_cell' or 'fig_pr_cycle'.

        **kwargs: consumed first in current function, rest sent to backend in sequence_plotter.

    Returns:
        styled figure object
    """
    # --- pre-processing ---
    logging.debug("picking kwargs for current level - rest goes to sequence_plotter")
    title = kwargs.pop("fig_title", default_title)
    width = kwargs.pop("width", 900)
    height = kwargs.pop("height", None)
    palette = kwargs.pop("palette", None)
    legend_position = kwargs.pop("legend_position", None)
    legend_title = kwargs.pop("legend_title", None)
    show_legend = kwargs.pop("show_legend", None)
    cols = kwargs.pop("cols", 3)
    sub_fig_min_height = kwargs.pop("sub_fig_min_height", 200)
    figure_border_height = kwargs.pop("figure_border_height", 100)
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
        height = figure_border_height + no_rows * sub_fig_min_height

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
        print("Could not create figure!")
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
        if not match_axes:
            fig.update_yaxes(matches=None)
            fig.update_xaxes(matches=None)

    return fig


def summary_plotter(collected_curves, cycles_to_plot=None, backend="plotly", **kwargs):
    """Plot summaries (value vs cycle number).

    Assuming data as pandas.DataFrame with either
    1) long format (where variables, for example charge capacity, are in the column "variable") or
    2) mixed long and wide format where the variables are own columns.
    """

    col_headers = collected_curves.columns.to_list()

    # need to manually update this if new columns are added to collected_curves that should not be plotted:
    not_available_for_plotting = ["label", "group_label", "selected"]

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
    for n in not_available_for_plotting:
        if n in col_headers:
            col_headers.remove(n)

    if "variable" not in col_headers:
        collected_curves = collected_curves.melt(id_vars=id_vars, value_vars=col_headers)

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

    # TODO: need to refactor and fix how the classes are created so that leftover kwargs are not sent to the backend
    #  (for example if another collector is used and registers a kwarg without popping it)

    _ = kwargs.pop("method", None)  # also set in BatchCyclesCollector

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

    if backend == "plotly":
        # TODO: implement having different heights of the subplots
        height_fractions = kwargs.pop("height_fractions", [])
        if len(height_fractions) < 0:
            # this was suggested by CoPilot (not sure if it works):
            for i, h in enumerate(height_fractions):
                fig.update_yaxes(row=i + 1, matches=None, showticklabels=True, fixedrange=True)
                fig.update_layout(height=fig.layout.height + h)
        fig.update_yaxes(matches=None, showticklabels=True)
        return fig
    if backend == "seaborn":
        print("using seaborn (experimental feature)")
        return fig
    if backend == "matplotlib":
        print("using matplotlib (experimental feature)")
        return fig
    if backend == "bokeh":
        print("using bokeh (experimental feature)")
        return fig


def cycles_plotter(
    collected_curves,
    cycles_to_plot=None,
    backend="plotly",
    method="fig_pr_cell",
    x_unit="mAh/g",
    y_unit="V",
    **kwargs,
):
    """Plot charge-discharge curves.

    Args:
        collected_curves(pd.DataFrame): collected data in long format.
        cycles_to_plot (list): cycles to plot
        backend (str): what backend to use.
        method (str): 'fig_pr_cell' or 'fig_pr_cycle'.
        x_unit (str): unit for x-axis.
        y_unit (str): unit for y-axis.

        **kwargs: consumed first in current function, rest sent to backend in sequence_plotter.

    Returns:
        styled figure object
    """

    if cycles_to_plot is not None:
        unique_cycles = list(collected_curves.cycle.unique())
        if len(unique_cycles) > 50:
            print(f"Too many cycles - setting it to default {DEFAULT_CYCLES}")
            cycles_to_plot = DEFAULT_CYCLES

    return _cycles_plotter(
        collected_curves,
        x="capacity",
        y="voltage",
        z="cycle",
        g="cell",
        x_unit=x_unit,
        y_unit=y_unit,
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
    if method == "film":
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
        default_title=f"Incremental Analysis Plots",
        direction=direction,
        backend=backend,
        method=method,
        cycles=cycles_to_plot,
        **kwargs,
    )


def histogram_equalization(image: np.array) -> np.array:
    """Perform histogram equalization on a numpy array."""
    # from http://www.janeriksolem.net/histogram-equalization-with-python-and.html
    number_bins = 256
    scale = 100
    image[np.isnan(image)] = 0.0
    image_histogram, bins = np.histogram(image.flatten(), number_bins, density=True)
    cdf = image_histogram.cumsum()  # cumulative distribution function
    cdf = (scale - 1) * cdf / cdf[-1]  # normalize
    # use linear interpolation of cdf to find new pixel values
    image_equalized = np.interp(image.flatten(), bins[:-1], cdf)

    return image_equalized.reshape(image.shape)


def _check():
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


if __name__ == "__main__":
    _check()
