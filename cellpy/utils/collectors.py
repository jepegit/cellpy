from pathlib import Path
from typing import Any

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
    b: Batch = None
    data: pd.DataFrame = None
    figure: Any = None
    name: str = None
    figure_directory: Path = Path("out")
    data_directory: Path = Path("data/processed/")

    def update(self):
        pass

    def show(self):
        pass

    def to_csv(self):
        pass

    def to_html(self):
        pass

    def save(self):
        pass


class BatchSummaryCollector(BatchCollector):
    data_collector_arguments = {
        "columns": ["charge_capacity_gravimetric"],
    }
    plotter_arguments = {
        "extension": "bokeh",
    }

    def __init__(
        self,
        b: Batch,
        name=None,
        nick=None,
        autorun=True,
        data_collector_arguments: dict = None,
        plotter_arguments: dict = None,
        **kwargs,
    ):
        if data_collector_arguments is not None:
            self.data_collector_arguments = {**self.data_collector_arguments, **data_collector_arguments}

        if plotter_arguments is not None:
            self.plotter_arguments = {**self.plotter_arguments, **plotter_arguments}

        self._set_attributes(**kwargs)
        self.b = b
        self.nick = nick

        if name is None:
            name = self._generate_name()
        self.name = name

        if autorun:
            self.update(update_name=False)

    def _set_attributes(self, **kwargs):
        self.sep = kwargs.get("sep", ";")
        self.csv_include_index = kwargs.get("csv_include_index", True)
        self.toolbar = kwargs.get("toolbar", True)

    def _generate_name(self):
        names = ["collected_summaries"]
        cols = self.data_collector_arguments.get("columns")
        grouped = self.data_collector_arguments.get("group_it")
        if self.nick:
            names.insert(0, self.nick)
        if cols:
            names.extend(cols)
        if grouped:
            names.append("average")
        name = "_".join(names)
        return name

    def update(
        self,
        data_collector_arguments: dict = None,
        plotter_arguments: dict = None,
        update_name=True,
        **kwargs,
    ):
        self.data = concatenate_summaries(self.b, **self.data_collector_arguments)
        if HOLOVIEWS_AVAILABLE:
            self.figure = plot_concatenated(
                self.data, journal=self.b.journal, **self.plotter_arguments
            )
        if update_name:
            self.name = self._generate_name()

    def show(self):
        if HOLOVIEWS_AVAILABLE:
            return self.figure

    def to_csv(self):
        self.data.to_csv(
            f"{self.data_directory}/{self.name}.csv",
            sep=self.sep,
            index=self.csv_include_index,
        )

    def to_html(self):
        hv.save(
            self.figure,
            f"{self.figure_directory}/{self.name}.html",
            toolbar=self.toolbar,
        )

    def save(self):
        if HOLOVIEWS_AVAILABLE:
            Pickler.save(
                self.figure,
                f"{self.figure_directory}/{self.name}.hvz",
            )
        self.to_csv()
        self.to_html()
