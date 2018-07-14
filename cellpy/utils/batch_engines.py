import logging
import os
import pandas as pd


class BaseExperiment:
    def __init__(self):
        self.journal = None
        self.data = None


class BaseJournal:
    def __init__(self):
        self.pages = None  # pandas.DataFrame
        self.name = None
        self.project = None
        self.parameter_values = None
        self.file_name = None

    def from_db(self):
        pass

    def from_file(self, file_name):
        pass

    def to_file(self, file_name=None):
        pass

    def generate_file_name(self):
        pass

    def look_for_file(self):
        pass


class BaseExporter:
    def __init__(self):
        self.engines = None
        self.dumpers = None
        self.experiment = None

    def _assign_engine(self, name=None):
        pass

    def _assign_dumper(self, name=None):
        pass


class BasePlotter:
    pass


class BaseReporter:
    pass


class BaseAnalyzer:
    pass


# Engines
def cycles_engine():
    pass


def dq_dv_engine():
    pass


# Dumpers
def csv_dumper():
    pass


def excel_dumper():
    pass


def origin_dumper():
    pass


# Experiments
class CyclingExperiment(BaseExperiment):
    pass


class ImpedanceExperiment(BaseExperiment):
    pass


class LifeTimeExperiment(BaseExperiment):
    pass


# Journals
class LabJournal(BaseJournal):
    pass


# Exporters
class CSVExporter(BaseExporter):
    def __init__(self):
        super()
        self._assign_engine("cycles_engine")
        self._assign_dumper("csv_dumper")


class OriginLabExporter(BaseExporter):
    pass


class ExcelExporter(BaseExporter):
    pass


def main():
    my_exporter = CSVExporter()
    print(my_exporter)


if __name__ == "__main__":
    print("running main in batch_engines")
    main()
