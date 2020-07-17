"""Routines for batch processing of cells (v2)."""

import logging
import pathlib
import shutil
import warnings
import os
import sys

import pandas as pd
from tqdm.auto import tqdm

from cellpy import prms
from cellpy import log
import cellpy.exceptions
from cellpy.parameters.internal_settings import (
    get_headers_step_table,
    get_headers_journal,
    get_headers_summary,
)
from cellpy.utils.batch_tools.batch_exporters import CSVExporter
from cellpy.utils.batch_tools.batch_experiments import CyclingExperiment
from cellpy.utils.batch_tools.batch_plotters import CyclingSummaryPlotter
from cellpy.utils.batch_tools.batch_analyzers import OCVRelaxationAnalyzer
from cellpy.utils.batch_tools.batch_journals import LabJournal
from cellpy.utils.batch_tools.dumpers import ram_dumper

# logger = logging.getLogger(__name__)
logging.captureWarnings(True)
hdr_journal = get_headers_journal()
hdr_summary = get_headers_summary()

COLUMNS_SELECTED_FOR_VIEW = [
    hdr_journal.mass,
    # hdr_journal.total_mass,
    hdr_journal.loading,
]


class Batch:
    """A convenient class for running batch procedures."""

    def __init__(self, *args, **kwargs):
        """Initialize the Batch class.

        The initialization accepts arbitrary arguments and keyword arguments.
        It first looks for the file_name and db_reader keyword arguments.

        Usage:
            b = Batch((name, (project)), **kwargs)

        Examples:
            >>> b = Batch("experiment001", "main_project")
            >>> b = Batch("experiment001", "main_project", batch_col="b02")
            >>> b = Batch(name="experiment001", project="main_project", batch_col="b02")
            >>> b = Batch(file_name="cellpydata/batchfiles/cellpy_batch_experiment001.json")

        Keyword Args (priority):
            file_name (str or pathlib.Path): journal file name to load.
            db_reader (str): data-base reader to use (defaults to "default" as given
                in the config-file or prm-class).
        Args:
            *args: name (str) (project (str))

        Keyword Args (other):
            default_log_level (str): custom log-level (defaults to None (i.e. default log-level in cellpy)).
            custom_log_dir (str or pathlib.Path): custom folder for putting the log-files.
            force_raw_file (bool): load from raw regardless (defaults to False).
            force_cellpy (bool): load cellpy-files regardless (defaults to False).
            force_recalc (bool): Always recalculate (defaults to False).
            export_cycles (bool): Extract and export individual cycles to csv (defaults to True).
            export_raw (bool): Extract and export raw-data to csv (defaults to True).
            export_ica (bool): Extract and export individual dQ/dV data to csv (defaults to True).
            accept_errors (bool): Continue automatically to next file if error is raised (defaults to False).
            nom_cap (float): give a nominal capacity if you want to use another value than
                the one given in the config-file or prm-class.
        """
        default_log_level = kwargs.pop("log_level", None)
        custom_log_dir = kwargs.pop("custom_log_dir", None)
        if default_log_level is not None or custom_log_dir is not None:
            log.setup_logging(
                custom_log_dir=custom_log_dir,
                default_level=default_log_level,
                reset_big_log=True,
            )

        db_reader = kwargs.pop("db_reader", "default")

        file_name = kwargs.pop("file_name", None)

        logging.debug("creating CyclingExperiment")
        self.experiment = CyclingExperiment(db_reader=db_reader)
        logging.info("created CyclingExperiment")

        self.experiment.force_cellpy = kwargs.pop("force_cellpy", False)
        self.experiment.force_raw = kwargs.pop("force_raw_file", False)
        self.experiment.force_recalc = kwargs.pop("force_recalc", False)
        self.experiment.export_cycles = kwargs.pop("export_cycles", True)
        self.experiment.export_raw = kwargs.pop("export_raw", True)
        self.experiment.export_ica = kwargs.pop("export_ica", False)
        self.experiment.accept_errors = kwargs.pop("accept_errors", False)
        self.experiment.nom_cap = kwargs.pop("nom_cap", None)

        if not file_name:
            if len(args) > 0:
                self.experiment.journal.name = args[0]

            if len(args) > 1:
                self.experiment.journal.project = args[1]

            for key in kwargs:
                if key == "name":
                    self.experiment.journal.name = kwargs[key]
                elif key == "project":
                    self.experiment.journal.project = kwargs[key]
                elif key == "batch_col":
                    self.experiment.journal.batch_col = kwargs[key]

        else:
            self.experiment.journal.from_file(file_name=file_name)

        self.exporter = CSVExporter()
        self.exporter._assign_dumper(ram_dumper)
        self.exporter.assign(self.experiment)
        self.plotter = CyclingSummaryPlotter()
        self.plotter.assign(self.experiment)
        self._journal_name = self.journal_name
        self.headers_step_table = get_headers_step_table()

    def __str__(self):
        return str(self.experiment)

    def show_pages(self, number_of_rows=5):
        warnings.warn("Deprecated - use pages.head() instead", DeprecationWarning)
        return self.experiment.journal.pages.head(number_of_rows)

    @property
    def view(self):
        warnings.warn("Deprecated - use report instead", DeprecationWarning)
        pages = self.experiment.journal.pages
        pages = pages[COLUMNS_SELECTED_FOR_VIEW]
        return pages

    def _check_cell_raw(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            return len(c.cell.raw)
        except Exception:
            return None

    def _check_cell_steps(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            return len(c.cell.steps)
        except Exception:
            return None

    def _check_cell_summary(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            return len(c.cell.summary)
        except Exception as e:
            return None

    def _check_cell_max_cap(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            s = c.cell.summary
            return s[hdr_summary.charge_capacity].max()

        except Exception as e:
            return None

    def _check_cell_min_cap(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            s = c.cell.summary
            return s[hdr_summary.charge_capacity].min()

        except Exception as e:
            return None

    def _check_cell_avg_cap(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            s = c.cell.summary
            return s[hdr_summary.charge_capacity].mean()

        except Exception as e:
            return None

    def _check_cell_std_cap(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            s = c.cell.summary
            return s[hdr_summary.charge_capacity].std()

        except Exception as e:
            return None

    def _check_cell_empty(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            return c.empty
        except Exception:
            return None

    def _check_cell_cycles(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            return c.cell.steps[self.headers_step_table.cycle].max()
        except Exception:
            return None

    def report(self, stylize=True):
        """ Create a report on all the cells in the batch object.

        Remark! To perform a reporting, cellpy needs to access all the data (and it might take some time).

        Returns:
            pandas.DataFrame
        """
        pages = self.experiment.journal.pages
        pages = pages[COLUMNS_SELECTED_FOR_VIEW].copy()
        # pages["empty"] = pages.index.map(self._check_cell_empty)
        pages["raw_rows"] = pages.index.map(self._check_cell_raw)
        pages["steps_rows"] = pages.index.map(self._check_cell_steps)
        pages["summary_rows"] = pages.index.map(self._check_cell_summary)
        pages["last_cycle"] = pages.index.map(self._check_cell_cycles)
        pages["average_capacity"] = pages.index.map(self._check_cell_avg_cap)
        pages["max_capacity"] = pages.index.map(self._check_cell_max_cap)
        pages["min_capacity"] = pages.index.map(self._check_cell_min_cap)
        pages["std_capacity"] = pages.index.map(self._check_cell_std_cap)

        avg_last_cycle = pages.last_cycle.mean()
        avg_max_capacity = pages.max_capacity.mean()

        if stylize:

            def highlight_outlier(s):
                average = s.mean()
                outlier = (s < average / 2) | (s > 2 * average)
                return ["background-color: #f09223" if v else "" for v in outlier]

            def highlight_small(s):
                average = s.mean()
                outlier = s < average / 4
                return ["background-color: #41A1D8" if v else "" for v in outlier]

            def highlight_very_small(s):
                outlier = s <= 3
                return ["background-color: #416CD8" if v else "" for v in outlier]

            def highlight_big(s):
                average = s.mean()
                outlier = s > 2 * average
                return ["background-color: #D85F41" if v else "" for v in outlier]

            styled_pages = (
                pages.style.apply(highlight_small, subset=["last_cycle"])
                .apply(
                    highlight_outlier,
                    subset=["min_capacity", "max_capacity", "average_capacity"],
                )
                .apply(
                    highlight_big,
                    subset=["min_capacity", "max_capacity", "average_capacity"],
                )
                .apply(
                    highlight_very_small,
                    subset=["max_capacity", "average_capacity", "last_cycle"],
                )
                # .format({'min_capacity': "{:.2f}",
                #        'max_capacity': "{:.2f}",
                #        'average_capacity': "{:.2f}",
                #        'std_capacity': '{:.2f}'})
            )
            pages = styled_pages

        return pages

    @property
    def info_file(self):
        # renamed to journal_name
        warnings.warn("Deprecated - use journal_name instead", DeprecationWarning)
        return self.experiment.journal.file_name

    @property
    def journal_name(self):
        return self.experiment.journal.file_name

    @property
    def summaries(self):
        # should add link-mode?
        try:
            keys = [df.name for df in self.experiment.memory_dumped["summary_engine"]]
            return pd.concat(
                self.experiment.memory_dumped["summary_engine"], keys=keys, axis=1
            )
        except KeyError:
            logging.info("no summary exists")
            print("no summaries exists (probably not loaded yet)")

    @property
    def summary_headers(self):
        try:
            return self.summaries.columns.get_level_values(0)
        except AttributeError:
            logging.info("can't get any columns")

    @property
    def cell_names(self):
        return self.experiment.cell_names

    @property
    def raw_headers(self):
        return self.experiment.data[0].cell.raw.columns

    @property
    def step_headers(self):
        return self.experiment.data[0].cell.steps.columns

    @property
    def pages(self):
        return self.experiment.journal.pages

    @pages.setter
    def pages(self, df):
        self.experiment.journal.pages = df

    @property
    def journal(self):
        return self.experiment.journal

    @journal.setter
    def journal(self, new):
        # self.experiment.journal = new
        raise NotImplementedError(
            "Setting a new journal object on directly on a "
            "batch object is not allowed at the moment. Try modifying "
            "the journal.pages instead."
        )

    def create_journal(self, description=None, from_db=True):
        """Create journal pages.

        This method is a wrapper for the different Journal methods for making
        journal pages (Batch.experiment.journal.xxx). It is under development. If you
        want to use 'advanced' options (i.e. not loading from a db), please consider
        using the methods available in Journal for now.

        Args:
            description: the information and meta-data needed to generate the journal
                pages.
                "empty": create an empty journal
                dictionary: create journal pages from a dictionary
                pd.DataFrame: create  journal pages from a pandas DataFrame
                filename.json: load cellpy batch file

                filename.xlxs: create journal pages from an excel file
                    (not implemented yet)
            from_db (bool): Deprecation Warning: this parameter will be removed as it is
                the default anyway. Generate the pages from a db (the default option).
                This will be over-ridden if description is given.
        """

        logging.debug("Creating a journal")
        logging.debug(f"description: {description}")
        logging.debug(f"from_db: {from_db}")
        logging.info(f"name: {self.experiment.journal.name}")
        logging.info(f"project: {self.experiment.journal.project}")

        if description is not None:
            from_db = False

        if from_db:
            self.experiment.journal.from_db()
            self.experiment.journal.to_file()
            self.duplicate_journal(prms.Paths.batchfiledir)

        else:
            is_str = isinstance(description, str)
            is_file = False

            if is_str and pathlib.Path(description).is_file():
                description = pathlib.Path(description)
                is_file = True

            if isinstance(description, pathlib.Path):
                logging.debug("pathlib.Path object given")
                is_file = True

            if is_file:
                logging.info(f"loading file {description}")
                if description.suffix == ".json":
                    logging.debug("loading batch json file")
                    self.experiment.journal.from_file(description)
                elif description.suffix == ".xlxs":
                    logging.debug("loading excel file")
                    warnings.warn("not implemented yet")
                else:
                    warnings.warn("unknown file extension")

            else:

                if is_str and description.lower() == "empty":
                    logging.debug("creating empty journal pages")

                    self.experiment.journal.pages = (
                        self.experiment.journal.create_empty_pages()
                    )

                elif isinstance(description, pd.DataFrame):
                    logging.debug("pandas DataFrame given")

                    p = self.experiment.journal.create_empty_pages()
                    columns = p.columns

                    for column in columns:
                        try:
                            p[column] = description[column]
                        except KeyError:
                            logging.debug(f"missing key: {column}")

                    # checking if filenames is a column
                    if "filenames" in description.columns:
                        indexes = description["filenames"]
                    else:
                        indexes = description.index

                    p.index = indexes
                    self.experiment.journal.pages = p

                elif isinstance(description, dict):
                    logging.debug("dictionary given")
                    self.experiment.journal.pages = (
                        self.experiment.journal.create_empty_pages()
                    )
                    for k in self.experiment.journal.pages.columns:
                        try:
                            value = description[k]
                        except KeyError:
                            warnings.warn(f"missing key: {k}")
                        else:

                            if not isinstance(value, list):
                                warnings.warn("encountered item that is not a list")
                                logging.debug(f"converting '{k}' to list-type")
                                value = [value]
                            if k == "raw_file_names":
                                if not isinstance(value[0], list):
                                    warnings.warn(
                                        "encountered raw file description"
                                        "that is not of list-type"
                                    )
                                    logging.debug(
                                        "converting raw file description to a"
                                        "list of lists"
                                    )
                                    value = [value]
                            self.experiment.journal.pages[k] = value

                    try:
                        value = description["filenames"]
                        if not isinstance(value, list):
                            warnings.warn("encountered item that is not a list")
                            logging.debug(f"converting '{k}' to list-type")
                            value = [value]
                        self.experiment.journal.pages.index = value
                    except KeyError:
                        logging.debug("could not interpret the index")

                else:
                    logging.debug(
                        "the option you provided seems to be either of "
                        "an unknown type or a file not found"
                    )
                    logging.info(
                        "did not understand the option - creating empty journal pages"
                    )

            # finally
            self.experiment.journal.to_file()
            self.experiment.journal.generate_folder_names()
            self.experiment.journal.paginate()
            self.duplicate_journal(prms.Paths.batchfiledir)

    def create_folder_structure(self):
        warnings.warn("Deprecated - use paginate instead.", DeprecationWarning)
        self.experiment.journal.paginate()
        logging.info("created folders")

    def paginate(self):
        """Create the folders where cellpy will put its output."""

        self.experiment.journal.paginate()
        logging.info("created folders")

    def save_journal(self):
        """Save the journal (json-format).

        The journal file will be saved in the project directory and in the
        batch-file-directory (prms.Paths.batchfiledir). The latter is useful
        for processing several batches using the iterate_batches functionality.
        """

        # Remark! Got an recursive error when running on mac.
        self.experiment.journal.to_file()
        self.duplicate_journal(prms.Paths.batchfiledir)
        logging.info("saving journal pages")

    def duplicate_journal(self, folder=None):
        """Copy the journal to folder.

        Args:
            folder (str or pathlib.Path): folder to copy to (defaults to the
            current folder).
        """

        logging.debug(f"duplicating journal to folder {folder}")
        journal_name = pathlib.Path(self.experiment.journal.file_name)
        if not journal_name.is_file():
            logging.info("No journal saved")
            return
        new_journal_name = journal_name.name
        if folder is not None:
            new_journal_name = pathlib.Path(folder) / new_journal_name
        try:
            shutil.copy(journal_name, new_journal_name)
        except shutil.SameFileError:
            logging.debug("same file exception encountered")

    def duplicate_cellpy_files(self, location="standard"):
        """Copy the cellpy files and make a journal with the new names available in
        the current folder.

        Args:
            location: where to copy the files. Either choose among the following
                options:
                "standard": data/interim folder
                "here": current directory
                "cellpydatadir": the stated cellpy data dir in your settings (prms)
            or if the location is not one of the above, use the actual value of the
                location argument.

        Returns:
            The updated journal pages.
        """
        pages = self.experiment.journal.pages
        cellpy_file_dir = pathlib.Path(prms.Paths.cellpydatadir)

        if location == "standard":
            batch_data_dir = pathlib.Path("data") / "interim"

        elif location == "here":
            batch_data_dir = pathlib.Path(".")

        elif location == "cellpydatadir":
            batch_data_dir = cellpy_file_dir

        else:
            batch_data_dir = location

        def _new_file_path(x):
            return str(batch_data_dir / pathlib.Path(x).name)

        # update the journal pages
        columns = pages.columns
        pages["new_cellpy_file_name"] = pages.cellpy_file_name.apply(_new_file_path)

        # copy the cellpy files
        for n, row in pages.iterrows():
            logging.info(f"{row.cellpy_file_name} -> {row.new_cellpy_file_name}")
            try:
                from_file = row.cellpy_file_name
                to_file = row.new_cellpy_file_name
                os.makedirs(os.path.dirname(to_file), exist_ok=True)
                shutil.copy(from_file, to_file)
            except shutil.SameFileError:
                logging.info("Same file! No point in copying")

        # save the journal pages
        pages["cellpy_file_name"] = pages["new_cellpy_file_name"]
        self.experiment.journal.pages = pages[columns]
        journal_file_name = pathlib.Path(self.experiment.journal.file_name).name
        logging.info(f"saving journal to {journal_file_name}")
        self.experiment.journal.to_file(journal_file_name)

        # return pages

    # TODO: load_journal
    # TODO: list_journals?

    def link(self):
        """Link journal content to the cellpy-files and load the step information."""
        self.experiment.link()

    def load(self):
        # does the same as update
        warnings.warn("Deprecated - use update instead.", DeprecationWarning)
        self.experiment.update()

    def update(self, **kwargs):
        """Load cells as defined in the journal"""
        self.experiment.errors["update"] = []
        self.experiment.update(**kwargs)

    def make_summaries(self):
        warnings.warn("Deprecated - use combine_summaries instead.", DeprecationWarning)
        self.exporter.do()

    def combine_summaries(self, export_to_csv=True):
        """Combine selected columns from each of the cells into single frames"""
        self.exporter.do()

    def plot_summaries(self, output_filename=None, backend=None):
        """Plot the summaries (should be run after running combine_summaries)"""
        if backend is None:
            backend = prms.Batch.backend

        if backend in ["bokeh", "matplotlib"]:
            prms.Batch.backend = backend

        if backend == "bokeh":
            try:
                import bokeh.plotting

                prms.Batch.backend = "bokeh"

                if output_filename is not None:
                    bokeh.plotting.output_file(output_filename)
                else:
                    if prms.Batch.notebook:
                        bokeh.plotting.output_notebook()

            except ModuleNotFoundError:
                prms.Batch.backend = "matplotlib"
                logging.warning(
                    "could not find the bokeh module -> using matplotlib instead"
                )

        self.plotter.do()


def init(*args, **kwargs):
    """Returns an initialized instance of the Batch class.

    Args:
        *args: passed directly to Batch()
            name: name of batch
            project: name of project
            batch_col: batch column identifier
        **kwargs:
            file_name: json file if loading from pages
            default_log_level: "INFO" or "DEBUG"
            The rest is passed directly to Batch()

    Usage:
        >>> empty_batch = Batch.init(db_reader=None)
        >>> batch_from_file = Batch.init(file_name="cellpy_batch_my_experiment.json")
        >>> normal_init_of_batch = Batch.init()
    """
    # set up cellpy logger
    default_log_level = kwargs.pop("default_log_level", None)
    file_name = kwargs.pop("file_name", None)

    log.setup_logging(default_level=default_log_level, reset_big_log=True)

    logging.debug(f"returning Batch(kwargs: {kwargs})")
    if file_name is not None:
        kwargs.pop("db_reader", None)
        return Batch(*args, file_name=file_name, db_reader=None, **kwargs)
    return Batch(*args, **kwargs)


def from_journal(journal_file):
    """Create a Batch from a journal file"""
    b = init(db_reader=None, file_name=journal_file)
    return b


def load_pages(file_name):
    """Retrieve pages from a Journal file.

    This function is here to let you easily inspect a Journal file without
    starting up the full batch-functionality.

    Examples:
        >>> from cellpy.utils import batch
        >>> journal_file_name = 'cellpy_journal_one.json'
        >>> pages = batch.load_pages(journal_file_name)

    Returns:
        pandas.DataFrame

    """
    logging.info(f"Loading pages from {file_name}")
    pages, _ = LabJournal.read_journal_jason_file(file_name)
    return pages


def process_batch(*args, **kwargs):
    """Execute a batch run, either from a given file_name or by giving the name and project as input.

    Usage:
        process_batch(file_name | (name, project), **kwargs)

    Args:
        *args: file_name or name and project (both string)

    Optional keyword arguments:
        backend (str): what backend to use when plotting ('bokeh' or 'matplotlib').
            Defaults to 'matplotlib'.
        dpi (int): resolution used when saving matplotlib plot(s). Defaults to 300 dpi.
        default_log_level (str): What log-level to use for console output. Chose between
            'CRITICAL', 'DEBUG', or 'INFO'. The default is 'CRITICAL' (i.e. usually no log output to console).

    Returns:
        cellpy.batch.Batch object
    """
    silent = kwargs.pop("silent", False)
    backend = kwargs.pop("backend", None)
    if backend is not None:
        prms.Batch.backend = backend
    else:
        prms.Batch.backend = "matplotlib"

    dpi = kwargs.pop("dpi", 300)

    default_log_level = kwargs.pop("default_log_level", "CRITICAL")
    if len(args) == 1:
        file_name = args[0]
    else:
        file_name = kwargs.pop("file_name", None)

    log.setup_logging(default_level=default_log_level, reset_big_log=True)
    logging.debug(f"creating Batch(kwargs: {kwargs})")

    if file_name is not None:
        kwargs.pop("db_reader", None)
        b = Batch(*args, file_name=file_name, db_reader=None, **kwargs)
        b.create_journal(file_name)
    else:
        b = Batch(*args, **kwargs)
        b.create_journal()

    steps = {
        "paginate": (b.paginate,),
        "update": (b.update,),
        "combine": (b.combine_summaries,),
        "plot": (b.plot_summaries,),
        "save": (_pb_save_plot, b, dpi),
    }

    with tqdm(total=(100 * len(steps) + 20), leave=False, file=sys.stdout) as pbar:
        pbar.update(10)
        for description in steps:
            func, *args = steps[description]
            pbar.set_description(description)
            pbar.update(10)
            try:
                func(*args)
            except cellpy.exceptions.NullData as e:
                if not silent:
                    tqdm.write(f"\nEXCEPTION (NullData): {str(e)}")
                    tqdm.write("...aborting")
                    return
                else:
                    raise e

        pbar.set_description(f"final")
        pbar.update(10)

    return b


def _pb_save_plot(b, dpi):
    name = b.experiment.journal.name
    out_dir = pathlib.Path(b.experiment.journal.batch_dir)

    for n, farm in enumerate(b.plotter.farms):
        if len(b.plotter.farms) > 1:
            file_name = f"summary_plot_{name}_{str(n + 1).zfill(3)}.png"
        else:
            file_name = f"summary_plot_{name}.png"
        out = out_dir / file_name
        logging.info(f"saving file {file_name} in\n{out}")
        farm.savefig(out, dpi=dpi)
    # and other stuff


def iterate_batches(folder, extension=".json", glob_pattern=None, **kwargs):
    """Iterate through all journals in given folder.

    Args:
        folder (str or pathlib.Path): folder containing the journal files.
        extension (str): extension for the journal files (used when creating a default glob-pattern).
        glob_pattern (str): optional glob pattern.
        **kwargs: keyword arguments passed to ´batch.process_batch´.
    """

    folder = pathlib.Path(folder)
    logging.info(f"Folder for batches to be iterated: {folder}")
    if not folder.is_dir():
        print(f"Could not find the folder ({folder})")
        print("Aborting...")
        logging.info("ABORTING - folder not found.")
        return
    print(" Iterating through the folder ".center(80, "="))
    print(f"Folder name: {folder}")
    if not glob_pattern:
        glob_pattern = f"*{extension}"
    print(f"Glob pattern: {glob_pattern}")
    files = sorted(folder.glob(glob_pattern))
    if not files:
        print("No files found! Aborting...")
        logging.info("ABORTING - no files detected.")
        return
    print("Found the following files:")
    for n, file in enumerate(files):
        logging.debug(f"file: {file}")
        print(f"  {str(n).zfill(4)} - {file}")

    print(" Processing ".center(80, "-"))
    output = []
    failed = []
    with tqdm(files, file=sys.stdout) as pbar:
        for n, file in enumerate(pbar):
            output_str = f"[{str(n).zfill(4)}]"
            pbar.set_description(output_str)
            output_str += f"({file.name})"
            logging.debug(f"processing file: {file.name}")
            try:
                process_batch(file, **kwargs)
                output_str += " [OK]"
                logging.debug(f"No errors detected.")
            except Exception as e:
                output_str += " [FAILED!]"
                failed.append(str(file))
                logging.debug("Error detected.")
                logging.debug(e)

            output.append(output_str)

    print(" Result ".center(80, "-"))
    print("\n".join(output))
    if failed:
        print("\nFailed:")
        failed_txt = "\n".join(failed)
        print(failed_txt)
        logging.info(failed_txt)
    print("\n...Finished ")


def main():
    from pathlib import Path

    # Use these when working on my work PC:
    test_data_path = r"C:\Scripting\MyFiles\development_cellpy\testdata"
    out_data_path = r"C:\Scripting\Processing\Test\out"

    # Use these when working on my MacBook:
    # test_data_path = "/Users/jepe/scripting/cellpy/testdata"
    # out_data_path = "/Users/jepe/cellpy_data"

    test_data_path = Path(test_data_path)
    out_data_path = Path(out_data_path)

    logging.info("---SETTING SOME PRMS---")
    prms.Paths["db_filename"] = "cellpy_db.xlsx"
    prms.Paths["cellpydatadir"] = test_data_path / "hdf5"
    prms.Paths["outdatadir"] = out_data_path
    prms.Paths["rawdatadir"] = test_data_path / "data"
    prms.Paths["db_path"] = test_data_path / "db"
    prms.Paths["filelogdir"] = test_data_path / "log"

    project = "prebens_experiment"
    name = "test"
    batch_col = "b01"

    logging.info("---INITIALISATION OF BATCH---")
    b = init(name, project, batch_col=batch_col)
    b.experiment.export_raw = True
    b.experiment.export_cycles = True
    logging.info("*creating info df*")
    b.create_journal()
    logging.info("*creating folder structure*")
    b.paginate()
    logging.info("*load and save*")
    b.update()
    logging.info("*make summaries*")
    try:
        b.combine_summaries()
        summaries = b.experiment.memory_dumped
    except cellpy.exeptions.NullData:
        print("NO DATA")
        return
    # except cellpy.exceptions.NullData:
    #     print("NOTHING")
    #     return

    logging.info("*plotting summaries*")
    b.plot_summaries("tmp_bokeh_plot.html")

    # logging.info("*using special features*")
    # logging.info(" - select_ocv_points")
    # analyzer = OCVRelaxationAnalyzer()
    # analyzer.assign(b.experiment)
    # analyzer.do()
    # ocv_df_list = analyzer.farms[0]
    # for df in ocv_df_list:
    #     df_up = df.loc[df.type == "ocvrlx_up", :]
    #     df_down = df.loc[df.type == "ocvrlx_down", :]
    #     logging.info(df_up)
    logging.info("---FINISHED---")


def check_new():
    use_db = False
    f = r"C:\scripts\processing_cellpy\out\SecondLife\cellpy_batch_embla_002.json"
    # f = r"C:\Scripting\Processing\Celldata\outdata\SilcRoad\cellpy_batch_uio66.json"
    # f = r"C:\Scripting\Processing\Celldata\outdata\MoZEES\cellpy_batch_round_robin_001.json"
    name = "embla_test"
    project = "cellpy_test"
    batch_col = "b02"
    if use_db:
        process_batch(name, project, batch_col=batch_col, nom_cap=372)
    else:
        # process_batch(f, nom_cap=372)
        process_batch(f, force_raw_file=False, force_cellpy=True, nom_cap=372)


# TODO: allow exporting html when processing batch instead of just png


def check_iterate():
    folder_name = r"C:\Scripting\Processing\Celldata\live"
    iterate_batches(folder_name, export_cycles=False, export_raw=False)


if __name__ == "__main__":
    print("---IN BATCH 2 MAIN---")
    check_new()
