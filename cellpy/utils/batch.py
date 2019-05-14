"""Routines for batch processing of cells (v2)."""

import logging

import pandas as pd

from cellpy import prms
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
        db_reader = kwargs.pop("db_reader", "default")
        logger.debug("creating CyclingExperiment")
        self.experiment = CyclingExperiment(db_reader=db_reader)
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

        self.exporter = CSVExporter()
        self.exporter._assign_dumper(ram_dumper)
        self.exporter.assign(self.experiment)
        self.plotter = CyclingSummaryPlotter()
        self.plotter.assign(self.experiment)
        self._info_df = self.info_file

    def __str__(self):
        return str(self.experiment)

    def show_pages(self, number_of_rows=5):
        return self.experiment.journal.pages.head(number_of_rows)

    @property
    def view(self):
        pages = self.experiment.journal.pages
        pages = pages[COLUMNS_SELECTED_FOR_VIEW]
        return pages

    @property
    def info_file(self):
        return self.experiment.journal.file_name

    @property
    def summaries(self):
        try:
            keys = [df.name for df in self.experiment.memory_dumped["summary_engine"]]
            return pd.concat(self.experiment.memory_dumped["summary_engine"], keys=keys, axis=1)
        except KeyError:
            logging.info("no summary exists")

    @property
    def summary_columns(self):
        return self.summaries.columns.get_level_values(0)

    @property
    def info_df(self):
        return self.experiment.journal.pages

    @info_df.setter
    def info_df(self, df):
        self.experiment.journal.pages = df

    def create_empty_info_df(self):
        logging.info("Creating an empty info dataframe")
        logging.info(f"name: {self.experiment.journal.name}")
        logging.info(f"project: {self.experiment.journal.project}")

        self.experiment.journal.pages = pd.DataFrame(columns=[
                "filenames", "masses", "total_masses", "loadings",
                "fixed", "labels", "cell_type", "raw_file_names",
                "cellpy_file_names", "groups", "sub_groups",
        ])
        self.experiment.journal.pages.set_index("filenames", inplace=True)

        self.experiment.journal.generate_folder_names()
        self.experiment.journal.paginate()

    def create_info_df(self):
        logging.info(f"name: {self.experiment.journal.name}")
        logging.info(f"project: {self.experiment.journal.project}")
        self.experiment.journal.from_db()
        self.experiment.journal.to_file()

    def create_folder_structure(self):
        self.experiment.journal.paginate()
        logging.info("created folders")

    def save_info_df(self):
        self.experiment.journal.to_file()
        logging.info("saving journal pages")
        print(" journal ".center(80, "-"))
        print(self.experiment.journal.pages.head(10))
        print()
        print("->")
        print(self.experiment.journal.file_name)

    def load_and_save_raw(self):
        self.experiment.update()

    def make_summaries(self):
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
                    "could not find the bokeh "
                    "module -> using matplotlib instead"
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
    b.create_info_df()
    print("*creating folder structure*")
    b.create_folder_structure()
    print("*load and save*")
    b.load_and_save_raw()
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
    """Returns an initialized instance of the Batch class"""
    # set up cellpy logger
    default_log_level = kwargs.pop("default_log_level", None)
    import cellpy.log as log
    log.setup_logging(custom_log_dir=prms.Paths["filelogdir"],
                      default_level=default_log_level)
    logging.debug(f"returning Batch(args: {args}, kwargs: {kwargs})")
    return Batch(*args, **kwargs)


if __name__ == "__main__":
    print("---IN BATCH 2 MAIN---")
    main()
