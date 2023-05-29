"""Collectors are used for simplifying plotting and exporting batch objects."""

import textwrap
from pprint import pprint
from pathlib import Path
from typing import Any
import inspect
import logging

import pandas as pd

import cellpy
from cellpy.readers.core import group_by_interpolate
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
    print("Could not import Holoviews. Plotting will be disabled.")
    HOLOVIEWS_AVAILABLE = False

CELLPY_MINIMUM_VERSION = "0.4.3"


def _setup():
    _welcome_message()
    _register_holoviews_renderers()


def _welcome_message():
    cellpy_version = cellpy.__version__
    logging.info(f"cellpy version: {cellpy_version}")
    logging.info(f"collectors need at least: {CELLPY_MINIMUM_VERSION}")


def _register_holoviews_renderers(extensions=None):
    if HOLOVIEWS_AVAILABLE:
        if extensions is None:
            extensions = "bokeh", "matplotlib"
        logging.info(
            f"Registering Holoviews extensions {extensions} for the cellpy collectors."
        )
        hv.extension(*extensions)
    else:
        logging.info(
            "Could not import Holoviews. Your collectors will not be able to make figures."
        )


def _set_holoviews_renderer(extension=None):
    if HOLOVIEWS_AVAILABLE:
        extension = extension.lower()
        current_backend = hv.Store.current_backend
        if not extension == current_backend:
            logging.info(f"switching backend to {extension}")
            hv.Store.set_current_backend(extension)


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
        use_templates=True,
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

        if nick is None:
            self.nick = b.name

        if name is None:
            name = self.generate_name()
        self.name = name

        if autorun:
            self.update(update_name=False)
            if use_templates:
                self.apply_templates()

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

    def _dynamic_update_template_parameter(self, hv_opt, extension, *args, **kwargs):
        return hv_opt

    def _register_template(self, hv_opts, extension="bokeh", *args, **kwargs):
        """Register template for given extension.

        It is also possible to set the options directly in the constructor of the
        class. But it is recommended to use this method instead to allow for
        sanitation of the options in the templates

        Args:
            hv_opts: list of holoviews.core.options.Options- instances
                e.g. [hv.opts.Curve(xlim=(0,2)), hv.opts.NdLayout(title="Super plot")]
            extension: Holoviews backend ("matplotlib", "bokeh", or "plotly")

        Returns:
            None
        """
        if extension not in ["bokeh", "matplotlib", "plotly"]:
            print(f"extension='{extension}' is not supported.")
        if not isinstance(hv_opts, (list, tuple)):
            hv_opts = [hv_opts]

        cleaned_hv_opts = []
        for o in hv_opts:
            logging.debug(f"Setting prm: {o}")
            o = self._dynamic_update_template_parameter(o, extension, *args, **kwargs)
            # ensure all options are registered with correct backend:
            o.kwargs["backend"] = extension
            cleaned_hv_opts.append(o)

        self._templates[extension] = cleaned_hv_opts

    def apply_templates(self):
        if not self._figure_valid():
            return

        for backend, hv_opt in self._templates.items():
            try:
                if len(hv_opt):
                    print(f"Applying template for {backend}:{hv_opt}")
                    self.figure = self._set_hv_opts(hv_opt)
            except TypeError:
                print("possible bug in apply_template experienced")
                print(self._templates)

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
        if isinstance(hv_opts, (tuple, list)):
            return self.figure.options(*hv_opts)
        else:
            return self.figure.options(hv_opts)

    def show(self, hv_opts=None):
        if not self._figure_valid():
            return

        print(f"figure name: {self.name}")
        return self._set_hv_opts(hv_opts)

    def redraw(self, hv_opts=None, extension=None):
        print("EXPERIMENTAL FEATURE! THIS MIGHT NOT WORK PROPERLY YET")
        if not self._figure_valid():
            return

        if extension is not None:
            _set_holoviews_renderer(extension)

        print(f"figure name: {self.name}")
        self.figure = self._set_hv_opts(hv_opts)
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

        filename_hv = filename_pre.with_suffix(".html")
        hv.save(
            self.figure,
            filename_hv,
            toolbar=self.toolbar,
        )
        print(f"saved file: {filename_hv}")

        filename_png = filename_pre.with_suffix(".png")
        try:
            current_renderer = _get_current_holoviews_renderer()

            _set_holoviews_renderer("matplotlib")
            self.figure.opts(hv.opts.NdOverlay(legend_position="right"))
            hv.save(
                self.figure,
                filename_png,
                dpi=300,
            )
            print(f"saved file: {filename_png}")
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
            try:
                Pickler.save(
                    self.figure,
                    filename,
                )
                print(f"pickled holoviews file: {filename}")
            except TypeError as e:
                print("could not save as hvz file")
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


def cycles_plotter_simple_holo_map(collected_curves, journal=None, **kwargs):
    p = hv.Curve(
        collected_curves, kdims="capacity", vdims=["voltage", "cycle", "cell"]
    ).groupby("cell")
    return p


def ica_plotter(
    collected_curves,
    journal=None,
    palette="Blues",
    palette_range=(0.2, 1.0),
    method="fig_pr_cell",
    extension="bokeh",
    cycles_to_plot=None,
    cols=1,
    width=None,
    height=None,
    xlim_charge=(None, None),
    xlim_discharge=(None, None),
    **kwargs,
):
    if method == "film":
        if extension == "matplotlib":
            print("SORRY, PLOTTING FILM WITH MATPLOTLIB IS NOT IMPLEMENTED YET")
            return

        return ica_plotter_film_bokeh(
            collected_curves,
            journal=journal,
            palette=palette,
            extension="bokeh",
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
            extension=extension,
            cycles=cycles_to_plot,
            cols=cols,
            width=width,
        )


def ica_plotter_film_bokeh(
    collected_curves,
    palette="Blues",
    cycles=None,
    xlim_charge=(None, None),
    xlim_discharge=(None, None),
    ylim=(None, None),
    shared_axes=True,
    width=400,
    height=500,
    cformatter="%02.0e",
    **kwargs,
):
    if cycles is not None:
        filtered_curves = collected_curves.loc[collected_curves.cycle.isin(cycles), :]
    else:
        filtered_curves = collected_curves

    options = {
        "xlabel": "Voltage (V)",
        "ylabel": "Cycle",
        "ylim": ylim,
        "tools": ["hover"],
        "width": width,
        "height": height,
        "cmap": palette,
        "cformatter": cformatter,
        "cnorm": "eq_hist",
        "shared_axes": shared_axes,
        "colorbar_opts": {
            "title": "dQ/dV",
        },
    }

    all_charge_plots = {}
    all_discharge_plots = {}
    for label, df in filtered_curves.groupby("cell"):
        _charge = df.query("direction==1")
        _discharge = df.query("direction==-1")
        _dq_charge = group_by_interpolate(
            _charge, x="voltage", y="dq", group_by="cycle", number_of_points=400
        )
        _dq_discharge = group_by_interpolate(
            _discharge, x="voltage", y="dq", group_by="cycle", number_of_points=400
        )

        _v_charge = _dq_charge.index.values.ravel()
        _v_discharge = _dq_discharge.index.values.ravel()

        _cycles_charge = _charge.cycle.unique().ravel()
        _cycles_discharge = _discharge.cycle.unique().ravel()

        _dq_charge = -_dq_charge.values.T
        _dq_discharge = _dq_discharge.values.T

        charge_plot = hv.Image(
            (_v_charge, _cycles_charge, _dq_charge), group="ica", label="charge"
        ).opts(title=f"{label}", xlim=xlim_charge, colorbar=True, **options)

        discharge_plot = hv.Image(
            (_v_discharge, _cycles_discharge, _dq_discharge),
            group="ica",
            label="discharge",
        ).opts(title=f"{label}", xlim=xlim_discharge, colorbar=True, **options)

        all_charge_plots[f"{label}_charge"] = charge_plot
        all_discharge_plots[f"{label}_discharge"] = discharge_plot

    all_plots = {**all_charge_plots, **all_discharge_plots}
    return (
        hv.NdLayout(all_plots)
        .opts(title="Incremental Capacity Analysis Film-plots")
        .cols(2)
    )


def cycles_plotter(
    collected_curves,
    method="fig_pr_cell",
    extension="bokeh",
    cycles_to_plot=None,
    width=None,
    palette=None,
    palette_range=(0.1, 1.0),
    legend_position=None,
    show_legend=None,
    fig_title="",
    cols=None,
    **kwargs,
):
    if cols is None:
        if extension == "matplotlib":
            cols = 3
        else:
            cols = 3 if method == "fig_pr_cell" else 1

    if width is None:
        width = 400 if method == "fig_pr_cell" else int(800 / cols)

    if palette is None:
        palette = "Blues" if method == "fig_pr_cell" else "Category10"

    if palette_range is None:
        palette_range = (0.2, 1.0) if method == "fig_pr_cell" else (0, 1)

    if legend_position is None:
        legend_position = None if method == "fig_pr_cell" else "right"

    if show_legend is None:
        show_legend = True

    reverse_palette = True if method == "fig_pr_cell" else False

    backend_specific_kwargs = {
        "NdLayout": {},
        "NdOverlay": {},
        "Curve": {},
    }

    if extension != "matplotlib":
        logging.debug(f"setting width for bokeh and plotly: {width}")
        backend_specific_kwargs["Curve"]["width"] = width

    p = sequence_plotter(
        collected_curves,
        x="capacity",
        y="voltage",
        z="cycle",
        g="cell",
        method=method,
        cycles=cycles_to_plot,
        **kwargs,
    ).cols(cols)

    p.opts(
        hv.opts.NdLayout(
            title=fig_title,
            **backend_specific_kwargs["NdLayout"],
            backend=extension,
        ),
        hv.opts.NdOverlay(
            **backend_specific_kwargs["NdOverlay"],
            backend=extension,
        ),
        hv.opts.Curve(
            # TODO: should replace this with custom mapping (see how it is done in plotutils):
            color=hv.Palette(palette, reverse=reverse_palette, range=palette_range),
            show_legend=show_legend,
            **backend_specific_kwargs["Curve"],
            backend=extension,
        ),
    )

    if legend_position is not None:
        p.opts(hv.opts.NdOverlay(legend_position=legend_position))

    return p


def sequence_plotter(
    collected_curves,
    x,
    y,
    z,
    g,
    method="fig_pr_cell",
    group_label="group",
    group_txt="cell-group",
    z_lim=10,
    cycles=None,
    **kwargs,
):
    for k in kwargs:
        logging.debug(f"keyword argument {k} given, but not used")

    x_label = "Capacity"
    x_unit = "mAh"

    y_label = "Voltage"
    y_unit = "V"

    g_label = "Cell"
    g_unit = ""

    z_label = "Cycle"
    z_unit = ""

    x_dim = hv.Dimension(f"{x}", label=x_label, unit=x_unit)
    y_dim = hv.Dimension(f"{y}", label=y_label, unit=y_unit)
    g_dim = hv.Dimension(f"{g}", label=g_label, unit=g_unit)
    z_dim = hv.Dimension(f"{z}", label=z_label, unit=z_unit)

    family = {}
    curves = None

    if method == "fig_pr_cell":
        if cycles is not None:
            curves = collected_curves.loc[collected_curves.cycle.isin(cycles), :]
        else:
            curves = collected_curves
        logging.debug(f"filtered_curves:\n{curves}")

    elif method == "fig_pr_cycle":
        if cycles is None:
            unique_cycles = list(collected_curves.cycle.unique())
            if len(unique_cycles) > 10:
                cycles = [1, 10, 20]
        if cycles is not None:
            curves = collected_curves.loc[collected_curves.cycle.isin(cycles), :]
        else:
            curves = collected_curves
        # g (what we split the figures by) : cycle
        # z (the "dimension" of the individual curves in one figure): cell
        z, g = g, z
        z_dim, g_dim = g_dim, z_dim

        # dirty (?) fix to make plots with a lot of cells look a bit better:
        unique_z_values = collected_curves[z].unique()
        no_unique_z_values = len(unique_z_values)
        if no_unique_z_values > z_lim:
            logging.critical(
                f"number of cells ({no_unique_z_values}) larger than z_lim ({z_lim}): grouping"
            )
            logging.critical(
                f"prevent this by modifying z_lim to your plotter_arguments"
            )
            z = group_label
            z_dim = hv.Dimension(f"{z}", label=group_txt, unit="")

    kdims = x_dim
    vdims = [y_dim, z_dim]
    for cyc, df in curves.groupby(g):
        family[cyc] = hv.Curve(df, kdims=kdims, vdims=vdims).groupby(z).overlay()

    return hv.NdLayout(family, kdims=g_dim)


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
        logging.debug(f"processing {n} (session name: {c.cell_name})")
        if not curves.empty:
            curves = curves.assign(group=g, sub_group=sg)
            all_curves.append(curves)
            keys.append(n)
        else:
            if abort_on_missing:
                raise ValueError(f"{n} is empty - aborting!")
            logging.critical(f"[{n} (session name: {c.cell_name}) empty]")
    collected_curves = pd.concat(
        all_curves, keys=keys, axis=0, names=["cell", "point"]
    ).reset_index(level="cell")
    return collected_curves


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
        "extension": "bokeh",
    }

    _bokeh_template = [
        hv.opts.Curve(fontsize={"title": "medium"}, width=800, backend="bokeh"),
        hv.opts.NdOverlay(legend_position="right", backend="bokeh"),
    ]

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
        extension: str = None,
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
            extension (str): extension used (defaults to Bokeh)
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
            "extension": extension,
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

        self._register_template(self._bokeh_template, extension="bokeh")

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
    _default_data_collector_arguments = {}
    _default_plotter_arguments = {
        "extension": "bokeh",
    }

    def __init__(self, b, plot_type="fig_pr_cell", *args, **kwargs):
        """Create a collection of ica (dQ/dV) plots."""

        self.plot_type = plot_type

        if plot_type == "fig_pr_cell":
            _tight = True
            _fig_inches = 3.5
        else:
            _tight = False
            _fig_inches = 5.5

        matplotlib_template = [
            hv.opts.Curve(
                show_frame=True,
                fontsize={"title": "medium"},
                backend="matplotlib",
            ),
            hv.opts.NdLayout(
                fig_inches=_fig_inches, tight=_tight, backend="matplotlib"
            ),
        ]

        bokeh_template = [
            hv.opts.Curve(xlabel="Voltage (V)", backend="bokeh"),
        ]
        self._default_plotter_arguments["method"] = plot_type
        self._register_template(matplotlib_template, extension="matplotlib")
        self._register_template(bokeh_template, extension="bokeh")
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
    _default_plotter_arguments = {
        "extension": "bokeh",
    }

    def __init__(
        self,
        b,
        plot_type="fig_pr_cell",
        collector_type="back-and-forth",
        cycles=None,
        max_cycle=None,
        label_mapper=None,
        extension=None,
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
            extension (str): extension used (defaults to Bokeh)
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
            extension=extension,
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

        # moving it to after init to allow for using prms set in init
        if plot_type == "fig_pr_cell":
            _tight = True
            _fig_inches = 3.5
        else:
            _tight = False
            _fig_inches = 5.5

        matplotlib_template = [
            hv.opts.Curve(
                show_frame=True,
                fontsize={"title": "medium"},
                ylim=(0, 1),
                backend="matplotlib",
            ),
            hv.opts.NdLayout(
                fig_inches=_fig_inches, tight=_tight, backend="matplotlib"
            ),
        ]

        self._max_letters_in_cell_names = max(len(x) for x in b.cell_names)
        self._register_template(matplotlib_template, extension="matplotlib")
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

    def _dynamic_update_template_parameter(self, hv_opt, extension, *args, **kwargs):
        k = hv_opt.key
        if k == "NdLayout" and extension == "matplotlib":
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
