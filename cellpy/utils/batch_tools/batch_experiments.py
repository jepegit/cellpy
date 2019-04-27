import logging
import os

from cellpy.readers import cellreader
from cellpy import prms
from cellpy.utils.batch_tools import batch_helpers as helper
from cellpy.utils.batch_tools.batch_core import BaseExperiment
from cellpy.utils.batch_tools.batch_journals import LabJournal

logger = logging.getLogger(__name__)


class CyclingExperiment(BaseExperiment):
    """Load experimental data into memory.

    This is a re-implementation of the old batch behaviour where
    all the data-files are processed secuentially (and optionally exported)
    while the summary tables are kept and processed. This implementation
    also saves the step tables (for later use when using look-up
    functionallity).


    Attributes:
        journal (:obj: LabJournal): information about the experiment.
        force_cellpy (bool): tries only to load the cellpy-file if True.
        force_raw_file (bool): loads raw-file(s) even though appropriate cellpy-file
           exists if True.
        save_cellpy (bool): saves a cellpy-file for each cell if True.
        accept_errors (bool): in case of error, dont raise an exception, but
           continue to the next file if True.
        all_in_memory (bool): store the cellpydata-objects in memory if True.
        export_cycles (bool): export voltage-capacity curves if True.
        shifted_cycles (bool): set this to True if you want to export the
           voltage-capacity curves using the shifted-cycles option (only valid
           if you set export_cycles to True).
        export_raw (bool): export the raw-data if True.
        export_ica (bool): export dq-dv curves if True.
        last_cycle (int): sets the last cycle (i.e. the highest cycle number)
           that you would like to process dq-dv on). Use all if None (the
           default value).
        selected_summaries (list): a list of summary labels defining what
           summary columns to make joint summaries from (optional).
        errors (dict): contains a dictionary listing all the errors encountered.

    Args:
        db_reader (str or object): custom db_reader (see doc on db_reader).

    Example:


    """

    def __init__(self, *args, **kwargs):
        db_reader = kwargs.pop("db_reader", "default")
        super().__init__(*args)
        self.journal = LabJournal(db_reader=db_reader)
        self.errors = dict()

        self.force_cellpy = False
        self.force_raw_file = False
        self.force_recalc = False
        self.save_cellpy = True
        self.accept_errors = False
        self.all_in_memory = False

        self.export_cycles = False
        self.shifted_cycles = False
        self.export_raw = True
        self.export_ica = False
        self.last_cycle = None

        self.selected_summaries = None

    def update(self, all_in_memory=None):
        """Updates the selected datasets.

        Args:
            all_in_memory (bool): store the cellpydata in memory (default
            False)

        """
        logging.info("[update experiment]")
        if all_in_memory is not None:
            self.all_in_memory = all_in_memory

        pages = self.journal.pages
        summary_frames = dict()
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
            if not self.force_cellpy or self.force_recalc:
                logging.info(
                    "setting cycle mode (%s)..." % row.cell_type)
                cell_data.cycle_mode = row.cell_type

            logging.info("loading cell")
            if not self.force_cellpy:
                logging.debug("not forcing to load cellpy-file instead of raw file.")
                try:
                    cell_data.loadcell(
                        raw_files=row.raw_file_names,
                        cellpy_file=row.cellpy_file_names,
                        mass=row.masses,
                        summary_on_raw=True,
                        force_raw=self.force_raw_file,
                        use_cellpy_stat_file=prms.Reader.use_cellpy_stat_file
                    )
                except Exception as e:
                    logging.info('Failed to load: ' + str(e))
                    errors.append("loadcell:" + str(indx))
                    if not self.accept_errors:
                        raise e
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
                        raise e
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

            if cell_data.dataset.step_table is None or self.force_recalc:
                logging.info(
                    "Running make_step_table"
                )

                cell_data.make_step_table()

            if summary_tmp is None or self.force_recalc:
                logging.info(
                    "Running make_summary"
                )

                cell_data.make_summary(find_end_voltage=True,
                                       find_ir=True)

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

            summary_frames[indx] = summary_tmp

            if self.all_in_memory:
                cell_data_frames[indx] = cell_data
            else:
                cell_data_frames[indx] = cellreader.CellpyData(initialize=True)
                cell_data_frames[indx].dataset.step_table = \
                    cell_data.dataset.step_table
                # cell_data_frames[indx].dataset.step_table_made = True

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
        self.cell_data_frames = cell_data_frames

    @property
    def cell_names(self):
        try:
            return [key for key in self.cell_data_frames]
        except TypeError:
            return None

    def status(self):
        print("\n")
        print(" STATUS ".center(80, "="))
        print(self)
        print(" summary frames ".center(80, "-"))
        if self.summary_frames is not None:
            for key in self.summary_frames:
                print(f" {{{key}}}")
        print(" memory dumped ".center(80, "-"))
        if self.memory_dumped is not None:
            for key in self.memory_dumped:
                print(f"{key}: {type(self.memory_dumped[key])}")
        print(80 * "=")

    def link(self):
        """Ensure that an appropriate link to the cellpy-files exists for
        each cell.

        The experiment will then contain a CellpyData object for each cell
        (in the cell_data_frames attribute) with only the step-table stored.

        Remark that running update persists the summary frames instead (or
        everything in case you specify all_in_memory=True).
        This might be considered "a strange and unexpected behaviour". Sorry
        for that (but the authors of this package is also a bit strange...).

        """
        logging.info("[estblishing links]")
        logging.debug("checking and establishing link to data")
        cell_data_frames = dict()
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

                cell_data_frames[indx] = cellreader.CellpyData(initialize=True)

                step_table = helper.look_up_and_get(
                    row.cellpy_file_names,
                    "step_table"
                )

                cell_data_frames[indx].dataset.step_table = step_table

            self.cell_data_frames = cell_data_frames

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

