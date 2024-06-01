"""Routines for batch processing of cells (v2)."""

import logging
import os
import pathlib
import shutil
import sys
import warnings
from typing import List, Optional, Any

import pandas as pd
from pandas import Index
from tqdm.auto import tqdm

import cellpy.exceptions
from cellpy import log, prms
from cellpy.readers import filefinder
from cellpy.parameters.internal_settings import (
    headers_journal,
    headers_step_table,
    headers_summary,
)
from cellpy.internals.core import OtherPath
from cellpy.utils.batch_tools.batch_analyzers import (
    BaseSummaryAnalyzer,
    OCVRelaxationAnalyzer,
)
from cellpy.utils.batch_tools.batch_core import Data
from cellpy.utils.batch_tools.batch_experiments import CyclingExperiment
from cellpy.utils.batch_tools.batch_exporters import CSVExporter
from cellpy.utils.batch_tools.batch_journals import LabJournal
from cellpy.utils.batch_tools.batch_plotters import CyclingSummaryPlotter
from cellpy.utils.batch_tools.dumpers import ram_dumper

# logger = logging.getLogger(__name__)
logging.captureWarnings(True)

COLUMNS_SELECTED_FOR_VIEW = [
    headers_journal.mass,
    headers_journal.total_mass,
    headers_journal.loading,
    headers_journal.nom_cap,
]


class Batch:
    """A convenience class for running batch procedures.

    The Batch class contains (among other things):

    - iterator protocol
    - a journal with info about the different cells where the
      main information is accessible as a pandas.DataFrame through the ``.pages`` attribute
    - a data lookup accessor ``.data`` that behaves similarly as a dict.

    """

    def __init__(self, *args, **kwargs):
        """
        The initialization accepts arbitrary arguments and keyword arguments.
        It first looks for the ``file_name`` and ``db_reader`` keyword arguments.

        **Usage**::

            b = Batch((name, (project)), **kwargs)

        Examples:

            >>> b = Batch("experiment001", "main_project")
            >>> b = Batch("experiment001", "main_project", batch_col="b02")
            >>> b = Batch(name="experiment001", project="main_project", batch_col="b02")
            >>> b = Batch(file_name="cellpydata/batchfiles/cellpy_batch_experiment001.json")

        Args:
            name (str): (project (str))

        Keyword Args:
            file_name (str or pathlib.Path): journal file name to load.
            db_reader (str): data-base reader to use (defaults to "default" as given
              in the config-file or prm-class).
            frame (pandas.DataFrame): load from given dataframe.
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

        # TODO: add option for setting max cycle number
        #   use self.experiment.last_cycle = xxx
        default_log_level = kwargs.pop("default_log_level", None)
        custom_log_dir = kwargs.pop("custom_log_dir", None)
        if default_log_level is not None or custom_log_dir is not None:
            log.setup_logging(
                custom_log_dir=custom_log_dir,
                default_level=default_log_level,
                reset_big_log=True,
            )

        db_reader = kwargs.pop("db_reader", "default")

        file_name = kwargs.pop("file_name", None)
        frame = kwargs.pop("frame", None)

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
            if frame is not None:
                self.experiment.journal.from_frame(frame, **kwargs)
            else:
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
            self.experiment.journal.from_file(file_name=file_name, **kwargs)

        self.exporter = CSVExporter()
        self.exporter._assign_dumper(ram_dumper)
        self.exporter.assign(self.experiment)

        self.summary_collector = BaseSummaryAnalyzer()
        self.summary_collector.assign(self.experiment)

        self.plotter = CyclingSummaryPlotter()
        self.plotter.assign(self.experiment)
        self._journal_name = self.journal_name
        self.headers_step_table = headers_step_table

    def __str__(self):
        return str(self.experiment)

    def _repr_html_(self):
        txt = f"<h2>Batch-object</h2> id={hex(id(self))}"
        txt += f"<h3>batch.journal</h3>"
        txt += f"<blockquote>{self.journal._repr_html_()}</blockquote>"
        txt += f"<h3>batch.experiment</h3>"
        txt += f"<blockquote>{self.experiment._repr_html_()}</blockquote>"

        return txt

    def __len__(self):
        return len(self.experiment)

    def __iter__(self):
        return self.experiment.__iter__()

    def show_pages(self, number_of_rows=5):
        """Show the journal pages.

        Warnings:
            Will be deprecated soon - use pages.head() instead.

        """
        warnings.warn("Deprecated - use pages.head() instead", DeprecationWarning)
        return self.experiment.journal.pages.head(number_of_rows)

    @property
    def view(self):
        """Show the selected info about each cell.

        Warnings:
            Will be deprecated soon - use report() instead.

        """
        warnings.warn("Deprecated - use report instead", DeprecationWarning)
        pages = self.experiment.journal.pages
        pages = pages[COLUMNS_SELECTED_FOR_VIEW]
        return pages

    @property
    def name(self):
        return self.experiment.journal.name

    def _check_cell_data_points(self, cell_id):
        error_code = 0
        try:
            c = self.experiment.data[cell_id]
            if not c.has_no_partial_duplicates(subset="data_point"):
                error_code = 1
            return error_code
        except Exception as e:
            logging.debug(f"Exception ignored: {e}")
            return None

    def _check_cell_raw(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            return len(c.data.raw)
        except Exception as e:
            logging.debug(f"Exception ignored: {e}")
            return None

    def _check_cell_steps(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            return len(c.data.steps)
        except Exception as e:
            logging.debug(f"Exception ignored: {e}")
            return None

    def _check_cell_summary(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            return len(c.data.summary)
        except Exception as e:
            logging.debug(f"Exception ignored: {e}")
            return None

    def _check_cell_max_cap(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            s = c.data.summary
            return s[headers_summary["charge_capacity_gravimetric"]].max()

        except Exception as e:
            logging.debug(f"Exception ignored: {e}")
            return None

    def _check_cell_min_cap(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            s = c.data.summary
            return s[headers_summary["charge_capacity_gravimetric"]].min()

        except Exception as e:
            logging.debug(f"Exception ignored: {e}")
            return None

    def _check_cell_avg_cap(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            s = c.data.summary
            return s[headers_summary["charge_capacity_gravimetric"]].mean()

        except Exception as e:
            logging.debug(f"Exception ignored: {e}")
            return None

    def _check_cell_std_cap(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            s = c.data.summary
            return s[headers_summary["charge_capacity_gravimetric"]].std()

        except Exception as e:
            logging.debug(f"Exception ignored: {e}")
            return None

    def _check_cell_empty(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            return c.empty
        except Exception as e:
            logging.debug(f"Exception ignored: {e}")
            return None

    def _check_cell_cycles(self, cell_id):
        try:
            c = self.experiment.data[cell_id]
            return c.data.steps[self.headers_step_table.cycle].max()
        except Exception as e:
            logging.debug(f"Exception ignored: {e}")
            return None

    def drop(self, cell_label=None):
        """Drop cells from the journal.

        If ``cell_label`` is not given, ``cellpy`` will look into the journal for session
        info about bad cells, and if it finds it, it will remove those from the
        journal.

        Note:
            Remember to save your journal again after modifying it.

        Warning:
            This method has not been properly tested yet.

        Args:
            cell_label (str): the cell label of the cell you would like to remove.

        Returns:
            ``cellpy.utils.batch`` object (returns a copy if `keep_old` is ``True``).

        """
        if cell_label is None:
            try:
                cell_labels = self.journal.session["bad_cells"]
            except AttributeError:
                logging.critical(
                    "session info about bad cells is missing - cannot drop"
                )
                return
        else:
            cell_labels = [cell_label]

        for cell_label in cell_labels:
            if cell_label not in self.pages.index:
                logging.critical(f"could not find {cell_label}")
            else:
                self.pages = self.pages.drop(cell_label)

    def report(self, stylize=True, grouped=False, check=False):
        """Create a report on all the cells in the batch object.

        Important:
            To perform a reporting, cellpy needs to access all the data (and it might take some time).

        Args:
            stylize (bool): apply some styling to the report (default True).
            grouped (bool): add information based on the group cell belongs to (default False).
            check (bool): check if the data seems to be without errors (0 = no errors, 1 = partial duplicates)
                (default False).

        Returns:
            ``pandas.DataFrame``

        """
        pages = self.experiment.journal.pages
        r_pages = self.experiment.journal.pages[COLUMNS_SELECTED_FOR_VIEW].copy()
        r_pages["empty"] = pages.index.map(self._check_cell_empty)
        r_pages["raw_rows"] = pages.index.map(self._check_cell_raw)
        r_pages["steps_rows"] = pages.index.map(self._check_cell_steps)
        r_pages["summary_rows"] = pages.index.map(self._check_cell_summary)
        r_pages["last_cycle"] = pages.index.map(self._check_cell_cycles)
        r_pages["average_capacity"] = pages.index.map(self._check_cell_avg_cap)
        r_pages["max_capacity"] = pages.index.map(self._check_cell_max_cap)
        r_pages["min_capacity"] = pages.index.map(self._check_cell_min_cap)
        r_pages["std_capacity"] = pages.index.map(self._check_cell_std_cap)
        if check:
            r_pages["error_code"] = pages.index.map(self._check_cell_data_points)

        avg_last_cycle = r_pages.last_cycle.mean()
        avg_max_capacity = r_pages.max_capacity.mean()

        logging.info(f"average last cycle: {avg_last_cycle:.2f}")
        logging.info(f"average max capacity: {avg_max_capacity:.2f}")

        if grouped:
            # TODO: currently does not use cumulative values - consider implementing this
            r_pages["group"] = pages.group
            r_pages["group_avg_last_cycle"] = r_pages.group.map(
                r_pages.groupby("group").last_cycle.mean()
            )
            r_pages["group_avg_max_capacity"] = r_pages.group.map(
                r_pages.groupby("group").max_capacity.mean()
            )
            r_pages["group_avg_min_capacity"] = r_pages.group.map(
                r_pages.groupby("group").min_capacity.mean()
            )
            r_pages["group_avg_std_capacity"] = r_pages.group.map(
                r_pages.groupby("group").std_capacity.mean()
            )
            r_pages["group_avg_average_capacity"] = r_pages.group.map(
                r_pages.groupby("group").average_capacity.mean()
            )

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
                r_pages.style.apply(highlight_small, subset=["last_cycle"])
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
            r_pages = styled_pages

        return r_pages

    @property
    def info_file(self):
        """The name of the info file.

        Warnings:
            Will be deprecated soon - use ``journal_name`` instead.

        """

        # renamed to journal_name
        warnings.warn("Deprecated - use journal_name instead", DeprecationWarning)
        return self.experiment.journal.file_name

    @property
    def journal_name(self):
        return self.experiment.journal.file_name

    def _concat_memory_dumped(self, engine_name):
        keys = [df.name for df in self.experiment.memory_dumped[engine_name]]
        return pd.concat(self.experiment.memory_dumped[engine_name], keys=keys, axis=1)

    @property
    def summaries(self):
        """Concatenated summaries from all cells (multiindex dataframe)."""
        try:
            return self._concat_memory_dumped("summary_engine")
        except KeyError:
            logging.critical("no summaries exists (dumping to ram first)")
            self.summary_collector.do()
            return self._concat_memory_dumped("summary_engine")

    @property
    def summary_headers(self):
        """The column names of the concatenated summaries"""
        try:
            return self.summaries.columns.get_level_values(0)
        except AttributeError:
            logging.info("can't get any columns")

    @property
    def cell_names(self) -> list:
        return self.experiment.cell_names

    @property
    def labels(self):
        # Plan: allow cells to both have a label and a cell_name, where that latter should be a unique
        # identifier. Consider also to allow for a group-name.
        # The label and cell name can be the same. Consider allowing several cells to share the same label
        # thus returning several cellpy cell objects. Our use "group" for this purpose.
        print(
            "Label-based look-up is not supported yet. Performing cell-name based look-up instead."
        )
        return self.experiment.cell_names

    @property
    def cells(self) -> Data:
        """Access cells as a Data object (attribute lookup and automatic loading).

        Note:
            Write ``b.cells.x`` and press <TAB>. Then a pop-up might appear, and you can choose the
            cell you would like to retrieve.

        Warning:
            It seems that it is not always working as intended,
            at least not in my jupyter lab anymore. Instead, you can use ``b.experiment.data`` or
            write ``cells = b.cells`` and then use ``cells.x`` and press <TAB> to get the pop-up.

        """
        return self.experiment.data

    @property
    def cell_summary_headers(self) -> Index:
        return self.experiment.data[self.experiment.cell_names[0]].data.summary.columns

    @property
    def cell_raw_headers(self) -> Index:
        return self.experiment.data[self.experiment.cell_names[0]].data.raw.columns

    @property
    def cell_step_headers(self) -> Index:
        return self.experiment.data[self.experiment.cell_names[0]].data.steps.columns

    @property
    def pages(self) -> pd.DataFrame:
        return self.experiment.journal.pages

    @pages.setter
    def pages(self, df: pd.DataFrame):
        self.experiment.journal.pages = df
        all_cell_labels = set(self.experiment.cell_data_frames.keys())
        cell_labels_to_keep = set(self.journal.pages.index)
        cell_labels_to_remove = all_cell_labels - cell_labels_to_keep
        for cell_label in cell_labels_to_remove:
            del self.experiment.cell_data_frames[cell_label]

    def drop_cell(self, cell_label):
        """Drop a cell from the journal.

        Args:
            cell_label: the cell label of the cell you would like to remove.

        """

        if cell_label not in self.pages.index:
            logging.critical(f"could not find {cell_label}")
        else:
            self.pages = self.pages.drop(cell_label)

    def drop_cells(self, cell_labels):
        """Drop cells from the journal.

        Args:
            cell_labels: the cell labels of the cells you would like to remove.

        """

        for cell_label in cell_labels:
            self.drop_cell(cell_label)

    def drop_cells_marked_bad(self):
        """Drop cells that has been marked as bad from the journal (experimental feature)."""

        try:
            cell_labels = self.journal.session["bad_cells"]
        except AttributeError:
            logging.critical("session info about bad cells is missing - cannot drop")
            return
        if cell_labels is None:
            logging.debug("no bad cells to drop")
            return
        self.drop_cells(cell_labels)

    def mark_as_bad(self, cell_label):
        """Mark a cell as bad (experimental feature).

        Args:
            cell_label: the cell label of the cell you would like to mark as bad.

        """
        if cell_label not in self.pages.index:
            logging.critical(f"could not find {cell_label}")
            return

        try:
            cell_labels = self.journal.session["bad_cells"]
        except AttributeError:
            cell_labels = []
        if cell_labels is None:
            cell_labels = []

        if cell_label not in cell_labels:
            cell_labels.append(cell_label)
        self.journal.session["bad_cells"] = cell_labels

    def remove_mark_as_bad(self, cell_label):
        """Remove the bad cell mark from a cell (experimental feature).

        Args:
            cell_label: the cell label of the cell you would like to remove the bad mark from.

        """

        if cell_label not in self.pages.index:
            logging.critical(f"could not find {cell_label} in pages")
        try:
            cell_labels = self.journal.session["bad_cells"]
        except AttributeError:
            logging.critical(f"could not find 'bad_cells' session info")
            return

        if not cell_labels:
            logging.critical(f"nothing to remove - found nothing marked as 'bad_cells'")
            return

        if cell_label in cell_labels:
            cell_labels.remove(cell_label)
            logging.info(f"removed {cell_label} from bad_cells")
        self.journal.session["bad_cells"] = cell_labels

    @property
    def journal(self) -> LabJournal:
        return self.experiment.journal

    @journal.setter
    def journal(self, new):
        # self.experiment.journal = new
        raise NotImplementedError(
            "Setting a new journal object directly on a "
            "batch object is not allowed at the moment. Try modifying "
            "the journal.pages instead."
        )

    def _old_duplicate_journal(self, folder=None) -> None:
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

    def duplicate_journal(self, folder=None) -> None:
        """Copy the journal to folder.

        Args:
            folder (str or pathlib.Path): folder to copy to (defaults to the
            current folder).

        """
        self.experiment.journal.duplicate_journal(folder)

    def create_journal(
        self,
        description=None,
        from_db=True,
        auto_use_file_list=None,
        file_list_kwargs=None,
        **kwargs,
    ):
        """Create journal pages.

        This method is a wrapper for the different Journal methods for making
        journal pages (``Batch.experiment.journal.xxx``). It is under development. If you
        want to use 'advanced' options (i.e. not loading from a db), please consider
        using the methods available in Journal for now.

        Args:
            description: the information and meta-data needed to generate the journal pages:

                - empty: create an empty journal
                - ``dict``: create journal pages from a dictionary
                - ``pd.DataFrame``: create journal pages from a ``pandas.DataFrame``
                - 'filename.json': load cellpy batch file
                - 'filename.xlsx': create journal pages from an Excel file.

            from_db (bool): Deprecation Warning: this parameter will be removed as it is
                the default anyway. Generate the pages from a db (the default option).
                This will be over-ridden if description is given.
            auto_use_file_list (bool): Experimental feature. If True, a file list will be generated and used
                instead of searching for files in the folders.
            file_list_kwargs (dict): Experimental feature. Keyword arguments to be sent to the file list generator.

            **kwargs: sent to sub-function(s) (*e.g.* ``from_db`` -> ``simple_db_reader`` -> ``find_files`` ->
                ``filefinder.search_for_files``).

        The following keyword arguments are picked up by ``from_db``:

        Transferred Parameters:
            project: None
            name: None
            batch_col: None

        The following keyword arguments are picked up by ``simple_db_reader``:

        Transferred Parameters:
            reader: a reader object (defaults to dbreader.Reader)
            cell_ids: keys (cell IDs)
            file_list: file list to send to filefinder (instead of searching in folders for files).
            pre_path: prepended path to send to filefinder.
            include_key: include the key col in the pages (the cell IDs).
            include_individual_arguments: include the argument column in the pages.
            additional_column_names: list of additional column names to include in the pages.

        The following keyword arguments are picked up by ``filefinder.search_for_files``:

        Transferred Parameters:
            run_name(str): run-file identification.
            raw_extension(str): optional, extension of run-files (without the '.').
            cellpy_file_extension(str): optional, extension for cellpy files
                (without the '.').
            raw_file_dir(path): optional, directory where to look for run-files
                (default: read prm-file)
            project_dir(path): subdirectory in raw_file_dir to look for run-files
            cellpy_file_dir(path): optional, directory where to look for
                cellpy-files (default: read prm-file)
            prm_filename(path): optional parameter file can be given.
            file_name_format(str): format of raw-file names or a glob pattern
                (default: YYYYMMDD_[name]EEE_CC_TT_RR).
            reg_exp(str): use regular expression instead (defaults to None).
            sub_folders (bool): perform search also in sub-folders.
            file_list (list of str): perform the search within a given list
                of filenames instead of searching the folder(s). The list should
                not contain the full filepath (only the actual file names). If
                you want to provide the full path, you will have to modify the
                file_name_format or reg_exp accordingly.
            pre_path (path or str): path to prepend the list of files selected
                 from the file_list.

        The following keyword arguments are picked up by ``journal.to_file``:

        Transferred Parameters:
            duplicate_to_local_folder (bool): default True.

        Returns:
            None

        """

        # TODO (jepe): create option to update journal without looking for files

        logging.debug("Creating a journal")
        logging.debug(f"description: {description}")
        logging.debug(f"from_db: {from_db}")
        logging.info(f"name: {self.experiment.journal.name}")
        logging.info(f"project: {self.experiment.journal.project}")

        if auto_use_file_list is None:
            auto_use_file_list = prms.Batch.auto_use_file_list

        to_project_folder = kwargs.pop("to_project_folder", True)
        duplicate_to_local_folder = kwargs.pop("duplicate_to_local_folder", True)

        if description is not None:
            from_db = False
        else:
            if self.experiment.journal.pages is not None:
                warnings.warn(
                    "You created a journal - but you already have a "
                    "journal. Hope you know what you are doing!"
                )

        if from_db:
            if auto_use_file_list:
                warnings.warn(
                    "auto_use_file_list is True - this is an experimental feature"
                )
                if file_list_kwargs is None:
                    file_list_kwargs = {}
                try:
                    kwargs["file_list"] = filefinder.find_in_raw_file_directory(
                        **file_list_kwargs
                    )
                except Exception as e:
                    logging.critical(
                        "You have set auto_use_file_list to True, but I could not create any file list."
                    )
                    logging.critical(
                        "I recommend that you set auto_use_file_list to False and try again."
                    )
                    logging.critical(
                        "This can be done by setting the correct parameters in "
                        "the prms-file or by providing the correct kwargs "
                        "(e.g. b.create_journal(auto_use_file_list=False))."
                    )
                    raise e
            self.experiment.journal.from_db(**kwargs)
            self.experiment.journal.to_file(
                duplicate_to_local_folder=duplicate_to_local_folder
            )

            # TODO: remove these:
            if duplicate_to_local_folder:
                self.experiment.journal.duplicate_journal()
            if to_project_folder:
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
                if description.suffix in [".json", ".xlsx"]:
                    self.experiment.journal.from_file(description)
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
            self.experiment.journal.to_file(
                duplicate_to_local_folder=duplicate_to_local_folder
            )
            self.experiment.journal.generate_folder_names()
            self.experiment.journal.paginate()
            self.duplicate_journal(prms.Paths.batchfiledir)

    def _create_folder_structure(self) -> None:
        warnings.warn("Deprecated - use paginate instead.", DeprecationWarning)
        self.experiment.journal.paginate()
        logging.info("created folders")

    def paginate(self) -> None:
        """Create the folders where cellpy will put its output."""

        self.experiment.journal.paginate()
        logging.info("created folders")

    def save(self) -> None:
        """Save journal and cellpy files.

        The journal file will be saved in the project directory and in the
        batch-file-directory (``prms.Paths.batchfiledir``). The latter is useful
        for processing several batches using the ``iterate_batches`` functionality.

        The name and location of the cellpy files is determined by the journal pages.
        """

        self.save_journal()
        self.experiment.save_cells()

    def save_journal(self) -> None:
        """Save the journal (json-format).

        The journal file will be saved in the project directory and in the
        batch-file-directory (``prms.Paths.batchfiledir``). The latter is useful
        for processing several batches using the ``iterate_batches`` functionality.

        """

        # Remark! Got a recursive error when running on Mac.
        self.experiment.journal.to_file(to_project_folder=True, paginate=False)
        logging.info("saved journal pages to project folder")
        self.duplicate_journal(prms.Paths.batchfiledir)
        logging.info("duplicated journal pages to batch dir")
        self.duplicate_journal()
        logging.info("duplicated journal pages to current dir")

    def export_journal(self, filename=None) -> None:
        """Export the journal to xlsx.

        Args:
            filename (str or pathlib.Path): the name of the file to save the journal to.
                If not given, the journal will be saved to the default name.

        """
        if filename is None:
            filename = self.experiment.journal.file_name
        filename = pathlib.Path(filename).with_suffix(".xlsx")
        self.experiment.journal.to_file(
            file_name=filename, to_project_folder=False, paginate=False
        )

    def duplicate_cellpy_files(
        self, location: str = "standard", selector: dict = None, **kwargs
    ) -> None:
        """Copy the cellpy files and make a journal with the new names available in
        the current folder.

        Args:
            location: where to copy the files. Either choose among the following options:

                - 'standard': data/interim folder
                - 'here': current directory
                - 'cellpydatadir': the stated cellpy data dir in your settings (prms)

                or if the location is not one of the above, use the actual value of the location argument.

            selector (dict): if given, the cellpy files are reloaded after duplicating and
                modified based on the given selector(s).

            **kwargs: sent to ``Batch.experiment.update`` if selector is provided

        Returns:
            The updated journal pages.

        """

        pages = self.experiment.journal.pages
        cellpy_file_dir = OtherPath(prms.Paths.cellpydatadir)

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
            except FileNotFoundError:
                logging.info("File not found! Cannot copy it!")

        # save the journal pages
        pages["cellpy_file_name"] = pages["new_cellpy_file_name"]
        self.experiment.journal.pages = pages[columns]
        journal_file_name = pathlib.Path(self.experiment.journal.file_name).name
        self.experiment.journal.to_file(
            journal_file_name, paginate=False, to_project_folder=False
        )
        if selector is not None:
            logging.info("Modifying the cellpy-files.")
            logging.info(f"selector: {selector}")
            self.experiment.force_cellpy = True
            self.update(selector=selector, **kwargs)

    # TODO: list_journals?

    def link(
        self,
        max_cycle: Optional[int] = None,
        mark_bad=False,
        force_combine_summaries=False,
    ) -> None:
        """Link journal content to the cellpy-files and load the step information.

        Args:
            max_cycle (int): set maximum cycle number to link to.
            mark_bad (bool): mark cells as bad if they are not linked.
            force_combine_summaries (bool): automatically run combine_summaries (set this to True
                if you are re-linking without max_cycle for a batch that previously were linked
                with max_cycle)

        """

        self.experiment.link(max_cycle=max_cycle, mark_bad=mark_bad)
        if force_combine_summaries or max_cycle:
            self.summary_collector.do(reset=True)

    def load(self) -> None:
        """Load the selected datasets.

        Warnings:
            Will be deprecated soon - use ``update`` instead.
        """
        # does the same as update
        warnings.warn("Deprecated - use update instead.", DeprecationWarning)
        self.experiment.update()

    def update(self, pool=False, **kwargs) -> None:
        """Updates the selected datasets.

        Keyword Args:
            all_in_memory (bool): store the `cellpydata` in memory (default
                False)
            cell_specs (dict of dicts): individual arguments pr. cell. The ``cellspecs`` key-word argument
                dictionary will override the **kwargs and the parameters from the journal pages
                for the indicated cell.
            logging_mode (str): sets the logging mode for the loader(s).
            accept_errors (bool): if True, the loader will continue even if it encounters errors.

        Additional keyword arguments are sent to the loader(s)  if not
        picked up earlier. Remark that you can obtain the same pr. cell by
        providing a ``cellspecs`` dictionary. The kwargs have precedence over the
        parameters given in the journal pages, but will be overridden by parameters
        given by ``cellspecs``.

        Merging picks up the following keyword arguments:

        Transferred Parameters:
            recalc (Bool): set to False if you don't want automatic recalculation of
                cycle numbers etc. when merging several data-sets.


        Loading picks up the following keyword arguments:

        Transferred Parameters:
            selector (dict): selector-based parameters sent to the cellpy-file loader (hdf5) if
                loading from raw is not necessary (or turned off).

        """

        self.experiment.errors["update"] = []
        if pool:
            self.experiment.parallel_update(**kwargs)
        else:
            self.experiment.update(**kwargs)

    def export_cellpy_files(self, path=None, **kwargs) -> None:
        if path is None:
            path = pathlib.Path(".").resolve()
        self.experiment.errors["export_cellpy_files"] = []
        self.experiment.export_cellpy_files(path=path, **kwargs)

    def recalc(self, **kwargs) -> None:
        """Run ``make_step_table`` and ``make_summary`` on all cells.

        Keyword Args:
            save (bool): Save updated cellpy-files if True (defaults to True).
            step_opts (dict): parameters to inject to make_steps (defaults to None).
            summary_opts (dict): parameters to inject to make_summary (defaults to None).
            indexes (list): Only recalculate for given indexes (i.e. list of cell-names) (defaults to None).
            calc_steps (bool): Run make_steps before making the summary (defaults to True).
            testing (bool): Only for testing purposes (defaults to False).

        Returns:
            None
        """
        self.experiment.errors["recalc"] = []
        self.experiment.recalc(**kwargs)

    def make_summaries(self) -> None:
        """Combine selected columns from each of the cells into single frames and export.

        Warnings:
            This method will be deprecated in the future. Use ``combine_summaries`` instead.

        """
        warnings.warn("Deprecated - use combine_summaries instead.", DeprecationWarning)

        self.exporter.do()

    def combine_summaries(self, export_to_csv=True, **kwargs) -> None:
        """Combine selected columns from each of the cells into single frames.

        Keyword Args:
            export_to_csv (bool): export the combined summaries to csv (defaults to True).
            **kwargs: sent to the summary_collector.

        Returns:
            None

        """

        if export_to_csv:
            self.exporter.do()
        else:
            self.summary_collector.do(**kwargs)

    def plot(self, backend=None, reload_data=False, **kwargs):
        """Plot the summaries (e.g. capacity vs. cycle number).

        Args:
            backend (str): plotting backend (plotly, bokeh, matplotlib, seaborn)
            reload_data (bool): reload the data before plotting
            **kwargs: sent to the plotter

        Keyword Args:
            color_map (str, any): color map to use (defaults to ``px.colors.qualitative.Set1``
                for ``plotly`` and "Set1" for ``seaborn``)

            ce_range (list): optional range for the coulombic efficiency plot
            min_cycle (int): minimum cycle number to plot
            max_cycle (int): maximum cycle number to plot

            title (str): title of the figure (defaults to "Cycle Summary")
            x_label (str): title of the x-label (defaults to "Cycle Number")
            direction (str): plot charge or discharge (defaults to "charge")
            rate (bool): (defaults to False)
            ir (bool): (defaults to True)

            group_legends (bool): group the legends so that they can be turned visible/invisible
                as a group (defaults to True) (only for plotly)
            base_template (str): template to use for the plot (only for plotly)

            filter_by_group (int or list of ints): show only the selected group(s)
            filter_by_name (str): show only cells containing this string

        """

        if reload_data or ("summary_engine" not in self.experiment.memory_dumped):
            logging.debug("running summary_collector")
            self.summary_collector.do(reset=True)

        if backend is None:
            backend = prms.Batch.backend
            if backend in ["bokeh", "matplotlib"]:
                logging.debug(
                    f"over-riding default backend ('{backend}' will soon be deprecated)"
                )
                backend = "plotly"

        if backend in ["bokeh", "matplotlib", "plotly", "seaborn"]:
            prms.Batch.backend = backend

        if backend == "bokeh":
            print("...Using old plotter - this will change soon")
            self.plot_summaries(
                output_filename=None,
                backend="bokeh",
                reload_data=False,
                **kwargs,
            )

        elif backend == "matplotlib":
            print("...Using old plotter - this will change soon")
            self.plot_summaries(
                output_filename=None,
                backend="matplotlib",
                reload_data=False,
                **kwargs,
            )
            # 1: summary_plotting_engine
            # 2:   _preparing_data_and_plotting_legacy
            # 3:   _plotting_data_legacy
            # 4:   plot_cycle_life_summary_[backend]

        elif backend == "plotly":
            self.plotter.do(**kwargs)

        elif backend == "seaborn":
            self.plotter.do(**kwargs)
            # 1: summary_plotting_engine
            # 2:   generate_summary_plots
            # 3:   generate_summary_frame_for_plotting
            # 4:   plot_cycle_life_summary_[backend]

        else:
            print(f"backend {backend} not supported yet")

    def plot_summaries(
        self, output_filename=None, backend=None, reload_data=False, **kwargs
    ) -> None:
        """Plot the summaries.

        Warnings:
            This method will be deprecated in the future. Use ``plot`` instead.

        """

        warnings.warn("Deprecated - use plot instead.", DeprecationWarning)
        if reload_data or ("summary_engine" not in self.experiment.memory_dumped):
            logging.debug("running summary_collector")
            self.summary_collector.do(reset=True)

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

        self.plotter.do(**kwargs)


def load_journal(journal_file, **kwargs):
    """Load a journal file.

    Args:
        journal_file (str): path to journal file.
        **kwargs: sent to ``Journal.from_file``

    Returns:
        journal

    """
    journal = LabJournal(db_reader=None)
    journal.from_file(journal_file, **kwargs)
    return journal


def load(
    name,
    project,
    batch_col=None,
    allow_from_journal=True,
    drop_bad_cells=True,
    force_reload=False,
    **kwargs,
):
    """
    Load a batch from a journal file or create a new batch and load it if the journal file does not exist.

    Args:
        name (str): name of batch
        project (str): name of project
        batch_col (str): batch column identifier (only used for loading from db with simple_db_reader)
        allow_from_journal (bool): if True, the journal file will be loaded if it exists
        force_reload (bool): if True, the batch will be reloaded even if the journal file exists
        drop_bad_cells (bool): if True, bad cells will be dropped (only apply if journal file is loaded)
        auto_use_file_list (bool): Experimental feature. If True, a file list will be generated and used
            instead of searching for files in the folders.
        **kwargs: sent to Batch during initialization

    Keyword Args:
        db_reader (str): data-base reader to use (defaults to "default" as given
          in the config-file or prm-class).
        frame (pandas.DataFrame): load from given dataframe.
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
        max_cycle (int or None): maximum number of cycles to link up to (defaults to None).
        force_combine_summaries (bool): automatically run combine_summaries when linking.


    Returns:
        populated Batch object (``cellpy.utils.batch.Batch``)

    """

    if allow_from_journal:
        b = Batch(name=name, project=project, batch_col=batch_col, db_reader=None)
        try:
            print("checking if it is possible to load from journal file")
            b.experiment.journal.generate_file_name()
            journal_file = b.experiment.journal.file_name
            print(f" - journal file name: {journal_file}")
        except Exception as e:
            print(f"could not generate journal file name: {e}")
        else:
            if pathlib.Path(journal_file).is_file():
                print(f" - loading journal file {journal_file}")
                b.experiment.journal.from_file(journal_file)
                if force_reload:
                    print(f" - reloading")
                    b.update()
                else:
                    print(f" - linking")
                    b.link(
                        max_cycle=kwargs.pop("max_cycle", None),
                        mark_bad=True,
                        force_combine_summaries=kwargs.pop(
                            "force_combine_summaries", False
                        ),
                    )

                if drop_bad_cells:
                    print(f" - dropping cells marked as bad")
                    b.drop_cells_marked_bad()
                print("OK!")
                return b

            else:
                print(f" - journal file not found")

    auto_use_file_list = kwargs.pop("auto_use_file_list", None)
    try:
        print("loading information from db")
        if batch_col is None:
            batch_col = "b01"  # this is needed due to a bug in cellpy (will be fixed when new db reader is ready)
        print("initializing batch object")
        b = init(name=name, project=project, batch_col=batch_col, **kwargs)
    except Exception as e:
        print(f"could not initialize batch: {e}")
        return None
    print("processing batch")
    try:
        print("creating journal")
        b.create_journal(auto_use_file_list=auto_use_file_list)
        print(" - created journal")
    except Exception as e:
        print(f"could not create journal: {e}")
        print("you might have duplicates in your database index or cell names")
        return None
    try:
        b.duplicate_journal()
        print(" - duplicated journal")
        b.paginate()
        print(" - paginated")
        print(" - updating...")
        b.update()
        print(" - updated")
        print("collecting and combining summaries")
        b.combine_summaries()
        print(" - collected and combined summaries")
        print("OK!")
    except Exception as e:
        print("something went wrong")
        print(e)
        print("returning possibly incomplete batch")

    return b


def init(*args, empty=False, **kwargs) -> Batch:
    """Returns an initialized instance of the Batch class.

    Args:
        empty (bool): if True, the batch will not be linked to any database and
            an empty batch is returned
        *args: passed directly to Batch()

            - **name**: name of batch.
            - **project**: name of project.
            - **batch_col**: batch column identifier.

    Keyword Args:
        file_name: json file if loading from pages (journal).
        default_log_level: "INFO" or "DEBUG". Defaults to "CRITICAL".

    Other keyword arguments are sent to the Batch object.

    Examples:
        >>> empty_batch = Batch.init(db_reader=None)
        >>> batch_from_file = Batch.init(file_name="cellpy_batch_my_experiment.json")
        >>> normal_init_of_batch = Batch.init()

    """
    # TODO: add option for setting max cycle number (experiment.last_cycle)
    # TODO: promote most used kwargs to named arguments
    # set up cellpy logger
    default_log_level = kwargs.pop("default_log_level", None)
    testing = kwargs.pop("testing", False)

    log.setup_logging(
        default_level=default_log_level, testing=testing, reset_big_log=True
    )
    if empty:
        logging.debug("returning naked Batch")
        return naked(*args, **kwargs)

    file_name = kwargs.pop("file_name", None)
    frame = kwargs.pop("frame", None)

    logging.debug(f"returning Batch(kwargs: {kwargs})")
    if file_name is not None:
        kwargs.pop("db_reader", None)
        return Batch(*args, file_name=file_name, db_reader=None, **kwargs)
    if frame is not None:
        kwargs.pop("db_reader", None)
        return Batch(*args, file_name=None, db_reader=None, frame=frame, **kwargs)

    return Batch(*args, **kwargs)


def naked(name=None, project=None) -> Batch:
    """Returns an empty instance of the Batch class.

    Examples:
        >>> empty_batch = naked()

    """
    b = Batch(db_reader=None)
    b.pages = b.experiment.journal.create_empty_pages()
    if name is not None:
        b.experiment.journal.name = name
    if project is not None:
        b.experiment.journal.project = project

    return b


def from_journal(journal_file, autolink=True, testing=False) -> Batch:
    """Create a Batch from a journal file"""
    # TODO: add option for setting max cycle number (experiment.last_cycle)
    b = init(db_reader=None, file_name=journal_file, testing=testing)
    if autolink:
        b.link()
    return b


def load_pages(file_name) -> pd.DataFrame:
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
    try:
        pages, *_ = LabJournal.read_journal_jason_file(file_name)
        return pages
    except cellpy.exceptions.UnderDefined:
        logging.critical("could not find any pages.")


def process_batch(*args, **kwargs) -> Batch:
    """Execute a batch run, either from a given file_name or by giving the name and project as input.

    Warnings:
        This function is from ancient times and needs to be updated. It might have grown old and grumpy.
        Expect it to change in the near future.

    Examples:
        >>> process_batch(file_name | (name, project), **kwargs)

    Args:
        *args: file_name or name and project (both string)

    Keyword Args:
        backend (str): what backend to use when plotting ('bokeh' or 'matplotlib').
            Defaults to 'matplotlib'.
        dpi (int): resolution used when saving matplotlib plot(s). Defaults to 300 dpi.
        default_log_level (str): What log-level to use for console output. Chose between
            'CRITICAL', 'DEBUG', or 'INFO'. The default is 'CRITICAL' (i.e. usually no log output to console).

    Returns:
        ``cellpy.batch.Batch`` object
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
    testing = kwargs.pop("testing", False)
    log.setup_logging(
        default_level=default_log_level, reset_big_log=True, testing=testing
    )
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
        "plot": (b.plot,),
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

    Warnings:
        This function is from ancient times and needs to be updated. It might have grown old and grumpy.
        Expect it to change in the near future.

    Args:
        folder (str or pathlib.Path): folder containing the journal files.
        extension (str): extension for the journal files (used when creating a default glob-pattern).
        glob_pattern (str): optional glob pattern.
        **kwargs: keyword arguments passed to ``batch.process_batch``.

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


def _check_standard():
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
    prms.Paths.db_filename = "cellpy_db.xlsx"
    prms.Paths.cellpydatadir = test_data_path / "hdf5"
    prms.Paths.outdatadir = out_data_path
    prms.Paths.rawdatadir = test_data_path / "data"
    prms.Paths.db_path = test_data_path / "db"
    prms.Paths.filelogdir = test_data_path / "log"

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


def _check_new():
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


def _check_iterate():
    folder_name = r"C:\Scripting\Processing\Celldata\live"
    iterate_batches(folder_name, export_cycles=False, export_raw=False)


if __name__ == "__main__":
    print("---IN BATCH 2 MAIN---")
    _check_new()
