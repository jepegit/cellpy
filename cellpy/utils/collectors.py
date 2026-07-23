"""Collectors are used for simplifying plotting and exporting batch objects."""

import functools
import inspect
import logging
import math
import pickle as pkl
from pprint import pprint
from pathlib import Path
import textwrap
from typing import Any, Union
import time
from itertools import count
from multiprocessing import Process
import warnings

import pandas as pd
import numpy as np

try:
    import matplotlib.pyplot as plt
except ImportError:  # pragma: no cover - optional for non-plot imports
    plt = None

import cellpy
from cellpycore.config import CurveCols

from cellpy.parameters.internal_settings import get_headers_journal

# get_cap curve frames use native CurveCols names (#540): potential/cycle_num
# replace the legacy voltage/cycle. The capacity-curve plotters below default
# their x/y/z column selectors to these. (Summary and ICA collectors use their
# own schemas and are left untouched.)
_CCOLS = CurveCols()
from cellpy.readers.data_structures import group_by_interpolate
from cellpy.utils.batch import Batch
from cellpy.utils.helpers import concat_summaries
from cellpy.utils import ica

# Single copies (#567); collectors used to carry its own, and its
# load_plotly_figure was the unguarded one that raised without plotly.
from cellpy.plotting.figures import (  # noqa: F401
    load_figure,
    load_matplotlib_figure,
    load_plotly_figure,
    make_matplotlib_manager,
    save_matplotlib_figure,
)
from cellpy.plotting.labels import legend_replacer, remove_markers  # noqa: F401
from cellpy.plotting import theme
from cellpy.plotting.collected import collected_plot, _select_direction  # noqa: F401

hdr_journal = get_headers_journal()

supported_backends = []

try:
    import plotly  # noqa: F401

    supported_backends.append("plotly")
except ImportError:
    print("WARNING: plotly not installed")

try:
    import seaborn  # noqa: F401

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


def incremental_image_exporter_plotly(
    figure, filename, timeout=IMAGE_TO_FILE_TIMEOUT, **kwargs
):
    use_subprocess = kwargs.pop("use_subprocess", True)

    if not use_subprocess:
        print(f"saving image to {filename}")
        figure.write_image(filename, **kwargs)
        return
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
    else:
        print(f"Oops, {p} failed with exitcode: {p.exitcode}")
        print("Could it be that you have not installed the required packages?")
        print("Try to install kaleido:")
        print("pip install kaleido")


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

    incremental_image_exporter_plotly(figure, filename_png, scale=3.0)
    incremental_image_exporter_plotly(figure, filename_svg)
    figure.write_json(filename_json)
    print(f" - saved plotly json file: {filename_json}")


if not supported_backends:
    print("WARNING: no supported backends found")
    print("WARNING: install plotly or seaborn to enable plotting")

# The collector templates live in cellpy.plotting.theme now and are built
# lazily (#567): constructing them here at import time made this whole module
# unimportable without the `batch` extra.
px_template_all_axis_shown = theme.ALL_AXIS_SHOWN


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

    # Drawing family for cellpy.plotting.collected_plot (#657).
    family_kind: str = "cycles"

    def __init__(
        self,
        b,
        data_collector,
        plotter=None,
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
        family_kind: str = None,
        **kwargs,
    ):
        """Update both the collected data and the plot(s).

        Args:
            b (cellpy.utils.Batch): the batch object.
            data_collector (callable): method that collects the data.
            plotter (callable): optional custom plotter; default ``None`` uses
                :func:`cellpy.plotting.collected_plot` (#657).
            collector_name (str): name of collector.
            name (str or bool): name used for auto-generating filenames etc.
            autorun (bool): run collector and plotter immediately if True.
            use_templates (bool): also apply template(s) in autorun mode if True.
            backend (str): name of plotting backend to use ("plotly" or "matplotlib").
            elevated_data_collector_arguments (dict): arguments picked up by the child class' initializer.
            elevated_plotter_arguments (dict): arguments picked up by the child class' initializer.
            data_collector_arguments (dict): keyword arguments sent to the data collector.
            plotter_arguments (dict): keyword arguments sent to the plotter.
            family_kind (str): ``summary`` | ``cycles`` | ``ica`` for collected_plot.
            update_name (bool): update the name (using automatic name generation) based on new settings.
            **kwargs: set Collector attributes.

        """

        self.b = b
        self.data_collector = data_collector
        self.plotter = plotter
        self.nick = nick
        self.experimental = experimental
        if family_kind is not None:
            self.family_kind = family_kind
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
        # Templates live in cellpy.plotting.theme; collected_plot also ensures
        # registration on first draw (#657). Keep a lazy hook for autorun.
        try:
            import plotly.io as _pio

            _pio.templates.default = PLOTLY_BASE_TEMPLATE
        except ImportError:
            pass
        theme.make_collector_templates()

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
        """Generate a name for the collection."""

        names = ["collector", self.collector_name]
        if self.nick:
            names.insert(0, self.nick)
        name = "_".join(names)
        return name

    def render(self, **kwargs):
        """Render the figure via ``cellpy.plotting.collected_plot`` (#657)."""

        kwargs = {**self.plotter_arguments, **kwargs}
        if self.plotter is not None:
            self.figure = self.plotter(
                self.data,
                backend=self.backend,
                journal=self.b.journal,
                units=self.units,
                **kwargs,
            )
            return
        self.figure = collected_plot(
            self.data,
            family_kind=self.family_kind,
            backend=self.backend,
            journal=self.b.journal,
            units=self.units,
            **kwargs,
        )

    def plot(self, **kwargs):
        """Alias for :meth:`render` (plotting redesign §3.3 / #657)."""
        return self.render(**kwargs)

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
        self.data = self.data_collector(
            self.b, **self.data_collector_arguments, **kwargs
        )
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
            print(
                "WARNING: skipping rendering for seaborn, assuming it is already rendered during the plotter call"
            )
            print(
                "WARNING: if you want to show the figure, provide `skip_render_for_seaborn=False` as keyword argument"
            )
        else:
            return self.figure

    def preprocess_data_for_csv(self):
        logging.debug(f"the data layout {self.csv_layout} is not supported yet!")
        not_needed_columns = [
            hdr_journal.group,
            hdr_journal.sub_group,
            hdr_journal.group_label,
            hdr_journal.label,
            hdr_journal.selected,
        ]
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

        # Convert categorical columns to strings to avoid HDF5 issues
        for col in data.columns:
            if pd.api.types.is_categorical_dtype(data[col]):
                logging.info(f"converting categorical column {col} to string")
                data[col] = data[col].astype(str)

        data.to_hdf(filename, key=HDF_KEY, mode="w")
        print(f" - saved hdf5 file: {filename}")

    def _image_exporter_plotly(self, filename, timeout=IMAGE_TO_FILE_TIMEOUT, **kwargs):
        use_subprocess = kwargs.pop("use_subprocess", True)

        if not use_subprocess:
            print(f"saving image to {filename}")
            self.figure.write_image(filename, **kwargs)
            return
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
        else:
            print(f"Oops, {p} failed with exitcode: {p.exitcode}")
            print("Could it be that you have not installed the required packages?")
            print("Try to install kaleido:")
            print("pip install kaleido")

    def to_image_files(self, serial_number=None, **kwargs):
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
            self._image_exporter_plotly(filename_png, scale=3.0, **kwargs)
            self._image_exporter_plotly(filename_svg, **kwargs)
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

    def save(
        self,
        serial_number=None,
        save_hdf5=True,
        save_image_files=True,
        to_csv_kwargs: Union[dict, None] = None,
        to_image_files_kwargs: Union[dict, None] = None,
    ):
        """Save to csv, hdf5 and image files.

        Args:
            serial_number (int): serial number to append to the filename.
            save_hdf5 (bool): save to hdf5 file.
            save_image_files (bool): save to image files.
            to_csv_kwargs (dict): keyword arguments sent to the csv writer.

        """

        if to_csv_kwargs is None:
            to_csv_kwargs = {}
        self.to_csv(serial_number=serial_number, **to_csv_kwargs)
        if save_hdf5:
            try:
                self.to_hdf5(serial_number=serial_number)
            except Exception as e:
                print(f"Error saving hdf5 file: {e}")

        if self._figure_valid():
            if save_image_files:
                if to_image_files_kwargs is None:
                    to_image_files_kwargs = {}
                self.to_image_files(
                    serial_number=serial_number, **to_image_files_kwargs
                )

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


def standard_gravimetric_collector(b, norm_factor=120.0, **kwargs):
    """Create a standard gravimetric collector.

    This is a temporary hack to allow for making standard plot no. 1.

    Coulombic Efficiency
    Discharge Capacity (gravimetric)
    Discharge Capacity Retention (Normalized)
    CV share Charge Capacity (Normalized)

    Args:
        norm_factor (float): the factor to normalize the discharge capacity retention by.
        group_it (bool): if True, group the cells by the key_index_bounds.
        data_collector_arguments (dict): the data collector arguments.
        plotter_arguments (dict): the plotter arguments.
        **kwargs: additional arguments sent to the collector.
    """

    from functools import partial

    def _copy_and_normalize(
        df,
        columns,
        col="discharge_capacity_gravimetric",
        norm_factor=120.0,
        *args,
        **kwargs,
    ):
        # modify the dataframe:
        _kwargs = {
            f"{col}_norm": lambda x: 100 * (x[col]) / norm_factor,
        }
        df = df.assign(**_kwargs)

        # modify the output columns:
        if f"{col}_norm" not in columns:
            columns.append(f"{col}_norm")
        return df, columns

    group_it = kwargs.pop("group_it", True)
    interactive = kwargs.pop("interactive", True)

    _copy_and_normalize_discharge_capacity_gravimetric_partial = partial(
        _copy_and_normalize, norm_factor=norm_factor
    )
    _copy_and_normalize_discharge_capacity_gravimetric_partial.__name__ = (
        "copy_and_normalize_discharge_capacity_gravimetric"
    )

    _copy_and_normalize_charge_capacity_gravimetric_cv_partial = partial(
        _copy_and_normalize,
        norm_factor=norm_factor,
        col="charge_capacity_gravimetric_cv",
    )
    _copy_and_normalize_charge_capacity_gravimetric_cv_partial.__name__ = (
        "copy_and_normalize_charge_capacity_gravimetric_cv"
    )

    if not interactive:
        raise NotImplementedError(
            "Only interactive mode is implemented for standard_gravimetric_collector"
        )
    backend = kwargs.pop("backend", "plotly")
    if backend != "plotly":
        raise NotImplementedError(
            "Only plotly backend is implemented for standard_gravimetric_collector"
        )
    columns = [
        "charge_capacity_gravimetric",
        "discharge_capacity_gravimetric",
        "coulombic_efficiency",
    ]
    data_collector_arguments = dict(
        partition_by_cv=True,
        individual_summary_hooks=[
            _copy_and_normalize_discharge_capacity_gravimetric_partial,
            _copy_and_normalize_charge_capacity_gravimetric_cv_partial,
        ],
        drop_columns=[
            "charge_capacity_gravimetric_cv",
            "charge_capacity_gravimetric",
            "charge_capacity_gravimetric_non_cv",
            "discharge_capacity_gravimetric_cv",
            "discharge_capacity_gravimetric_non_cv",
        ],
        average_method="mean",
        key_index_bounds=[0, 4],
    )
    plotter_arguments = dict(
        spread=group_it,
        markers=True,
        height_fractions_spread=[0.1, 0.3, 0.3, 0.3],
        order_variables=[
            "coulombic_efficiency",
            "discharge_capacity_gravimetric",
            "discharge_capacity_gravimetric_norm",
            "charge_capacity_gravimetric_cv_norm",
        ],
    )
    data_collector_arguments.update(kwargs.pop("data_collector_arguments", {}))
    plotter_arguments.update(kwargs.pop("plotter_arguments", {}))
    return BatchSummaryCollector(
        b,
        group_it=group_it,
        interactive=interactive,
        backend=backend,
        columns=columns,
        data_collector_arguments=data_collector_arguments,
        plotter_arguments=plotter_arguments,
        **kwargs,
    )


class BatchSummaryCollector(BatchCollector):
    # Three main levels of arguments to the plotter and collector funcs is available:
    #  - through dictionaries (`data_collector_arguments`, `plotter_arguments`) to init
    #  - given as defaults in the subclass (`_default_data_collector_arguments`, `_default_plotter_arguments`)
    #  - as elevated arguments (i.e. arguments normally given in the dictionaries elevated
    #    to their own keyword parameters)

    _default_data_collector_arguments = {
        "columns": ["charge_capacity_gravimetric"],
    }

    _default_plotter_arguments = {
        "match_axes": False,
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
            data_collector=summary_collector,
            collector_name="summary",
            family_kind="summary",
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
        # summary collectors label the cycle column "cycle"; curve collectors
        # carry the native CurveCols name "cycle_num" (#540).
        if "cycle" in cols:
            index = "cycle"
            cols.remove("cycle")
        elif _CCOLS.cycle_num in cols:
            index = _CCOLS.cycle_num
            cols.remove(_CCOLS.cycle_num)
        else:
            print("Could not find index")
            return self.data

        if hdr_journal.sub_group in cols:
            cols.remove(hdr_journal.sub_group)

        if hdr_journal.group in cols:
            cols.remove(hdr_journal.group)

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
            family_kind="ica",
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
            plotter_arguments (dict) - arguments transferred to ``collected_plot``.
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
            family_kind="cycles",
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
                    f"{self.units['cellpy_units'].charge}/{self.units['cellpy_units'].gravimetric}"
                )
            elif m == "areal":
                self.plotter_arguments["x_unit"] = (
                    f"{self.units['cellpy_units'].charge}/{self.units['cellpy_units'].areal}"
                )
            elif m == "volumetric":
                self.plotter_arguments["x_unit"] = (
                    f"{self.units['cellpy_units'].charge}/{self.units['cellpy_units'].volumetric}"
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
        group = b.pages.loc[n, hdr_journal.group]
        sub_group = b.pages.loc[n, hdr_journal.sub_group]
        logging.debug(f"processing {n} (group={group}, sub_group={sub_group})")
        # putting this check here for backwards compatibility:
        if hdr_journal.selected in b.pages.columns:
            selected = b.pages.loc[n, hdr_journal.selected]
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
                label = b.pages.loc[n, hdr_journal.label]

                if label is None:
                    logging.info(
                        f"label from journal.pages: {label} -> using original name ({n})"
                    )
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
    collected_curves = pd.concat(
        all_curves, keys=keys, axis=0, names=["cell", "point"]
    ).reset_index(level="cell")
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
        label_direction: no-op since 2.0 (kept for signature compatibility; the
            specced ICA frame always carries a direction column)
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
        # The specced ICA frame (#566): cycle, direction, voltage, capacity,
        # dqdv (+ the deprecated `dq` duplicate until 2.1). `direction` is
        # spelled "charge"/"discharge" and is **cell-centric** — decision
        # #591: it agrees with get_ccap/get_dcap and the summary columns, so
        # for an anode cell the first half-cycle is "discharge". Film-plot
        # labels flipped accordingly (release-noted on #572).
        curves = ica.dqdv(
            c,
            cycles=cycles,
            voltage_resolution=voltage_resolution,
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


# Drawing lives in cellpy.plotting.collected (#657). Collection helpers below
# stay here. `_select_direction` is re-exported from plotting.collected for
# tests / callers that still import it from this module.


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


def _make_a_new_feature():
    from pathlib import Path
    import cellpy
    from cellpy.utils import batch, helpers, plotutils
    from cellpy.utils import collectors

    import plotly.io as pio

    pio.renderers.default = "browser"

    journal = Path(r"C:\Users\jepe\processor_project/journal.json")
    assert journal.is_file()
    b = batch.from_journal(journal)
    b.link()

    coll = collectors.BatchSummaryCollector(
        b,
        max_cycle=100,
        columns=[
            "charge_capacity_gravimetric",
            "discharge_capacity_gravimetric",
            "coulombic_efficiency",
        ],
        data_collector_arguments=dict(
            partition_by_cv=True
        ),  # NOTE! currently, partition_by_cv is "dumb" and does the partition for all selected columns.
    )

    print(coll.data.columns)
    coll.figure.show()


if __name__ == "__main__":
    _make_a_new_feature()
