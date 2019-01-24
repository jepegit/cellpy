import logging

from cellpy.utils.batch_tools.batch_core import BaseExporter
from cellpy.utils.batch_tools.dumpers import csv_dumper, screen_dumper
from cellpy.utils.batch_tools.engines import summary_engine, cycles_engine


class CSVExporter(BaseExporter):
    """Export experiment(s) to csv-files.

    CSV Exporter looks at your experiments and exports data to csv
    format. It contains two engines: summary_engine and cycles_engine,
    and two dumpers: csv_dumper and screen_dumper.

    You assign experiments to CSVExporter either as input during
    instantiation or by issuing the assign(experiment) method.

    To perform the exporting, issue CSVExporter.do()

    Example:
        >>> exporter = CSVExporter(my_experiment)
        >>> exporter.do()

    Args:
        use_screen_dumper (bool): dump info to screen (default False).


    """
    def __init__(self, use_screen_dumper=False):
        super().__init__()
        self._assign_engine(summary_engine)
        self._assign_engine(cycles_engine)
        self._assign_dumper(csv_dumper)
        if use_screen_dumper:
            self._assign_dumper(screen_dumper)
        self.current_engine = None

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
        """
        logging.debug("running engine")
        self.current_engine = engine

        self.farms, self.barn = engine(
            experiments=self.experiments,
            farms=self.farms
        )

    def run_dumper(self, dumper):
        """run dumber (once pr. engine)

        Args:
            dumper: dumper to run (function or method).

        The dumper takes the attributes experiments, farms, and barn as input.
        """

        logging.debug("running dumper")
        dumper(
            experiments=self.experiments,
            farms=self.farms,
            barn=self.barn,
            engine=self.current_engine,
        )


class OriginLabExporter(BaseExporter):
    """Exporter that saves the files in a format convinent for OriginLab."""

    def __init__(self):
        super().__init__()


class ExcelExporter(BaseExporter):
    """Exporter that saves the file in a format that Excel likes."""
    def __init__(self):
        super().__init__()
