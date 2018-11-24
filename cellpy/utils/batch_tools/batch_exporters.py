import logging

from cellpy.utils.batch_tools.batch_core import BaseExporter
from cellpy.utils.batch_tools.dumpers import csv_dumper
from cellpy.utils.batch_tools.engines import summary_engine, cycles_engine


class CSVExporter(BaseExporter):
    def __init__(self):
        super().__init__()
        self._assign_engine(summary_engine)
        self._assign_engine(cycles_engine)
        self._assign_dumper(csv_dumper)
        # self._assign_dumper(screen_dumper)

    def run_engine(self, engine):
        logging.debug("running engine")
        self.farms, self.barn = engine(
            experiments=self.experiments,
            farms=self.farms
        )

    def run_dumper(self, dumper):
        logging.debug("running dumper")
        dumper(
            experiments=self.experiments,
            farms=self.farms,
            barn=self.barn
        )


class OriginLabExporter(BaseExporter):
    def __init__(self):
        super().__init__()


class ExcelExporter(BaseExporter):
    def __init__(self):
        super().__init__()
