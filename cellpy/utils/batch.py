"""Routines for batch processing of cells (v2)."""

import logging
import pathlib
import shutil
import warnings
import os

import pandas as pd

from cellpy import prms
from cellpy import log
from cellpy.utils.batch_tools.batch_exporters import CSVExporter
from cellpy.utils.batch_tools.batch_experiments import CyclingExperiment
from cellpy.utils.batch_tools.batch_plotters import CyclingSummaryPlotter
from cellpy.utils.batch_tools.batch_analyzers import OCVRelaxationAnalyzer
from cellpy.utils.batch_tools.dumpers import ram_dumper

logger = logging.getLogger(__name__)
logging.captureWarnings(True)

COLUMNS_SELECTED_FOR_VIEW = ["masses", "total_masses", "loadings"]


class Batch:
    def __init__(self, *args, **kwargs):
        default_log_level = kwargs.pop("log_level", None)
        if default_log_level is not None:
            log.setup_logging(
                custom_log_dir=prms.Paths.filelogdir, default_level=default_log_level
            )

        db_reader = kwargs.pop("db_reader", "default")

        file_name = kwargs.pop("file_name", None)

        logger.debug("creating CyclingExperiment")
        self.experiment = CyclingExperiment(db_reader=db_reader)

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

    @property
    def report(self):
        pages = self.experiment.journal.pages
        pages = pages[COLUMNS_SELECTED_FOR_VIEW]
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
                dictionary: create journal pages from a dictionary (not implemented yet)
                pd.DataFrame: create  journal pages from a pandas DataFrame
                    (not implemented yet)
                filename.xlxs: create journal pages from an excel file
                    (not implemented yet)
                filename.json: load cellpy batch file
                    (not implemented yet, use .experiment.journal.from_file() instead).
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

        else:
            is_file = False
            if isinstance(description, str):
                if description.lower() == "empty":
                    logging.debug("creating empty journal pages")

                if pathlib.Path(description).is_file():
                    is_file = True

            elif isinstance(description, pathlib.Path):
                logging.debug("pathlib.Path object given")
                is_file = True

            elif isinstance(description, pd.DataFrame):
                logging.debug("pandas DataFrame given")

            elif isinstance(description, dict):
                logging.debug("dictionary given")

            else:
                logging.debug(
                    "the option you provided seems to be either of "
                    "an unknown type or a file not found"
                )
                logging.info(
                    "did not understand the option - creating empty journal pages"
                )

            if is_file:
                logging.info(f"loading file {description}")
                logging.debug("not implemented yet")

            # empty journal pages (this might go further up)
            self.experiment.journal.pages = (
                self.experiment.journal._create_empty_pages()
            )

            # finally
            self.experiment.journal.generate_folder_names()
            self.experiment.journal.paginate()

    def create_folder_structure(self):
        warnings.warn("Deprecated - use paginate instead.", DeprecationWarning)
        self.experiment.journal.paginate()
        logging.info("created folders")

    def paginate(self):
        self.experiment.journal.paginate()
        logging.info("created folders")

    def save_journal(self):
        # rename to: save_journal
        # Remark! Got an recursive error when running on mac.
        self.experiment.journal.to_file()
        logging.info("saving journal pages")

    def duplicate_journal(self):
        journal_name = pathlib.Path(self.experiment.journal.file_name)
        if not journal_name.is_file():
            print("No journal saved")
            return
        new_journal_name = journal_name.name
        shutil.copy(journal_name, new_journal_name)

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
        pages["new_cellpy_file_names"] = pages.cellpy_file_names.apply(_new_file_path)

        # copy the cellpy files
        for n, row in pages.iterrows():
            print(f"{row.cellpy_file_names} -> {row.new_cellpy_file_names}")
            try:
                from_file = row.cellpy_file_names
                to_file = row.new_cellpy_file_names
                os.makedirs(os.path.dirname(to_file), exist_ok=True)
                shutil.copy(from_file, to_file)
            except shutil.SameFileError:
                print("Same file! No point in copying")

        # save the journal pages
        pages["cellpy_file_names"] = pages["new_cellpy_file_names"]
        self.experiment.journal.pages = pages[columns]
        journal_file_name = pathlib.Path(self.experiment.journal.file_name).name
        print(f"saving journal to {journal_file_name}")
        self.experiment.journal.to_file(journal_file_name)

        # return pages

    # TODO: load_journal
    # TODO: list_journals?

    def link(self):
        self.experiment.link()

    def load(self):
        # does the same as update
        warnings.warn("Deprecated - use update instead.", DeprecationWarning)
        self.experiment.update()

    def update(self):
        self.experiment.update()

    def make_summaries(self):
        # rename to: combine_summaries
        # also: need a similar function that does not save to csv
        self.exporter.do()

    def plot_summaries(self):
        if prms.Batch.backend == "bokeh":

            try:
                import bokeh.plotting

                if prms.Batch.notebook:
                    bokeh.plotting.output_notebook()

            except ModuleNotFoundError:
                prms.Batch.backend = "matplotlib"
                logging.warning(
                    "could not find the bokeh " "module -> using matplotlib instead"
                )

        self.plotter.do()


def main():
    from pathlib import Path

    # Use these when working on my work PC:
    test_data_path = r"C:\Scripting\MyFiles\development_cellpy\testdata"
    out_data_path = r"C:\Scripting\Processing\Test\out"

    # Use these when working on my MacBook:
    test_data_path = "/Users/jepe/scripting/cellpy/testdata"
    out_data_path = "/Users/jepe/cellpy_data"

    test_data_path = Path(test_data_path)
    out_data_path = Path(out_data_path)

    print("---SETTING SOME PRMS---")
    prms.Paths["db_filename"] = "cellpy_db.xlsx"
    prms.Paths["cellpydatadir"] = test_data_path / "hdf5"
    prms.Paths["outdatadir"] = out_data_path
    prms.Paths["rawdatadir"] = test_data_path / "data"
    prms.Paths["db_path"] = test_data_path / "db"
    prms.Paths["filelogdir"] = test_data_path / "log"

    project = "prebens_experiment"
    name = "test"
    batch_col = "b01"

    print("---INITIALISATION OF BATCH---")
    b = init(name, project, batch_col=batch_col)
    b.experiment.export_raw = True
    b.experiment.export_cycles = True
    print("*creating info df*")
    b.create_journal()
    print("*creating folder structure*")
    b.create_folder_structure()
    print("*load and save*")
    b.update()
    print("*make summaries*")
    b.make_summaries()
    summaries = b.experiment.memory_dumped
    print("*plotting summaries*")
    b.plot_summaries()
    print("*using special features*")
    print(" - select_ocv_points")
    analyzer = OCVRelaxationAnalyzer()
    analyzer.assign(b.experiment)
    analyzer.do()
    ocv_df_list = analyzer.farms[0]
    for df in ocv_df_list:
        df_up = df.loc[df.type == "ocvrlx_up", :]
        df_down = df.loc[df.type == "ocvrlx_down", :]
        print(df_up)
    print("---FINISHED---")


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
    default_log_level = kwargs.pop("default_log_level", "INFO")
    file_name = kwargs.pop("file_name", None)

    log.setup_logging(
        custom_log_dir=prms.Paths["filelogdir"], default_level=default_log_level
    )
    logging.debug(f"returning Batch(kwargs: {kwargs})")
    if file_name is not None:
        kwargs.pop("db_reader", None)
        return Batch(*args, file_name=file_name, db_reader=None, **kwargs)
    return Batch(*args, **kwargs)


if __name__ == "__main__":
    print("---IN BATCH 2 MAIN---")
    main()
