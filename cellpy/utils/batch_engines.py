import logging
import os
import pandas as pd
import json


class Doer:
    """Base class for all the classes that do something to the experiment"""
    def __init__(self, *args):
        self.experiments = []
        args = self._validate_base_experiment_type(args)
        if args:
            self.experiments.extend(args)

    def __str__(self):
        return self.__class__.__name__

    def __repr__(self):
        return self.__class__.__name__

    @staticmethod
    def _validate_base_experiment_type(args):
        if len(args) == 0:
            return None

        for arg in args:
            if not isinstance(arg, BaseExperiment):
                err = f"{repr(arg)} is not instance of BaseExperiment"
                raise TypeError(err)
        return args

    def info(self):
        print("Sorry, but I don't have much to share.")
        print("This is me:")
        print(self)
        print("And these are the experiments assigned to me:")
        print(self.experiments)

    def assign(self, experiment):
        self.experiments.append(experiment)

    def do(self):
        print("Sorry, don't know what I should do!")


class BaseExperiment:
    """An experiment contains experimental data and meta-data."""
    def __init__(self):
        self.journal = None
        self.data = None
        self.log_level = "INFO"

    def __str__(self):
        return f"{self.__class__.__name__}\n" \
               f"journal: \n{str(self.journal)}\n" \
               f"data: \n{str(self.data)}"

    def __repr__(self):
        return self.__class__.__name__

    def update(self):
        """get data"""
        pass


class BaseJournal:
    """A journal keeps track of the details of the experiment.

    The journal should at a mimnimum conain information about the name and
    project the experiment has."""

    packable = [
        'name', 'project',
        'time_stamp', 'project_dir',
        'batch_dir', 'raw_dir'
    ]

    def __init__(self):
        self.pages = None  # pandas.DataFrame
        self.name = None
        self.project = None
        self.parameter_values = None
        self.file_name = None
        self.time_stamp = None
        self.project_dir = None
        self.batch_dir = None
        self.raw_dir = None

    def __str__(self):
        return f"{self.__class__.__name__}\n" \
               f"  - name: {str(self.name)}\n" \
               f"  - project: {str(self.project)}\n"\
               f"  - parameter_values: {str(self.parameter_values)}\n" \
               f"  - file_name: {str(self.file_name)}\n" \
               f"  - pages: \n{str(self.pages)}"

    def __repr__(self):
        return self.__class__.__name__

    def _prm_packer(self, metadata=None):
        if metadata is None:
            _metadata = dict()
            for p in self.packable:
                _metadata[p] = getattr(self, p)
            return _metadata

        else:
            for p in metadata:
                if hasattr(self, p):
                    setattr(self, p, metadata[p])
                else:
                    print(f"UNKNOWN VAR: {p}")

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


# Do-ers
class BaseExporter(Doer):
    """An exporter exports your data to a given format"""
    def __init__(self, *args):
        super().__init__(*args)
        self.engines = None
        self.dumpers = None
        self.experiment = None

    def _assign_engine(self, name=None):
        pass

    def _assign_dumper(self, name=None):
        pass

    def _generate_name(self):
        pass


class BasePlotter(Doer):
    def __init__(self, *args):
        super().__init__(*args)


class BaseReporter(Doer):
    def __init__(self, *args):
        super().__init__(*args)


class BaseAnalyzer(Doer):
    def __init__(self, *args):
        super().__init__(*args)


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
        self.journal = LabJournal()


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
        self.db_reader = "excel"

    def _check_file_name(self, file_name):
        if file_name is None:
            if not self.file_name:
                self.generate_file_name()
            file_name = self.file_name
        return file_name

    def from_db(self, col=5):
        name = self.name
        project = self.project

        # self.pages = None  # pandas.DataFrame
        # self.name = None
        # self.project = None
        # self.parameter_values = None
        # self.file_name = None

    def from_file(self, file_name=None):
        """Loads a DataFrame with all the needed info about the run
            (JSON file)"""

        file_name = self._check_file_name(file_name)

        with open(file_name, 'r') as infile:
            top_level_dict = json.load(infile)

        pages_dict = top_level_dict['info_df']
        pages = pd.DataFrame(pages_dict)
        self.pages = pages
        self.file_name = file_name
        self._prm_packer(top_level_dict['metadata'])

    def to_file(self, file_name=None):
        file_name = self._check_file_name(file_name)

    def generate_file_name(self):
        return "filename"

    def look_for_file(self):
        pass


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
    pages = "/Users/jepe/scripting/cellpy/dev_data/cellpy_batch_test.json"
    my_experiment = CyclingExperiment()
    my_experiment.journal.from_file(pages)
    prebens_experiment = CyclingExperiment()

    my_exporter = CSVExporter()
    my_analyzer = BaseAnalyzer()
    my_plotter = BasePlotter()

    # print(my_experiment)
    # print(my_exporter)

    print("-----plotter-----")
    my_plotter.assign(my_experiment)
    my_plotter.do()
    my_plotter.info()

    print("----reporter----")
    my_reporter = BaseReporter(my_experiment, prebens_experiment)
    my_reporter.do()
    my_reporter.info()

    print("----content-in-journal----")
    print(my_experiment.journal)


if __name__ == "__main__":
    print(60 * "-")
    print("Running main in batch_engines")
    print(60 * "-")
    main()
    print(60 * "-")
