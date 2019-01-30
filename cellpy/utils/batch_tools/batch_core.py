import logging
import abc

from cellpy import cellreader
from cellpy.exceptions import UnderDefined


empty_farm = []


class Doer(metaclass=abc.ABCMeta):
    """Base class for all the classes that do something to the experiment.

    Attributes:
        experiments: list of experiments.
        farms: list of farms (containing pandas DataFrames) (one pr experiment).
        barn (str): identifier for where to place the output-files.
    """

    def __init__(self, *args):
        self.experiments = []
        self.farms = []
        self.barn = None
        args = self._validate_base_experiment_type(args)
        if args:
            self.experiments.extend(args)
            self.farms.append(empty_farm)

    def __str__(self):
        return f"({self.__class__.__name__})"

    def __repr__(self):
        return self.__class__.__name__

    @staticmethod
    def _validate_base_experiment_type(args):
        if len(args) == 0:
            return None

        for arg in args:
            if not isinstance(arg, BaseExperiment):
                err = f"{repr(arg)} is not an instance of BaseExperiment"
                raise TypeError(err)
        return args

    def info(self):
        """Delivers some info to you about the class."""

        print("Sorry, but I don't have much to share.")
        print("This is me:")
        print(self)
        print("And these are the experiments assigned to me:")
        print(self.experiments)

    def assign(self, experiment):
        """Assign an experiment."""

        self.experiments.append(experiment)
        self.farms.append(empty_farm)

    def empty_the_farms(self):
        """Free all the farms for content (empty all lists)."""

        logging.debug("emptying the farm for all the pandas")
        self.farms = [[] for _ in self.farms]

    @abc.abstractmethod
    def do(self):
        pass


class Data(dict):
    """Class that is used to access the experiment.journal.pages DataFrame.

    The Data class loads the complete cellpy-file if dfdata is not already
    loaded in memory. In future version, it could be that the Data object
    will return a link allowing querying instead to save memory usage...

    Remark that some cellpy (cellreader.CellpyData) function might not work if
    you have the dfdata in memory, but not summary data (if the cellpy function
    requires summary data or other settings not set as default).
    """

    # TODO (jepe): decide if we should inclued querying functionallity here.

    def __init__(self, experiment, *args):
        super().__init__(*args)
        self.experiment = experiment
        self.query_mode = False

    def __getitem__(self, id):
        cellpy_data_object = self.__look_up__(id)
        return cellpy_data_object

    def __str__(self):
        t = ""
        if not self.experiment.cell_data_frames:
            t += "{}"
        else:
            for k in self.experiment.cell_data_frames:
                t += f"'{k}'\n"
                t += str(self.experiment.cell_data_frames[k])
                t += "\n"

        t += "\n"
        return t

    def __look_up__(self, identification):
        try:
            if not self.experiment.cell_data_frames[
                identification
            ].dataset.dfdata.empty:
                return self.experiment.cell_data_frames[identification]
            else:
                raise AttributeError

        except AttributeError:
            logging.debug("looking up from cellpyfile")
            pages = self.experiment.journal.pages
            info = pages.loc[identification, :]
            cellpy_file = info["cellpy_file_names"]
            # linking not implemented yet - loading whole file in mem instead
            if not self.query_mode:
                return self.experiment._load_cellpy_file(cellpy_file)
            else:
                raise NotImplementedError


class BaseExperiment(metaclass=abc.ABCMeta):
    """An experiment contains experimental data and meta-data."""
    def __init__(self, *args):
        self.journal = None
        self.summary_frames = None
        self.cell_data_frames = None
        self.memory_dumped = dict()
        self.parent_level = "CellpyData"
        self.log_level = "INFO"

    def __str__(self):
        return f"[{self.__class__.__name__}]\n" \
               f"journal: \n{str(self.journal)}\n" \
               f"data: \n{str(self.data)}"

    def __repr__(self):
        return self.__class__.__name__

    def _link_cellpy_file(self, file_name):
        raise NotImplementedError

    def _load_cellpy_file(self, file_name):
        cellpy_data = cellreader.CellpyData()
        cellpy_data.load(file_name, self.parent_level)
        logging.info(f" <- {file_name}")
        return cellpy_data

    @property
    def data(self):
        """Property for accessing the underlying data in an experiment.

        Example:
            >>> cell_data_one = experiment.data["2018_cell_001"]
            >>> capacity, voltage = cell_data_one.get_cap(cycle=1)
        """

        data_object = Data(self)
        return data_object

    @abc.abstractmethod
    def update(self):
        """Get or link data."""
        pass

    def status(self):
        """Describe the status and health of your experiment."""
        raise NotImplementedError

    def info(self):
        """Print information about the experiment."""
        print(self)


class BaseJournal:
    """A journal keeps track of the details of the experiment.

    The journal should at a mimnimum contain information about the name and
    project the experiment has.

    Attributes:
        pages (pandas.DataFrame): table with information about each cell/file.
        name (str): the name of the experiment (used in db-lookup).
        project(str): the name of the project the experiment belongs to (used
           for making folder names).
        file_name (str or path): the file name used in the to_file method.
        project_dir: folder where to put the batch (or experiment) files and
           information.
        batch_dir: folder in project_dir where summary-files and information
            and results related to the current experiment are stored.
        raw_dir: folder in batch_dir where cell-specific information and results
            are stored (e.g. raw-data, dq/dv data, voltage-capacity cycles).

    """

    packable = [
        'name', 'project',
        'time_stamp', 'project_dir',
        'batch_dir', 'raw_dir'
    ]

    def __init__(self):
        self.pages = None  # pandas.DataFrame
        self.name = None
        self.project = None
        self.file_name = None
        self.time_stamp = None
        self.project_dir = None
        self.batch_dir = None
        self.raw_dir = None

    def __str__(self):
        return f"({self.__class__.__name__})\n" \
               f"  - name: {str(self.name)}\n" \
               f"  - project: {str(self.project)}\n"\
               f"  - file_name: {str(self.file_name)}\n" \
               f"  - pages: ->\n{str(self.pages)}\n" \
               f"           <-\n"

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
                    logging.debug(f"unknown variable encountered: {p}")

    def from_db(self):
        """Make journal pages by looking up a database.

        Default to using the simple excel "database" provided by cellpy.

        If you dont have a database or you dont know how to make and use one,
        look in the cellpy documentation for other solutions
        (e.g. manually create a file that can be loaded by the ``from_file``
        method).
        """
        logging.debug("not implemented")

    def from_file(self, file_name):
        raise NotImplementedError

    def create(self):
        """Create a journal manually"""
        raise NotImplementedError

    def to_file(self, file_name=None):
        """Save journal pages to a file.

        The file can then be used in later sessions using the
        `from_file` method."""
        raise NotImplementedError

    def paginate(self):
        """Create folders used for saving the different output files."""
        raise NotImplementedError

    def generate_file_name(self):
        """Create a file name for saving the journal."""
        logging.debug("not implemented")


# Do-ers
class BaseExporter(Doer, metaclass=abc.ABCMeta):
    """An exporter exports your data to a given format."""
    def __init__(self, *args):
        super().__init__(*args)
        self.engines = list()
        self.dumpers = list()
        self._use_dir = None

    def _assign_engine(self, engine):
        self.engines.append(engine)

    def _assign_dumper(self, dumper):
        self.dumpers.append(dumper)

    @abc.abstractmethod
    def run_engine(self, engine):
        pass

    @abc.abstractmethod
    def run_dumper(self, dumper):
        pass

    def do(self):
        if not self.experiments:
            raise UnderDefined("cannot run until "
                               "you have assigned an experiment")
        for engine in self.engines:
            self.empty_the_farms()
            logging.debug(f"running - {str(engine)}")
            self.run_engine(engine)

            for dumper in self.dumpers:
                logging.debug(f"exporting - {str(dumper)}")
                self.run_dumper(dumper)


class BasePlotter(Doer):
    def __init__(self, *args):
        super().__init__(*args)


class BaseReporter(Doer):
    def __init__(self, *args):
        super().__init__(*args)


class BaseAnalyzer(Doer):
    def __init__(self, *args):
        super().__init__(*args)


