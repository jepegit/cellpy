"""Collectors are used for simplifying plotting and exporting batch objects."""

import textwrap
from pprint import pprint
from pathlib import Path
from typing import Any
import inspect

import pandas as pd

from cellpy.utils.batch import Batch
from cellpy.utils.helpers import concatenate_summaries
from cellpy.utils.plotutils import plot_concatenated

try:
    import holoviews as hv
    from holoviews.core.io import Pickler
    from holoviews import opts

    HOLOVIEWS_AVAILABLE = True
except ImportError:
    print("Could not import holoviews. Plotting will be disabled.")
    HOLOVIEWS_AVAILABLE = False


class BatchCollector:
    data: pd.DataFrame = None
    figure: Any = None
    name: str = None
    nick: str = None
    autorun: bool = True
    figure_directory: Path = Path("out")
    data_directory: Path = Path("data/processed/")
    # defaults when resetting:
    _data_collector_arguments = {}
    _plotter_arguments = {}

    def __init__(
        self,
        b,
        data_collector,
        plotter,
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
        self.data_collector_arguments = self._data_collector_arguments.copy()
        self.plotter_arguments = self._plotter_arguments.copy()
        self._update_arguments(data_collector_arguments, plotter_arguments)
        self._set_attributes(**kwargs)

        if nick is None:
            self.nick = b.name

        if name is None:
            name = self.generate_name()
        self.name = name

        if autorun:
            self.update(update_name=False)

    def _set_attributes(self, **kwargs):
        self.sep = kwargs.get("sep", ";")
        self.csv_include_index = kwargs.get("csv_include_index", True)
        self.toolbar = kwargs.get("toolbar", True)

    def generate_name(self):
        names = [f"collector{self}"]
        if self.nick:
            names.insert(0, self.nick)
        name = "_".join(names)
        return name

    def _update_arguments(
        self, data_collector_arguments: dict = None, plotter_arguments: dict = None
    ):
        if data_collector_arguments is not None:
            self.data_collector_arguments = {
                **self.data_collector_arguments,
                **data_collector_arguments,
            }

        if plotter_arguments is not None:
            self.plotter_arguments = {**self.plotter_arguments, **plotter_arguments}

    def reset_arguments(
        self, data_collector_arguments: dict = None, plotter_arguments: dict = None
    ):
        """Reset the arguments to the defaults.
        Args:
            data_collector_arguments (dict): optional additional keyword arguments for the data collector.
            plotter_arguments (dict): optional additional keyword arguments for the plotter.
        """
        self.data_collector_arguments = self._data_collector_arguments.copy()
        self.plotter_arguments = self._plotter_arguments.copy()
        self._update_arguments(data_collector_arguments, plotter_arguments)

    def update(
        self,
        data_collector_arguments: dict = None,
        plotter_arguments: dict = None,
        reset: bool = False,
        update_name: bool = False,
    ):
        """Update both the collected data and the plot(s).
        Args:
            data_collector_arguments (dict): keyword arguments sent to the data collector.
            plotter_arguments (dict): keyword arguments sent to the plotter.
            reset (bool): reset the arguments first.
            update_name (bool): update the name (using automatic name generation) based on new settings.
        """
        if reset:
            self.reset_arguments(data_collector_arguments, plotter_arguments)
        else:
            self._update_arguments(data_collector_arguments, plotter_arguments)
        try:
            self.data = self.data_collector(self.b, **self.data_collector_arguments)
        except TypeError as e:
            print("Type error:", e)
            print("Registered data_collector_arguments:")
            pprint(self.data_collector_arguments)
            print("Hint: fix it and then re-run using reset=True")
            return

        if HOLOVIEWS_AVAILABLE:
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

    def show(self, hv_opts=None):
        print(f"figure name: {self.name}")
        if HOLOVIEWS_AVAILABLE:
            if hv_opts is not None:
                return self.figure.opts(hv_opts)
            else:
                return self.figure

    def to_csv(self):
        filename = (Path(self.data_directory) / self.name).with_suffix(".csv")
        self.data.to_csv(
            filename,
            sep=self.sep,
            index=self.csv_include_index,
        )
        print(f"saved csv file: {filename}")

    def to_image_files(self):
        # TODO: include png
        filename_pre = Path(self.figure_directory) / self.name
        if HOLOVIEWS_AVAILABLE:
            filename_hv = filename_pre.with_suffix(".html")
            hv.save(
                self.figure,
                filename_hv,
                toolbar=self.toolbar,
            )
            print(f"saved file: {filename_pre}")

    def save(self):
        if HOLOVIEWS_AVAILABLE:
            filename = (Path(self.figure_directory) / self.name).with_suffix(".hvz")
            Pickler.save(
                self.figure,
                filename,
            )
            print(f"pickled holoviews file: {filename}")
        self.to_csv()
        self.to_image_files()


class BatchSummaryCollector(BatchCollector):
    _data_collector_arguments = {
        "columns": ["charge_capacity_gravimetric"],
    }
    _plotter_arguments = {
        "extension": "bokeh",
    }

    def __init__(self, b, *args, **kwargs):
        super().__init__(
            b,
            plotter=plot_concatenated,
            data_collector=concatenate_summaries,
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


def cycles_plotter(
    collected_curves, journal=None, palette="Spectral", plot_method=None, **kwargs
):
    plot_method = plot_method or "fig_pr_cell"
    if plot_method == "fig_pr_cell":
        p = hv.NdLayout(
            {
                label: hv.Curve(df, kdims="capacity", vdims=["voltage", "cycle"])
                .groupby("cycle")
                .overlay()
                .opts(hv.opts.Curve(color=hv.Palette(palette), title=label))
                for label, df in collected_curves.groupby("cell")
            }
        )
    elif plot_method == "fig_pr_cycles":
        cycles = kwargs.pop("cycles", [1, 10, 20])
        cols = kwargs.pop("cols", 1)
        width = kwargs.pop("width", int(800 / cols))
        filtered_curves = collected_curves.loc[collected_curves.cycle.isin(cycles), :]
        p = (
            hv.NdLayout(
                {
                    cyc: hv.Curve(df, kdims="capacity", vdims=["voltage", "cell"])
                    .groupby("cell")
                    .overlay()
                    .opts(
                        hv.opts.Curve(
                            color=hv.Palette(palette), title=f"cycle-{cyc}", width=width
                        )
                    )
                    for cyc, df in filtered_curves.groupby("cycle")
                }
            )
            .cols(1)
            .opts(hv.opts.NdOverlay(legend_position="right"))
        )
    return p


class BatchCyclesCollector(BatchCollector):
    _data_collector_arguments = {
        "interpolated": True,
        "number_of_points": 100,
        "max_cycle": 50,
        "abort_on_missing": False,
    }
    _plotter_arguments = {
        # "extension": "bokeh",
    }

    def __init__(self, b, *args, **kwargs):
        super().__init__(
            b, plotter=cycles_plotter, data_collector=cycles_collector, *args, **kwargs
        )

    def generate_name(self):
        names = ["collected_cycles"]
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
