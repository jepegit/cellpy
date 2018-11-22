import logging
import abc
import pandas as pd
import json

from cellpy import cellreader, dbreader
from cellpy.utils import batch_helpers as helper
from cellpy.exceptions import UnderDefined
from cellpy.utils.dumpers import csv_dumper, screen_dumper
from cellpy.utils.engines import cycles_engine, summary_engine, simple_db_engine

# logging = logging.getLogger(__name__)

empty_farm = []


class Doer:
    """Base class for all the classes that do something to the experiment"""
    def __init__(self, *args):
        self.experiments = []
        self.farms = []
        self.barn = None
        args = self._validate_base_experiment_type(args)
        if args:
            self.experiments.extend(args)
            self.farms.append(empty_farm)

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
                err = f"{repr(arg)} is not an instance of BaseExperiment"
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
        self.farms.append(empty_farm)

    def empty_the_farms(self):
        logging.debug("emptying the farm for all the pandas")
        self.farms = [[] for _ in self.farms]

    def do(self):
        print("Sorry, don't know what I should do!")


class BaseExperiment:
    """An experiment contains experimental data and meta-data."""
    def __init__(self, *args):
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
        """get or link data"""
        pass

    def status(self):
        """describe the status and health of your experiment"""
        pass

    def info(self):
        """print information about the experiment"""
        print(self)


class BaseJournal:
    """A journal keeps track of the details of the experiment.

    The journal should at a mimnimum contain information about the name and
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
        self.file_name = None
        self.time_stamp = None
        self.project_dir = None
        self.batch_dir = None
        self.raw_dir = None

    def __str__(self):
        return f"{self.__class__.__name__}\n" \
               f"  - name: {str(self.name)}\n" \
               f"  - project: {str(self.project)}\n"\
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
                    logging.debug(f"unknown variable encountered: {p}")

    def from_db(self):
        logging.debug("not implemented")

    def from_file(self, file_name):
        raise NotImplementedError

    def create(self):
        """create a journal manually"""
        raise NotImplementedError

    def to_file(self, file_name=None):
        raise NotImplementedError

    def paginate(self):
        """create folders for saving output"""
        raise NotImplementedError

    def generate_file_name(self):
        """create a file name for saving the journal"""
        logging.debug("not implemented")


# Do-ers
class BaseExporter(Doer, metaclass=abc.ABCMeta):
    """An exporter exports your data to a given format"""
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
    def generate_name(self):
        pass

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


# ------------------------------------------------------------------------------
# Experiments (will be refactored to own file soon)
# ------------------------------------------------------------------------------
class CyclingExperiment(BaseExperiment):
    """Load experimental data into memory.

    This is a re-implementation of the old batch behaviour where
    all the data-files are processed secuentially (and optionally exported)
    while the summary tables are kept and processed. This implementation
    also saves the step tables (for later use when using look-up
    functionallity).
    """

    def __init__(self, *args):
        super().__init__(*args)
        self.journal = LabJournal()

        self.force_cellpy = False
        self.force_raw = False
        self.save_cellpy = True
        self.parent_level = "CellpyData"
        self.accept_errors = True
        self.all_in_memory = False

        self.export_cycles = False
        self.shifted_cycles = False
        self.export_raw = True
        self.export_ica = False
        self.last_cycle = None

        self.summary_frames = None
        self.step_table_frames = None
        self.cell_data_frames = None
        self.selected_summaries = None
        self.errors = dict()

    def update(self):
        logging.info("[update experiment]")
        pages = self.journal.pages
        summary_frames = dict()
        step_table_frames = dict()
        cell_data_frames = dict()
        number_of_runs = len(pages)
        counter = 0
        errors = []

        for indx, row in pages.iterrows():
            counter += 1
            h_txt = "[" + counter * "|" + (
                    number_of_runs - counter) * "." + "]"
            l_txt = "starting to process file # %i (index=%s)" % (counter, indx)
            logging.debug(l_txt)
            print(h_txt)

            if not row.raw_file_names and not self.force_cellpy:
                logging.info("File(s) not found!")
                logging.info(indx)
                logging.debug("File(s) not found for index=%s" % indx)
                errors.append(indx)
                continue

            else:
                logging.info(f"Processing {indx}")

            cell_data = cellreader.CellpyData()
            if not self.force_cellpy:
                logging.info(
                    "setting cycle mode (%s)..." % row.cell_type)
                cell_data.set_cycle_mode(row.cell_type)

            logging.info("loading cell")
            if not self.force_cellpy:
                logging.info("not forcing")
                try:
                    cell_data.loadcell(
                        raw_files=row.raw_file_names,
                        cellpy_file=row.cellpy_file_names,
                        mass=row.masses,
                        summary_on_raw=True,
                        force_raw=self.force_raw,
                        use_cellpy_stat_file=prms.Reader.use_cellpy_stat_file
                    )
                except Exception as e:
                    logging.info('Failed to load: ' + str(e))
                    errors.append("loadcell:" + str(indx))
                    if not self.accept_errors:
                        raise Exception(e)
                    continue

            else:
                logging.info("forcing")
                try:
                    cell_data.load(row.cellpy_file_names,
                                   parent_level=self.parent_level)
                except Exception as e:
                    logging.info(
                        f"Critical exception encountered {type(e)} "
                        "- skipping this file")
                    logging.debug(
                        'Failed to load. Error-message: ' + str(e))
                    errors.append("load:" + str(indx))
                    if not self.accept_errors:
                        raise Exception(e)
                    continue

            if not cell_data.check():
                logging.info("...not loaded...")
                logging.debug(
                    "Did not pass check(). Could not load cell!")
                errors.append("check:" + str(indx))
                continue

            logging.info("...loaded successfully...")

            summary_tmp = cell_data.dataset.dfsummary
            logging.info("Trying to get summary_data")

            step_table_tmp = cell_data.dataset.step_table

            if step_table_tmp is None:
                logging.info(
                    "No existing steptable made - running make_step_table"
                )

                cell_data.make_step_table()

            if summary_tmp is None:
                logging.info(
                    "No existing summary made - running make_summary"
                )

                cell_data.make_summary(find_end_voltage=True,
                                       find_ir=True)

            if self.all_in_memory:
                cell_data_frames[indx] = cell_data

            if summary_tmp.index.name == b"Cycle_Index":
                logging.debug("Strange: 'Cycle_Index' is a byte-string")
                summary_tmp.index.name = 'Cycle_Index'

            if not summary_tmp.index.name == "Cycle_Index":
                logging.debug("Setting index to Cycle_Index")
                # check if it is a byte-string
                if b"Cycle_Index" in summary_tmp.columns:
                    logging.debug(
                        "Seems to be a byte-string in the column-headers")
                    summary_tmp.rename(
                        columns={b"Cycle_Index": 'Cycle_Index'},
                        inplace=True)
                summary_tmp.set_index("Cycle_Index", inplace=True)

            step_table_frames[indx] = step_table_tmp
            summary_frames[indx] = summary_tmp

            if self.save_cellpy:
                logging.info("saving to cellpy-format")
                if not row.fixed:
                    logging.info("saving cell to %s" % row.cellpy_file_names)
                    cell_data.ensure_step_table = True
                    cell_data.save(row.cellpy_file_names)
                else:
                    logging.debug(
                        "saving cell skipped (set to 'fixed' in info_df)")

            if self.export_raw or self.export_cycles:
                export_text = "exporting"
                if self.export_raw:
                    export_text += " [raw]"
                if self.export_cycles:
                    export_text += " [cycles]"
                logging.info(export_text)
                cell_data.to_csv(
                    self.journal.raw_dir,
                    sep=prms.Reader.sep,
                    cycles=self.export_cycles,
                    shifted=self.shifted_cycles,
                    raw=self.export_raw,
                    last_cycle=self.last_cycle
                )

            if self.export_ica:
                logging.info("exporting [ica]")
                try:
                    helper.export_dqdv(
                        cell_data,
                        savedir=self.journal.raw_dir,
                        sep=prms.Reader.sep,
                        last_cycle=self.last_cycle
                    )
                except Exception as e:
                    logging.error(
                        "Could not make/export dq/dv data"
                    )
                    logging.debug(
                        "Failed to make/export "
                        "dq/dv data (%s): %s" % (indx, str(e))
                    )
                    errors.append("ica:" + str(indx))

        self.errors["update"] = errors
        self.summary_frames = summary_frames
        self.step_table_frames = step_table_frames
        if self.all_in_memory:
            self.cell_data_frames = cell_data_frames

    def link(self):
        logging.info("[estblishing links]")
        logging.info("checking and establishing link to data")
        step_table_frames = dict()
        counter = 0
        errors = []
        try:
            for indx, row in self.journal.pages.iterrows():

                counter += 1
                l_txt = "starting to process file # %i (index=%s)" % (counter, indx)
                logging.debug(l_txt)
                logging.info(f"linking cellpy-file: {row.cellpy_file_names}")

                if not os.path.isfile(row.cellpy_file_names):
                    logging.error("File does not exist")
                    raise IOError

                step_table_frames[indx] = helper.look_up_and_get(
                    row.cellpy_file_names,
                    "step_table"
                )
            self.step_table_frames = step_table_frames

        except IOError as e:
            logging.warning(e)
            e_txt = "links not established - try update"
            logging.warning(e_txt)
            errors.append(e_txt)

        self.errors["link"] = errors


class ImpedanceExperiment(BaseExperiment):
    def __init__(self):
        super().__init__()


class LifeTimeExperiment(BaseExperiment):
    def __init__(self):
        super().__init__()


# ------------------------------------------------------------------------------
# Journals (will be refactored to own file soon)
# ------------------------------------------------------------------------------
class LabJournal(BaseJournal):
    def __init__(self):
        super().__init__()
        self.db_reader = dbreader.Reader()
        self.batch_col = 5

    def _check_file_name(self, file_name):
        if file_name is None:
            if not self.file_name:
                self.generate_file_name()
            file_name = self.file_name
        return file_name

    def from_db(self, project=None, name=None, batch_col=None):
        if batch_col is None:
            batch_col = self.batch_col
        if project is not None:
            self.project = project
        if name is None:
            name = self.name
        else:
            self.name = name
        logging.debug(
            "batch_name, batch_col: (%s,%i)" % (name, batch_col)
        )
        srnos = self.db_reader.select_batch(name, batch_col)
        self.pages = simple_db_engine(self.db_reader, srnos)
        self.generate_folder_names()
        self.paginate()

    def from_file(self, file_name=None):
        """Loads a DataFrame with all the needed info about the experiment"""

        file_name = self._check_file_name(file_name)

        with open(file_name, 'r') as infile:
            top_level_dict = json.load(infile)

        pages_dict = top_level_dict['info_df']
        pages = pd.DataFrame(pages_dict)
        self.pages = pages
        self.file_name = file_name
        self._prm_packer(top_level_dict['metadata'])
        self.generate_folder_names()
        self.paginate()

    def to_file(self, file_name=None):
        """Saves a DataFrame with all the needed info about the experiment"""

        file_name = self._check_file_name(file_name)
        pages = self.pages

        top_level_dict = {
            'info_df': pages,
            'metadata': self._prm_packer()
        }

        jason_string = json.dumps(
            top_level_dict,
            default=lambda info_df: json.loads(
                info_df.to_json()
            )
        )

        self.paginate()

        with open(file_name, 'w') as outfile:
            outfile.write(jason_string)

        self.file_name = file_name
        logging.info("Saved file to {}".format(file_name))

    def generate_folder_names(self):
        self.project_dir = os.path.join(prms.Paths.outdatadir, self.project)
        self.batch_dir = os.path.join(self.project_dir, self.name)
        self.raw_dir = os.path.join(self.batch_dir, "raw_data")

    def paginate(self):
        """make folders where we would like to put results etc"""

        project_dir = self.project_dir
        raw_dir = self.raw_dir
        batch_dir = self.batch_dir

        if project_dir is None:
            raise UnderDefined("no project directory defined")
        if raw_dir is None:
            raise UnderDefined("no raw directory defined")
        if batch_dir is None:
            raise UnderDefined("no batcb directory defined")

        # create the folders
        if not os.path.isdir(project_dir):
            os.mkdir(project_dir)
            logging.info(f"created folder {project_dir}")
        if not os.path.isdir(batch_dir):
            os.mkdir(batch_dir)
            logging.info(f"created folder {batch_dir}")
        if not os.path.isdir(raw_dir):
            os.mkdir(raw_dir)
            logging.info(f"created folder {raw_dir}")

        return project_dir, batch_dir, raw_dir

    def generate_file_name(self):
        """generate a suitable file name for the experiment"""
        if not self.project:
            raise UnderDefined("project name not given")

        out_data_dir = prms.Paths.outdatadir
        project_dir = os.path.join(out_data_dir, self.project)
        file_name = "cellpy_batch_%s.json" % self.name
        self.file_name = os.path.join(project_dir, file_name)

    def look_for_file(self):
        pass


# ------------------------------------------------------------------------------
# Exporters (will be refactored to own file soon)
# ------------------------------------------------------------------------------
class CSVExporter(BaseExporter):
    def __init__(self):
        super().__init__()
        self._assign_engine(summary_engine)
        self._assign_engine(cycles_engine)
        self._assign_dumper(csv_dumper)
        # self._assign_dumper(screen_dumper)

    def generate_name(self):
        """function for generating appropriate file-name(s)"""
        print("GENERATE NAME")

    def run_engine(self, engine):
        logging.debug("running engine")
        self.farms, self.barn = engine(experiments=self.experiments, farms=self.farms)

    def run_dumper(self, dumper):
        logging.debug("running dumper")
        dumper(experiments=self.experiments, farms=self.farms, barn=self.barn)


class OriginLabExporter(BaseExporter):
    def __init__(self):
        super().__init__()


class ExcelExporter(BaseExporter):
    def __init__(self):
        super().__init__()


# ------------------------------------------------------------------------------
# Analyzers (will be refactored to own file soon)
# ------------------------------------------------------------------------------
class ICAAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()


class EISAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()


class OCVRelaxationAnalyzer(BaseAnalyzer):
    def __init__(self):
        super().__init__()


# ------------------------------------------------------------------------------
# Reporters (will be refactored to own file soon)
# ------------------------------------------------------------------------------
class HTMLReporter(BaseReporter):
    def __init__(self):
        super().__init__()


class PPTReporter(BaseReporter):
    def __init__(self):
        super().__init__()


def main():
    # --------------------------------------------------------------------------
    # my_analyzis
    # --------------------------------------------------------------------------
    # pages = "/Users/jepe/scripting/cellpy/dev_data/cellpy_batch_test.json"
    # my_experiment = CyclingExperiment()
    # my_experiment.journal.from_file(pages)
    # print("lab-journal pages for my_experiment:")
    # print(my_experiment.journal.pages.head(10))

    # setting up the experiment
    prebens_experiment = CyclingExperiment()
    prebens_experiment.export_raw = True
    prebens_experiment.export_cycles = True
    prebens_experiment.export_ica = True
    prebens_experiment.journal.project = "prebens_experiment"
    prebens_experiment.journal.name = "test"
    prebens_experiment.journal.batch_col = 5
    prebens_experiment.journal.from_db()
    prebens_experiment.journal.to_file()

    print("lab-journal pages for prebens_experiment:")
    print(prebens_experiment.journal.pages.head(10))
    prebens_experiment.update()

    # prebens_experiment.link()  # Not implemented yet (linking without checking)
    #

    # TODO: pick data from h5-files

    # print(prebens_experiment.step_table_frames)
    # print(prebens_experiment.summary_frames)

    print("\nNow it is time for exporting data")
    exporter = CSVExporter()
    exporter.assign(prebens_experiment)
    exporter.do()

    # my_exporter = CSVExporter()
    # my_analyzer = BaseAnalyzer()
    # my_plotter = BasePlotter()
    #
    # # print(my_experiment)
    # # print(my_exporter)
    #
    # print("-----exporter-----")
    # my_exporter.assign(my_experiment)
    # my_exporter.do()
    # my_exporter.info()

    # print("----reporter----")
    # my_reporter = BaseReporter(my_experiment, prebens_experiment)
    # my_reporter.do()
    # my_reporter.info()
    #
    # print("----content-in-journal-1--")
    # print(my_experiment.journal)
    #
    # print("----content-in-journal-2--")
    # print(prebens_experiment.journal)


if __name__ == "__main__":
    import cellpy.log
    from cellpy import prms
    import os

    prms.Paths["db_filename"] = "cellpy_db.xlsx"
    # These prms works for me on my mac, but probably not for you:
    prms.Paths["cellpydatadir"] = "/Users/jepe/scripting/cellpy/testdata/hdf5"
    prms.Paths["outdatadir"] = "/Users/jepe/cellpy_data"
    prms.Paths["rawdatadir"] = "/Users/jepe/scripting/cellpy/testdata/data"
    prms.Paths["db_path"] = "/Users/jepe/scripting/cellpy/testdata/db"
    prms.Paths["filelogdir"] = "/Users/jepe/scripting/cellpy/testdata/log"

    cellpy.log.setup_logging(default_level="INFO")
    logging.info("If you see this - then logging works")

    print(60 * "=")
    print("Running main in batch_engines")
    print(60 * "-")

    main()

    print(60 * "-")
