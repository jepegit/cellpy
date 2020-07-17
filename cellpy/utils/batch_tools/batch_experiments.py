import logging
import warnings
import os
import sys

from tqdm.auto import tqdm

from cellpy.readers import cellreader
from cellpy import prms
from cellpy.parameters.internal_settings import get_headers_journal, get_headers_summary
from cellpy.utils.batch_tools import batch_helpers as helper
from cellpy.utils.batch_tools.batch_core import BaseExperiment
from cellpy.utils.batch_tools.batch_journals import LabJournal

hdr_journal = get_headers_journal()
hdr_summary = get_headers_summary()


class CyclingExperiment(BaseExperiment):
    """Load experimental data into memory.

    This is a re-implementation of the old batch behaviour where
    all the data-files are processed sequentially (and optionally exported)
    while the summary tables are kept and processed. This implementation
    also saves the step tables (for later use when using look-up
    functionality).


    Attributes:
        journal (:obj: LabJournal): information about the experiment.
        force_cellpy (bool): tries only to load the cellpy-file if True.
        force_raw (bool): loads raw-file(s) even though appropriate cellpy-file
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
        self.log = dict()

        self.force_cellpy = False
        self.force_raw = False
        self.force_recalc = False
        self.save_cellpy = True
        self.accept_errors = False
        self.all_in_memory = False

        self.export_cycles = False
        self.shifted_cycles = False
        self.export_raw = True
        self.export_ica = False
        self.last_cycle = None
        self.nom_cap = None

        self.selected_summaries = None

    def update(self, all_in_memory=None, **kwargs):
        """Updates the selected datasets.

        Args:
            all_in_memory (bool): store the cellpydata in memory (default
                False)

        """
        logging.info("[update experiment]")
        if all_in_memory is not None:
            self.all_in_memory = all_in_memory

        pages = self.journal.pages
        if self.nom_cap:
            pages[hdr_journal.nom_cap] = self.nom_cap

        if pages.empty:
            raise Exception("your journal is empty")

        summary_frames = dict()
        cell_data_frames = dict()
        number_of_runs = len(pages)
        counter = 0
        errors = []
        pbar = tqdm(list(pages.iterrows()), file=sys.stdout, leave=False)
        for indx, row in pbar:
            counter += 1
            h_txt = f"{indx}"
            n_txt = f"loading {counter}"
            l_txt = f"starting to process file # {counter} ({indx})"
            logging.debug(l_txt)
            pbar.set_description(n_txt)
            pbar.set_postfix_str(s=h_txt, refresh=True)

            if not row[hdr_journal.raw_file_names] and not self.force_cellpy:
                logging.info("File(s) not found!")
                logging.info(indx)
                logging.debug("File(s) not found for index=%s" % indx)
                errors.append(indx)
                h_txt += " [-]"
                pbar.set_postfix_str(s=h_txt, refresh=True)
                continue

            else:
                logging.info(f"Processing {indx}")

            cell_data = cellreader.CellpyData()
            if not self.force_cellpy or self.force_recalc:
                logging.info("setting cycle mode (%s)..." % row[hdr_journal.cell_type])
                cell_data.cycle_mode = row[hdr_journal.cell_type]

            logging.info("loading cell")
            if not self.force_cellpy:
                if self.force_raw:
                    h_txt += " (r)"
                    pbar.set_postfix_str(s=h_txt, refresh=True)
                logging.debug("not forcing to load cellpy-file instead of raw file.")

                try:
                    cell_data.loadcell(
                        raw_files=row[hdr_journal.raw_file_names],
                        cellpy_file=row[hdr_journal.cellpy_file_name],
                        mass=row[hdr_journal.mass],
                        summary_on_raw=True,
                        force_raw=self.force_raw,
                        use_cellpy_stat_file=prms.Reader.use_cellpy_stat_file,
                        nom_cap=row[hdr_journal.nom_cap],
                        **kwargs,
                    )
                except Exception as e:
                    logging.info("Failed to load: " + str(e))
                    errors.append("loadcell:" + str(indx))
                    h_txt += " [-]"
                    pbar.set_postfix_str(s=h_txt, refresh=True)
                    if not self.accept_errors:
                        raise e
                    continue

            else:
                logging.info("forcing")
                h_txt += " (f)"
                pbar.set_postfix_str(s=h_txt, refresh=True)
                try:
                    cell_data.load(
                        row[hdr_journal.cellpy_file_name],
                        parent_level=self.parent_level,
                    )
                except Exception as e:
                    logging.info(
                        f"Critical exception encountered {type(e)} "
                        "- skipping this file"
                    )
                    logging.debug("Failed to load. Error-message: " + str(e))
                    errors.append("load:" + str(indx))
                    h_txt += " [-]"
                    pbar.set_postfix_str(s=h_txt, refresh=True)
                    if not self.accept_errors:
                        raise e
                    continue

            if not cell_data.check():
                logging.info("...not loaded...")
                logging.debug("Did not pass check(). Could not load cell!")
                errors.append("check:" + str(indx))
                h_txt += " [-]"
                pbar.set_postfix_str(s=h_txt, refresh=True)
                continue

            logging.info("...loaded successfully...")
            h_txt += " [OK]"
            pbar.set_postfix_str(s=h_txt, refresh=True)
            summary_tmp = cell_data.cell.summary
            logging.info("Trying to get summary_data")

            if cell_data.cell.steps is None or self.force_recalc:
                logging.info("Running make_step_table")
                n_txt = f"steps {counter}"
                pbar.set_description(n_txt, refresh=True)
                cell_data.make_step_table()

            if summary_tmp is None or self.force_recalc:
                logging.info("Running make_summary")
                n_txt = f"summary {counter}"
                pbar.set_description(n_txt, refresh=True)
                cell_data.make_summary(find_end_voltage=True, find_ir=True)

            # if summary_tmp.index.name == b"Cycle_Index":
            #     logging.debug("Strange: 'Cycle_Index' is a byte-string")
            #     summary_tmp.index.name = "Cycle_Index"

            if not summary_tmp.index.name == hdr_summary.cycle_index:
                # TODO: Why did I do this? Does not make any sense. It seems like
                #    batch forces Summary to have "Cycle_Index" as index, but
                #    files not processed by batch will not have.
                #    I think I should choose what should and what should not have
                #    a measurement col as index. Current:
                #    steps - not sure
                #    raw - data_point (already implemented I think)
                #    summary - not sure
                logging.debug("Setting index to Cycle_Index")
                # check if it is a byte-string
                if b"Cycle_Index" in summary_tmp.columns:
                    logging.debug("Seems to be a byte-string in the column-headers")
                    summary_tmp.rename(
                        columns={b"Cycle_Index": "Cycle_Index"}, inplace=True
                    )
                # TODO: check if drop=False works [#index]
                try:
                    summary_tmp.set_index("cycle_index", inplace=True)
                except KeyError:
                    logging.debug("cycle_index already an index")

            summary_frames[indx] = summary_tmp

            if self.all_in_memory:
                cell_data_frames[indx] = cell_data
            else:
                cell_data_frames[indx] = cellreader.CellpyData(initialize=True)
                cell_data_frames[indx].cell.steps = cell_data.cell.steps
                # cell_data_frames[indx].dataset.steps_made = True

            if self.save_cellpy:
                logging.info("saving to cellpy-format")
                n_txt = f"saving {counter}"
                pbar.set_description(n_txt, refresh=True)
                if not row.fixed:
                    logging.info("saving cell to %s" % row.cellpy_file_name)
                    cell_data.ensure_step_table = True
                    try:
                        cell_data.save(row.cellpy_file_name)
                    except Exception as e:
                        logging.error("saving file failed")
                        logging.error(e)

                else:
                    logging.debug("saving cell skipped (set to 'fixed' in info_df)")
            else:
                warnings.warn("you opted to not save to cellpy-format")
                logging.info("I strongly recommend you to save to cellpy-format:")
                logging.info(" >>> b.save_cellpy = True")
                logging.info(
                    "Without the cellpy-files, you cannot select specific cells"
                    " if you did not opt to store all in memory"
                )

            if self.export_raw or self.export_cycles:
                export_text = "exporting"
                if self.export_raw:
                    export_text += " [raw]"
                if self.export_cycles:
                    export_text += " [cycles]"
                logging.info(export_text)
                n_txt = f"{export_text} {counter}"
                pbar.set_description(n_txt, refresh=True)
                cell_data.to_csv(
                    self.journal.raw_dir,
                    sep=prms.Reader.sep,
                    cycles=self.export_cycles,
                    shifted=self.shifted_cycles,
                    raw=self.export_raw,
                    last_cycle=self.last_cycle,
                )

            if self.export_ica:
                logging.info("exporting [ica]")
                try:
                    helper.export_dqdv(
                        cell_data,
                        savedir=self.journal.raw_dir,
                        sep=prms.Reader.sep,
                        last_cycle=self.last_cycle,
                    )
                except Exception as e:
                    logging.error("Could not make/export dq/dv data")
                    logging.debug(
                        "Failed to make/export " "dq/dv data (%s): %s" % (indx, str(e))
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

        (OK, I will change it. Soon.)

        """
        logging.info("[establishing links]")
        logging.debug("checking and establishing link to data")
        cell_data_frames = dict()
        counter = 0
        errors = []
        try:
            for indx, row in self.journal.pages.iterrows():
                counter += 1
                l_txt = f"starting to process file # {counter} (index={indx})"
                logging.debug(l_txt)
                logging.debug(f"linking cellpy-file: {row.name}")

                if not os.path.isfile(row[hdr_journal.cellpy_file_name]):
                    logging.error(row[hdr_journal.cellpy_file_name])
                    logging.error("File does not exist")
                    raise IOError

                cell_data_frames[indx] = cellreader.CellpyData(initialize=True)

                step_table = helper.look_up_and_get(
                    row[hdr_journal.cellpy_file_name], prms._cellpyfile_step
                )

                cell_data_frames[indx].cell.steps = step_table

            self._data = None
            self.cell_data_frames = cell_data_frames

        except IOError as e:
            logging.warning(e)
            e_txt = "links not established - try update instead"
            logging.warning(e_txt)
            errors.append(e_txt)

        self.errors["link"] = errors

    def recalc(self, save=True, step_opts=None, summary_opts=None, testing=False):
        """Run make_step_table and make_summary on all cells.

        Args:
            save (bool): Save updated cellpy-files if True.
            step_opts (dict): parameters to inject to make_steps.
            summary_opts (dict): parameters to inject to make_summary.

        Returns:
            None
        """
        errors = []
        log = []
        if testing:
            pbar = tqdm(
                list(self.journal.pages.iloc[0:2, :].iterrows()),
                file=sys.stdout,
                leave=False,
            )
        else:
            pbar = tqdm(
                list(self.journal.pages.iterrows()), file=sys.stdout, leave=False
            )
        for indx, row in pbar:
            nom_cap = row[hdr_journal.nom_cap]
            pbar.set_description(indx)
            try:
                c = self.data[indx]
            except TypeError as e:
                e_txt = (
                    f"could not extract data for {indx} - have you forgotten to link?"
                )
                errors.append(e_txt)
                warnings.warn(e_txt)

            else:
                if nom_cap:
                    c.set_nom_cap(nom_cap)
                try:
                    pbar.set_postfix_str(s="steps", refresh=True)
                    if step_opts is not None:
                        c.make_step_table(**step_opts)
                    else:
                        c.make_step_table()

                    pbar.set_postfix_str(s="summary", refresh=True)
                    if summary_opts is not None:
                        c.make_summary(**summary_opts)
                    else:
                        c.make_summary()

                except Exception as e:
                    e_txt = f"recalculating for {indx} failed!"
                    errors.append(e_txt)
                    warnings.warn(e_txt)
                else:
                    if save:
                        # remark! got a win error when trying to save (hdf5-file in use) (must fix this)
                        pbar.set_postfix_str(s="save", refresh=True)
                        try:
                            c.save(row.cellpy_file_name)
                            log.append(f"saved {indx} to {row.cellpy_file_name}")
                        except Exception as e:
                            e_txt = f"saving {indx} to {row.cellpy_file_name} failed!"
                            errors.append(e_txt)
                            warnings.warn(e_txt)
        self.errors["recalc"] = errors
        self.log["recalc"] = log


class ImpedanceExperiment(BaseExperiment):
    def __init__(self):
        super().__init__()


class LifeTimeExperiment(BaseExperiment):
    def __init__(self):
        super().__init__()
