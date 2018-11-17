import logging
import os
import pandas as pd


class BaseExperiment:
    """An experiment contains experimental data and meta-data."""
    def __init__(self):
        self.journal = None
        self.data = None

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__class__.__name__


class BaseJournal:
    """A journal keeps track of the details of the experiment.

    The journal should at a mimnimum conain information about the name and
    project the experiment has."""

    def __init__(self):
        self.pages = None  # pandas.DataFrame
        self.name = None
        self.project = None
        self.parameter_values = None
        self.file_name = None

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__class__.__name__

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
    """An exporter ..."""
    def __init__(self):
        self.engines = None
        self.dumpers = None
        self.experiment = None

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__class__.__name__

    def _assign_engine(self, name=None):
        pass

    def _assign_dumper(self, name=None):
        pass


class BasePlotter:
    def __init__(self):
        pass

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__class__.__name__


class BaseReporter:
    def __init__(self):
        pass

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__class__.__name__


class BaseAnalyzer:
    def __init__(self):
        pass

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__class__.__name__


# Engines
def cycles_engine():
    """engine to extract cycles"""
    pass


def dq_dv_engine():
    """engine that performs incremental analysis of the cycle-data"""
    pass


# Dumpers
def csv_dumper():
    """dump data to csv"""
    pass


def excel_dumper():
    """dump data to excel xlxs-format"""
    pass


def origin_dumper():
    """dump data to a format suitable for use in OriginLab"""
    pass


# Experiments
class CyclingExperiment(BaseExperiment):
    def __init__(self):
        super().__init__()


class ImpedanceExperiment(BaseExperiment):
    def __init__(self):
        super().__init__()


class LifeTimeExperiment(BaseExperiment):
    def __init__(self):
        super().__init__()


# Journals
class LabJournal(BaseJournal):
    def __init__(self):
        super().__init__()


# Exporters
class CSVExporter(BaseExporter):
    def __init__(self):
        super().__init__()
        self._assign_engine("cycles_engine")
        self._assign_dumper("csv_dumper")


class OriginLabExporter(BaseExporter):
    def __init__(self):
        super().__init__()


class ExcelExporter(BaseExporter):
    def __init__(self):
        super().__init__()


def main():
    my_experiment = CyclingExperiment()
    my_journal = LabJournal()
    my_exporter = CSVExporter()

    my_experiment.journal = my_journal
    print(my_journal)
    print(my_experiment)
    print(my_exporter)


if __name__ == "__main__":
    print(60 * "-")
    print("Running main in batch_engines")
    print(60 * "-")
    main()
    print(60 * "-")
