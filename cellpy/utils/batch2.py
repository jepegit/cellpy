"""Routines for batch processing of cells (v2)."""

import logging

from cellpy import prms
from cellpy.utils.batch_tools.batch_exporters import CSVExporter
from cellpy.utils.batch_tools.batch_experiments import CyclingExperiment

logger = logging.getLogger(__name__)
logging.captureWarnings(True)


class Batch:
    def __init__(self, *args, **kwargs):
        self.experiment = CyclingExperiment()
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
        self.exporter.assign(self.experiment)

    def create_info_df(self):
        print(self.experiment.journal.name)
        print(self.experiment.journal.project)
        self.experiment.journal.from_db()
        self.experiment.journal.to_file()

    def create_folder_structure(self):
        self.experiment.journal.paginate()

    def save_info_df(self):
        self.experiment.journal.to_file()
        print(self.experiment.journal.pages.head(10))
        print()
        print("saved to:")
        print(self.experiment.journal.file_name)

    def load_and_save_raw(self):
        self.experiment.update()

    def make_summaries(self):
        self.exporter.do()


def main():
    print("---SETTING SOME PRMS---")
    prms.Paths["db_filename"] = "cellpy_db.xlsx"
    # These prms works for me on my mac, but probably not for you:
    prms.Paths["cellpydatadir"] = "/Users/jepe/scripting/cellpy/testdata/hdf5"
    prms.Paths["outdatadir"] = "/Users/jepe/cellpy_data"
    prms.Paths["rawdatadir"] = "/Users/jepe/scripting/cellpy/testdata/data"
    prms.Paths["db_path"] = "/Users/jepe/scripting/cellpy/testdata/db"
    prms.Paths["filelogdir"] = "/Users/jepe/scripting/cellpy/testdata/log"

    project = "prebens_experiment"
    name = "test"
    batch_col = 5

    print("---INITIALISATION OF BATCH---")
    b = init(name, project, batch_col=batch_col)
    b.export_raw = True
    b.export_cycles = True
    b.create_info_df()
    b.create_folder_structure()
    b.load_and_save_raw()
    b.make_summaries()

    print("---FINISHED---")


def init(*args, **kwargs):
    """Returns an initialized instance of the Batch class"""
    # set up cellpy logger
    default_log_level = kwargs.pop("default_log_level", None)
    import cellpy.log as log
    log.setup_logging(custom_log_dir=prms.Paths["filelogdir"],
                      default_level=default_log_level)
    return Batch(*args, **kwargs)


if __name__ == "__main__":
    print("---IN BATCH 2 MAIN---")
    main()
