import ast
import logging
import os
import pathlib
import sys
import warnings

import pandas as pd
from tqdm.auto import tqdm

import cellpy
from cellpy import prms
from cellpy.parameters.internal_settings import get_headers_journal, get_headers_summary
from cellpy.readers import cellreader
from cellpy.internals.core import OtherPath
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
        self.instrument = None
        self.custom_data_folder = None

        self.selected_summaries = None

    def _repr_html_(self):
        txt = f"<h2>CyclingExperiment-object</h2> id={hex(id(self))}"
        txt += "<h3>Main attributes</h3>"
        txt += f"""
        <table>
            <thead>
                <tr>
                    <th>Attribute</th>
                    <th>Value</th>
                </tr>
            </thead>
            <tbody>
                <tr><td><b>force_cellpy</b></td><td>{self.force_cellpy}</td></tr>
                <tr><td><b>force_raw</b></td><td>{self.force_raw}</td></tr>
                <tr><td><b>force_recalc</b></td><td>{self.force_recalc}</td></tr>
                <tr><td><b>save_cellpy</b></td><td>{self.save_cellpy}</td></tr>
                <tr><td><b>accept_errors</b></td><td>{self.accept_errors}</td></tr>
                <tr><td><b>all_in_memory</b></td><td>{self.all_in_memory}</td></tr>
                <tr><td><b>export_cycles</b></td><td>{self.export_cycles}</td></tr>
                <tr><td><b>shifted_cycles</b></td><td>{self.shifted_cycles}</td></tr>
                <tr><td><b>export_raw</b></td><td>{self.export_raw}</td></tr>
                <tr><td><b>export_ica</b></td><td>{self.export_ica}</td></tr>
                <tr><td><b>last_cycle</b></td><td>{self.last_cycle}</td></tr>
                <tr><td><b>nom_cap</b></td><td>{self.nom_cap}</td></tr>
                <tr><td><b>instrument</b></td><td>{self.instrument}</td></tr>
                <tr><td><b>custom_data_folder</b></td><td>{self.custom_data_folder}</td></tr>
                <tr><td><b>selected_summaries</b></td><td>{self.selected_summaries}</td></tr>
            </tbody>
        </table>
        """
        txt += "<h3>Cells</h3>"
        txt += f"<p><b>data</b>: contains {len(self)} cells.</p>"
        return txt

    @staticmethod
    def _get_cell_spec_from_page(indx: int, row: pd.Series) -> dict:
        # Edit this if we decide to make "argument families", e.g. loader_split or merger_recalc.

        PRM_SPLITTER = ";"
        EQUAL_SIGN = "="

        def _arg_parser(text: str) -> None:
            individual_specs = text.split(PRM_SPLITTER)
            for p in individual_specs:
                p, a = p.split(EQUAL_SIGN)

        logging.debug(f"getting cell_spec from journal pages ({indx})")
        try:
            cell_spec = row[hdr_journal.argument]
            logging.debug(cell_spec)
            if not isinstance(cell_spec, dict):
                raise TypeError("the cell spec argument is not a dictionary")
        except Exception as e:
            logging.warning(f"could not get cell spec for {indx}")
            logging.warning(f"error message: {e}")
            return {}

        # converting from str if needed
        for spec in cell_spec:
            if isinstance(cell_spec[spec], str):
                if cell_spec[spec].lower() == "true":
                    cell_spec[spec] = True
                elif cell_spec[spec].lower() == "false":
                    cell_spec[spec] = False
                elif cell_spec[spec].lower() == "none":
                    cell_spec[spec] = None
                else:
                    try:
                        logging.debug(
                            f"Using ast.literal_eval to convert cell-spec value from str '{cell_spec[spec]}'"
                        )
                        cell_spec[spec] = ast.literal_eval(cell_spec[spec])
                    except ValueError as e:
                        logging.warning(
                            f"ERROR! Could not convert from str to python object!"
                        )
                        logging.debug(e)
        return cell_spec

    def update(
        self,
        all_in_memory=None,
        cell_specs=None,
        logging_mode=None,
        accept_errors=None,
        **kwargs,
    ):
        """Updates the selected datasets.

        Args:
            all_in_memory (bool): store the `cellpydata` in memory (default
                False)
            cell_specs (dict of dicts): individual arguments pr. cell. The `cellspecs` key-word argument
                dictionary will override the **kwargs and the parameters from the journal pages
                for the indicated cell.
            logging_mode (str): sets the logging mode for the loader(s).
            accept_errors (bool): if True, the loader will continue even if it encounters errors.

            kwargs:
                transferred all the way to the instrument loader, if not
                picked up earlier. Remark that you can obtain the same pr. cell by
                providing a `cellspecs` dictionary. The kwargs have precedence over the
                parameters given in the journal pages, but will be overridden by parameters
                given by `cellspecs`.

                Merging:
                    recalc (Bool): set to False if you don't want automatic "recalc" of
                        cycle numbers etc. when merging several data-sets.
                Loading:
                    selector (dict): selector-based parameters sent to the cellpy-file loader (hdf5) if
                    loading from raw is not necessary (or turned off).

                Debugging:
                    debug (Bool): set to True if you want to run in debug mode (should never be used by non-developers).

        Debug-mode:
                 - runs only for the first item in your journal

        Examples:
            >>> # Don't perform recalculation of cycle numbers etc. when merging
            >>> # All cells:
            >>> b.update(recalc=False)
            >>> # For specific cell(s):
            >>> cell_specs_cell_01 = {"name_of_cell_01": {"recalc": False}}
            >>> b.update(cell_specs=cell_specs_cell_01)

        """

        # TODO: implement experiment.last_cycle
        accept_errors = accept_errors or self.accept_errors

        debugging = kwargs.pop("debug", False)
        testing = kwargs.pop("testing", False)

        # --- cleaning up attributes / arguments etc ---
        force_cellpy = kwargs.pop("force_cellpy", self.force_cellpy)
        force_raw = kwargs.pop("force_raw", self.force_raw)

        logging.info("[update experiment]")
        if all_in_memory is not None:
            self.all_in_memory = all_in_memory

        logging.info(f"Additional keyword arguments: {kwargs}")
        selector = kwargs.get("selector", None)

        pages = self.journal.pages
        if self.nom_cap:
            warnings.warn(
                "Setting nominal capacity through attributes will be deprecated soon since it modifies "
                "the journal pages."
            )
            pages[hdr_journal.nom_cap] = self.nom_cap

        if self.instrument:
            warnings.warn(
                "Setting instrument through attributes will be deprecated soon since it modifies the journal pages."
            )
            pages[hdr_journal.instrument] = self.instrument

        if x := kwargs.pop("instrument", None):
            warnings.warn(
                "Setting instrument through params will be deprecated soon since it modifies the journal pages."
                "Future version will require instrument in the journal pages."
            )
            pages[hdr_journal.instrument] = x

        if pages.empty:
            raise Exception("your journal is empty")

        # --- init ---
        summary_frames = dict()
        cell_data_frames = dict()
        number_of_runs = len(pages)
        logging.debug(f"You have {number_of_runs} cells in your journal")
        counter = 0
        errors = []

        pbar = tqdm(list(pages.iterrows()), file=sys.stdout, leave=False)

        if debugging:
            pbar = tqdm(list(pages.iterrows())[0:1], file=sys.stdout, leave=False)

        # --- iterating ---
        # TODO: create a multiprocessing pool and get one statusbar pr cell
        for index, row in pbar:
            counter += 1
            h_txt = f"{index}"
            n_txt = f"loading {counter}"
            l_txt = f"starting to process file # {counter} ({index})"
            pbar.set_description(n_txt, refresh=True)
            cell_spec_page = self._get_cell_spec_from_page(index, row)

            if cell_specs is not None:
                cell_spec = cell_specs.get(index, dict())
            else:
                cell_spec = dict()

            cell_spec = {**cell_spec_page, **kwargs, **cell_spec}
            l_txt += f" cell_spec: {cell_spec}"
            logging.debug(l_txt)

            # --- UPDATING ARGUMENTS ---
            filename = None
            instrument = None
            cellpy_file = OtherPath(row[hdr_journal.cellpy_file_name])
            _cellpy_file = None
            if not force_raw and cellpy_file.is_file():
                _cellpy_file = cellpy_file
                logging.debug(f"Got cellpy file: {_cellpy_file}")
            if not force_cellpy:
                filename = row[hdr_journal.raw_file_names]
                instrument = row[hdr_journal.instrument]

            cycle_mode = row[hdr_journal.cell_type]
            mass = row[hdr_journal.mass]
            nom_cap = row[hdr_journal.nom_cap]

            loading = None
            area = None
            if hdr_journal.loading in row:
                loading = row[hdr_journal.loading]
            if hdr_journal.area in row:
                area = row[hdr_journal.area]

            summary_kwargs = {
                "use_cellpy_stat_file": prms.Reader.use_cellpy_stat_file,
            }

            step_kwargs = {}
            if not filename and not force_cellpy:
                logging.info(
                    f"Raw file(s) not given in the journal.pages for index={index}"
                )
                errors.append(index)
                continue

            elif not cellpy_file and force_cellpy:
                logging.info(
                    f"Cellpy file not given in the journal.pages for index={index}"
                )
                errors.append(index)
                continue

            else:
                logging.info(f"Processing {index}")

            logging.info("loading cell")
            try:
                logging.debug("inside try: running cellpy.get")
                cell_data = cellpy.get(
                    filename=filename,
                    instrument=instrument,
                    cellpy_file=_cellpy_file,
                    cycle_mode=cycle_mode,
                    mass=mass,
                    nom_cap=nom_cap,
                    loading=loading,
                    area=area,
                    step_kwargs=step_kwargs,
                    summary_kwargs=summary_kwargs,
                    selector=selector,
                    logging_mode=logging_mode,
                    testing=testing,
                    **cell_spec,
                )
                logging.info("loaded cell")

            except Exception as e:
                logging.info("Failed to load: " + str(e))
                errors.append("update:" + str(index))
                h_txt += " [-]"
                pbar.set_postfix_str(s=h_txt, refresh=True)
                if not accept_errors:
                    raise e
                continue

            if cell_data.empty:
                logging.info("...not loaded...")
                logging.debug("Data is empty. Could not load cell!")
                errors.append("check:" + str(index))
                h_txt += " [-]"
                pbar.set_postfix_str(s=h_txt, refresh=True)
                continue

            logging.info("...loaded successfully...")
            h_txt += " [OK]"
            pbar.set_postfix_str(s=h_txt, refresh=True)
            summary_tmp = cell_data.data.summary
            logging.info("Trying to get summary_data")

            if cell_data.data.steps is None or self.force_recalc:
                logging.info("Running make_step_table")
                n_txt = f"steps {counter}"
                pbar.set_description(n_txt, refresh=True)
                cell_data.make_step_table()

            if summary_tmp is None or self.force_recalc:
                logging.info("Running make_summary")
                n_txt = f"summary {counter}"
                pbar.set_description(n_txt, refresh=True)
                cell_data.make_summary(find_end_voltage=True, find_ir=True)

            # some clean-ups (might not be needed anymore):
            if not summary_tmp.index.name == hdr_summary.cycle_index:
                logging.debug("Setting index to Cycle_Index")
                # check if it is a byte-string
                if b"Cycle_Index" in summary_tmp.columns:
                    logging.debug("Seems to be a byte-string in the column-headers")
                    summary_tmp.rename(
                        columns={b"Cycle_Index": "Cycle_Index"}, inplace=True
                    )
                try:
                    summary_tmp.set_index("cycle_index", inplace=True)
                except KeyError:
                    logging.debug("cycle_index already an index")

            summary_frames[index] = summary_tmp

            if self.all_in_memory:
                cell_data_frames[index] = cell_data
            else:
                cell_data_frames[index] = cellreader.CellpyCell(initialize=True)
                cell_data_frames[index].data.steps = cell_data.data.steps

            if self.save_cellpy:
                logging.info("saving to cellpy-format")
                n_txt = f"saving {counter}"
                pbar.set_description(n_txt, refresh=True)
                if self.custom_data_folder is not None:
                    print("Save to custom data-folder not implemented yet")
                    print(f"Saving to {row.cellpy_file_name} instead")
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
                logging.info("You opted to not save to cellpy-format")
                logging.info("It is usually recommended to save to cellpy-format:")
                logging.info(" >>> b.experiment.save_cellpy = True")
                logging.info(
                    "Without the cellpy-files, you cannot select specific cells"
                )
                logging.info("if you did not opt to store all in memory")

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
                        "Failed to make/export " "dq/dv data (%s): %s" % (index, str(e))
                    )
                    errors.append("ica:" + str(index))

        self.errors["update"] = errors
        self.summary_frames = summary_frames
        self.cell_data_frames = cell_data_frames

    def parallel_update(
        self, all_in_memory=None, cell_specs=None, logging_mode=None, **kwargs
    ):
        """Updates the selected datasets in parallel.

        Args:
            all_in_memory (bool): store the `cellpydata` in memory (default
                False)
            cell_specs (dict of dicts): individual arguments pr. cell. The `cellspecs` key-word argument
                dictionary will override the **kwargs and the parameters from the journal pages
                for the indicated cell.
            logging_mode (str): sets the logging mode for the loader(s).

            kwargs:
                transferred all the way to the instrument loader, if not
                picked up earlier. Remark that you can obtain the same pr. cell by
                providing a `cellspecs` dictionary. The kwargs have precedence over the
                parameters given in the journal pages, but will be overridden by parameters
                given by `cellspecs`.

                Merging:
                    recalc (Bool): set to False if you don't want automatic "recalc" of
                        cycle numbers etc. when merging several data-sets.
                Loading:
                    selector (dict): selector-based parameters sent to the cellpy-file loader (hdf5) if
                    loading from raw is not necessary (or turned off).

                Debugging:
                    debug (Bool): set to True if you want to run in debug mode (should never be used by non-developers).

        Debug-mode:
                 - runs only for the first item in your journal

        Examples:
            >>> # Don't perform recalculation of cycle numbers etc. when merging
            >>> # All cells:
            >>> b.update(recalc=False)
            >>> # For specific cell(s):
            >>> cell_specs_cell_01 = {"name_of_cell_01": {"recalc": False}}
            >>> b.update(cell_specs=cell_specs_cell_01)

        """
        status = "PROD"  # set this to DEV when developing this
        async_mode = "threading"
        logging.debug("PARALLEL UPDATE")
        # TODO: implement experiment.last_cycle
        if status != "DEV":
            print("SORRY - MULTIPROCESSING IS NOT IMPLEMENTED PROPERLY YET")
            return self.update(
                all_in_memory=all_in_memory,
                cell_specs=cell_specs,
                logging_mode=logging_mode,
                **kwargs,
            )

        import concurrent.futures
        import multiprocessing

        max_number_processes = multiprocessing.cpu_count()

        if async_mode == "threading":
            pool_executor = concurrent.futures.ThreadPoolExecutor
        else:
            pool_executor = concurrent.futures.ProcessPoolExecutor

        debugging = kwargs.pop("debug", False)

        # --- cleaning up attributes / arguments etc ---
        force_cellpy = kwargs.pop("force_cellpy", self.force_cellpy)
        force_raw = kwargs.pop("force_raw", self.force_raw)

        logging.info("[update experiment]")
        if all_in_memory is not None:
            self.all_in_memory = all_in_memory

        logging.info(f"Additional keyword arguments: {kwargs}")
        selector = kwargs.get("selector", None)

        pages = self.journal.pages
        if self.nom_cap:
            warnings.warn(
                "Setting nominal capacity through attributes will be deprecated soon since it modifies "
                "the journal pages."
            )
            pages[hdr_journal.nom_cap] = self.nom_cap

        if self.instrument:
            warnings.warn(
                "Setting instrument through attributes will be deprecated soon since it modifies the journal pages."
            )
            pages[hdr_journal.instrument] = self.instrument

        if x := kwargs.pop("instrument", None):
            warnings.warn(
                "Setting instrument through params will be deprecated soon since it modifies the journal pages."
                "Future version will require instrument in the journal pages."
            )
            pages[hdr_journal.instrument] = x

        if pages.empty:
            raise Exception("your journal is empty")

        # --- init ---
        summary_frames = dict()
        cell_data_frames = dict()
        number_of_runs = len(pages)
        logging.debug(f"You have {number_of_runs} cells in your journal")
        counter = 0
        errors = []

        pbar = tqdm(list(pages.iterrows()), file=sys.stdout, leave=False)

        if debugging:
            pbar = tqdm(list(pages.iterrows())[0:1], file=sys.stdout, leave=False)

        # --- iterating ---
        # TODO: create a multiprocessing pool and get one statusbar pr cell
        params = []
        with pool_executor(max_number_processes) as executor:
            for index, row in pages.iterrows():
                counter += 1
                cell_spec_page = self._get_cell_spec_from_page(index, row)

                if cell_specs is not None:
                    cell_spec = cell_specs.get(index, dict())
                else:
                    cell_spec = dict()

                cell_spec = {**cell_spec_page, **kwargs, **cell_spec}

                # --- UPDATING ARGUMENTS ---
                filename = None
                instrument = None
                cellpy_file = OtherPath(row[hdr_journal.cellpy_file_name])
                _cellpy_file = None
                if not force_raw and cellpy_file.is_file():
                    _cellpy_file = cellpy_file
                    logging.debug(f"Got cellpy file: {_cellpy_file}")
                if not force_cellpy:
                    filename = row[hdr_journal.raw_file_names]
                    instrument = row[hdr_journal.instrument]

                cycle_mode = row[hdr_journal.cell_type]
                mass = row[hdr_journal.mass]
                nom_cap = row[hdr_journal.nom_cap]

                loading = None
                area = None
                if hdr_journal.loading in row:
                    loading = row[hdr_journal.loading]
                if hdr_journal.area in row:
                    area = row[hdr_journal.area]

                summary_kwargs = {
                    "use_cellpy_stat_file": prms.Reader.use_cellpy_stat_file,
                }

                step_kwargs = {}
                if not filename and not force_cellpy:
                    logging.info(
                        f"Raw file(s) not given in the journal.pages for index={index}"
                    )
                    errors.append(index)
                    continue

                elif not cellpy_file and force_cellpy:
                    logging.info(
                        f"Cellpy file not given in the journal.pages for index={index}"
                    )
                    errors.append(index)
                    continue

                else:
                    logging.info(f"Processing {index}")

                logging.info("loading cell")
                params.append(
                    dict(
                        filename=filename,
                        instrument=instrument,
                        cellpy_file=_cellpy_file,
                        cycle_mode=cycle_mode,
                        mass=mass,
                        nom_cap=nom_cap,
                        loading=loading,
                        area=area,
                        step_kwargs=step_kwargs,
                        summary_kwargs=summary_kwargs,
                        selector=selector,
                        logging_mode=logging_mode,
                        testing=False,
                        **cell_spec,
                    )
                )

            pool = [executor.submit(cellpy.get, **param) for param in params]
            for i in concurrent.futures.as_completed(pool):
                cell_data = i.result()
                if cell_data.empty:
                    logging.info("...not loaded...")
                    logging.debug("Data is empty. Could not load cell!")
                    errors.append("check:" + str(index))

                logging.info("...loaded successfully...")
                summary_tmp = cell_data.data.summary
                logging.info("Trying to get summary_data")

                if cell_data.data.steps is None or self.force_recalc:
                    logging.info("Running make_step_table")
                    cell_data.make_step_table()

                if summary_tmp is None or self.force_recalc:
                    logging.info("Running make_summary")
                    cell_data.make_summary(find_end_voltage=True, find_ir=True)

                # some clean-ups (might not be needed anymore):
                if not summary_tmp.index.name == hdr_summary.cycle_index:
                    logging.debug("Setting index to Cycle_Index")
                    # check if it is a byte-string
                    if b"Cycle_Index" in summary_tmp.columns:
                        logging.debug("Seems to be a byte-string in the column-headers")
                        summary_tmp.rename(
                            columns={b"Cycle_Index": "Cycle_Index"}, inplace=True
                        )
                    try:
                        summary_tmp.set_index("cycle_index", inplace=True)
                    except KeyError:
                        logging.debug("cycle_index already an index")

                summary_frames[index] = summary_tmp

                if self.all_in_memory:
                    cell_data_frames[index] = cell_data
                else:
                    cell_data_frames[index] = cellreader.CellpyCell(initialize=True)
                    cell_data_frames[index].data.steps = cell_data.data.steps

                if self.save_cellpy:
                    logging.info("saving to cellpy-format")
                    n_txt = f"saving {counter}"
                    pbar.set_description(n_txt, refresh=True)
                    if self.custom_data_folder is not None:
                        print("Save to custom data-folder not implemented yet")
                        print(f"Saving to {row.cellpy_file_name} instead")
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
                    logging.info("You opted to not save to cellpy-format")
                    logging.info("It is usually recommended to save to cellpy-format:")
                    logging.info(" >>> b.experiment.save_cellpy = True")
                    logging.info(
                        "Without the cellpy-files, you cannot select specific cells"
                    )
                    logging.info("if you did not opt to store all in memory")

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
                            "Failed to make/export "
                            "dq/dv data (%s): %s" % (index, str(e))
                        )
                        errors.append("ica:" + str(index))

        self.errors["update"] = errors
        self.summary_frames = summary_frames
        self.cell_data_frames = cell_data_frames

    def export_cellpy_files(self, path=None, **kwargs):
        """Export all cellpy-files to a given path.

        Remarks:
            This method can only export to local folders
            (OtherPath objects are not formally supported, but
            might still work if the path is local).

        Args:
            path (str, pathlib.Path): path to export to (default: current working directory)
        """
        if path is None:
            path = "."
        errors = []
        path = pathlib.Path(path)
        cell_names = self.cell_names
        for cell_name in cell_names:
            cellpy_file_name = self.journal.pages.loc[
                cell_name, hdr_journal.cellpy_file_name
            ]
            cellpy_file_name = path / pathlib.Path(cellpy_file_name).name
            print(f"Exporting {cell_name} to {cellpy_file_name}")
            try:
                c = self.data[cell_name]
            except TypeError as e:
                errors.append(f"could not extract data for {cell_name} - linking")
                self._link_cellpy_file(cell_name)

            c.save(cellpy_file_name, **kwargs)
        self.errors["export_cellpy_files"] = errors

    @property
    def cell_names(self):
        """Returns a list of cell-names (strings)"""
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

    def link(self, **kwargs):
        """Ensure that an appropriate link to the cellpy-files exists for
        each cell.

        The experiment will then contain a CellpyCell object for each cell
        (in the cell_data_frames attribute) with only the step-table stored.

        Remark that running update persists the summary frames instead (or
        everything in case you specify all_in_memory=True).
        This might be considered "a strange and unexpected behaviour". Sorry
        for that (but the authors of this package is also a bit strange...).

        (OK, I will change it. Soon.)

        **kwargs: passed to _link_cellpy_file
            max_cycle (int): maximum cycle number to link/load (remark that the
                cellpy objects will get the property overwrite_able set to False
                if you give a max_cycle to prevent accidentally saving a "truncated"
                file (use c.save(filename, overwrite=True) to force overwrite))


        """
        logging.info("[establishing links]")
        logging.debug("checking and establishing link to data")

        errors = []

        for cell_label in self.journal.pages.index:
            logging.debug(f"trying to link {cell_label}")
            try:
                self._link_cellpy_file(cell_label, **kwargs)
            except IOError as e:
                logging.warning(e)
                e_txt = f"{cell_label}: links not established - try update instead"
                logging.warning(e_txt)
                errors.append(e_txt)

        self.errors["link"] = errors

    def recalc(
        self,
        save=True,
        step_opts=None,
        summary_opts=None,
        indexes=None,
        calc_steps=True,
        testing=False,
    ):
        """Run make_step_table and make_summary on all cells.

        Args:
            save (bool): Save updated cellpy-files if True.
            step_opts (dict): parameters to inject to make_steps.
            summary_opts (dict): parameters to inject to make_summary.
            indexes (list): Only recalculate for given indexes (i.e. list of cell-names).
            calc_steps (bool): Run make_steps before making the summary.
            testing (bool): Only for testing purposes.

        Returns:
            None
        """

        # TODO: option (default) to only recalc if the values (mass, nom_cap,...) have changed
        errors = []
        log = []
        if testing:
            pbar = tqdm(
                list(self.journal.pages.iloc[0:2, :].iterrows()),
                file=sys.stdout,
                leave=False,
            )
        elif indexes is not None:
            pbar = tqdm(
                list(self.journal.pages.loc[indexes, :].iterrows()),
                file=sys.stdout,
                leave=False,
            )
        else:
            pbar = tqdm(
                list(self.journal.pages.iterrows()), file=sys.stdout, leave=False
            )
        for indx, row in pbar:
            nom_cap = row[hdr_journal.nom_cap]
            mass = row[hdr_journal.mass]
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
                if mass:
                    c.set_mass(mass)
                try:
                    if calc_steps:
                        pbar.set_postfix_str(s="steps", refresh=True)
                        if step_opts is not None:
                            c.make_step_table(**step_opts)
                        else:
                            c.make_step_table()

                    pbar.set_postfix_str(s="summary", refresh=True)
                    if summary_opts is not None:
                        c.make_summary(**summary_opts)
                    else:
                        c.make_summary(find_end_voltage=True, find_ir=True)

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


if __name__ == "__main__":
    from pathlib import Path
    import os
    import pandas as pd
    import numpy as np
    import seaborn as sns
    import plotly.express as px

    import cellpy
    from cellpy.utils import batch, helpers, plotutils

    project_dir = Path("../../../testdata/batch_project")
    print(f"{project_dir.resolve()=}")
    journal = project_dir / "test_project.json"
    journal = journal.resolve()
    print(f"{journal=}")
    assert project_dir.is_dir()
    assert journal.is_file()
    os.chdir(project_dir)

    print(f"cellpy version: {cellpy.__version__}")
    cellpy.log.setup_logging("INFO")

    b = batch.from_journal(journal)
    b.update()

    print("Ended OK")
