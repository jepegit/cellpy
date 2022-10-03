"""Collectors are used for simplifying plotting and exporting batch objects."""

import textwrap
from pprint import pprint
from pathlib import Path
from typing import Any
import inspect

import pandas as pd

import cellpy
from cellpy.utils.batch import Batch
from cellpy.utils.helpers import concatenate_summaries
from cellpy.utils.plotutils import plot_concatenated
from cellpy.utils import ica

try:
    import holoviews as hv
    from holoviews.core.io import Pickler
    from holoviews import opts

    HOLOVIEWS_AVAILABLE = True
except ImportError:
    print("Could not import holoviews. Plotting will be disabled.")
    HOLOVIEWS_AVAILABLE = False

CELLPY_MINIMUM_VERSION = "0.4.3"


def _setup():
    _welcome_message()
    _register_holoviews_renderers()


def _welcome_message():
    cellpy_version = cellpy.__version__
    print(f"cellpy version: {cellpy_version}")
    print(f"collectors need at least: {CELLPY_MINIMUM_VERSION}")


def _register_holoviews_renderers(extensions=None):
    if HOLOVIEWS_AVAILABLE:
        if extensions is None:
            extensions = "bokeh", "matplotlib"
        print(
            f"Registering Holoviews extensions {extensions} for the cellpy collectors."
        )
        hv.extension(*extensions)
    else:
        print(
            "Could not import Holoviews. Your collectors will not be able to make figures."
        )


def _set_holoviews_renderer(extension=None):
    if HOLOVIEWS_AVAILABLE:
        extension = extension.lower()
        current_backend = hv.Store.current_backend
        if not extension == current_backend:
            print(f"switching backend to {extension}")
            hv.extension(extension)


def _get_current_holoviews_renderer():
    return hv.Store.current_backend


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

    # defaults when resetting:
    _default_data_collector_arguments = {}
    _default_plotter_arguments = {}

    # TODO: refactor this (and _set_hv_opts) so that its possible to append options in subclasses of subclasses etc.
    _templates = {
        "bokeh": {},
        "matplotlib": {},
        "plotly": {},
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
        data_collector_arguments: dict = None,
        plotter_arguments: dict = None,
        **kwargs,
    ):
        """Update both the collected data and the plot(s).
        Args:
            b (cellpy.utils.Batch): the batch object.
            name (str or bool): name of the collector used for auto-generating filenames etc.
            autorun (bool): run collector and plotter immediately if True.
            data_collector_arguments (dict): keyword arguments sent to the data collector.
            plotter_arguments (dict): keyword arguments sent to the plotter.
            update_name (bool): update the name (using automatic name generation) based on new settings.
            **kwargs: set Collector attributes.
        """
        self.b = b
        self.data_collector = data_collector
        self.plotter = plotter
        self.nick = nick
        self.collector_name = collector_name or "base"
        self._data_collector_arguments = self._default_data_collector_arguments.copy()
        self._plotter_arguments = self._default_plotter_arguments.copy()
        self._update_arguments(data_collector_arguments, plotter_arguments)
        self._set_attributes(**kwargs)

        if nick is None:
            self.nick = b.name

        if name is None:
            name = self.generate_name()
        self.name = name

        if autorun:
            self.update(update_name=False)
            self.apply_template()

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

    def _update_arguments(
        self, data_collector_arguments: dict = None, plotter_arguments: dict = None
    ):
        self.data_collector_arguments = data_collector_arguments
        self.plotter_arguments = plotter_arguments

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
    ):
        """Update both the collected data and the plot(s).
        Args:
            data_collector_arguments (dict): keyword arguments sent to the data collector.
            plotter_arguments (dict): keyword arguments sent to the plotter.
            reset (bool): reset the arguments first.
            update_data (bool): update the data before updating the plot even if data has been collected before.
            update_name (bool): update the name (using automatic name generation) based on new settings.
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

        if HOLOVIEWS_AVAILABLE:
            _set_holoviews_renderer(self.plotter_arguments.get("extension"))
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

    def apply_template(self):
        # This method should apply a template to the figure
        if not self._figure_valid():
            return
        extension = _get_current_holoviews_renderer()
        templates = self._templates

        # templates is a dict of dicts.
        # e.g.
        # >>> matplotlib_template = templates["matplotlib"]
        # >>> self.figure = self._set_hv_opts(matplotlib_template)
        # The template is either a dict of dicts or a list of hv.opts.xxx instances.
        # Remark that there is only one set of templates pr. plotter.
        # Also, we must make sure that the hv opts contains the backend="matplotlib" kwarg.
        # Since this is a bit tricky (I think) to achieve for the hv.opts.Xxx instances,
        # I make it a rule for the developer to make sure that each instance contains the backend keyword.
        pass

    def _figure_valid(self):
        # TODO: create a decorator
        if self.figure is None:
            print("No figure to show!")
            return False
        if not HOLOVIEWS_AVAILABLE:
            print("Requires Holoviews - please install it first!")
            return False
        return True

    def _set_hv_opts(self, hv_opts):
        if hv_opts is None:
            return self.figure

        if isinstance(hv_opts, tuple):
            return self.figure.opts(*hv_opts)
        else:
            return self.figure.opts(hv_opts)

    def show(self, hv_opts=None):
        if not self._figure_valid():
            return

        print(f"figure name: {self.name}")
        return self._set_hv_opts(hv_opts)

    def redraw(self, hv_opts=None, extension=None):
        if not self._figure_valid():
            return

        if extension is not None:
            _set_holoviews_renderer(extension)

        print(f"figure name: {self.name}")
        self.figure = self._set_hv_opts(hv_opts)
        return self.figure

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

        filename_hv = filename_pre.with_suffix(".html")
        hv.save(
            self.figure,
            filename_hv,
            toolbar=self.toolbar,
        )
        print(f"saved file: {filename_pre}")

        filename_png = filename_pre.with_suffix(".png")
        try:
            current_renderer = _get_current_holoviews_renderer()
            _set_holoviews_renderer("matplotlib")
            hv.save(
                self.figure,
                filename_png,
                dpi=300,
            )
            print(f"saved file: {filename_pre}")
        except Exception as e:
            print("Could not save png-file.")
            print(e)
        finally:
            _set_holoviews_renderer(current_renderer)

    def save(self, serial_number=None):
        self.to_csv(serial_number=serial_number)

        if self._figure_valid():
            filename = self._output_path(serial_number)
            filename = filename.with_suffix(".hvz")
            Pickler.save(
                self.figure,
                filename,
            )
            print(f"pickled holoviews file: {filename}")
            self.to_image_files(serial_number=serial_number)

    def _output_path(self, serial_number=None):
        d = Path(self.figure_directory)
        n = self.name
        if serial_number is not None:
            n = f"{n}_{serial_number:03}"
        f = d / n
        return f


# TODO: allow for storing more than one figure setup pr collector
#    It is time-consuming and memory demanding to re-collect the data
#    for each time we need a new figure for the collector. We should
#    allow for creating multiple figures within one collector or for
#    sharing (passing) collected data. One solution might be to extend
#    the capabilities of the base class. Another solution might be to
#    add another sub-class in the chain from the base class to the actual one:
class BatchMultiFigureCollector(BatchCollector):
    pass


def cycles_collector(
    b,
    cycles=None,
    interpolated=True,
    number_of_points=100,
    max_cycle=50,
    abort_on_missing=False,
    method="back-and-forth",
):
    if cycles is None:
        cycles = list(range(1, max_cycle + 1))
    all_curves = []
    keys = []
    for c in b:
        curves = c.get_cap(
            cycle=cycles,
            label_cycle_number=True,
            interpolated=interpolated,
            number_of_points=number_of_points,
            method=method,
        )
        if not curves.empty:
            all_curves.append(curves)
            keys.append(c.name)
        else:
            if abort_on_missing:
                raise ValueError(f"{c.name} is empty - aborting!")
            print(f"[{c.name} empty]")
    collected_curves = pd.concat(
        all_curves, keys=keys, axis=0, names=["cell", "point"]
    ).reset_index(level="cell")
    return collected_curves


def cycles_plotter_simple_holo_map(collected_curves, journal=None, **kwargs):
    p = hv.Curve(
        collected_curves, kdims="capacity", vdims=["voltage", "cycle", "cell"]
    ).groupby("cell")
    return p


def ica_plotter(
    collected_curves,
    journal=None,
    palette="Spectral",
    method="fig_pr_cell",
    extension="bokeh",
    cycles=None,
    cols=1,
    width=None,
):
    return sequence_plotter(
        collected_curves,
        x="voltage",
        y="dq",
        z="cycle",
        g="cell",
        journal=journal,
        palette=palette,
        method=method,
        extension=extension,
        cycles=cycles,
        cols=cols,
        width=width,
    )


def cycles_plotter(
    collected_curves,
    journal=None,
    palette="Spectral",
    method="fig_pr_cell",
    extension="bokeh",
    cycles=None,
    cols=1,
    width=None,
):
    return sequence_plotter(
        collected_curves,
        x="capacity",
        y="voltage",
        z="cycle",
        g="cell",
        journal=journal,
        palette=palette,
        method=method,
        extension=extension,
        cycles=cycles,
        cols=cols,
        width=width,
    )


def sequence_plotter(
    collected_curves,
    x,
    y,
    z,
    g,
    journal=None,
    palette="Spectral",
    method="fig_pr_cell",
    extension="bokeh",
    cycles=None,
    cols=1,
    width=None,
):
    # Should check current extension and 'set' it here if needed
    if method == "fig_pr_cell":
        if cycles is not None:
            filtered_curves = collected_curves.loc[
                collected_curves.cycle.isin(cycles), :
            ]
        else:
            filtered_curves = collected_curves
        p = hv.NdLayout(
            {
                label: hv.Curve(df, kdims=x, vdims=[y, z])
                .groupby(z)
                .overlay()
                .opts(hv.opts.Curve(color=hv.Palette(palette), title=label, backend=extension))
                for label, df in filtered_curves.groupby(g)
            }
        )
    elif method == "fig_pr_cycle":
        if cycles is None:
            cycles = [1, 10, 20]
        if width is None:
            width = int(800 / cols)

        z, g = g, z
        filtered_curves = collected_curves.loc[collected_curves.cycle.isin(cycles), :]
        p = (
            hv.NdLayout(
                {
                    cyc: hv.Curve(df, kdims=x, vdims=[y, z])
                    .groupby(z)
                    .overlay()
                    .opts(
                        hv.opts.Curve(
                            color=hv.Palette(palette), title=f"cycle-{cyc}", width=width, backend=extension
                        )
                    )
                    for cyc, df in filtered_curves.groupby(g)
                }
            )
            .cols(cols)
            .opts(hv.opts.NdOverlay(legend_position="right", backend=extension))
        )
    return p


def ica_collector(
    b,
    cycles=None,
    voltage_resolution=0.005,
    max_cycle=50,
    abort_on_missing=False,
    **kwargs,
):
    if cycles is None:
        cycles = list(range(1, max_cycle + 1))
    all_curves = []
    keys = []
    for c in b:
        curves = ica.dqdv_frames(
            c, cycle=cycles, voltage_resolution=voltage_resolution, **kwargs
        )
        if not curves.empty:
            all_curves.append(curves)
            keys.append(c.name)
        else:
            if abort_on_missing:
                raise ValueError(f"{c.name} is empty - aborting!")
            print(f"[{c.name} empty]")
    collected_curves = pd.concat(
        all_curves, keys=keys, axis=0, names=["cell", "point"]
    ).reset_index(level="cell")
    return collected_curves


class BatchSummaryCollector(BatchCollector):
    _default_data_collector_arguments = {
        "columns": ["charge_capacity_gravimetric"],
    }
    _default_plotter_arguments = {
        "extension": "bokeh",
    }

    def __init__(self, b, *args, **kwargs):
        super().__init__(
            b,
            plotter=plot_concatenated,
            data_collector=concatenate_summaries,
            collector_name="summary",
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
    _default_data_collector_arguments = {}
    _default_plotter_arguments = {
        "extension": "bokeh",
    }

    def __init__(self, b, plot_type="fig_pr_cell", *args, **kwargs):
        """Create a collection of ica (dQ/dV) plots."""

        self._default_plotter_arguments["method"] = plot_type
        super().__init__(
            b,
            plotter=ica_plotter,
            data_collector=ica_collector,
            collector_name="ica",
            *args,
            **kwargs,
        )

        self._templates["bokeh"] = hv.opts.Curve(xlabel="Voltage (V)", backend="bokeh", )


class BatchCyclesCollector(BatchCollector):
    _default_data_collector_arguments = {
        "interpolated": True,
        "number_of_points": 100,
        "max_cycle": 50,
        "abort_on_missing": False,
        "method": "back-and-forth",
    }
    _default_plotter_arguments = {
        "extension": "bokeh",
    }

    def __init__(
        self,
        b,
        plot_type="fig_pr_cell",
        collector_type="back-and-forth",
        *args,
        **kwargs,
    ):
        """Create a collection of capacity plots."""

        self._default_data_collector_arguments["method"] = collector_type
        self._default_plotter_arguments["method"] = plot_type
        super().__init__(
            b,
            plotter=cycles_plotter,
            data_collector=cycles_collector,
            collector_name="cycles",
            *args,
            **kwargs,
        )

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
