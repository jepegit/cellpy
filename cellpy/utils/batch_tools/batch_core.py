import logging
import os
import abc
import collections

#  import box

from cellpy import cellreader
from cellpy import prms
from cellpy.exceptions import UnderDefined
from cellpy.parameters.internal_settings import get_headers_journal
from cellpy.utils.batch_tools import batch_helpers as helper

hdr_journal = get_headers_journal()
empty_farm = []


class Doer(metaclass=abc.ABCMeta):
    """Base class for all the classes that do something to the experiment(s).

    Attributes:
        experiments: list of experiments.
        farms: list of farms (one pr experiment) (containing pandas DataFrames).
        barn (str): identifier for where to place the output-files (i.e. the animals)
            (typically a directory path).

    The do-er iterates through all the connected engines and dumpers (the dumpers are
    run for each engine).

    It is the responsibility of the engines and dumpers to iterate through the experiments.
    The most natural way is to work with just one experiment.
    """

    def __init__(self, *args):
        """Setting up the Do-er.

        Args:
            *args: list of experiments
        """
        self.experiments = []
        self.farms = (
            []
        )  # A list of lists, each list is a green field where your animals wander around
        self.engines = []  # The engines creates the animals
        self.dumpers = []  # The dumpers places animals in the barn
        self.barn = (
            None  # This is where we put the animals during winter (and in the night)
        )

        # Decide if the farm should be locked or not. If not locked, the farm will be emptied
        # before each engine run (if the farm is not locked, the animals will escape).
        # Typically, you would not want to lock the farm.
        # Remark that also the engines have access to the farms (gets the farm
        # as input and sends a modified version back), and most of them empties the farm before populating
        # them with new content anyway:
        self.locked = False

        args = self._validate_base_experiment_type(args)
        if args:
            self.experiments.extend(args)
            self.farms.append(empty_farm)

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
        if not self.locked:
            logging.debug("emptying the farm for all the pandas")
            self.farms = [[] for _ in self.farms]

    def do(self):
        """Do what is needed and dump it for each engine."""

        if not self.experiments:
            raise UnderDefined("cannot run until you have assigned an experiment")
        for engine in self.engines:
            self.empty_the_farms()
            logging.debug(f"running - {str(engine)}")
            self.run_engine(engine)

            for dumper in self.dumpers:
                logging.debug(f"exporting - {str(dumper)}")
                self.run_dumper(dumper)


class Data(collections.UserDict):
    """Class that is used to access the experiment.journal.pages DataFrame.

    The Data class loads the complete cellpy-file if raw-data is not already
    loaded in memory. In future version, it could be that the Data object
    will return a link allowing querying instead to save memory usage...

    Remark that some cellpy (cellreader.CellpyData) function might not work if
    you have the raw-data in memory, but not summary data (if the cellpy function
    requires summary data or other settings not set as default).
    """

    # TODO (jepe): decide if we should included querying functionality here.
    # TODO (jepe): implement experiment.last_cycle

    def __init__(self, experiment, *args):
        super().__init__(*args)
        self.experiment = experiment
        self.query_mode = False
        self.accessor_pre = "x_"
        self.accessors = {}
        self._create_accessors()

    def _create_accessor_label(self, cell_label):
        return self.accessor_pre + cell_label

    def _create_cell_label(self, accessor_label):
        return accessor_label.lstrip(self.accessor_pre)

    def _create_accessors(self):
        cell_labels = self.experiment.journal.pages.index
        for cell_label in cell_labels:
            try:
                self.accessors[
                    self._create_accessor_label(cell_label)
                ] = self.experiment.cell_data_frames[cell_label]
            except KeyError as e:
                logging.debug(
                    f"Could not create accessors for {cell_label}"
                    f"(probably missing from the experiment.cell_data_frames"
                    f"attribute) {e}"
                )

    def __getitem__(self, cell_id):
        cellpy_data_object = self.__look_up__(cell_id)
        return cellpy_data_object

    def __dir__(self):
        # This is the secret sauce that allows jupyter to do tab-completion
        return self.accessors

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

    def __getattr__(self, item):
        if item in self.accessors:
            item = self._create_cell_label(item)
            return self.__getitem__(item)
        else:
            return super().__getattribute__(item)

    def __look_up__(self, cell_id):
        try:
            if not self.experiment.cell_data_frames[cell_id].cell.raw.empty:
                return self.experiment.cell_data_frames[cell_id]
            else:
                raise AttributeError

        except AttributeError:
            logging.debug("Need to do a look-up from the cellpy file")
            pages = self.experiment.journal.pages
            info = pages.loc[cell_id, :]
            cellpy_file = info[hdr_journal.cellpy_file_name]
            # linking (query_mode) not implemented yet - loading whole file in mem instead
            if not self.query_mode:
                cell = self.experiment._load_cellpy_file(cellpy_file)
                self.experiment.cell_data_frames[cell_id] = cell
                # trick for making tab-completion work:
                self.accessors[
                    self._create_accessor_label(cell_id)
                ] = self.experiment.cell_data_frames[cell_id]
                return cell
            else:
                raise NotImplementedError


class BaseExperiment(metaclass=abc.ABCMeta):
    """An experiment contains experimental data and meta-data."""

    def __init__(self, *args):
        self.journal = None
        self.summary_frames = None
        self.cell_data_frames = dict()
        self.memory_dumped = dict()
        self.parent_level = "CellpyData"
        self.log_level = "CRITICAL"
        self._data = None
        self._store_data_object = True
        self._cellpy_object = None
        self.limit = 10

    def __str__(self):
        return (
            f"[{self.__class__.__name__}]\n"
            f"journal: \n{str(self.journal)}\n"
            f"data: \n{str(self.data)}"
        )

    def __repr__(self):
        return self.__class__.__name__

    def __len__(self):
        try:
            length = len(self.journal.pages.index)
        except TypeError:
            length = 0
        return length

    def __iter__(self):
        self._counter = 0
        self._limit = len(self)
        return self

    def __next__(self):
        counter = self._counter
        limit = self._limit
        if counter >= limit:
            raise StopIteration
        else:
            self._counter += 1
            cell_label = self.journal.pages.index[counter]
            try:
                logging.debug(f"looking for cell {cell_label}")
                cellpy_object = self.data[cell_label]
            except (TypeError, KeyError):
                logging.debug("There is no data available - trying to link")
                try:
                    self._link_cellpy_file(cell_label)
                    cellpy_object = self.data[cell_label]
                except (IOError, KeyError, UnderDefined):
                    raise StopIteration
            return cellpy_object

    def _link_cellpy_file(self, cell_label):
        logging.debug("linking cellpy file")
        cellpy_file_name = self.journal.pages.loc[
            cell_label, hdr_journal.cellpy_file_name
        ]
        if not os.path.isfile(cellpy_file_name):
            raise IOError

        cellpy_object = cellreader.CellpyData(initialize=True)
        step_table = helper.look_up_and_get(cellpy_file_name, prms._cellpyfile_step)
        if step_table.empty:
            raise UnderDefined

        cellpy_object.cell.steps = step_table
        self._data = None
        self.cell_data_frames[cell_label] = cellpy_object

    def _load_cellpy_file(self, file_name):
        cellpy_data = cellreader.CellpyData()
        cellpy_data.load(file_name, self.parent_level)
        logging.info(f" <- grabbing ( {file_name} )")
        return cellpy_data

    @property
    def data(self):
        """Property for accessing the underlying data in an experiment.

        Example:
            >>> cell_data_one = experiment.data["2018_cell_001"]
            >>> capacity, voltage = cell_data_one.get_cap(cycle=1)
        """

        # TODO: implement max cycle number (experiment.last_cycle)
        if self._data is None:
            data = Data(self)
            if self._store_data_object:
                # for cell_name in self.journal.pages.index:
                #     data[cell_name] = None
                self._data = data
            return data
        else:
            return self._data

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

    packable = ["name", "project", "time_stamp", "project_dir", "batch_dir", "raw_dir"]

    def __init__(self):
        self.pages = None  # pandas.DataFrame
        self.session = None  # dictionary
        self.name = None
        self.project = None
        self.file_name = None
        self.time_stamp = None
        self.project_dir = None
        self.batch_dir = None
        self.raw_dir = None

    def __str__(self):
        return (
            f"({self.__class__.__name__})\n"
            f"  - name: {str(self.name)}\n"
            f"  - project: {str(self.project)}\n"
            f"  - file_name: {str(self.file_name)}\n"
            f"  - pages: ->\n{str(self.pages)}\n"
            f"  - session: ->\n{str(self.session)}\n"
            f"           <-\n"
        )

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
        self._use_dir = None
        self.current_engine = None

    def run_engine(self, engine):
        logging.debug(f"start engine::{engine.__name__}")
        self.current_engine = engine
        self.farms, self.barn = engine(experiments=self.experiments, farms=self.farms)
        logging.debug("::engine ended")

    def run_dumper(self, dumper):
        logging.debug(f"start dumper::{dumper.__name__}")
        dumper(
            experiments=self.experiments,
            farms=self.farms,
            barn=self.barn,
            engine=self.current_engine,
        )
        logging.debug("::engine ended")


class BasePlotter(Doer, metaclass=abc.ABCMeta):
    def __init__(self, *args):
        super().__init__(*args)

    @abc.abstractmethod
    def run_engine(self, engine):
        pass

    @abc.abstractmethod
    def run_dumper(self, dumper):
        pass


class BaseReporter(Doer, metaclass=abc.ABCMeta):
    def __init__(self, *args):
        super().__init__(*args)

    @abc.abstractmethod
    def run_engine(self, engine):
        pass

    @abc.abstractmethod
    def run_dumper(self, dumper):
        pass


class BaseAnalyzer(Doer, metaclass=abc.ABCMeta):
    def __init__(self, *args):
        super().__init__(*args)
        self.current_engine = None

    def run_engine(self, engine):
        """Run the engine, build the barn and put the animals on the farm"""
        logging.debug(f"start engine::{engine.__name__}")
        self.current_engine = engine
        self.farms, self.barn = engine(experiments=self.experiments, farms=self.farms)
        logging.debug("::engine ended")

    def run_dumper(self, dumper):
        """Place the animals in the barn"""
        logging.debug(f"start dumper::{dumper.__name__}")
        dumper(
            experiments=self.experiments,
            farms=self.farms,
            barn=self.barn,
            engine=self.current_engine,
        )
        logging.debug("::engine ended")
