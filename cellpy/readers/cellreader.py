# -*- coding: utf-8 -*-
"""Datareader for cell testers and potentiostats.

This module is used for loading data and databases created by different cell
testers. Currently it only accepts arbin-type res-files (access) data as
raw data files, but we intend to implement more types soon. It also creates
processed files in the hdf5-format.

Example:
    >>> d = CellpyData()
    >>> d.loadcell(names = [file1.res, file2.res]) # loads and merges the runs
    >>> voltage_curves = d.get_cap()
    >>> d.save("mytest.hdf")

"""

import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import logging
import sys
import collections
import warnings
import csv
import itertools
import time
import copy

import numpy as np
import pandas as pd
from pandas.errors import PerformanceWarning
from scipy import interpolate

from cellpy.parameters import prms
from cellpy.parameters.legacy import internal_settings as old_settings
from cellpy.exceptions import WrongFileVersion, DeprecatedFeature, NullData
from cellpy.parameters.internal_settings import (
    get_headers_summary,
    get_cellpy_units,
    get_headers_normal,
    get_headers_step_table,
    ATTRS_CELLPYFILE,
    ATTRS_DATASET,
    ATTRS_DATASET_DEEP,
    ATTRS_CELLPYDATA,
)
from cellpy.readers.core import (
    FileID,
    Cell,
    CELLPY_FILE_VERSION,
    MINIMUM_CELLPY_FILE_VERSION,
    xldate_as_datetime,
    interpolate_y_on_x,
    identify_last_data_point,
    pickle_protocol,
    PICKLE_PROTOCOL,
)

HEADERS_NORMAL = get_headers_normal()
HEADERS_SUMMARY = get_headers_summary()
HEADERS_STEP_TABLE = get_headers_step_table()

# TODO: @jepe - new feature - method for assigning new cycle numbers and step numbers
#   - Sometimes the user forgets to increment the cycle number and it would be good
#   to have a method so that its possible to set new cycle numbers manually
#   - Some testers merges different steps into one (e.g CC-CV), it would be nice to have
#   a method for "splitting that up"

# TODO: @jepe - performance warnings - mixed types within cols (pytables)
performance_warning_level = "ignore"  # "ignore", "error"
warnings.filterwarnings(
    performance_warning_level, category=pd.io.pytables.PerformanceWarning
)
pd.set_option("mode.chained_assignment", None)  # "raise", "warn", None

module_logger = logging.getLogger(__name__)


class CellpyData(object):
    """Main class for working and storing data.

    This class is the main work-horse for cellpy where all the functions for
    reading, selecting, and tweaking your data is located. It also contains the
    header definitions, both for the cellpy hdf5 format, and for the various
    cell-tester file-formats that can be read. The class can contain
    several cell-tests and each test is stored in a list. If you see what I mean...

    Attributes:
        cells (list): list of DataSet objects.
    """

    def __repr__(self):
        txt = f"CellpyData-object (id={hex(id(self))})"
        if self.name:
            txt += f"\nname: {self.name}"
        if self.table_names:
            txt += f"\ntable_names: {self.table_names}"
        if self.tester:
            txt += f"\ntester: {self.tester}"

        number_of_cells = len(self.cells)
        txt += f"\ncells: {number_of_cells}"
        return txt

    def _repr_html_(self):
        header = f"""
         <p>
            <h3>CellpyData-object</h3>
            <b>id</b>: {hex(id(self))} <br>
            <b>name</b>: {self.name} <br>
            <b>table names</b>: {self.table_names} <br>
            <b>tester</b>: {self.tester} <br>
            <b>cells</b>: {len(self.cells)} <br>
            <b>cycle_mode</b>: {self.cycle_mode} <br>
            <b>sep</b>: {self.sep} <br>
            <b>daniel_number</b>: {self.daniel_number} <br>
            <b>cellpy_datadir</b>: {self.cellpy_datadir} <br>
            <b>raw_datadir</b>: {self.raw_datadir} <br>
         </p>
        """
        all_vars = "<p>"
        all_vars += f"""
            <b>capacity_modifiers</b>: {self.capacity_modifiers} <br>
            <b>empty</b>: {self.empty} <br>
            <b>ensure_step_table</b>: {self.ensure_step_table} <br>
            <b>filestatuschecker</b>: {self.filestatuschecker} <br>
            <b>force_step_table_creation</b>: {self.force_step_table_creation} <br>
            <b>forced_errors</b>: {self.forced_errors} <br>
            <b>limit_loaded_cycles</b>: {self.limit_loaded_cycles} <br>
            <b>load_only_summary</b>: {self.load_only_summary} <br>
            <b>profile</b>: {self.profile} <br>
            <b>raw_limits</b>: {self.raw_limits} <br>
            <b>raw_units</b>: {self.raw_units} <br>
            <b>select_minimal</b>: {self.select_minimal} <br>
            <b>selected_cell_number</b>: {self.selected_cell_number} <br>
            <b>selected_scans</b>: {self.selected_scans} <br>
            <b>status_datasets</b>: {self.status_datasets} <br>
            <b>summary_exists (deprecated)</b>: {self.summary_exists} <br>


        """
        all_vars += "</p>"

        cell_txt = ""
        for i, cell in enumerate(self.cells):
            cell_txt += f"<h4>cell {i + 1} of {len(self.cells)}</h4>"
            cell_txt += cell._repr_html_()

        return header + all_vars + cell_txt

    def __str__(self):
        txt = "<CellpyData>\n"
        if self.name:
            txt += f"name: {self.name}\n"
        if self.table_names:
            txt += f"table_names: {self.table_names}\n"
        if self.tester:
            txt += f"tester: {self.tester}\n"
        if self.cells:
            txt += "datasets: [ ->\n"
            for i, d in enumerate(self.cells):
                txt += f"   ({i})\n"
                for t in str(d).split("\n"):
                    txt += "     "
                    txt += t
                    txt += "\n"
                txt += "\n"
            txt += "]"
        else:
            txt += "datasets: []"
        txt += "\n"
        return txt

    def __bool__(self):
        if self.cells:
            return True
        else:
            return False

    def __init__(
        self,
        filenames=None,
        selected_scans=None,
        profile=False,
        filestatuschecker=None,  # "modified"
        fetch_one_liners=False,
        tester=None,
        initialize=False,
    ):
        """CellpyData object

        Args:
            filenames: list of files to load.
            selected_scans:
            profile: experimental feature.
            filestatuschecker: property to compare cellpy and raw-files;
               default read from prms-file.
            fetch_one_liners: experimental feature.
            tester: instrument used (e.g. "arbin") (checks prms-file as
               default).
            initialize: create a dummy (empty) dataset; defaults to False.
        """

        if tester is None:
            self.tester = prms.Instruments.tester
        else:
            self.tester = tester
        self.loader = None  # this will be set in the function set_instrument
        self.logger = logging.getLogger(__name__)
        logging.debug("created CellpyData instance")
        self.name = None
        self.profile = profile
        self.minimum_selection = {}
        if filestatuschecker is None:
            self.filestatuschecker = prms.Reader.filestatuschecker
        else:
            self.filestatuschecker = filestatuschecker
        self.forced_errors = 0
        self.summary_exists = False

        if not filenames:
            self.file_names = []
        else:
            self.file_names = filenames
            if not self._is_listtype(self.file_names):
                self.file_names = [self.file_names]
        if not selected_scans:
            self.selected_scans = []
        else:
            self.selected_scans = selected_scans
            if not self._is_listtype(self.selected_scans):
                self.selected_scans = [self.selected_scans]

        self.cells = []
        self.status_datasets = []
        self.selected_cell_number = 0
        self.number_of_datasets = 0

        self.capacity_modifiers = ["reset"]

        self.list_of_step_types = [
            "charge",
            "discharge",
            "cv_charge",
            "cv_discharge",
            "taper_charge",
            "taper_discharge",
            "charge_cv",
            "discharge_cv",
            "ocvrlx_up",
            "ocvrlx_down",
            "ir",
            "rest",
            "not_known",
        ]
        # - options
        self.force_step_table_creation = prms.Reader.force_step_table_creation
        self.force_all = prms.Reader.force_all
        self.sep = prms.Reader.sep
        self._cycle_mode = None
        # self.max_res_filesize = prms.Reader.max_res_filesize
        self.load_only_summary = prms.Reader.load_only_summary
        self.select_minimal = prms.Reader.select_minimal
        # self.chunk_size = prms.Reader.chunk_size  # 100000
        # self.max_chunks = prms.Reader.max_chunks
        # self.last_chunk = prms.Reader.last_chunk
        self.limit_loaded_cycles = prms.Reader.limit_loaded_cycles
        self.limit_data_points = None
        # self.load_until_error = prms.Reader.load_until_error
        self.ensure_step_table = prms.Reader.ensure_step_table
        self.daniel_number = prms.Reader.daniel_number
        # self.raw_datadir = prms.Reader.raw_datadir
        self.raw_datadir = prms.Paths.rawdatadir
        # self.cellpy_datadir = prms.Reader.cellpy_datadir
        self.cellpy_datadir = prms.Paths.cellpydatadir
        # search in prm-file for res and hdf5 dirs in loadcell:
        self.auto_dirs = prms.Reader.auto_dirs

        # - headers and instruments
        self.headers_normal = get_headers_normal()
        self.headers_summary = get_headers_summary()
        self.headers_step_table = get_headers_step_table()

        self.table_names = None  # dictionary defined in set_instruments
        self.set_instrument()

        # - units used by cellpy
        self.cellpy_units = get_cellpy_units()

        if initialize:
            self.initialize()

    def initialize(self):
        logging.debug("Initializing...")
        self.cells.append(Cell())

    @property
    def cell(self):
        """returns the DataSet instance"""
        # could insert a try-except thingy here...
        cell = self.cells[self.selected_cell_number]
        return cell

    @cell.setter
    def cell(self, new_cell):
        self.cells[self.selected_cell_number] = new_cell

    @property
    def dataset(self):
        """returns the DataSet instance"""
        # could insert a try-except thingy here...
        warnings.warn(
            "The .dataset property is deprecated, please use .cell instead.",
            DeprecationWarning,
        )
        cell = self.cells[self.selected_cell_number]
        return cell

    @property
    def empty(self):
        """gives False if the CellpyData object is empty (or un-functional)"""
        return not self.check()

    @classmethod
    def vacant(cls, cell=None):
        """Create a CellpyData instance.
        Args:
            cell (CellpyData instance): the attributes from the cell will be copied
                to the new Cellpydata instance.

         Returns:
            CellpyData instance.
        """

        new_cell = cls(initialize=True)
        if cell is not None:
            for attr in ATTRS_DATASET:
                value = getattr(cell.cell, attr)
                setattr(new_cell.cell, attr, value)

            for attr in ATTRS_DATASET_DEEP:
                value = getattr(cell.cell, attr)
                setattr(new_cell.cell, attr, copy.deepcopy(value))

            for attr in ATTRS_CELLPYDATA:
                value = getattr(cell, attr)
                setattr(new_cell, attr, value)

        return new_cell

    def split(self, cycle=None):
        """Split experiment (CellpyData object) into two sub-experiments. if cycle
        is not give, it will split on the median cycle number"""

        if isinstance(cycle, int) or cycle is None:
            return self.split_many(base_cycles=cycle)

    def drop_from(self, cycle=None):
        """Select first part of experiment (CellpyData object) up to cycle number
         'cycle'"""
        if isinstance(cycle, int):
            c1, c2 = self.split_many(base_cycles=cycle)
            return c1

    def drop_to(self, cycle=None):
        """Select last part of experiment (CellpyData object) from cycle number
        'cycle'"""
        if isinstance(cycle, int):
            c1, c2 = self.split_many(base_cycles=cycle)
            return c2

    def drop_edges(self, start, end):
        """Select middle part of experiment (CellpyData object) from cycle
        number 'start' to 'end"""

        if end < start:
            raise ValueError("end cannot be larger than start")
        if end == start:
            raise ValueError("end cannot be the same as start")
        return self.split_many([start, end])[1]

    def split_many(self, base_cycles=None):
        """Split experiment (CellpyData object) into several sub-experiments.

        Args:
            base_cycles (int or list of ints): cycle(s) to do the split on.

        Returns:
            List of CellpyData objects
        """
        h_summary_index = HEADERS_SUMMARY.cycle_index
        h_raw_index = HEADERS_NORMAL.cycle_index_txt
        h_step_cycle = HEADERS_STEP_TABLE.cycle

        if base_cycles is None:
            all_cycles = self.get_cycle_numbers()
            base_cycles = int(np.median(all_cycles))

        cells = list()
        if not isinstance(base_cycles, (list, tuple)):
            base_cycles = [base_cycles]

        dataset = self.cell
        steptable = dataset.steps
        data = dataset.raw
        summary = dataset.summary

        # In case Cycle_Index has been promoted to index [#index]
        if h_summary_index not in summary.columns:
            summary = summary.reset_index(drop=False)

        for b_cycle in base_cycles:
            steptable0, steptable = [
                steptable[steptable[h_step_cycle] < b_cycle],
                steptable[steptable[h_step_cycle] >= b_cycle],
            ]
            data0, data = [
                data[data[h_raw_index] < b_cycle],
                data[data[h_raw_index] >= b_cycle],
            ]
            summary0, summary = [
                summary[summary[h_summary_index] < b_cycle],
                summary[summary[h_summary_index] >= b_cycle],
            ]

            new_cell = CellpyData.vacant(cell=self)
            old_cell = CellpyData.vacant(cell=self)

            new_cell.cell.steps = steptable0
            new_cell.cell.raw = data0
            new_cell.cell.summary = summary0
            new_cell.cell = identify_last_data_point(new_cell.cell)

            old_cell.cell.steps = steptable
            old_cell.cell.raw = data
            old_cell.cell.summary = summary
            old_cell.cell = identify_last_data_point(old_cell.cell)

            cells.append(new_cell)

        cells.append(old_cell)
        return cells

    # TODO: @jepe - merge the _set_xxinstrument methods into one method
    def set_instrument(self, instrument=None, **kwargs):
        """Set the instrument (i.e. tell cellpy the file-type you use).

        Args:
            instrument: (str) in ["arbin", "bio-logic-csv", "bio-logic-bin",...]
            kwargs (dict): key-word arguments sent to the initializer of the
                loader class

        Sets the instrument used for obtaining the data (i.e. sets file-format)

        """

        custom_instrument_splitter = "::"

        if instrument is None:
            instrument = self.tester

        logging.debug(f"Setting instrument: {instrument}")

        if instrument in ["arbin", "arbin_res"]:
            from cellpy.readers.instruments.arbin_res import ArbinLoader as RawLoader

            self._set_instrument(RawLoader)
            self.tester = "arbin"

        elif instrument == "arbin_sql":
            from cellpy.readers.instruments.arbin_sql import ArbinSQLLoader as RawLoader

            logging.warning(f"{instrument} is experimental! Not ready for production!")
            self._set_instrument(RawLoader)
            self.tester = "arbin_sql"

        elif instrument == "arbin_sql_csv":
            from cellpy.readers.instruments.arbin_sql_csv import (
                ArbinCsvLoader as RawLoader,
            )

            logging.warning(f"{instrument} is experimental! Not ready for production!")
            self._set_instrument(RawLoader, **kwargs)
            self.tester = "arbin_sql_csv"

        elif instrument in ["pec", "pec_csv"]:
            logging.warning("Experimental! Not ready for production!")
            from cellpy.readers.instruments.pec import PECLoader as RawLoader

            self._set_instrument(RawLoader)
            self.tester = "pec"

        elif instrument in ["biologics", "biologics_mpr"]:
            from cellpy.readers.instruments.biologics_mpr import MprLoader as RawLoader

            logging.warning("Experimental! Not ready for production!")
            self._set_instrument(RawLoader)
            self.tester = "biologic"

        elif instrument in ["maccor", "maccor_txt"]:
            from cellpy.readers.instruments.maccor_txt import MaccorTxtLoader as RawLoader
            logging.warning("Experimental! Not ready for production!")
            self._set_instrument(RawLoader, **kwargs)
            self.tester = "maccor"

        elif instrument.startswith("custom"):
            logging.debug(f"using custom instrument: {instrument}")
            _instrument = instrument.split(custom_instrument_splitter)
            try:
                custom_instrument_definition_file = _instrument[1]
                prms.Instruments.custom_instrument_definitions_file = (
                    custom_instrument_definition_file
                )
            except IndexError:
                logging.debug("no definition file provided")

            from cellpy.readers.instruments.custom import CustomLoader as RawLoader

            self._set_instrument(RawLoader)
            self.tester = "custom"

        else:
            raise Exception(f"option does not exist: '{instrument}'")

    def _set_instrument(self, loader_class, **kwargs):
        self.loader_class = loader_class(**kwargs)
        # ----- get information --------------------------
        self.raw_units = self.loader_class.get_raw_units()
        self.raw_limits = self.loader_class.get_raw_limits()
        # ----- create the loader ------------------------
        self.loader = self.loader_class.loader

    def _create_logger(self):
        from cellpy import log

        self.logger = logging.getLogger(__name__)
        log.setup_logging(default_level="DEBUG")

    @property
    def cycle_mode(self):
        try:
            cell = self.cell
            return cell.cycle_mode
        except IndexError:
            return self._cycle_mode

    @cycle_mode.setter
    def cycle_mode(self, cycle_mode):
        logging.debug(f"-> cycle_mode: {cycle_mode}")
        try:
            cell = self.cell
            cell.cycle_mode = cycle_mode
            self._cycle_mode = cycle_mode
        except IndexError:
            self._cycle_mode = cycle_mode

    def set_raw_datadir(self, directory=None):
        """Set the directory containing .res-files.

        Used for setting directory for looking for res-files.@
        A valid directory name is required.

        Args:
            directory (str): path to res-directory

        Example:
            >>> d = CellpyData()
            >>> directory = "MyData/Arbindata"
            >>> d.set_raw_datadir(directory)

        """

        if directory is None:
            logging.info("No directory name given")
            return
        if not os.path.isdir(directory):
            logging.info(directory)
            logging.info("Directory does not exist")
            return
        self.raw_datadir = directory

    def set_cellpy_datadir(self, directory=None):
        """Set the directory containing .hdf5-files.

        Used for setting directory for looking for hdf5-files.
        A valid directory name is required.

        Args:
            directory (str): path to hdf5-directory

        Example:
            >>> d = CellpyData()
            >>> directory = "MyData/HDF5"
            >>> d.set_raw_datadir(directory)

        """

        if directory is None:
            logging.info("No directory name given")
            return
        if not os.path.isdir(directory):
            logging.info("Directory does not exist")
            return
        self.cellpy_datadir = directory

    def check_file_ids(self, rawfiles, cellpyfile, detailed=False):
        """Check the stats for the files (raw-data and cellpy hdf5).

        This function checks if the hdf5 file and the res-files have the same
        timestamps etc to find out if we need to bother to load .res -files.

        Args:
            cellpyfile (str): filename of the cellpy hdf5-file.
            rawfiles (list of str): name(s) of raw-data file(s).
            detailed (bool): return a dict containing True or False for each
                individual raw-file

        Returns:
            If detailed is False:
                False if the raw files are newer than the cellpy hdf5-file
                    (update needed).
                True if update is not needed.
             If detailed is True it returns a dict containing True or False for each
                individual raw-file.
            """

        txt = f"Checking file ids - using '{self.filestatuschecker}'"
        logging.info(txt)

        ids_cellpy_file = self._check_cellpy_file(cellpyfile)

        logging.debug(f"cellpyfile ids: {ids_cellpy_file}")

        if not ids_cellpy_file:
            # logging.debug("hdf5 file does not exist - needs updating")
            return False

        ids_raw = self._check_raw(rawfiles)

        if detailed:
            similar = self._parse_ids(ids_raw, ids_cellpy_file)
            return similar

        else:
            similar = self._compare_ids(ids_raw, ids_cellpy_file)
            if not similar:
                # logging.debug("hdf5 file needs updating")
                return False
            else:
                # logging.debug("hdf5 file is updated")
                return True

    def _check_raw(self, file_names, abort_on_missing=False):
        """Get the file-ids for the res_files."""

        strip_file_names = True
        check_on = self.filestatuschecker
        if not self._is_listtype(file_names):
            file_names = [file_names]

        ids = dict()
        for f in file_names:
            logging.debug(f"checking raw file {f}")
            fid = FileID(f)
            # logging.debug(fid)
            if fid.name is None:
                warnings.warn(f"file does not exist: {f}")
                if abort_on_missing:
                    sys.exit(-1)
            else:
                if strip_file_names:
                    name = os.path.basename(f)
                else:
                    name = f
                if check_on == "size":
                    ids[name] = int(fid.size)
                elif check_on == "modified":
                    ids[name] = int(fid.last_modified)
                else:
                    ids[name] = int(fid.last_accessed)
        return ids

    def _check_cellpy_file(self, filename):
        """Get the file-ids for the cellpy_file."""

        use_full_filename_path = False
        parent_level = prms._cellpyfile_root
        fid_dir = prms._cellpyfile_fid
        check_on = self.filestatuschecker
        logging.debug("checking cellpy-file")
        logging.debug(filename)
        if not os.path.isfile(filename):
            logging.debug("cellpy-file does not exist")
            return None
        try:
            store = pd.HDFStore(filename)
        except Exception as e:
            logging.debug(f"could not open cellpy-file ({e})")
            return None
        fidtable = None
        try:
            fidtable = store.select(parent_level + fid_dir)
        except KeyError:
            logging.warning("no fidtable - you should update your hdf5-file")
        except NotImplementedError:
            logging.warning(
                "your system cannot read the fid-table (posix-windows confusion) "
                "hopefully this will be solved in a newer version of pytables."
            )
        finally:
            store.close()
        if fidtable is not None:
            raw_data_files, raw_data_files_length = self._convert2fid_list(fidtable)
            txt = "contains %i res-files" % (len(raw_data_files))
            logging.debug(txt)
            ids = dict()
            for fid in raw_data_files:
                full_name = fid.full_name
                name = fid.name
                size = fid.size
                mod = fid.last_modified
                logging.debug(f"fileID information for: {full_name}")
                logging.debug(f"   modified: {mod}")
                logging.debug(f"   size: {size}")

                if use_full_filename_path:
                    name = full_name

                if check_on == "size":
                    ids[name] = int(fid.size)
                elif check_on == "modified":
                    ids[name] = int(fid.last_modified)
                else:
                    ids[name] = int(fid.last_accessed)
            return ids
        else:
            return None

    @staticmethod
    def _compare_ids(ids_raw, ids_cellpy_file):
        similar = True
        l_res = len(ids_raw)
        l_cellpy = len(ids_cellpy_file)
        if l_res == l_cellpy and l_cellpy > 0:
            for name, value in list(ids_raw.items()):
                try:
                    c_value = ids_cellpy_file[name]
                except KeyError:
                    logging.debug("KeyError when comparing raw and cellpy file.")
                    logging.debug(
                        "Could be due to upper case vs. lower case confusion."
                    )
                    similar = False
                else:
                    if c_value != value:
                        similar = False
        else:
            similar = False

        return similar

    @staticmethod
    def _parse_ids(ids_raw, ids_cellpy_file):
        similar = dict()
        for name in ids_raw:
            v_cellpy = ids_cellpy_file.get(name, None)
            v_raw = ids_raw[name]
            similar[name] = False
            if v_raw is not None:
                if v_raw == v_cellpy:
                    similar[name] = True
        return similar

    def loadcell(
        self,
        raw_files,
        cellpy_file=None,
        mass=None,
        summary_on_raw=False,
        summary_ir=True,
        summary_ocv=False,
        summary_end_v=True,
        only_summary=False,
        force_raw=False,
        use_cellpy_stat_file=None,
        cell_type=None,
        selector=None,
        **kwargs,
    ):

        """Loads data for given cells.

        Args:
            raw_files (list): name of res-files
            cellpy_file (path): name of cellpy-file
            mass (float): mass of electrode or active material
            summary_on_raw (bool): use raw-file for summary
            summary_ir (bool): summarize ir
            summary_ocv (bool): summarize ocv steps
            summary_end_v (bool): summarize end voltage
            only_summary (bool): get only the summary of the runs
            force_raw (bool): only use raw-files
            use_cellpy_stat_file (bool): use stat file if creating summary
                from raw
            cell_type (str): set the cell type (e.g. "anode"). If not, the default from
               the config file is used.
            selector (dict): passed to load.
            **kwargs: passed to from_raw

        Example:

            >>> srnos = my_dbreader.select_batch("testing_new_solvent")
            >>> cell_datas = []
            >>> for srno in srnos:
            >>> ... my_run_name = my_dbreader.get_cell_name(srno)
            >>> ... mass = my_dbreader.get_mass(srno)
            >>> ... rawfiles, cellpyfiles = \
            >>> ...     filefinder.search_for_files(my_run_name)
            >>> ... cell_data = cellreader.CellpyData()
            >>> ... cell_data.loadcell(raw_files=rawfiles,
            >>> ...                    cellpy_file=cellpyfiles)
            >>> ... cell_data.set_mass(mass)
            >>> ... if not cell_data.summary_exists:
            >>> ...     cell_data.make_summary() # etc. etc.
            >>> ... cell_datas.append(cell_data)
            >>>
        """

        # This is a part of a dramatic API change. It will not be possible to
        # load more than one set of datasets (i.e. one single cellpy-file or
        # several raw-files that will be automatically merged)

        # TODO @jepe Make setting or prm so that it is possible to update only new data
        # TODO @jepe Allow passing handle to progress-bar or update a global progressbar

        logging.info("Started cellpy.cellreader.loadcell")
        if cellpy_file is None:
            similar = False
        elif force_raw:
            similar = False
        else:
            similar = self.check_file_ids(raw_files, cellpy_file)
        logging.debug("checked if the files were similar")

        if only_summary:
            self.load_only_summary = True
        else:
            self.load_only_summary = False

        if not similar:
            logging.debug("cellpy file(s) needs updating - loading raw")
            logging.info("Loading raw-file")
            logging.debug(raw_files)
            self.from_raw(raw_files, **kwargs)
            if cell_type is not None:
                self.cycle_mode = cell_type
                logging.debug(f"setting cycle mode: {cell_type}")
            logging.debug("loaded files")
            # Check if the run was loaded ([] if empty)
            if self.status_datasets:
                if mass:
                    self.set_mass(mass)
                if summary_on_raw:
                    nom_cap = kwargs.pop("nom_cap", None)
                    if nom_cap is not None:
                        self.set_nom_cap(nom_cap)
                    self.make_summary(
                        all_tests=False,
                        find_ocv=summary_ocv,
                        find_ir=summary_ir,
                        find_end_voltage=summary_end_v,
                        use_cellpy_stat_file=use_cellpy_stat_file,
                        # nom_cap=nom_cap,
                    )
            else:
                logging.warning("Empty run!")

        else:
            self.load(cellpy_file, selector=selector)
            nom_cap = kwargs.pop("nom_cap", None)
            if nom_cap is not None:
                self.set_nom_cap(nom_cap)
            if mass:
                self.set_mass(mass)

        return self

    def dev_update_loadcell(
        self,
        raw_files,
        cellpy_file=None,
        mass=None,
        summary_on_raw=False,
        summary_ir=True,
        summary_ocv=False,
        summary_end_v=True,
        force_raw=False,
        use_cellpy_stat_file=None,
        nom_cap=None,
        selector=None,
    ):

        logging.info("Started cellpy.cellreader.loadcell")

        if cellpy_file is None or force_raw:
            similar = None
        else:
            similar = self.check_file_ids(raw_files, cellpy_file, detailed=True)

        logging.debug("checked if the files were similar")

        if similar is None:
            # forcing to load only raw_files
            self.from_raw(raw_files)
            if self.status_datasets:
                if mass:
                    self.set_mass(mass)
                if summary_on_raw:
                    self.make_summary(
                        all_tests=False,
                        find_ocv=summary_ocv,
                        find_ir=summary_ir,
                        find_end_voltage=summary_end_v,
                        use_cellpy_stat_file=use_cellpy_stat_file,
                        nom_cap=nom_cap,
                    )
            else:
                logging.warning("Empty run!")
            return self

        self.load(cellpy_file, selector=selector)
        if mass:
            self.set_mass(mass)

        if all(similar.values()):
            logging.info("Everything is up to date")
            return

        start_file = True
        for i, f in enumerate(raw_files):
            f = Path(f)
            if not similar[f.name] and start_file:
                try:
                    last_data_point = self.cell.raw_data_files[i].last_data_point
                except IndexError:
                    last_data_point = 0

                self.dev_update_from_raw(
                    file_names=f, data_points=[last_data_point, None]
                )
                self.cell = self.dev_update_merge()

            elif not similar[f.name]:
                try:
                    last_data_point = self.cell.raw_data_files[i].last_data_point
                except IndexError:
                    last_data_point = 0

                self.dev_update_from_raw(
                    file_names=f, data_points=[last_data_point, None]
                )
                self.merge()

            start_file = False

        self.dev_update_make_steps()
        self.dev_update_make_summary(
            all_tests=False,
            find_ocv=summary_ocv,
            find_ir=summary_ir,
            find_end_voltage=summary_end_v,
            use_cellpy_stat_file=use_cellpy_stat_file,
        )
        return self

    def dev_update(self, file_names=None, **kwargs):
        print("NOT FINISHED YET - but close")
        if len(self.cell.raw_data_files) != 1:
            logging.warning("Merged cell. But can only update based on the last file")
            print(self.cell.raw_data_files)
            for fid in self.cell.raw_data_files:
                print(fid)
        last = self.cell.raw_data_files[0].last_data_point

        self.dev_update_from_raw(
            file_names=file_names, data_points=[last, None], **kwargs
        )
        print("lets try to merge")
        self.cell = self.dev_update_merge()
        print("now it is time to update the step table")
        self.dev_update_make_steps()
        print("and finally, lets update the summary")
        self.dev_update_make_summary()

    def dev_update_merge(self):
        print("NOT FINISHED YET - but very close")
        number_of_tests = len(self.cells)
        if number_of_tests != 2:
            logging.warning("Cannot merge if you do not have exactly two cell-objects")
            return
        t1, t2 = self.cells

        if t1.raw.empty:
            logging.debug("OBS! the first dataset is empty")

        if t2.raw.empty:
            t1.merged = True
            logging.debug("the second dataset was empty")
            logging.debug(" -> merged contains only first")
            return t1
        test = t1

        cycle_index_header = self.headers_normal.cycle_index_txt

        if not t1.raw.empty:
            t1.raw = t1.raw.iloc[:-1]
            raw2 = pd.concat([t1.raw, t2.raw], ignore_index=True)
            test.no_cycles = max(raw2[cycle_index_header])
            test.raw = raw2
        else:
            test.no_cycles = max(t2.raw[cycle_index_header])
            test = t2
        logging.debug(" -> merged with new dataset")

        return test

    def dev_update_make_steps(self, **kwargs):
        old_steps = self.cell.steps.iloc[:-1]
        # Note! hard-coding header name (might fail if changing default headers)
        from_data_point = self.cell.steps.iloc[-1].point_first
        new_steps = self.make_step_table(from_data_point=from_data_point, **kwargs)
        merged_steps = pd.concat([old_steps, new_steps]).reset_index(drop=True)
        self.cell.steps = merged_steps

    def dev_update_make_summary(self, **kwargs):
        print("NOT FINISHED YET - but not critical")
        # Update not implemented yet, running full summary calculations for now.
        # For later:
        # old_summary = self.cell.summary.iloc[:-1]
        cycle_index_header = self.headers_summary.cycle_index
        from_cycle = self.cell.summary.iloc[-1][cycle_index_header]
        self.make_summary(from_cycle=from_cycle, **kwargs)
        # For later:
        # (Remark! need to solve how to merge culumated columns)
        # new_summary = self.make_summary(from_cycle=from_cycle)
        # merged_summary = pd.concat([old_summary, new_summary]).reset_index(drop=True)
        # self.cell.summary = merged_summary

    def dev_update_from_raw(self, file_names=None, data_points=None, **kwargs):
        """This method is under development. Using this to develop updating files
        with only new data.
        """
        print("NOT FINISHED YET - but very close")
        if file_names:
            self.file_names = file_names

        if file_names is None:
            logging.info(
                "No filename given and no stored in the file_names "
                "attribute. Returning None"
            )
            return None

        if not isinstance(self.file_names, (list, tuple)):
            self.file_names = [file_names]

        raw_file_loader = self.loader

        set_number = 0
        test = None

        logging.debug("start iterating through file(s)")
        print(self.file_names)

        for f in self.file_names:
            logging.debug("loading raw file:")
            logging.debug(f"{f}")

            # get a list of cellpy.readers.core.Cell objects
            test = raw_file_loader(f, data_points=data_points, **kwargs)
            # remark that the bounds are included (i.e. the first datapoint
            # is 5000.

            logging.debug("added the data set - merging file info")

            # raw_data_file = copy.deepcopy(test[set_number].raw_data_files[0])
            # file_size = test[set_number].raw_data_files_length[0]

            # test[set_number].raw_data_files.append(raw_data_file)
            # test[set_number].raw_data_files_length.append(file_size)
            # return test

        self.cells.append(test[set_number])

        self.number_of_datasets = len(self.cells)
        self.status_datasets = self._validate_datasets()
        self._invent_a_name()
        return self

    def from_raw(self, file_names=None, **kwargs):
        """Load a raw data-file.

        Args:
            file_names (list of raw-file names): uses CellpyData.file_names if
                None. If the list contains more than one file name, then the
                runs will be merged together.

        Other keywords depending on loader:
            [ArbinLoader]:
                bad_steps (list of tuples): (c, s) tuples of steps s (in cycle c)
                    to skip loading.
                dataset_number (int): the data set number to select if you are dealing
                    with arbin files with more than one data-set.
                data_points (tuple of ints): load only data from data_point[0] to
                    data_point[1] (use None for infinite). NOT IMPLEMEMTED YET.

        """
        # This function only loads one test at a time (but could contain several
        # files). The function from_res() used to implement loading several
        # datasets (using list of lists as input), however it is now deprecated.

        if file_names:
            self.file_names = file_names

        if not isinstance(self.file_names, (list, tuple)):
            self.file_names = [file_names]

        # file_type = self.tester
        instrument = kwargs.pop("instrument", None)
        if instrument:
            logging.info("Setting custom instrument")
            logging.info(f"-> {instrument}")
            self.set_instrument(instrument)
        raw_file_loader = self.loader
        # test is currently a list of tests - this option will be removed in the future
        # so set_number is hard-coded to 0, i.e. actual-test is always test[0]
        set_number = 0
        test = None
        counter = 0
        logging.debug("start iterating through file(s)")

        for f in self.file_names:
            logging.debug("loading raw file:")
            logging.debug(f"{f}")
            new_tests = raw_file_loader(f, **kwargs)

            if new_tests:

                # retrieving the first cell data (e.g. first file)
                if test is None:
                    logging.debug("getting data from first file")
                    if new_tests[set_number].no_data:
                        logging.debug("NO DATA")
                    else:
                        test = new_tests

                # appending cell data file to existing
                else:
                    logging.debug("continuing reading files...")
                    _test = self._append(test[set_number], new_tests[set_number])

                    if not _test:
                        logging.warning(f"EMPTY TEST: {f}")
                        continue

                    test[set_number] = _test

                    # retrieving file info in a for-loop in case of multiple files
                    # Remark!
                    #    - the raw_data_files attribute is a list
                    #    - the raw_data_files_length attribute is a list
                    # The reason for this choice is not clear anymore, but
                    # let us keep it like this for now
                    logging.debug("added the data set - merging file info")
                    # TODO: include this into prms (and config-file):
                    max_raw_files_to_merge = 20
                    for j in range(len(new_tests[set_number].raw_data_files)):
                        raw_data_file = new_tests[set_number].raw_data_files[j]
                        file_size = new_tests[set_number].raw_data_files_length[j]
                        test[set_number].raw_data_files.append(raw_data_file)
                        test[set_number].raw_data_files_length.append(file_size)
                        counter += 1
                        if counter > max_raw_files_to_merge:
                            logging.debug("ERROR? Too many files to merge")
                            raise ValueError(
                                "Too many files to merge - "
                                "could be a p2-p3 zip thing"
                            )

            else:
                logging.debug("NOTHING LOADED")

        logging.debug("finished loading the raw-files")

        test_exists = False
        if test:
            if test[0].no_data:
                logging.debug(
                    "the first dataset (or only dataset) loaded from the raw data file is empty"
                )
            else:
                test_exists = True

        if test_exists:
            if not prms.Reader.sorted_data:
                logging.debug("sorting data")
                test[set_number] = self._sort_data(test[set_number])

            self.cells.append(test[set_number])
        else:
            logging.warning("No new datasets added!")
        self.number_of_datasets = len(self.cells)
        self.status_datasets = self._validate_datasets()
        self._invent_a_name()
        return self

    def from_res(self, filenames=None, check_file_type=True):
        """Convenience function for loading arbin-type data into the
        datastructure.

        Args:
            filenames: ((lists of) list of raw-file names): uses
                cellpy.file_names if None.
                If list-of-list, it loads each list into separate datasets.
                The files in the inner list will be merged.
            check_file_type (bool): check file type if True
                (res-, or cellpy-format)
        """
        raise DeprecatedFeature

    def _validate_datasets(self, level=0):
        logging.debug("validating test")
        level = 0
        # simple validation for finding empty datasets - should be expanded to
        # find not-complete datasets, datasets with missing prms etc
        v = []
        if level == 0:
            for test in self.cells:
                # check that it contains all the necessary headers
                # (and add missing ones)
                # test = self._clean_up_normal_table(test)
                # check that the test is not empty
                v.append(self._is_not_empty_dataset(test))
            logging.debug(f"validation array: {v}")
        return v

    def check(self):
        """Returns False if no datasets exists or if one or more of the datasets
        are empty"""

        if len(self.status_datasets) == 0:
            return False
        if all(self.status_datasets):
            return True
        return False

    # TODO: maybe consider being a bit more concice (re-implement)
    def _is_not_empty_dataset(self, dataset):
        if dataset is self._empty_dataset():
            return False
        else:
            return True

    # TODO: check if this is useful and if it is rename, if not delete
    def _clean_up_normal_table(self, test=None, dataset_number=None):
        # check that test contains all the necessary headers
        # (and add missing ones)
        raise NotImplementedError

    # TODO: this is used for the check-datasetnr-thing. Will soon be obsolete?
    def _report_empty_dataset(self):
        logging.info("Empty set")

    @staticmethod
    def _empty_dataset():
        return None

    def _invent_a_name(self, filename=None, override=False):
        if filename is None:
            self.name = "nameless"
            return
        if self.name and not override:
            return
        path = Path(filename)
        self.name = path.with_suffix("").name

    def partial_load(self, **kwargs):
        """Load only a selected part of the cellpy file."""
        raise NotImplementedError

    def link(self, **kwargs):
        """Create a link to a cellpy file.

        If the file is very big, it is sometimes better to work with the data
        out of memory (i.e. on disk). A CellpyData object with a linked file
        will in most cases work as a normal object. However, some of the methods
        might be disabled. And it will be slower.

        Notes:
            2020.02.08 - maybe this functionality is not needed and can be replaced
                by using dask or similar?
        """
        raise NotImplementedError

    def load(
        self,
        cellpy_file,
        parent_level=None,
        return_cls=True,
        accept_old=True,
        selector=None,
    ):
        """Loads a cellpy file.

        Args:
            cellpy_file (path, str): Full path to the cellpy file.
            parent_level (str, optional): Parent level. Warning! Deprecating this soon!
            return_cls (bool): Return the class.
            accept_old (bool): Accept loading old cellpy-file versions.
                Instead of raising WrongFileVersion it only issues a warning.
            selector (): under development

        Returns:
            cellpy.CellPyData class if return_cls is True
        """

        try:
            logging.debug("loading cellpy-file (hdf5):")
            logging.debug(cellpy_file)

            with pickle_protocol(PICKLE_PROTOCOL):
                new_datasets = self._load_hdf5(
                    cellpy_file, parent_level, accept_old, selector=selector
                )
            logging.debug("cellpy-file loaded")

        except AttributeError:
            new_datasets = []
            logging.warning(
                "This cellpy-file version is not supported by"
                "current reader (try to update cellpy)."
            )

        if new_datasets:
            for dataset in new_datasets:
                self.cells.append(dataset)
        else:
            # raise LoadError
            logging.warning("Could not load")
            logging.warning(str(cellpy_file))

        self.number_of_datasets = len(self.cells)
        self.status_datasets = self._validate_datasets()
        self._invent_a_name(cellpy_file)
        if return_cls:
            return self

    def old_load(
        self, cellpy_file, parent_level=None, return_cls=True, accept_old=False
    ):
        """Loads a cellpy file.

        Args:
            cellpy_file (path, str): Full path to the cellpy file.
            parent_level (str, optional): Parent level. Warning! Deprecating this soon!
            return_cls (bool): Return the class.
            accept_old (bool): Accept loading old cellpy-file versions.
                Instead of raising WrongFileVersion it only issues a warning.

        Returns:
            cellpy.CellPyData class if return_cls is True
        """

        try:
            logging.debug("loading cellpy-file (hdf5):")
            logging.debug(cellpy_file)
            with pickle_protocol(PICKLE_PROTOCOL):
                new_datasets = self._load_hdf5(cellpy_file, parent_level, accept_old)
            logging.debug("cellpy-file loaded")
        except AttributeError:
            new_datasets = []
            logging.warning(
                "This cellpy-file version is not supported by"
                "current reader (try to update cellpy)."
            )

        if new_datasets:
            for dataset in new_datasets:
                self.cells.append(dataset)
        else:
            # raise LoadError
            logging.warning("Could not load")
            logging.warning(str(cellpy_file))

        self.number_of_datasets = len(self.cells)
        self.status_datasets = self._validate_datasets()
        self._invent_a_name(cellpy_file)
        if return_cls:
            return self

    def _get_cellpy_file_version(self, filename, meta_dir="/info", parent_level=None):
        if parent_level is None:
            parent_level = prms._cellpyfile_root

        with pd.HDFStore(filename) as store:
            try:
                meta_table = store.select(parent_level + meta_dir)
            except KeyError:
                raise WrongFileVersion(
                    "This file is VERY old - cannot read file version number"
                )
        try:
            cellpy_file_version = self._extract_from_dict(
                meta_table, "cellpy_file_version"
            )
        except Exception as e:
            warnings.warn(f"Unhandled exception raised: {e}")
            return 0

        return cellpy_file_version

    def _load_hdf5(self, filename, parent_level=None, accept_old=False, selector=None):
        """Load a cellpy-file.

        Args:
            filename (str): Name of the cellpy file.
            parent_level (str) (optional): name of the parent level
                (defaults to "CellpyData"). DeprecationWarning!
            accept_old (bool): accept old file versions.
            selector (): select specific ranges (under development)

        Returns:
            loaded datasets (DataSet-object)
        """

        if parent_level is None:
            parent_level = prms._cellpyfile_root

        if parent_level != prms._cellpyfile_root:
            logging.debug(
                f"Using non-default parent label for the " f"hdf-store: {parent_level}"
            )

        if not os.path.isfile(filename):
            logging.info(f"File does not exist: {filename}")
            raise IOError(f"File does not exist: {filename}")

        cellpy_file_version = self._get_cellpy_file_version(filename)
        logging.debug(f"Cellpy file version {cellpy_file_version}; selector={selector}")
        if cellpy_file_version > CELLPY_FILE_VERSION:
            raise WrongFileVersion(
                f"File format too new: {filename} :: version: {cellpy_file_version}"
                f"Reload from raw or upgrade your cellpy!"
            )

        elif cellpy_file_version < MINIMUM_CELLPY_FILE_VERSION:
            raise WrongFileVersion(
                f"File format too old: {filename} :: version: {cellpy_file_version}"
                f"Reload from raw or downgrade your cellpy!"
            )

        elif cellpy_file_version < CELLPY_FILE_VERSION:
            if accept_old:
                logging.debug(f"old cellpy file version {cellpy_file_version}")
                logging.debug(f"filename: {filename}")
                logging.warning(
                    f"Loading old file-type. It is recommended that you remake the step table and the "
                    f"summary table."
                )
                new_data = self._load_old_hdf5(filename, cellpy_file_version)
            else:
                raise WrongFileVersion(
                    f"File format too old: {filename} :: version: {cellpy_file_version}"
                    f"Try loading setting accept_old=True"
                )

        else:
            logging.debug(f"Loading {filename} :: v{cellpy_file_version}")
            new_data = self._load_hdf5_current_version(filename, selector=selector)

        # self.__check_loaded_data(new_data)

        return new_data

    def _load_hdf5_current_version(
        self, filename, meta_dir="/info", parent_level=None, selector=None
    ):
        if parent_level is None:
            parent_level = prms._cellpyfile_root

        raw_dir = prms._cellpyfile_raw
        step_dir = prms._cellpyfile_step
        summary_dir = prms._cellpyfile_summary
        fid_dir = prms._cellpyfile_fid

        logging.debug(f"filename: {filename}")
        logging.debug(f"selector: {selector}")
        with pd.HDFStore(filename) as store:
            data, meta_table = self._create_initial_data_set_from_cellpy_file(
                meta_dir, parent_level, store
            )
            self._check_keys_in_cellpy_file(
                meta_dir, parent_level, raw_dir, store, summary_dir
            )
            self._extract_summary_from_cellpy_file(
                data, parent_level, store, summary_dir, selector=selector
            )
            self._extract_raw_from_cellpy_file(
                data, parent_level, raw_dir, store, selector=selector
            )
            self._extract_steps_from_cellpy_file(
                data, parent_level, step_dir, store, selector=selector
            )
            fid_table, fid_table_selected = self._extract_fids_from_cellpy_file(
                fid_dir, parent_level, store
            )

        self._extract_meta_from_cellpy_file(data, meta_table, filename)

        if fid_table_selected:
            (data.raw_data_files, data.raw_data_files_length,) = self._convert2fid_list(
                fid_table
            )
        else:
            data.raw_data_files = []
            data.raw_data_files_length = []
        # this does not yet allow multiple sets
        new_tests = [
            data
        ]  # but cellpy is ready when that time comes (if it ever happens)
        return new_tests

    def _load_hdf5_v5(self, filename, selector=None):
        parent_level = "CellpyData"
        raw_dir = "/raw"
        step_dir = "/steps"
        summary_dir = "/summary"
        fid_dir = "/fid"
        meta_dir = "/info"

        with pd.HDFStore(filename) as store:
            data, meta_table = self._create_initial_data_set_from_cellpy_file(
                meta_dir, parent_level, store
            )
            self._check_keys_in_cellpy_file(
                meta_dir, parent_level, raw_dir, store, summary_dir
            )
            self._extract_summary_from_cellpy_file(
                data, parent_level, store, summary_dir, selector=selector
            )
            self._extract_raw_from_cellpy_file(
                data, parent_level, raw_dir, store, selector=selector
            )
            self._extract_steps_from_cellpy_file(
                data, parent_level, step_dir, store, selector=selector
            )
            fid_table, fid_table_selected = self._extract_fids_from_cellpy_file(
                fid_dir, parent_level, store
            )

        self._extract_meta_from_cellpy_file(data, meta_table, filename)

        if fid_table_selected:
            (data.raw_data_files, data.raw_data_files_length,) = self._convert2fid_list(
                fid_table
            )
        else:
            data.raw_data_files = []
            data.raw_data_files_length = []

        # this does not yet allow multiple sets
        logging.debug("loaded new test")
        new_tests = [
            data
        ]  # but cellpy is ready when that time comes (if it ever happens)
        return new_tests

    def _load_old_hdf5(self, filename, cellpy_file_version):
        if cellpy_file_version < 5:
            new_data = self._load_old_hdf5_v3_to_v4(filename)
        elif cellpy_file_version == 5:
            new_data = self._load_hdf5_v5(filename)
        else:
            raise WrongFileVersion(f"version {cellpy_file_version} is not supported")

        if cellpy_file_version < 6:
            logging.debug("legacy cellpy file version needs translation")
            new_data = old_settings.translate_headers(new_data, cellpy_file_version)
            # self.__check_loaded_data(new_data)
        return new_data

    def __check_loaded_data(self, new_data):
        print("Checking loaded data".center(80, "="))
        print("file names:")
        print(self.file_names)
        print("new data sets:")
        print(len(new_data))
        print("first data set:")
        first = new_data[0]
        print(first)

    def _load_old_hdf5_v3_to_v4(self, filename):
        parent_level = "CellpyData"
        meta_dir = "/info"
        _raw_dir = "/dfdata"
        _step_dir = "/step_table"
        _summary_dir = "/dfsummary"
        _fid_dir = "/fidtable"

        with pd.HDFStore(filename) as store:
            data, meta_table = self._create_initial_data_set_from_cellpy_file(
                meta_dir, parent_level, store
            )

        self._check_keys_in_cellpy_file(
            meta_dir, parent_level, _raw_dir, store, _summary_dir
        )
        self._extract_summary_from_cellpy_file(data, parent_level, store, _summary_dir)
        self._extract_raw_from_cellpy_file(data, parent_level, _raw_dir, store)
        self._extract_steps_from_cellpy_file(data, parent_level, _step_dir, store)
        fid_table, fid_table_selected = self._extract_fids_from_cellpy_file(
            _fid_dir, parent_level, store
        )
        self._extract_meta_from_cellpy_file(data, meta_table, filename)
        warnings.warn(
            "Loaded old cellpy-file version (<5). " "Please update and save again."
        )
        if fid_table_selected:
            (data.raw_data_files, data.raw_data_files_length,) = self._convert2fid_list(
                fid_table
            )
        else:
            data.raw_data_files = []
            data.raw_data_files_length = []

        new_tests = [data]
        return new_tests

    def _create_initial_data_set_from_cellpy_file(self, meta_dir, parent_level, store):
        # Remark that this function is run before selecting loading method
        # based on version. If you change the meta_dir prm to something else than
        # "/info" it will most likely fail.
        # Remark! Used for versions 3, 4, 5

        data = Cell()
        meta_table = None

        try:
            meta_table = store.select(parent_level + meta_dir)
        except KeyError as e:
            logging.info("This file is VERY old - no info given here")
            logging.info("You should convert the files to a newer version!")
            logging.debug(e)
            return data, meta_table

        try:
            data.cellpy_file_version = self._extract_from_dict(
                meta_table, "cellpy_file_version"
            )
        except Exception as e:
            data.cellpy_file_version = 0
            warnings.warn(f"Unhandled exception raised: {e}")
            return data, meta_table

        logging.debug(f"cellpy file version. {data.cellpy_file_version}")
        return data, meta_table

    def _check_keys_in_cellpy_file(
        self, meta_dir, parent_level, raw_dir, store, summary_dir
    ):
        required_keys = [raw_dir, summary_dir, meta_dir]
        required_keys = ["/" + parent_level + _ for _ in required_keys]
        for key in required_keys:
            if key not in store.keys():
                logging.info(
                    f"This cellpy-file is not good enough - "
                    f"at least one key is missing: {key}"
                )
                raise Exception(
                    f"OH MY GOD! At least one crucial key is missing {key}!"
                )
        logging.debug(f"Keys in current cellpy-file: {store.keys()}")

    def _hdf5_cycle_filter(self, table=None):
        # this is not the best way to do it
        if max_cycle := self.limit_loaded_cycles:
            if table == "summary":
                logging.debug(f"limited to cycle_number {max_cycle}")
                return (f"index <= {int(max_cycle)}",)
            elif table == "raw":
                logging.debug(f"limited to data_point {self.limit_data_points}")
                return (f"index <= {int(self.limit_data_points)}",)

    def _unpack_selector(self, selector):
        # not implemented yet
        # should be used for trimming the selector so that it is not necessary to parse it individually
        # for all the _extract_xxx_from_cellpy_file methods.
        return selector

    def _extract_summary_from_cellpy_file(
        self, data, parent_level, store, summary_dir, selector=None
    ):
        if selector is not None:
            cycle_filter = []
            if max_cycle := selector.get("max_cycle", None):
                cycle_filter.append(f"index <= {int(max_cycle)}")
                self.limit_loaded_cycles = max_cycle
        else:
            # getting cycle filter by setting attributes:
            cycle_filter = self._hdf5_cycle_filter("summary")

        data.summary = store.select(parent_level + summary_dir, where=cycle_filter)

        # TODO: max data point should be an attribute
        max_data_point = data.summary["data_point"].max()
        self.limit_data_points = int(max_data_point)
        logging.debug(f"data-point max limit: {self.limit_data_points}")

    def _extract_raw_from_cellpy_file(
        self, data, parent_level, raw_dir, store, selector=None
    ):
        # selector is not implemented yet for only raw data
        # however, selector for max_cycle will still work since
        # the attribute self.limit_data_points is set while reading the summary
        cycle_filter = self._hdf5_cycle_filter(table="raw")
        data.raw = store.select(parent_level + raw_dir, where=cycle_filter)

    def _extract_steps_from_cellpy_file(
        self, data, parent_level, step_dir, store, selector=None
    ):
        try:
            data.steps = store.select(parent_level + step_dir)
            if self.limit_data_points:
                data.steps = data.steps.loc[
                    data.steps["point_last"] <= self.limit_data_points
                ]
                logging.debug(f"limited to data_point {self.limit_data_points}")
        except Exception as e:
            print(e)
            logging.debug("could not get steps from cellpy-file")
            data.steps = pd.DataFrame()
            warnings.warn(f"Unhandled exception raised: {e}")

    def _extract_fids_from_cellpy_file(self, fid_dir, parent_level, store):
        logging.debug(f"Extracting fid table from {fid_dir} in hdf5 store")
        try:
            fid_table = store.select(
                parent_level + fid_dir
            )  # remark! changed spelling from
            # lower letter to camel-case!
            fid_table_selected = True
        except Exception as e:
            logging.debug(e)
            logging.debug("could not get fid from cellpy-file")
            fid_table = []
            warnings.warn("no fid_table - you should update your cellpy-file")
            fid_table_selected = False
        return fid_table, fid_table_selected

    def _extract_meta_from_cellpy_file(self, data, meta_table, filename):
        # get attributes from meta table
        # remark! could also utilise the pandas to dictionary method directly
        # for example: meta_table.T.to_dict()
        # Maybe a good task for someone who would like to learn more about
        # how cellpy works..

        for attribute in ATTRS_CELLPYFILE:
            value = self._extract_from_dict(meta_table, attribute)
            # some fixes due to errors propagated into the cellpy-files
            if attribute == "creator":
                if not isinstance(value, str):
                    value = "no_name"

            if attribute == "test_no":
                if not isinstance(value, (int, float)):
                    value = 0

            setattr(data, attribute, value)

        if data.mass is None:
            data.mass = 1.0
        else:
            data.mass_given = True

        if data.cycle_mode is None:
            logging.critical("cycle mode not found")

        data.loaded_from = str(filename)

        # hack to allow the renaming of tests to datasets
        try:
            name = self._extract_from_dict_hard(meta_table, "name")
            if not isinstance(name, str):
                name = "no_name"
            data.name = name

        except KeyError:
            logging.debug(f"missing key in meta table: {name}")
            print(meta_table)
            warnings.warn("OLD-TYPE: Recommend to save in new format!")
            try:
                name = self._extract_from_dict(meta_table, "test_name")
            except Exception as e:
                name = "no_name"
                logging.debug("name set to 'no_name")
                warnings.warn(f"Unhandled exception raised: {e}")
            data.name = name

        # unpacking the raw data limits
        for key in data.raw_limits:
            try:
                data.raw_limits[key] = self._extract_from_dict_hard(meta_table, key)
            except KeyError:
                logging.debug(f"missing key in meta_table: {key}")
                warnings.warn("OLD-TYPE: Recommend to save in new format!")

    @staticmethod
    def _extract_from_dict(t, x, default_value=None):
        try:
            value = t[x].values
            if value:
                value = value[0]
        except KeyError:
            value = default_value
        return value

    @staticmethod
    def _extract_from_dict_hard(t, x):
        value = t[x].values
        if value:
            value = value[0]
        return value

    def _create_infotable(self, dataset_number=None):
        # needed for saving class/DataSet to hdf5

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return

        test = self.get_cell(dataset_number)

        infotable = collections.OrderedDict()

        for attribute in ATTRS_CELLPYFILE:
            value = getattr(test, attribute)
            infotable[attribute] = [value]

        infotable["cellpy_file_version"] = [CELLPY_FILE_VERSION]
        infotable["cycle_mode"] = [self.cycle_mode]

        limits = test.raw_limits
        for key in limits:
            infotable[key] = limits[key]

        infotable = pd.DataFrame(infotable)

        logging.debug("_create_infotable: fid")
        fidtable = collections.OrderedDict()
        fidtable["raw_data_name"] = []
        fidtable["raw_data_full_name"] = []
        fidtable["raw_data_size"] = []
        fidtable["raw_data_last_modified"] = []
        fidtable["raw_data_last_accessed"] = []
        fidtable["raw_data_last_info_changed"] = []
        fidtable["raw_data_location"] = []
        fidtable["raw_data_files_length"] = []
        fidtable["last_data_point"] = []
        fids = test.raw_data_files
        fidtable["raw_data_fid"] = fids
        if fids:
            for fid, length in zip(fids, test.raw_data_files_length):
                try:
                    fidtable["raw_data_name"].append(str(Path(fid.name).name))
                    fidtable["raw_data_full_name"].append(str(Path(fid.full_name)))
                    fidtable["raw_data_size"].append(fid.size)
                    fidtable["raw_data_last_modified"].append(fid.last_modified)
                    fidtable["raw_data_last_accessed"].append(fid.last_accessed)
                    fidtable["raw_data_last_info_changed"].append(fid.last_info_changed)
                except:
                    logging.debug("this is probably not from a file")
                    fidtable["raw_data_name"].append("db")
                    fidtable["raw_data_full_name"].append("db")
                    fidtable["raw_data_size"].append(fid.size)
                    fidtable["raw_data_last_modified"].append("db")
                    fidtable["raw_data_last_accessed"].append("db")
                    fidtable["raw_data_last_info_changed"].append("db")

                fidtable["raw_data_location"].append(fid.location)
                fidtable["raw_data_files_length"].append(length)
                fidtable["last_data_point"].append(fid.last_data_point)
        else:
            warnings.warn("seems you lost info about your raw-data (missing fids)")
        fidtable = pd.DataFrame(fidtable)
        return infotable, fidtable

    def _convert2fid_list(self, tbl):
        logging.debug("converting loaded fidtable to FileID object")
        fids = []
        lengths = []
        min_amount = 0
        for counter, item in enumerate(tbl["raw_data_name"]):
            fid = FileID()
            try:
                fid.name = Path(item).name
            except NotImplementedError:
                fid.name = os.path.basename(item)
            fid.full_name = tbl["raw_data_full_name"][counter]
            fid.size = tbl["raw_data_size"][counter]
            fid.last_modified = tbl["raw_data_last_modified"][counter]
            fid.last_accessed = tbl["raw_data_last_accessed"][counter]
            fid.last_info_changed = tbl["raw_data_last_info_changed"][counter]
            fid.location = tbl["raw_data_location"][counter]
            length = tbl["raw_data_files_length"][counter]
            if "last_data_point" in tbl.columns:
                fid.last_data_point = tbl["last_data_point"][counter]
            else:
                fid.last_data_point = 0
            fids.append(fid)
            lengths.append(length)
            min_amount = 1
        if min_amount < 1:
            logging.debug("info about raw files missing")
        return fids, lengths

    def merge(self, datasets=None, separate_datasets=False):
        """This function merges datasets into one set."""

        logging.info("Merging")
        if separate_datasets:
            warnings.warn(
                "The option separate_datasets=True is"
                "not implemented yet. Performing merging, but"
                "neglecting the option."
            )
        else:
            if datasets is None:
                datasets = list(range(len(self.cells)))
            first = True
            for dataset_number in datasets:
                if first:
                    dataset = self.cells[dataset_number]
                    first = False
                else:
                    dataset = self._append(dataset, self.cells[dataset_number])
                    for raw_data_file, file_size in zip(
                        self.cells[dataset_number].raw_data_files,
                        self.cells[dataset_number].raw_data_files_length,
                    ):
                        dataset.raw_data_files.append(raw_data_file)
                        dataset.raw_data_files_length.append(file_size)
            self.cells = [dataset]
            self.number_of_datasets = 1
        return self

    def _append(self, t1, t2, merge_summary=True, merge_step_table=True):
        logging.debug(
            f"merging two datasets\n(merge summary = {merge_summary})\n"
            f"(merge step table = {merge_step_table})"
        )
        if t1.raw.empty:
            logging.debug("OBS! the first dataset is empty")

        if t2.raw.empty:
            t1.merged = True
            logging.debug("the second dataset was empty")
            logging.debug(" -> merged contains only first")
            return t1
        test = t1
        # finding diff of time
        start_time_1 = t1.start_datetime
        start_time_2 = t2.start_datetime
        if self.tester in ["arbin", "arbin_res"]:
            diff_time = xldate_as_datetime(start_time_2) - xldate_as_datetime(
                start_time_1
            )
        else:
            diff_time = start_time_2 - start_time_1
        diff_time = diff_time.total_seconds()

        if diff_time < 0:
            logging.warning("Wow! your new dataset is older than the old!")
        logging.debug(f"diff time: {diff_time}")

        sort_key = self.headers_normal.datetime_txt  # DateTime
        # mod data points for set 2
        data_point_header = self.headers_normal.data_point_txt
        try:
            last_data_point = max(t1.raw[data_point_header])
        except ValueError:
            logging.debug("ValueError when getting last data point for r1")
            last_data_point = 0

        t2.raw[data_point_header] = t2.raw[data_point_header] + last_data_point
        logging.debug("No error getting last data point for r2")
        # mod cycle index for set 2
        cycle_index_header = self.headers_summary.cycle_index
        try:
            last_cycle = max(t1.raw[cycle_index_header])
        except ValueError:
            logging.debug("ValueError when getting last cycle index for r1")
            last_cycle = 0
        t2.raw[cycle_index_header] = t2.raw[cycle_index_header] + last_cycle
        # mod test time for set 2
        test_time_header = self.headers_normal.test_time_txt
        t2.raw[test_time_header] = t2.raw[test_time_header] + diff_time
        # merging
        if not t1.raw.empty:
            logging.debug("r1 is not empty - performing concat")
            raw2 = pd.concat([t1.raw, t2.raw], ignore_index=True)

            # checking if we already have made a summary file of these datasets
            # (to be used if merging summaries (but not properly implemented yet))
            if t1.summary.empty or t2.summary.empty:
                summary_made = False
            else:
                summary_made = True

            try:
                _ = t1.summary[
                    cycle_index_header
                ]  # during loading arbin res files, a stats-frame is loaded into
                _ = t2.summary[
                    cycle_index_header
                ]  # the summary. This prevents merging those.
            except KeyError:
                summary_made = False
                logging.info("The summary is not complete - run make_summary()")

            # checking if we already have made step tables for these datasets
            if t1.steps_made and t2.steps_made:
                step_table_made = True
            else:
                step_table_made = False

            if merge_summary and summary_made:
                # check if (self-made) summary exists.
                logging.debug("merge summaries")

                # This part of the code is seldom ran. Careful!
                # mod cycle index for set 2
                last_cycle = max(t1.summary[cycle_index_header])
                t2.summary[cycle_index_header] = (
                    t2.summary[cycle_index_header] + last_cycle
                )
                # mod test time for set 2
                t2.summary[test_time_header] = t2.summary[test_time_header] + diff_time
                # to-do: mod all the cumsum stuff in the summary (best to make
                # summary after merging) merging

                t2.summary[data_point_header] = (
                    t2.summary[data_point_header] + last_data_point
                )

                summary2 = pd.concat([t1.summary, t2.summary], ignore_index=True)

                test.summary = summary2
            else:
                logging.debug(
                    "could not merge summary tables "
                    "(non-existing) -"
                    "create them first!"
                )

            if merge_step_table:
                if step_table_made:
                    cycle_index_header = self.headers_normal.cycle_index_txt
                    t2.steps[self.headers_step_table.cycle] = (
                        t2.raw[self.headers_step_table.cycle] + last_cycle
                    )

                    steps2 = pd.concat([t1.steps, t2.steps], ignore_index=True)
                    test.steps = steps2
                else:
                    logging.debug(
                        "could not merge step tables "
                        "(non-existing) -"
                        "create them first!"
                    )

            test.no_cycles = max(raw2[cycle_index_header])
            test.raw = raw2
        else:
            test.no_cycles = max(t2.raw[cycle_index_header])
            test = t2
        test.merged = True
        logging.debug(" -> merged with new dataset")
        # TODO: @jepe -  update merging for more variables
        return test

    # --------------iterate-and-find-in-data-----------------------------------
    # TODO: make this obsolete (somehow)
    def _validate_dataset_number(self, n, check_for_empty=True):
        # Returns dataset_number (or None if empty)
        # Remark! _is_not_empty_dataset returns True or False

        if not len(self.cells):
            logging.info(
                "Can't see any datasets! Are you sure you have " "loaded anything?"
            )
            return

        if n is not None:
            v = n
        else:
            if self.selected_cell_number is None:
                v = 0
            else:
                v = self.selected_cell_number

        if check_for_empty:
            not_empty = self._is_not_empty_dataset(self.cells[v])
            if not_empty:
                return v
            else:
                return None
        else:
            return v

    # TODO: check if this can be moved to helpers
    def _validate_step_table(self, dataset_number=None, simple=False):
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return

        step_index_header = self.headers_normal.step_index_txt
        logging.debug("-validating step table")
        d = self.cells[dataset_number].raw
        s = self.cells[dataset_number].steps

        if not self.cells[dataset_number].steps_made:
            return False

        no_cycles_raw = np.amax(d[self.headers_normal.cycle_index_txt])
        headers_step_table = self.headers_step_table
        no_cycles_step_table = np.amax(s[headers_step_table.cycle])

        if simple:
            logging.debug("  (simple)")
            if no_cycles_raw == no_cycles_step_table:
                return True
            else:
                return False

        else:
            validated = True
            if no_cycles_raw != no_cycles_step_table:
                logging.debug("  differ in no. of cycles")
                validated = False
            else:
                for j in range(1, no_cycles_raw + 1):
                    cycle_number = j
                    no_steps_raw = len(
                        np.unique(
                            d.loc[
                                d[self.headers_normal.cycle_index_txt] == cycle_number,
                                self.headers_normal.step_index_txt,
                            ]
                        )
                    )
                    no_steps_step_table = len(
                        s.loc[
                            s[headers_step_table.cycle] == cycle_number,
                            headers_step_table.step,
                        ]
                    )
                    if no_steps_raw != no_steps_step_table:
                        validated = False
                        # txt = ("Error in step table "
                        #        "(cycle: %i) d: %i, s:%i)" % (
                        #         cycle_number,
                        #         no_steps_raw,
                        #         no_steps_steps
                        #     )
                        # )
                        #
                        # logging.debug(txt)
            return validated

    def print_steps(self, dataset_number=None):
        """Print the step table."""
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        st = self.cells[dataset_number].steps
        print(st)

    def get_step_numbers(
        self,
        steptype="charge",
        allctypes=True,
        pdtype=False,
        cycle_number=None,
        dataset_number=None,
        trim_taper_steps=None,
        steps_to_skip=None,
        steptable=None,
    ):
        # TODO: @jepe - include sub_steps here
        # TODO: @jepe - include option for not selecting taper steps here
        """Get the step numbers of selected type.

        Returns the selected step_numbers for the selected type of step(s).

        Args:
            steptype (string): string identifying type of step.
            allctypes (bool): get all types of charge (or discharge).
            pdtype (bool): return results as pandas.DataFrame
            cycle_number (int): selected cycle, selects all if not set.
            dataset_number (int): test number (default first)
                (usually not used).
            trim_taper_steps (integer): number of taper steps to skip (counted
                from the end, i.e. 1 means skip last step in each cycle).
            steps_to_skip (list): step numbers that should not be included.
            steptable (pandas.DataFrame): optional steptable

        Returns:
            A dictionary containing a list of step numbers corresponding
                to the selected steptype for the cycle(s).
            Returns a pandas.DataFrame instead of a dict of lists if pdtype is
                set to True. The frame is a sub-set of the step-table frame
                (i.e. all the same columns, only filtered by rows).

        Example:
            >>> my_charge_steps = CellpyData.get_step_numbers(
            >>>    "charge",
            >>>    cycle_number = 3
            >>> )
            >>> print my_charge_steps
            {3: [5,8]}

        """
        t0 = time.time()
        # logging.debug("Trying to get step-types")
        if steps_to_skip is None:
            steps_to_skip = []

        if steptable is None:
            dataset_number = self._validate_dataset_number(dataset_number)
            # logging.debug(f"dt 1: {time.time() - t0}")
            if dataset_number is None:
                self._report_empty_dataset()
                return

            if not self.cells[dataset_number].steps_made:
                logging.debug("steps is not made")

                if self.force_step_table_creation or self.force_all:
                    logging.debug("creating step_table for")
                    logging.debug(self.cells[dataset_number].loaded_from)
                    self.make_step_table(dataset_number=dataset_number)

                else:
                    logging.info("ERROR! Cannot use get_steps: create step_table first")
                    logging.info("You could use find_step_numbers method instead")
                    logging.info("(but I don't recommend it)")
                    return None

        # check if steptype is valid
        steptype = steptype.lower()
        steptypes = []
        helper_step_types = ["ocv", "charge_discharge"]
        valid_step_type = True
        # logging.debug(f"dt 2: {time.time() - t0}")
        if steptype in self.list_of_step_types:
            steptypes.append(steptype)
        else:
            txt = "%s is not a valid core steptype" % steptype
            if steptype in helper_step_types:
                txt = "but a helper steptype"
                if steptype == "ocv":
                    steptypes.append("ocvrlx_up")
                    steptypes.append("ocvrlx_down")
                elif steptype == "charge_discharge":
                    steptypes.append("charge")
                    steptypes.append("discharge")
            else:
                valid_step_type = False
            # logging.debug(txt)
        if not valid_step_type:
            return None

        # in case of selection allctypes, then modify charge, discharge
        if allctypes:
            add_these = []
            for st in steptypes:
                if st in ["charge", "discharge"]:
                    st1 = st + "_cv"
                    add_these.append(st1)
                    st1 = "cv_" + st
                    add_these.append(st1)
            for st in add_these:
                steptypes.append(st)

        # logging.debug("Your steptypes:")
        # logging.debug(steptypes)

        if steptable is None:
            st = self.cells[dataset_number].steps
        else:
            st = steptable
        shdr = self.headers_step_table

        # retrieving cycle numbers
        # logging.debug(f"dt 3: {time.time() - t0}")
        if cycle_number is None:
            cycle_numbers = self.get_cycle_numbers(dataset_number, steptable=steptable)
        else:
            if isinstance(cycle_number, collections.abc.Iterable):
                cycle_numbers = cycle_number
            else:
                cycle_numbers = [cycle_number]

        if trim_taper_steps is not None:
            trim_taper_steps = -trim_taper_steps
            # logging.debug("taper steps to trim given")

        if pdtype:
            # logging.debug("Return pandas dataframe.")
            if trim_taper_steps:
                logging.info(
                    "Trimming taper steps is currently not"
                    "possible when returning pd.DataFrame. "
                    "Do it manually insteaD."
                )
            out = st[st[shdr.type].isin(steptypes) & st[shdr.cycle].isin(cycle_numbers)]
            return out

        # if not pdtype, return a dict instead
        # logging.debug("out as dict; out[cycle] = [s1,s2,...]")
        # logging.debug("(same behaviour as find_step_numbers)")
        # logging.debug("return dict of lists")
        # logging.warning(
        #     "returning dict will be deprecated",
        # )
        out = dict()
        # logging.debug(f"return a dict")
        # logging.debug(f"dt 4: {time.time() - t0}")
        for cycle in cycle_numbers:
            steplist = []
            for s in steptypes:
                mask_type_and_cycle = (st[shdr.type] == s) & (st[shdr.cycle] == cycle)
                if not any(mask_type_and_cycle):
                    logging.debug(f"found nothing for cycle {cycle}")
                else:
                    step = st[mask_type_and_cycle][shdr.step].tolist()
                    for newstep in step[:trim_taper_steps]:
                        if newstep in steps_to_skip:
                            logging.debug(f"skipping step {newstep}")
                        else:
                            steplist.append(int(newstep))

            if not steplist:
                steplist = [0]
            out[cycle] = steplist
        # logging.debug(f"dt tot: {time.time() - t0}")
        return out

    def load_step_specifications(self, file_name, short=False, dataset_number=None):
        """ Load a table that contains step-type definitions.

        This function loads a file containing a specification for each step or
        for each (cycle_number, step_number) combinations if short==False. The
        step_cycle specifications that are allowed are stored in the variable
        cellreader.list_of_step_types.
        """

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return

        # if short:
        #     # the table only consists of steps (not cycle,step pairs) assuming
        #     # that the step numbers uniquely defines step type (this is true
        #     # for arbin at least).
        #     raise NotImplementedError

        step_specs = pd.read_csv(file_name, sep=prms.Reader.sep)
        if "step" not in step_specs.columns:
            logging.info("Missing column: step")
            raise IOError

        if "type" not in step_specs.columns:
            logging.info("Missing column: type")
            raise IOError

        if not short and "cycle" not in step_specs.columns:
            logging.info("Missing column: cycle")
            raise IOError

        self.make_step_table(step_specifications=step_specs, short=short)

    def _sort_data(self, dataset):
        # TODO: [# index]
        if self.headers_normal.data_point_txt in dataset.raw.columns:
            dataset.raw = dataset.raw.sort_values(
                self.headers_normal.data_point_txt
            ).reset_index()
            return dataset

        logging.debug("_sort_data: no datapoint header to sort by")

    def _ustep(self, n):
        un = []
        c = 0
        n = n.diff()
        for i in n:
            if i != 0:
                c += 1
            un.append(c)
        logging.debug("created u-steps")
        return un

    def make_step_table(
        self,
        step_specifications=None,
        short=False,
        profiling=False,
        all_steps=False,
        add_c_rate=True,
        skip_steps=None,
        sort_rows=True,
        dataset_number=None,
        from_data_point=None,
    ):

        """ Create a table (v.4) that contains summary information for each step.

        This function creates a table containing information about the
        different steps for each cycle and, based on that, decides what type of
        step it is (e.g. charge) for each cycle.

        The format of the steps is:

            index: cycleno - stepno - sub-step-no - ustep
            Time info (average, stdev, max, min, start, end, delta) -
            Logging info (average, stdev, max, min, start, end, delta) -
            Current info (average, stdev, max, min, start, end, delta) -
            Voltage info (average,  stdev, max, min, start, end, delta) -
            Type (from pre-defined list) - SubType -
            Info

         Args:
            step_specifications (pandas.DataFrame): step specifications
            short (bool): step specifications in short format
            profiling (bool): turn on profiling

            all_steps (bool): investigate all steps including same steps within
                one cycle (this is useful for e.g. GITT).
            add_c_rate (bool): include a C-rate estimate in the steps
            skip_steps (list of integers): list of step numbers that should not
                be processed (future feature - not used yet).
            sort_rows (bool): sort the rows after processing.
            dataset_number: defaults to self.dataset_number
            from_data_point (int): first data point to use

        Returns:
            None
        """
        # TODO: @jepe - include option for omitting steps
        # TODO: @jepe  - make it is possible to update only new data

        time_00 = time.time()
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return

        if profiling:
            print("PROFILING MAKE_STEP_TABLE".center(80, "="))

        def first(x):
            return x.iloc[0]

        def last(x):
            return x.iloc[-1]

        def delta(x):
            if x.iloc[0] == 0.0:
                # starts from a zero value
                difference = 100.0 * x.iloc[-1]
            else:
                difference = (x.iloc[-1] - x.iloc[0]) * 100 / abs(x.iloc[0])

            return difference

        nhdr = self.headers_normal
        shdr = self.headers_step_table

        if from_data_point is not None:
            df = self.cells[dataset_number].raw.loc[
                self.cells[dataset_number].raw[nhdr.data_point_txt] >= from_data_point
            ]
        else:
            df = self.cells[dataset_number].raw
        # df[shdr.internal_resistance_change] = \
        #     df[nhdr.internal_resistance_txt].pct_change()

        # selecting only the most important columns from raw:
        keep = [
            nhdr.data_point_txt,
            nhdr.test_time_txt,
            nhdr.step_time_txt,
            nhdr.step_index_txt,
            nhdr.cycle_index_txt,
            nhdr.current_txt,
            nhdr.voltage_txt,
            nhdr.ref_voltage_txt,
            nhdr.charge_capacity_txt,
            nhdr.discharge_capacity_txt,
            nhdr.internal_resistance_txt,
            # "ir_pct_change"
        ]

        # only use col-names that exist:
        keep = [col for col in keep if col in df.columns]
        df = df[keep]
        # preparing for implementation of sub_steps (will come in the future):
        df[nhdr.sub_step_index_txt] = 1

        # using headers as defined in the internal_settings.py file
        rename_dict = {
            nhdr.cycle_index_txt: shdr.cycle,
            nhdr.step_index_txt: shdr.step,
            nhdr.sub_step_index_txt: shdr.sub_step,
            nhdr.data_point_txt: shdr.point,
            nhdr.test_time_txt: shdr.test_time,
            nhdr.step_time_txt: shdr.step_time,
            nhdr.current_txt: shdr.current,
            nhdr.voltage_txt: shdr.voltage,
            nhdr.charge_capacity_txt: shdr.charge,
            nhdr.discharge_capacity_txt: shdr.discharge,
            nhdr.internal_resistance_txt: shdr.internal_resistance,
        }

        df = df.rename(columns=rename_dict)
        by = [shdr.cycle, shdr.step, shdr.sub_step]

        if skip_steps is not None:
            logging.debug(f"omitting steps {skip_steps}")
            df = df.loc[~df[shdr.step].isin(skip_steps)]

        if all_steps:
            by.append(shdr.ustep)
            df[shdr.ustep] = self._ustep(df[shdr.step])

        logging.debug(f"groupby: {by}")

        if profiling:
            time_01 = time.time()

        # TODO: make sure that all columns are nummeric

        gf = df.groupby(by=by)
        df_steps = gf.agg(
            [np.mean, np.std, np.amin, np.amax, first, last, delta]
        ).rename(columns={"amin": "min", "amax": "max", "mean": "avr"})

        df_steps = df_steps.reset_index()

        if profiling:
            print(f"*** groupby-agg: {time.time() - time_01} s")
            time_01 = time.time()

        # new cols

        # column with C-rates:
        if add_c_rate:
            nom_cap = self.cells[dataset_number].nom_cap
            mass = self.cells[dataset_number].mass
            spec_conv_factor = self.get_converter_to_specific()
            logging.debug(f"c-rate: nom_cap={nom_cap} spec_conv={spec_conv_factor}")

            df_steps[shdr.rate_avr] = abs(
                round(
                    df_steps.loc[:, (shdr.current, "avr")]
                    / (nom_cap / spec_conv_factor),
                    2,
                )
            )

        df_steps[shdr.type] = np.nan
        df_steps[shdr.sub_type] = np.nan
        df_steps[shdr.info] = np.nan

        if step_specifications is None:
            current_limit_value_hard = self.raw_limits["current_hard"]
            current_limit_value_soft = self.raw_limits["current_soft"]
            stable_current_limit_hard = self.raw_limits["stable_current_hard"]
            stable_current_limit_soft = self.raw_limits["stable_current_soft"]
            stable_voltage_limit_hard = self.raw_limits["stable_voltage_hard"]
            stable_voltage_limit_soft = self.raw_limits["stable_voltage_soft"]
            stable_charge_limit_hard = self.raw_limits["stable_charge_hard"]
            stable_charge_limit_soft = self.raw_limits["stable_charge_soft"]
            ir_change_limit = self.raw_limits["ir_change"]

            mask_no_current_hard = (
                df_steps.loc[:, (shdr.current, "max")].abs()
                + df_steps.loc[:, (shdr.current, "min")].abs()
            ) < current_limit_value_hard / 2

            mask_voltage_down = (
                df_steps.loc[:, (shdr.voltage, "delta")] < -stable_voltage_limit_hard
            )

            mask_voltage_up = (
                df_steps.loc[:, (shdr.voltage, "delta")] > stable_voltage_limit_hard
            )

            mask_voltage_stable = (
                df_steps.loc[:, (shdr.voltage, "delta")].abs()
                < stable_voltage_limit_hard
            )

            mask_current_down = (
                df_steps.loc[:, (shdr.current, "delta")] < -stable_current_limit_soft
            )

            mask_current_up = (
                df_steps.loc[:, (shdr.current, "delta")] > stable_current_limit_soft
            )

            mask_current_negative = (
                df_steps.loc[:, (shdr.current, "avr")] < -current_limit_value_hard
            )

            mask_current_positive = (
                df_steps.loc[:, (shdr.current, "avr")] > current_limit_value_hard
            )

            mask_galvanostatic = (
                df_steps.loc[:, (shdr.current, "delta")].abs()
                < stable_current_limit_soft
            )

            mask_charge_changed = (
                df_steps.loc[:, (shdr.charge, "delta")].abs() > stable_charge_limit_hard
            )

            mask_discharge_changed = (
                df_steps.loc[:, (shdr.discharge, "delta")].abs()
                > stable_charge_limit_hard
            )

            mask_no_change = (
                (df_steps.loc[:, (shdr.voltage, "delta")] == 0)
                & (df_steps.loc[:, (shdr.current, "delta")] == 0)
                & (df_steps.loc[:, (shdr.charge, "delta")] == 0)
                & (df_steps.loc[:, (shdr.discharge, "delta")] == 0)
            )

            # TODO: make an option for only checking unique steps
            #     e.g.
            #     df_x = df_steps.where.steps.are.unique

            df_steps.loc[
                mask_no_current_hard & mask_voltage_stable, (shdr.type, slice(None))
            ] = "rest"

            df_steps.loc[
                mask_no_current_hard & mask_voltage_up, (shdr.type, slice(None))
            ] = "ocvrlx_up"

            df_steps.loc[
                mask_no_current_hard & mask_voltage_down, (shdr.type, slice(None))
            ] = "ocvrlx_down"

            df_steps.loc[
                mask_discharge_changed & mask_current_negative, (shdr.type, slice(None))
            ] = "discharge"

            df_steps.loc[
                mask_charge_changed & mask_current_positive, (shdr.type, slice(None))
            ] = "charge"

            df_steps.loc[
                mask_voltage_stable & mask_current_negative & mask_current_down,
                (shdr.type, slice(None)),
            ] = "cv_discharge"

            df_steps.loc[
                mask_voltage_stable & mask_current_positive & mask_current_down,
                (shdr.type, slice(None)),
            ] = "cv_charge"

            # --- internal resistance ----
            df_steps.loc[mask_no_change, (shdr.type, slice(None))] = "ir"
            # assumes that IR is stored in just one row

            # --- sub-step-txt -----------
            df_steps[shdr.sub_type] = None

            # --- CV steps ----

            # "voltametry_charge"
            # mask_charge_changed
            # mask_voltage_up
            # (could also include abs-delta-cumsum current)

            # "voltametry_discharge"
            # mask_discharge_changed
            # mask_voltage_down

            if profiling:
                print(f"*** masking: {time.time() - time_01} s")
                time_01 = time.time()

        else:
            logging.debug("parsing custom step definition")
            if not short:
                logging.debug("using long format (cycle,step)")
                for row in step_specifications.itertuples():
                    df_steps.loc[
                        (df_steps[shdr.step] == row.step)
                        & (df_steps[shdr.cycle] == row.cycle),
                        (shdr.type, slice(None)),
                    ] = row.type
                    df_steps.loc[
                        (df_steps[shdr.step] == row.step)
                        & (df_steps[shdr.cycle] == row.cycle),
                        (shdr.info, slice(None)),
                    ] = row.info
            else:
                logging.debug("using short format (step)")
                for row in step_specifications.itertuples():
                    df_steps.loc[
                        df_steps[shdr.step] == row.step, (shdr.type, slice(None))
                    ] = row.type
                    df_steps.loc[
                        df_steps[shdr.step] == row.step, (shdr.info, slice(None))
                    ] = row.info

        if profiling:
            print(f"*** introspect: {time.time() - time_01} s")

        # check if all the steps got categorizes
        logging.debug("looking for un-categorized steps")
        empty_rows = df_steps.loc[df_steps[shdr.type].isnull()]
        if not empty_rows.empty:
            logging.warning(
                f"found {len(empty_rows)}"
                f":{len(df_steps)} non-categorized steps "
                f"(please, check your raw-limits)"
            )
            # logging.debug(empty_rows)

        # flatten (possible remove in the future),
        # (maybe we will implement mulitindexed tables)

        logging.debug(f"flatten columns")
        if profiling:
            time_01 = time.time()
        flat_cols = []
        for col in df_steps.columns:
            if isinstance(col, tuple):
                if col[-1]:
                    col = "_".join(col)
                else:
                    col = col[0]
            flat_cols.append(col)

        df_steps.columns = flat_cols
        if sort_rows:
            logging.debug("sorting the step rows")
            # TODO: [#index]
            # if this throws a KeyError: 'test_time_first' it probably
            # means that the df contains a non-nummeric 'test_time' column.
            df_steps = df_steps.sort_values(by=shdr.test_time + "_first").reset_index()

        if profiling:
            print(f"*** flattening: {time.time() - time_01} s")

        logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")

        if from_data_point is not None:
            return df_steps
        else:
            self.cells[dataset_number].steps = df_steps
            return self

    def select_steps(self, step_dict, append_df=False, dataset_number=None):
        """Select steps (not documented yet)."""
        raise DeprecatedFeature

    def _select_step(self, cycle, step, dataset_number=None):
        # TODO: @jepe - insert sub_step here
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        test = self.cells[dataset_number]

        # check if columns exist
        c_txt = self.headers_normal.cycle_index_txt
        s_txt = self.headers_normal.step_index_txt
        y_txt = self.headers_normal.voltage_txt
        x_txt = self.headers_normal.discharge_capacity_txt  # jepe fix

        # no_cycles=np.amax(test.raw[c_txt])
        # print d.columns

        if not any(test.raw.columns == c_txt):
            logging.info("ERROR - cannot find %s" % c_txt)
            sys.exit(-1)
        if not any(test.raw.columns == s_txt):
            logging.info("ERROR - cannot find %s" % s_txt)
            sys.exit(-1)

        # logging.debug(f"selecting cycle {cycle} step {step}")
        v = test.raw[(test.raw[c_txt] == cycle) & (test.raw[s_txt] == step)]

        if self.is_empty(v):
            logging.debug("empty dataframe")
            return None
        else:
            return v

    def populate_step_dict(self, step, dataset_number=None):
        """Returns a dict with cycle numbers as keys
        and corresponding steps (list) as values."""
        raise DeprecatedFeature

    def _export_cycles(
        self,
        dataset_number,
        setname=None,
        sep=None,
        outname=None,
        shifted=False,
        method=None,
        shift=0.0,
        last_cycle=None,
    ):
        # export voltage - capacity curves to .csv file

        logging.debug("START exporing cycles")
        time_00 = time.time()
        lastname = "_cycles.csv"
        if sep is None:
            sep = self.sep
        if outname is None:
            outname = setname + lastname

        logging.debug(f"outname: {outname}")

        list_of_cycles = self.get_cycle_numbers(dataset_number=dataset_number)
        if last_cycle is not None:
            list_of_cycles = [c for c in list_of_cycles if c <= int(last_cycle)]
            logging.debug(f"only processing up to cycle {last_cycle}")
            logging.debug(f"you have {len(list_of_cycles)}" f"cycles to process")
        out_data = []
        c = None
        if not method:
            method = "back-and-forth"
        if shifted:
            method = "back-and-forth"
            shift = 0.0
            _last = 0.0
        logging.debug(f"number of cycles: {len(list_of_cycles)}")
        for cycle in list_of_cycles:
            try:
                if shifted and c is not None:
                    shift = _last
                    # print(f"shifted = {shift}, first={_first}")
                df = self.get_cap(
                    cycle, dataset_number=dataset_number, method=method, shift=shift
                )
                if df.empty:
                    logging.debug("NoneType from get_cap")
                else:
                    c = df["capacity"]
                    v = df["voltage"]

                    _last = c.iat[-1]
                    _first = c.iat[0]

                    c = c.tolist()
                    v = v.tolist()
                    header_x = "cap cycle_no %i" % cycle
                    header_y = "voltage cycle_no %i" % cycle
                    c.insert(0, header_x)
                    v.insert(0, header_y)
                    out_data.append(c)
                    out_data.append(v)
                    # txt = "extracted cycle %i" % cycle
                    # logging.debug(txt)
            except IndexError as e:
                txt = "Could not extract cycle %i" % cycle
                logging.info(txt)
                logging.debug(e)

        # Saving cycles in one .csv file (x,y,x,y,x,y...)
        # print "saving the file with delimiter '%s' " % (sep)
        logging.debug("writing cycles to file")
        with open(outname, "w", newline="") as f:
            writer = csv.writer(f, delimiter=sep)
            writer.writerows(itertools.zip_longest(*out_data))
            # star (or asterix) means transpose (writing cols instead of rows)

        logging.info(f"The file {outname} was created")
        logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")
        logging.debug("END exporting cycles")

    # TODO: remove this
    def _export_cycles_old(
        self,
        dataset_number,
        setname=None,
        sep=None,
        outname=None,
        shifted=False,
        method=None,
        shift=0.0,
        last_cycle=None,
    ):
        # export voltage - capacity curves to .csv file

        logging.debug("*** OLD EXPORT-CYCLES METHOD***")
        lastname = "_cycles.csv"
        if sep is None:
            sep = self.sep
        if outname is None:
            outname = setname + lastname

        list_of_cycles = self.get_cycle_numbers(dataset_number=dataset_number)
        logging.debug(f"you have {len(list_of_cycles)} cycles")
        if last_cycle is not None:
            list_of_cycles = [c for c in list_of_cycles if c <= int(last_cycle)]
            logging.debug(f"only processing up to cycle {last_cycle}")
            logging.debug(f"you have {len(list_of_cycles)}" f"cycles to process")
        out_data = []
        c = None
        if not method:
            method = "back-and-forth"
        if shifted:
            method = "back-and-forth"
            shift = 0.0
            _last = 0.0

        for cycle in list_of_cycles:
            try:
                if shifted and c is not None:
                    shift = _last
                    # print(f"shifted = {shift}, first={_first}")
                c, v = self.get_cap(
                    cycle, dataset_number=dataset_number, method=method, shift=shift
                )
                if c is None:
                    logging.debug("NoneType from get_cap")
                else:
                    _last = c.iat[-1]
                    _first = c.iat[0]

                    c = c.tolist()
                    v = v.tolist()
                    header_x = "cap cycle_no %i" % cycle
                    header_y = "voltage cycle_no %i" % cycle
                    c.insert(0, header_x)
                    v.insert(0, header_y)
                    out_data.append(c)
                    out_data.append(v)
                    # txt = "extracted cycle %i" % cycle
                    # logging.debug(txt)
            except IndexError as e:
                txt = "Could not extract cycle %i" % cycle
                logging.info(txt)
                logging.debug(e)

        # Saving cycles in one .csv file (x,y,x,y,x,y...)
        # print "saving the file with delimiter '%s' " % (sep)
        logging.debug("writing cycles to file")
        with open(outname, "w", newline="") as f:
            writer = csv.writer(f, delimiter=sep)
            writer.writerows(itertools.zip_longest(*out_data))
            # star (or asterix) means transpose (writing cols instead of rows)
        logging.info(f"The file {outname} was created")

    def _export_normal(self, data, setname=None, sep=None, outname=None):
        time_00 = time.time()
        lastname = "_normal.csv"
        if sep is None:
            sep = self.sep
        if outname is None:
            outname = setname + lastname
        txt = outname
        try:
            data.raw.to_csv(outname, sep=sep)
            txt += " OK"
        except Exception as e:
            txt += " Could not save it!"
            logging.debug(e)
            warnings.warn(f"Unhandled exception raised: {e}")
        logging.info(txt)
        logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")

    def _export_stats(self, data, setname=None, sep=None, outname=None):
        time_00 = time.time()
        lastname = "_stats.csv"
        if sep is None:
            sep = self.sep
        if outname is None:
            outname = setname + lastname
        txt = outname
        try:
            data.summary.to_csv(outname, sep=sep)
            txt += " OK"
        except Exception as e:
            txt += " Could not save it!"
            logging.debug(e)
            warnings.warn(f"Unhandled exception raised: {e}")
        logging.info(txt)
        logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")

    def _export_steptable(self, data, setname=None, sep=None, outname=None):
        time_00 = time.time()
        lastname = "_steps.csv"
        if sep is None:
            sep = self.sep
        if outname is None:
            outname = setname + lastname
        txt = outname
        try:
            data.steps.to_csv(outname, sep=sep)
            txt += " OK"
        except Exception as e:
            txt += " Could not save it!"
            logging.debug(e)
            warnings.warn(f"Unhandled exception raised: {e}")
        logging.info(txt)
        logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")

    def to_csv(
        self,
        datadir=None,
        sep=None,
        cycles=False,
        raw=True,
        summary=True,
        shifted=False,
        method=None,
        shift=0.0,
        last_cycle=None,
    ):
        """Saves the data as .csv file(s).

        Args:
            datadir: folder where to save the data (uses current folder if not
                given).
            sep: the separator to use in the csv file
                (defaults to CellpyData.sep).
            cycles: (bool) export voltage-capacity curves if True.
            raw: (bool) export raw-data if True.
            summary: (bool) export summary if True.
            shifted (bool): export with cumulated shift.
            method (string): how the curves are given
                "back-and-forth" - standard back and forth; discharge
                    (or charge) reversed from where charge (or
                    discharge) ends.
                "forth" - discharge (or charge) continues along x-axis.
                "forth-and-forth" - discharge (or charge) also starts at 0 (or
                    shift if not shift=0.0)
            shift: start-value for charge (or discharge)
            last_cycle: process only up to this cycle (if not None).

        Returns: Nothing

        """

        if sep is None:
            sep = self.sep

        logging.debug("saving to csv")

        dataset_number = -1
        for data in self.cells:
            dataset_number += 1
            if not self._is_not_empty_dataset(data):
                logging.info("to_csv -")
                logging.info("empty test [%i]" % dataset_number)
                logging.info("not saved!")
            else:
                if isinstance(data.loaded_from, (list, tuple)):
                    txt = "merged file"
                    txt += "using first file as basename"
                    logging.debug(txt)
                    no_merged_sets = len(data.loaded_from)
                    no_merged_sets = "_merged_" + str(no_merged_sets).zfill(3)
                    filename = data.loaded_from[0]
                else:
                    filename = data.loaded_from
                    no_merged_sets = ""
                firstname, extension = os.path.splitext(filename)
                firstname += no_merged_sets
                if datadir:
                    firstname = os.path.join(datadir, os.path.basename(firstname))

                if raw:
                    outname_normal = firstname + "_normal.csv"
                    self._export_normal(data, outname=outname_normal, sep=sep)
                    if data.steps_made is True:
                        outname_steps = firstname + "_steps.csv"
                        self._export_steptable(data, outname=outname_steps, sep=sep)
                    else:
                        logging.debug("steps_made is not True")

                if summary:
                    outname_stats = firstname + "_stats.csv"
                    self._export_stats(data, outname=outname_stats, sep=sep)

                if cycles:
                    outname_cycles = firstname + "_cycles.csv"
                    self._export_cycles(
                        outname=outname_cycles,
                        dataset_number=dataset_number,
                        sep=sep,
                        shifted=shifted,
                        method=method,
                        shift=shift,
                        last_cycle=last_cycle,
                    )

    def save(
        self,
        filename,
        dataset_number=None,
        force=False,
        overwrite=True,
        extension="h5",
        ensure_step_table=None,
    ):
        """Save the data structure to cellpy-format.

        Args:
            filename: (str or pathlib.Path) the name you want to give the file
            dataset_number: (int) if you have several datasets, chose the one
                you want (probably leave this untouched)
            force: (bool) save a file even if the summary is not made yet
                (not recommended)
            overwrite: (bool) save the new version of the file even if old one
                exists.
            extension: (str) filename extension.
            ensure_step_table: (bool) make step-table if missing.

        Returns: Nothing at all.
        """
        logging.debug(f"Trying to save cellpy-file to {filename}")
        logging.info(f" -> {filename}")

        if ensure_step_table is None:
            ensure_step_table = self.ensure_step_table

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            logging.info("Saving test failed!")
            self._report_empty_dataset()
            return

        test = self.get_cell(dataset_number)
        summary_made = test.summary_made

        if not summary_made and not force:
            logging.info("You should not save datasets without making a summary first!")
            logging.info("If you really want to do it, use save with force=True")
            return

        step_table_made = test.steps_made
        if not step_table_made and not force and not ensure_step_table:
            logging.info(
                "You should not save datasets without making a step-table first!"
            )
            logging.info("If you really want to do it, use save with force=True")
            return

        outfile_all = Path(filename)
        if not outfile_all.suffix:
            outfile_all = outfile_all.with_suffix(f".{extension}")

        if os.path.isfile(outfile_all):
            logging.debug("Outfile exists")
            if overwrite:
                logging.debug("overwrite = True")
                try:
                    os.remove(outfile_all)
                except PermissionError as e:
                    logging.critical("Could not over write old file")
                    logging.info(e)
                    return
            else:
                logging.critical("Save (hdf5): file exist - did not save", end=" ")
                logging.info(outfile_all)
                return

        if ensure_step_table:
            logging.debug("ensure_step_table is on")
            if not test.steps_made:
                logging.debug("save: creating step table")
                self.make_step_table(dataset_number=dataset_number)

        # This method can probably be updated using pandas transpose trick
        logging.debug("trying to make infotable")
        infotbl, fidtbl = self._create_infotable(dataset_number=dataset_number)

        root = prms._cellpyfile_root

        if CELLPY_FILE_VERSION > 4:
            raw_dir = prms._cellpyfile_raw
            step_dir = prms._cellpyfile_step
            summary_dir = prms._cellpyfile_summary
            meta_dir = "/info"
            fid_dir = prms._cellpyfile_fid

        else:
            raw_dir = "/raw"
            step_dir = "/step_table"
            summary_dir = "/dfsummary"
            meta_dir = "/info"
            fid_dir = "/fidtable"

        logging.debug("trying to save to hdf5")
        txt = "\nHDF5 file: %s" % outfile_all
        logging.debug(txt)

        warnings.simplefilter("ignore", PerformanceWarning)
        try:
            with pickle_protocol(4):
                store = pd.HDFStore(
                    outfile_all,
                    complib=prms._cellpyfile_complib,
                    complevel=prms._cellpyfile_complevel,
                )

                logging.debug("trying to put raw data")

                logging.debug(" - lets set Data_Point as index")

                hdr_data_point = self.headers_normal.data_point_txt

                if test.raw.index.name != hdr_data_point:
                    test.raw = test.raw.set_index(hdr_data_point, drop=False)

                store.put(root + raw_dir, test.raw, format=prms._cellpyfile_raw_format)
                logging.debug(" raw -> hdf5 OK")

                logging.debug("trying to put summary")
                store.put(
                    root + summary_dir,
                    test.summary,
                    format=prms._cellpyfile_summary_format,
                )
                logging.debug(" summary -> hdf5 OK")

                logging.debug("trying to put meta data")
                store.put(
                    root + meta_dir, infotbl, format=prms._cellpyfile_infotable_format
                )
                logging.debug(" meta -> hdf5 OK")

                logging.debug("trying to put fidtable")
                store.put(
                    root + fid_dir, fidtbl, format=prms._cellpyfile_fidtable_format
                )
                logging.debug(" fid -> hdf5 OK")

                logging.debug("trying to put step")
                try:
                    store.put(
                        root + step_dir,
                        test.steps,
                        format=prms._cellpyfile_stepdata_format,
                    )
                    logging.debug(" step -> hdf5 OK")
                except TypeError:
                    test = self._fix_dtype_step_table(test)
                    store.put(
                        root + step_dir,
                        test.steps,
                        format=prms._cellpyfile_stepdata_format,
                    )
                    logging.debug(" fixed step -> hdf5 OK")

                # creating indexes
                # hdr_data_point = self.headers_normal.data_point_txt
                # hdr_cycle_steptable = self.headers_step_table.cycle
                # hdr_cycle_normal = self.headers_normal.cycle_index_txt

                # store.create_table_index(root + "/raw", columns=[hdr_data_point],
                #                          optlevel=9, kind='full')
        finally:
            store.close()
        logging.debug(" all -> hdf5 OK")
        warnings.simplefilter("default", PerformanceWarning)
        # del store

    # --------------helper-functions--------------------------------------------
    def _fix_dtype_step_table(self, dataset):
        hst = get_headers_step_table()
        try:
            cols = dataset.steps.columns
        except AttributeError:
            logging.info("Could not extract columns from steps")
            return
        for col in cols:
            if col not in [hst.cycle, hst.sub_step, hst.info]:
                dataset.steps[col] = dataset.steps[col].apply(pd.to_numeric)
            else:
                dataset.steps[col] = dataset.steps[col].astype("str")
        return dataset

    # TODO: check if this is useful and if it is rename, if not delete
    def _cap_mod_summary(self, summary, capacity_modifier="reset"):
        # modifies the summary table
        time_00 = time.time()
        discharge_title = self.headers_normal.discharge_capacity_txt
        charge_title = self.headers_normal.charge_capacity_txt
        chargecap = 0.0
        dischargecap = 0.0

        # TODO: @jepe - use pd.loc[row,column]

        if capacity_modifier == "reset":

            for index, row in summary.iterrows():
                dischargecap_2 = row[discharge_title]
                summary.loc[index, discharge_title] = dischargecap_2 - dischargecap
                dischargecap = dischargecap_2
                chargecap_2 = row[charge_title]
                summary.loc[index, charge_title] = chargecap_2 - chargecap
                chargecap = chargecap_2
        else:
            raise NotImplementedError

        logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")
        return summary

    # TODO: check if this is useful and if it is rename, if not delete
    def _cap_mod_normal(
        self, dataset_number=None, capacity_modifier="reset", allctypes=True
    ):
        # modifies the normal table
        time_00 = time.time()
        logging.debug("Not properly checked yet! Use with caution!")
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        cycle_index_header = self.headers_normal.cycle_index_txt
        step_index_header = self.headers_normal.step_index_txt
        discharge_index_header = self.headers_normal.discharge_capacity_txt
        discharge_energy_index_header = self.headers_normal.discharge_energy_txt
        charge_index_header = self.headers_normal.charge_capacity_txt
        charge_energy_index_header = self.headers_normal.charge_energy_txt

        raw = self.cells[dataset_number].raw

        chargecap = 0.0
        dischargecap = 0.0

        if capacity_modifier == "reset":
            # discharge cycles
            no_cycles = np.amax(raw[cycle_index_header])
            for j in range(1, no_cycles + 1):
                cap_type = "discharge"
                e_header = discharge_energy_index_header
                cap_header = discharge_index_header
                discharge_cycles = self.get_step_numbers(
                    steptype=cap_type,
                    allctypes=allctypes,
                    cycle_number=j,
                    dataset_number=dataset_number,
                )

                steps = discharge_cycles[j]
                txt = "Cycle  %i (discharge):  " % j
                logging.debug(txt)
                # TODO: @jepe - use pd.loc[row,column] e.g. pd.loc[:,"charge_cap"]
                # for col or pd.loc[(pd.["step"]==1),"x"]
                selection = (raw[cycle_index_header] == j) & (
                    raw[step_index_header].isin(steps)
                )
                c0 = raw[selection].iloc[0][cap_header]
                e0 = raw[selection].iloc[0][e_header]
                raw.loc[selection, cap_header] = raw.loc[selection, cap_header] - c0
                raw.loc[selection, e_header] = raw.loc[selection, e_header] - e0

                cap_type = "charge"
                e_header = charge_energy_index_header
                cap_header = charge_index_header
                charge_cycles = self.get_step_numbers(
                    steptype=cap_type,
                    allctypes=allctypes,
                    cycle_number=j,
                    dataset_number=dataset_number,
                )
                steps = charge_cycles[j]
                txt = "Cycle  %i (charge):  " % j
                logging.debug(txt)

                selection = (raw[cycle_index_header] == j) & (
                    raw[step_index_header].isin(steps)
                )

                if any(selection):
                    c0 = raw[selection].iloc[0][cap_header]
                    e0 = raw[selection].iloc[0][e_header]
                    raw.loc[selection, cap_header] = raw.loc[selection, cap_header] - c0
                    raw.loc[selection, e_header] = raw.loc[selection, e_header] - e0
        logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")

    def get_number_of_tests(self):
        return self.number_of_datasets

    def get_mass(self, set_number=None):
        set_number = self._validate_dataset_number(set_number)
        if set_number is None:
            self._report_empty_dataset()
            return
        if not self.cells[set_number].mass_given:
            logging.info("No mass")
        return self.cells[set_number].mass

    def get_cell(self, n=0):
        # TODO: remove me
        return self.cells[n]

    def sget_voltage(self, cycle, step, dataset_number=None):
        """Returns voltage for cycle, step.

        Convenience function; same as issuing
           raw[(raw[cycle_index_header] == cycle) &
                 (raw[step_index_header] == step)][voltage_header]

        Args:
            cycle: cycle number
            step: step number
            dataset_number: the dataset number (automatic selection if None)

        Returns:
            pandas.Series or None if empty
        """
        header = self.headers_normal.voltage_txt
        return self._sget(
            cycle, step, header, usteps=False, dataset_number=dataset_number
        )

    def sget_current(self, cycle, step, dataset_number=None):
        """Returns current for cycle, step.

                Convenience function; same as issuing
                   raw[(raw[cycle_index_header] == cycle) &
                         (raw[step_index_header] == step)][current_header]

                Args:
                    cycle: cycle number
                    step: step number
                    dataset_number: the dataset number (automatic selection if None)

                Returns:
                    pandas.Series or None if empty
                """
        header = self.headers_normal.current_txt
        return self._sget(
            cycle, step, header, usteps=False, dataset_number=dataset_number
        )

    def get_voltage(self, cycle=None, dataset_number=None, full=True):
        """Returns voltage (in V).

        Args:
            cycle: cycle number (all cycles if None)
            dataset_number: first dataset if None
            full: valid only for cycle=None (i.e. all cycles), returns the full
               pandas.Series if True, else a list of pandas.Series

        Returns:
            pandas.Series (or list of pandas.Series if cycle=None og full=False)
        """

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        cycle_index_header = self.headers_normal.cycle_index_txt
        voltage_header = self.headers_normal.voltage_txt
        # step_index_header  = self.headers_normal.step_index_txt

        test = self.cells[dataset_number].raw
        if cycle:
            logging.debug("getting voltage curve for cycle")
            c = test[(test[cycle_index_header] == cycle)]
            if not self.is_empty(c):
                v = c[voltage_header]
                return v
        else:
            if not full:
                logging.debug("getting list of voltage-curves for all cycles")
                v = []
                no_cycles = np.amax(test[cycle_index_header])
                for j in range(1, no_cycles + 1):
                    txt = "Cycle  %i:  " % j
                    logging.debug(txt)
                    c = test[(test[cycle_index_header] == j)]
                    v.append(c[voltage_header])
            else:
                logging.debug("getting frame of all voltage-curves")
                v = test[voltage_header]
            return v

    def get_current(self, cycle=None, dataset_number=None, full=True):
        """Returns current (in mA).

        Args:
            cycle: cycle number (all cycles if None)
            dataset_number: first dataset if None
            full: valid only for cycle=None (i.e. all cycles), returns the full
               pandas.Series if True, else a list of pandas.Series

        Returns:
            pandas.Series (or list of pandas.Series if cycle=None og full=False)
        """

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        cycle_index_header = self.headers_normal.cycle_index_txt
        current_header = self.headers_normal.current_txt
        # step_index_header  = self.headers_normal.step_index_txt

        test = self.cells[dataset_number].raw
        if cycle:
            logging.debug(f"getting current for cycle {cycle}")
            c = test[(test[cycle_index_header] == cycle)]
            if not self.is_empty(c):
                v = c[current_header]
                return v
        else:
            if not full:
                logging.debug("getting a list of current-curves for all cycles")
                v = []
                no_cycles = np.amax(test[cycle_index_header])
                for j in range(1, no_cycles + 1):
                    txt = "Cycle  %i:  " % j
                    logging.debug(txt)
                    c = test[(test[cycle_index_header] == j)]
                    v.append(c[current_header])
            else:
                logging.debug("getting all current-curves ")
                v = test[current_header]
            return v

    def sget_steptime(self, cycle, step, dataset_number=None):
        """Returns step time for cycle, step.

        Convenience function; same as issuing
           raw[(raw[cycle_index_header] == cycle) &
                 (raw[step_index_header] == step)][step_time_header]

        Args:
            cycle: cycle number
            step: step number
            dataset_number: the dataset number (automatic selection if None)

        Returns:
            pandas.Series or None if empty
        """

        header = self.headers_normal.step_time_txt
        return self._sget(
            cycle, step, header, usteps=False, dataset_number=dataset_number
        )

    def _sget(self, cycle, step, header, usteps=False, dataset_number=None):
        dataset_number = self._validate_dataset_number(dataset_number)
        logging.debug(f"searching for {header}")
        if dataset_number is None:
            self._report_empty_dataset()
            return

        cycle_index_header = self.headers_normal.cycle_index_txt
        step_index_header = self.headers_normal.step_index_txt

        if usteps:
            print("Using sget for usteps is not supported yet.")
            print("I encourage you to work with the DataFrames directly instead.")
            print(" - look up the 'ustep' in the steps DataFrame")
            print(" - get the start and end 'data_point'")
            print(" - look up the start and end 'data_point' in the raw DataFrame")
            print("")
            print(
                "(Just remember to run make_step_table with the all_steps set to True before you do it)"
            )
            return

        test = self.cells[dataset_number].raw

        if not isinstance(step, (list, tuple)):
            step = [step]

        return test.loc[
            (test[cycle_index_header] == cycle) & (test[step_index_header].isin(step)),
            header,
        ].reset_index(drop=True)

    def sget_timestamp(self, cycle, step, dataset_number=None):
        """Returns timestamp for cycle, step.

        Convenience function; same as issuing
           raw[(raw[cycle_index_header] == cycle) &
                 (raw[step_index_header] == step)][timestamp_header]

        Args:
            cycle: cycle number
            step: step number (can be a list of several step numbers)
            dataset_number: the dataset number (automatic selection if None)

        Returns:
            pandas.Series
        """

        header = self.headers_normal.test_time_txt
        return self._sget(
            cycle, step, header, usteps=False, dataset_number=dataset_number
        )

    def sget_step_numbers(self, cycle, step, dataset_number=None):
        """Returns step number for cycle, step.

        Convenience function; same as issuing
           raw[(raw[cycle_index_header] == cycle) &
                 (raw[step_index_header] == step)][step_index_header]

        Args:
            cycle: cycle number
            step: step number (can be a list of several step numbers)
            dataset_number: the dataset number (automatic selection if None)

        Returns:
            pandas.Series
        """

        header = self.headers_normal.step_index_txt
        return self._sget(
            cycle, step, header, usteps=False, dataset_number=dataset_number
        )

    def get_datetime(self, cycle=None, dataset_number=None, full=True):

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        cycle_index_header = self.headers_normal.cycle_index_txt
        datetime_header = self.headers_normal.datetime_txt

        v = pd.Series()
        test = self.cells[dataset_number].raw
        if cycle:
            c = test[(test[cycle_index_header] == cycle)]
            if not self.is_empty(c):
                v = c[datetime_header]

        else:
            if not full:
                logging.debug("getting datetime for all cycles")
                v = []
                cycles = self.get_cycle_numbers()
                for j in cycles:
                    txt = "Cycle  %i:  " % j
                    logging.debug(txt)
                    c = test[(test[cycle_index_header] == j)]
                    v.append(c[datetime_header])
            else:
                logging.debug("returning full datetime col")
                v = test[datetime_header]
        return v

    def get_timestamp(
        self, cycle=None, dataset_number=None, in_minutes=False, full=True
    ):
        """Returns timestamps (in sec or minutes (if in_minutes==True)).

        Args:
            cycle: cycle number (all if None)
            dataset_number: first dataset if None
            in_minutes: return values in minutes instead of seconds if True
            full: valid only for cycle=None (i.e. all cycles), returns the full
               pandas.Series if True, else a list of pandas.Series

        Returns:
            pandas.Series (or list of pandas.Series if cycle=None og full=False)
        """

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        cycle_index_header = self.headers_normal.cycle_index_txt
        timestamp_header = self.headers_normal.test_time_txt

        v = pd.Series()
        test = self.cells[dataset_number].raw
        if cycle:
            c = test[(test[cycle_index_header] == cycle)]
            if not self.is_empty(c):
                v = c[timestamp_header]

        else:
            if not full:
                logging.debug("getting timestapm for all cycles")
                v = []
                cycles = self.get_cycle_numbers()
                for j in cycles:
                    txt = "Cycle  %i:  " % j
                    logging.debug(txt)
                    c = test[(test[cycle_index_header] == j)]
                    v.append(c[timestamp_header])
            else:
                logging.debug("returning full timestamp col")
                v = test[timestamp_header]
                if in_minutes and v is not None:
                    v /= 60.0
        if in_minutes and v is not None:
            v /= 60.0
        return v

    def get_dcap(self, cycle=None, dataset_number=None, converter=None, **kwargs):
        """Returns discharge_capacity (in mAh/g), and voltage."""

        #  TODO - jepe: should return a DataFrame as default
        #   but remark that we then have to update e.g. batch_helpers.py
        #  TODO - jepe: change needed: should not use
        #   dataset_number as parameter

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        if converter is None:
            converter = self.get_converter_to_specific()

        dc, v = self._get_cap(
            cycle, dataset_number, "discharge", converter=converter, **kwargs
        )
        return dc, v

    def get_ccap(self, cycle=None, dataset_number=None, converter=None, **kwargs):
        """Returns charge_capacity (in mAh/g), and voltage."""

        #  TODO - jepe: should return a DataFrame as default
        #   but remark that we then have to update e.g. batch_helpers.py
        #  TODO - jepe: change needed: should not use
        #   dataset_number as parameter

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        if converter is None:
            converter = self.get_converter_to_specific()
        cc, v = self._get_cap(
            cycle, dataset_number, "charge", converter=converter, **kwargs
        )
        return cc, v

    def get_cap(
        self,
        cycle=None,
        dataset_number=None,
        method="back-and-forth",
        insert_nan=None,
        shift=0.0,
        categorical_column=False,
        label_cycle_number=False,
        split=False,
        interpolated=False,
        dx=0.1,
        number_of_points=None,
        ignore_errors=True,
        dynamic=False,
        inter_cycle_shift=True,
        **kwargs,
    ):
        """Gets the capacity for the run.

        Args:
            cycle (int): cycle number.
            method (string): how the curves are given
                "back-and-forth" - standard back and forth; discharge
                    (or charge) reversed from where charge (or discharge) ends.
                "forth" - discharge (or charge) continues along x-axis.
                "forth-and-forth" - discharge (or charge) also starts at 0
                    (or shift if not shift=0.0)
            insert_nan (bool): insert a np.nan between the charge and discharge curves.
                Defaults to True for "forth-and-forth", else False
            shift: start-value for charge (or discharge) (typically used when
                plotting shifted-capacity).
            categorical_column: add a categorical column showing if it is
                charge or discharge.
            dataset_number (int): test number (default first)
                (usually not used).
            label_cycle_number (bool): add column for cycle number
                (tidy format).
            split (bool): return a list of c and v instead of the default
                that is to return them combined in a DataFrame. This is only
                possible for some specific combinations of options (neither
                categorical_column=True or label_cycle_number=True are
                allowed).
            interpolated (bool): set to True if you would like to get
                interpolated data (typically if you want to save disk space
                or memory). Defaults to False.
            dx (float): the step used when interpolating.
            number_of_points (int): number of points to use (over-rides dx)
                for interpolation (i.e. the length of the interpolated data).
            ignore_errors (bool): don't break out of loop if an error occurs.
            dynamic: for dynamic retrieving data from cellpy-file.
                [NOT IMPLEMENTED YET]
            inter_cycle_shift (bool): cumulative shifts between consecutive
                cycles. Defaults to True.

        Returns:
            pandas.DataFrame ((cycle) voltage, capacity, (direction (-1, 1)))
                unless split is explicitly set to True. Then it returns a tuple
                with capacity (mAh/g) and voltage.
        """

        # TODO: allow for fixing the interpolation range (so that it is possible
        #   to run the function on several cells and have a common x-axis

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return

        # if cycle is not given, then this function should
        # iterate through cycles
        if cycle is None:
            cycle = self.get_cycle_numbers()

        if not isinstance(cycle, collections.abc.Iterable):
            cycle = [cycle]

        if split and not (categorical_column or label_cycle_number):
            return_dataframe = False
        else:
            return_dataframe = True

        method = method.lower()
        if method not in ["back-and-forth", "forth", "forth-and-forth"]:
            warnings.warn(
                f"method '{method}' is not a valid option "
                f"- setting to 'back-and-forth'"
            )
            method = "back-and-forth"

        if insert_nan is None:
            if method == "forth-and-forth":
                insert_nan = True
            else:
                insert_nan = False

        capacity = None
        voltage = None
        specific_converter = self.get_converter_to_specific()
        cycle_df = pd.DataFrame()

        initial = True
        for current_cycle in cycle:
            error = False
            try:
                cc, cv = self.get_ccap(
                    current_cycle,
                    dataset_number,
                    converter=specific_converter,
                    **kwargs,
                )
                dc, dv = self.get_dcap(
                    current_cycle,
                    dataset_number,
                    converter=specific_converter,
                    **kwargs,
                )

            except NullData as e:
                error = True
                logging.debug(e)
                if not ignore_errors:
                    logging.debug("breaking out of loop")
                    break
            if not error:
                if cc.empty:
                    logging.debug("get_ccap returns empty cc Series")

                if dc.empty:
                    logging.debug("get_ccap returns empty dc Series")

                if initial:
                    prev_end = shift
                    initial = False
                if self.cycle_mode == "anode":
                    first_interpolation_direction = -1
                    _first_step_c = dc
                    _first_step_v = dv
                    last_interpolation_direction = 1
                    _last_step_c = cc
                    _last_step_v = cv
                else:
                    first_interpolation_direction = 1
                    _first_step_c = cc
                    _first_step_v = cv
                    last_interpolation_direction = -1
                    _last_step_c = dc
                    _last_step_v = dv

                if method == "back-and-forth":
                    # _last = np.amax(_first_step_c)
                    _last = _first_step_c.iat[-1]
                    # should change amax to last point
                    _first = None
                    _new_first = None
                    if not inter_cycle_shift:
                        prev_end = 0.0
                    if _last_step_c is not None:
                        _last_step_c = _last - _last_step_c + prev_end
                    else:
                        logging.debug("no last charge step found")
                    if _first_step_c is not None:
                        _first = _first_step_c.iat[0]
                        _first_step_c += prev_end
                        _new_first = _first_step_c.iat[0]
                    else:
                        logging.debug("probably empty (_first_step_c is None)")
                    # logging.debug(f"current shifts used: prev_end = {prev_end}")
                    # logging.debug(f"shifting start from {_first} to "
                    #                   f"{_new_first}")

                    # prev_end = np.amin(_last_step_c)
                    prev_end = _last_step_c.iat[-1]
                elif method == "forth":
                    # _last = np.amax(_first_step_c)
                    _last = _first_step_c.iat[-1]
                    if _last_step_c is not None:
                        _last_step_c += _last + prev_end
                    else:
                        logging.debug("no last charge step found")
                    if _first_step_c is not None:
                        _first_step_c += prev_end
                    else:
                        logging.debug("no first charge step found")

                    # prev_end = np.amax(_last_step_c)
                    prev_end = _last_step_c.iat[-1]

                elif method == "forth-and-forth":
                    if _last_step_c is not None:
                        _last_step_c += shift
                    else:
                        logging.debug("no last charge step found")
                    if _first_step_c is not None:
                        _first_step_c += shift
                    else:
                        logging.debug("no first charge step found")

                if return_dataframe:

                    try:
                        _first_df = pd.DataFrame(
                            {"voltage": _first_step_v, "capacity": _first_step_c,}
                        )
                        if interpolated:
                            _first_df = interpolate_y_on_x(
                                _first_df,
                                y="capacity",
                                x="voltage",
                                dx=dx,
                                number_of_points=number_of_points,
                                direction=first_interpolation_direction,
                            )
                        if insert_nan:
                            _nan = pd.DataFrame(
                                {"capacity": [np.nan], "voltage": [np.nan]}
                            )
                            _first_df = _first_df.append(_nan)
                        if categorical_column:
                            _first_df["direction"] = -1

                        _last_df = pd.DataFrame(
                            {
                                "voltage": _last_step_v.values,
                                "capacity": _last_step_c.values,
                            }
                        )
                        if interpolated:
                            _last_df = interpolate_y_on_x(
                                _last_df,
                                y="capacity",
                                x="voltage",
                                dx=dx,
                                number_of_points=number_of_points,
                                direction=last_interpolation_direction,
                            )
                        if insert_nan:
                            _last_df = _last_df.append(_nan)
                        if categorical_column:
                            _last_df["direction"] = 1

                    except AttributeError:
                        logging.info(f"Could not extract cycle {current_cycle}")
                    else:
                        c = pd.concat([_first_df, _last_df], axis=0)
                        if label_cycle_number:
                            c.insert(0, "cycle", current_cycle)
                            # c["cycle"] = current_cycle
                            # c = c[["cycle", "voltage", "capacity", "direction"]]
                        if cycle_df.empty:
                            cycle_df = c
                        else:
                            cycle_df = pd.concat([cycle_df, c], axis=0)

                else:
                    logging.warning("returning non-dataframe")
                    c = pd.concat([_first_step_c, _last_step_c], axis=0)
                    v = pd.concat([_first_step_v, _last_step_v], axis=0)

                    capacity = pd.concat([capacity, c], axis=0)
                    voltage = pd.concat([voltage, v], axis=0)

        if return_dataframe:
            return cycle_df
        else:
            return capacity, voltage

    def _get_cap(
        self,
        cycle=None,
        dataset_number=None,
        cap_type="charge",
        trim_taper_steps=None,
        steps_to_skip=None,
        steptable=None,
        converter=None,
    ):
        # used when extracting capacities (get_ccap, get_dcap)
        # TODO: @jepe - does not allow for constant voltage yet?
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        test = self.cells[
            dataset_number
        ]  # not used anymore - will be removed when we skip several cells option

        if cap_type == "charge_capacity":
            cap_type = "charge"
        elif cap_type == "discharge_capacity":
            cap_type = "discharge"

        cycles = self.get_step_numbers(
            steptype=cap_type,
            allctypes=False,
            cycle_number=cycle,
            dataset_number=dataset_number,
            trim_taper_steps=trim_taper_steps,
            steps_to_skip=steps_to_skip,
            steptable=steptable,
        )

        if cap_type == "charge":
            column_txt = self.headers_normal.charge_capacity_txt
        else:
            column_txt = self.headers_normal.discharge_capacity_txt
        if cycle:
            steps = cycles[cycle]
            _v = []
            _c = []

            for step in sorted(steps):
                selected_step = self._select_step(cycle, step, dataset_number)
                if not self.is_empty(selected_step):
                    _v.append(selected_step[self.headers_normal.voltage_txt])
                    _c.append(selected_step[column_txt] * converter)
            try:
                voltage = pd.concat(_v, axis=0)
                cap = pd.concat(_c, axis=0)
            except:
                logging.debug("could not find any steps for this cycle")
                raise NullData(f"no steps found (c:{cycle} s:{step} type:{cap_type})")
        else:
            # get all the discharge cycles
            # this is a dataframe filtered on step and cycle
            # This functionality is not crucial since get_cap (that uses this method) has it
            # (but it might be nice to improve performance)
            raise NotImplementedError(
                "Not yet possible to extract without giving cycle numbers (use get_cap instead)"
            )

        return cap, voltage

    def get_ocv(
        self,
        cycles=None,
        direction="up",
        remove_first=False,
        interpolated=False,
        dx=None,
        number_of_points=None,
    ):

        """get the open circuit voltage relaxation curves.

        Args:
            cycles (list of ints or None): the cycles to extract from
                (selects all if not given).
            direction ("up", "down", or "both"): extract only relaxations that
                is performed during discharge for "up" (because then the
                voltage relaxes upwards) etc.
            remove_first: remove the first relaxation curve (typically,
                the first curve is from the initial rest period between
                assembling the cell to the actual testing/cycling starts)
            interpolated (bool): set to True if you want the data to be
                interpolated (e.g. for creating smaller files)
            dx (float): the step used when interpolating.
            number_of_points (int): number of points to use (over-rides dx)
                for interpolation (i.e. the length of the interpolated data).

        Returns:
            A pandas.DataFrame with cycle-number, step-number, step-time, and
                voltage columns.
        """

        if cycles is None:
            cycles = self.get_cycle_numbers()
        else:
            if not isinstance(cycles, (list, tuple, np.ndarray)):
                cycles = [cycles]
            else:
                remove_first = False

        ocv_rlx_id = "ocvrlx"
        if direction == "up":
            ocv_rlx_id += "_up"
        elif direction == "down":
            ocv_rlx_id += "_down"

        steps = self.cell.steps
        raw = self.cell.raw

        ocv_steps = steps.loc[steps["cycle"].isin(cycles), :]

        ocv_steps = ocv_steps.loc[
            ocv_steps.type.str.startswith(ocv_rlx_id, na=False), :
        ]

        if remove_first:
            ocv_steps = ocv_steps.iloc[1:, :]

        step_time_label = self.headers_normal.step_time_txt
        voltage_label = self.headers_normal.voltage_txt
        cycle_label = self.headers_normal.cycle_index_txt
        step_label = self.headers_normal.step_index_txt

        selected_df = raw.where(
            raw[cycle_label].isin(ocv_steps.cycle)
            & raw[step_label].isin(ocv_steps.step)
        ).dropna()

        selected_df = selected_df.loc[
            :, [cycle_label, step_label, step_time_label, voltage_label]
        ]

        if interpolated:
            if dx is None and number_of_points is None:
                dx = prms.Reader.time_interpolation_step
            new_dfs = list()
            groupby_list = [cycle_label, step_label]

            for name, group in selected_df.groupby(groupby_list):
                new_group = interpolate_y_on_x(
                    group,
                    x=step_time_label,
                    y=voltage_label,
                    dx=dx,
                    number_of_points=number_of_points,
                )

                for i, j in zip(groupby_list, name):
                    new_group[i] = j
                new_dfs.append(new_group)

            selected_df = pd.concat(new_dfs)

        return selected_df

    def get_number_of_cycles(self, dataset_number=None, steptable=None):
        """Get the number of cycles in the test."""
        if steptable is None:
            dataset_number = self._validate_dataset_number(dataset_number)
            if dataset_number is None:
                self._report_empty_dataset()
                return
            d = self.cells[dataset_number].raw
            no_cycles = np.amax(d[self.headers_normal.cycle_index_txt])
        else:
            no_cycles = np.amax(steptable[self.headers_step_table.cycle])
        return no_cycles

    def get_cycle_numbers_old(self, dataset_number=None, steptable=None):
        """Get a list containing all the cycle numbers in the test."""
        logging.debug("getting cycle numbers")
        if steptable is None:
            dataset_number = self._validate_dataset_number(dataset_number)
            if dataset_number is None:
                self._report_empty_dataset()
                return
            d = self.cells[dataset_number].raw
            cycles = d[self.headers_normal.cycle_index_txt].dropna().unique()
        else:
            logging.debug("steptable is not none")
            cycles = steptable[self.headers_step_table.cycle].dropna().unique()
        logging.debug(f"got {len(cycles)} cycle numbers")
        return cycles

    def get_cycle_numbers(
        self,
        dataset_number=None,
        steptable=None,
        rate=None,
        rate_on=None,
        rate_std=None,
        rate_column=None,
        inverse=False,
    ):
        """Get a list containing all the cycle numbers in the test.

        Parameters:
            rate (float): the rate to filter on. Remark that it should be given
                as a float, i.e. you will have to convert from C-rate to
                the actual numeric value. For example, use rate=0.05 if you want
                to filter on cycles that has a C/20 rate.
            rate_on (str): only select cycles if based on the rate of this step-type (e.g. on="charge").
            rate_std (float): allow for this inaccuracy in C-rate when selecting cycles
            rate_column (str): column header name of the rate column,
            inverse (bool): select steps that does not have the given C-rate.

        Returns:
            numpy.ndarray of cycle numbers.
        """

        logging.debug("getting cycle numbers")
        if steptable is None:
            dataset_number = self._validate_dataset_number(dataset_number)
            if dataset_number is None:
                self._report_empty_dataset()
                return
            d = self.cells[dataset_number].raw
            cycles = d[self.headers_normal.cycle_index_txt].dropna().unique()
            steptable = self.cells[dataset_number].steps
        else:
            logging.debug("steptable is given as input parameter")
            cycles = steptable[self.headers_step_table.cycle].dropna().unique()

        if rate is None:
            return cycles

        logging.debug("filtering on rate")
        if rate_on is None:
            rate_on = ["charge"]
        else:
            if not isinstance(rate_on, (list, tuple)):
                rate_on = [rate_on]

        if rate_column is None:
            rate_column = self.headers_step_table["rate_avr"]

        if rate_on:
            on_column = self.headers_step_table["type"]

        if rate is None:
            rate = 0.05

        if rate_std is None:
            rate_std = 0.1 * rate

        if rate_on:
            cycles_mask = (
                (steptable[rate_column] < (rate + rate_std))
                & (steptable[rate_column] > (rate - rate_std))
                & (steptable[on_column].isin(rate_on))
            )
        else:
            cycles_mask = (steptable[rate_column] < (rate + rate_std)) & (
                steptable[rate_column] > (rate - rate_std)
            )

        if inverse:
            cycles_mask = ~cycles_mask

        filtered_step_table = steptable[cycles_mask]
        filtered_cycles = filtered_step_table[self.headers_step_table["cycle"]].unique()

        return filtered_cycles

    def get_ir(self, dataset_number=None):
        """Get the IR data (Deprecated)."""
        raise DeprecatedFeature

    def get_converter_to_specific(
        self, dataset=None, mass=None, to_unit=None, from_unit=None
    ):
        """get the conversion values

        Args:
            dataset: DataSet object
            mass: mass of electrode (for example active material in mg)
            to_unit: (float) unit of input, f.ex. if unit of charge
              is mAh and unit of mass is g, then to_unit for charge/mass
              will be 0.001 / 1.0 = 0.001
            from_unit: float) unit of output, f.ex. if unit of charge
              is mAh and unit of mass is g, then to_unit for charge/mass
              will be 1.0 / 0.001 = 1000.0

        Returns:
            multiplier (float) from_unit/to_unit * mass

        """

        if not dataset:
            dataset_number = self._validate_dataset_number(None)
            if dataset_number is None:
                self._report_empty_dataset()
                return
            dataset = self.cells[dataset_number]

        if not mass:
            mass = dataset.mass

        if not to_unit:
            to_unit_cap = self.cellpy_units["charge"]
            to_unit_mass = self.cellpy_units["specific"]
            to_unit = to_unit_cap / to_unit_mass
        if not from_unit:
            from_unit_cap = self.raw_units["charge"]
            from_unit_mass = self.raw_units["mass"]
            from_unit = from_unit_cap / from_unit_mass
        logging.debug(f"from-unit: {from_unit}")
        logging.debug(f"to-unit: {to_unit}")
        logging.debug(f"mass: {mass}")
        conversion_factor = from_unit / to_unit / mass
        logging.debug(f"conversion factor: {conversion_factor}")

        return conversion_factor

    def get_diagnostics_plots(self, dataset_number=None, scaled=False):
        raise DeprecatedFeature(
            "This feature is deprecated. "
            "Extract diagnostics from the summary instead."
        )

    def _set_mass(self, dataset_number, value):
        try:
            self.cells[dataset_number].mass = value
            self.cells[dataset_number].mass_given = True
        except AttributeError as e:
            logging.info("This test is empty")
            logging.info(e)

    def _set_tot_mass(self, dataset_number, value):
        try:
            self.cells[dataset_number].tot_mass = value
        except AttributeError as e:
            logging.info("This test is empty")
            logging.info(e)

    def _set_nom_cap(self, dataset_number, value):
        try:
            self.cells[dataset_number].nom_cap = value
        except AttributeError as e:
            logging.info("This test is empty")
            logging.info(e)

    def _set_run_attribute(self, attr, vals, dataset_number=None, validated=None):
        # Sets the val (vals) for the test (datasets).
        # Remark! This is left-over code from old ages when we thought we needed
        #   to have data-sets with multiple cells. And before we learned about
        #   setters and getters in Python. Feel free to refactor it.

        if attr == "mass":
            setter = self._set_mass
        elif attr == "tot_mass":
            setter = self._set_tot_mass
        elif attr == "nom_cap":
            setter = self._set_nom_cap

        number_of_tests = len(self.cells)
        if not number_of_tests:
            logging.info("No datasets have been loaded yet")
            logging.info(f"Cannot set {attr} before loading datasets")
            sys.exit(-1)

        if not dataset_number:
            dataset_number = list(range(len(self.cells)))

        if not self._is_listtype(dataset_number):
            dataset_number = [dataset_number]

        if not self._is_listtype(vals):
            vals = [vals]
        if validated is None:
            for t, m in zip(dataset_number, vals):
                setter(t, m)
        else:
            for t, m, v in zip(dataset_number, vals, validated):
                if v:
                    setter(t, m)
                else:
                    logging.debug("_set_run_attribute: this set is empty")

    def set_mass(self, masses, dataset_number=None, validated=None):
        """Sets the mass (masses) for the test (datasets).
        """
        self._set_run_attribute(
            "mass", masses, dataset_number=dataset_number, validated=validated
        )

    def set_tot_mass(self, masses, dataset_number=None, validated=None):
        """Sets the mass (masses) for the test (datasets).
        """
        self._set_run_attribute(
            "tot_mass", masses, dataset_number=dataset_number, validated=validated
        )

    def set_nom_cap(self, nom_caps, dataset_number=None, validated=None):
        """Sets the mass (masses) for the test (datasets).
        """
        self._set_run_attribute(
            "nom_cap", nom_caps, dataset_number=dataset_number, validated=validated
        )

    @staticmethod
    def set_col_first(df, col_names):
        """set selected columns first in a pandas.DataFrame.

        This function sets cols with names given in  col_names (a list) first in
        the DataFrame. The last col in col_name will come first (processed last)
        """

        column_headings = df.columns
        column_headings = column_headings.tolist()
        try:
            for col_name in col_names:
                i = column_headings.index(col_name)
                column_headings.pop(column_headings.index(col_name))
                column_headings.insert(0, col_name)

        finally:
            df = df.reindex(columns=column_headings)
            return df

    def set_dataset_number_force(self, dataset_number=0):
        """Force to set testnumber.

        Sets the DataSet number default (all functions with prm dataset_number
        will then be run assuming the default set dataset_number)
        """
        self.selected_cell_number = dataset_number

    def set_cellnumber(self, dataset_number):
        """Set the cell number.

        Set the cell number that will be used
        (CellpyData.selected_dataset_number).
        The class can save several datasets (but its not a frequently used
        feature), the datasets are stored in a list and dataset_number is the
        selected index in the list.

        Several options are available:
              n - int in range 0..(len-1) (python uses offset as index, i.e.
                  starts with 0)
              last, end, newest - last (index set to -1)
              first, zero, beginning, default - first (index set to 0)
        """
        warnings.warn("Deprecated", DeprecationWarning)
        logging.debug("***set_testnumber(n)")
        if not isinstance(dataset_number, int):
            dataset_number_txt = dataset_number
            try:
                if dataset_number_txt.lower() in ["last", "end", "newest"]:
                    dataset_number = -1
                elif dataset_number_txt.lower() in [
                    "first",
                    "zero",
                    "beginning",
                    "default",
                ]:
                    dataset_number = 0
            except Exception as e:
                logging.debug("assuming numeric")
                warnings.warn(f"Unhandled exception raised: {e}")

        number_of_tests = len(self.cells)
        if dataset_number >= number_of_tests:
            dataset_number = -1
            logging.debug("you dont have that many datasets, setting to last test")
        elif dataset_number < -1:
            logging.debug("not a valid option, setting to first test")
            dataset_number = 0
        self.selected_cell_number = dataset_number

    # TODO: deprecate this
    def get_summary(self, dataset_number=None, use_summary_made=False):
        """Retrieve summary returned as a pandas DataFrame."""
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return None

        test = self.get_cell(dataset_number)

        # This is a bit convoluted; in the old days, we used an attribute
        # called summary_made,
        # that was set to True when the summary was made successfully.
        # It is most likely never
        # used anymore. And will most probably be deleted.
        if use_summary_made:
            summary_made = test.summary_made
        else:
            summary_made = True

        if not summary_made:
            warnings.warn("Summary is not made yet")
            return None
        else:
            logging.info("Returning datasets[test_no].summary")
            return test.summary

    # -----------internal-helpers-----------------------------------------------

    # TODO: clean it up a bit
    @staticmethod
    def is_empty(v):
        try:
            if not v:
                return True
            else:
                return False
        except Exception:
            try:
                if v.empty:
                    return True
                else:
                    return False
            except Exception:
                if v.isnull:
                    return False
                else:
                    return True

    @staticmethod
    def _is_listtype(x):
        if isinstance(x, (list, tuple)):
            return True
        else:
            return False

    @staticmethod
    def _check_file_type(filename):
        warnings.warn(DeprecationWarning("this method will be removed " "in v.0.4.0"))
        extension = os.path.splitext(filename)[-1]
        filetype = "res"
        if extension.lower() == ".res":
            filetype = "res"
        elif extension.lower() == ".h5":
            filetype = "h5"
        return filetype

    @staticmethod
    def _bounds(x):
        return np.amin(x), np.amax(x)

    @staticmethod
    def _roundup(x):
        n = 1000.0
        x = np.ceil(x * n)
        x /= n
        return x

    def _rounddown(self, x):
        x = self._roundup(-x)
        x = -x
        return x

    @staticmethod
    def _reverse(x):
        x = x[::-1]
        # x = x.sort_index(ascending=True)
        return x

    def _select_y(self, x, y, points):
        # uses interpolation to select y = f(x)
        min_x, max_x = self._bounds(x)
        if x[0] > x[-1]:
            # need to reverse
            x = self._reverse(x)
            y = self._reverse(y)
        f = interpolate.interp1d(y, x)
        y_new = f(points)
        return y_new

    def _select_last(self, raw):
        # this function gives a set of indexes pointing to the last
        # datapoints for each cycle in the dataset

        c_txt = self.headers_normal.cycle_index_txt
        d_txt = self.headers_normal.data_point_txt
        steps = []
        unique_steps = raw[c_txt].unique()
        max_step = max(raw[c_txt])
        for j in range(int(max_step)):
            if j + 1 not in unique_steps:
                logging.debug(f"Warning: Cycle {j + 1} is missing!")
            else:
                last_item = max(raw.loc[raw[c_txt] == j + 1, d_txt])
                steps.append(last_item)

        last_items = raw[d_txt].isin(steps)
        return last_items

    # TODO: find out what this is for and probably delete it
    def _modify_cycle_number_using_cycle_step(
        self, from_tuple=None, to_cycle=44, dataset_number=None
    ):
        # modify step-cycle tuple to new step-cycle tuple
        # from_tuple = [old cycle_number, old step_number]
        # to_cycle    = new cycle_number

        if from_tuple is None:
            from_tuple = [1, 4]
        logging.debug("**- _modify_cycle_step")
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return

        cycle_index_header = self.headers_normal.cycle_index_txt
        step_index_header = self.headers_normal.step_index_txt

        step_table_txt_cycle = self.headers_step_table.cycle
        step_table_txt_step = self.headers_step_table.step

        # modifying steps
        st = self.cells[dataset_number].steps
        st[step_table_txt_cycle][
            (st[step_table_txt_cycle] == from_tuple[0])
            & (st[step_table_txt_step] == from_tuple[1])
        ] = to_cycle
        # modifying normal_table
        nt = self.cells[dataset_number].raw
        nt[cycle_index_header][
            (nt[cycle_index_header] == from_tuple[0])
            & (nt[step_index_header] == from_tuple[1])
        ] = to_cycle
        # modifying summary_table
        # not implemented yet

    # ----------making-summary------------------------------------------------------
    def make_summary(
        self,
        find_ocv=False,
        find_ir=False,
        find_end_voltage=True,
        use_cellpy_stat_file=None,
        all_tests=True,
        dataset_number=0,
        ensure_step_table=True,
        add_normalized_cycle_index=True,
        add_c_rate=True,
        normalization_cycles=None,
        nom_cap=None,
        from_cycle=None,
    ):
        """Convenience function that makes a summary of the cycling data."""

        # TODO: @jepe - include option for omitting steps
        # TODO: @jepe  - make it is possible to update only new data by implementing
        #  from_cycle (only calculate summary from a given cycle number).
        #  Probably best to keep the old summary and make
        #  a new one for the rest, then use pandas.concat to merge them.
        #  Might have to create the culumative cols etc after merging?

        # first - check if we need some "instrument-specific" prms
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return

        if ensure_step_table is None:
            ensure_step_table = self.ensure_step_table

        if use_cellpy_stat_file is None:
            use_cellpy_stat_file = prms.Reader.use_cellpy_stat_file
            logging.debug("using use_cellpy_stat_file from prms")
            logging.debug(f"use_cellpy_stat_file: {use_cellpy_stat_file}")

        if all_tests is True:
            for j in range(len(self.cells)):
                txt = "creating summary for file "
                test = self.cells[j]
                if not self._is_not_empty_dataset(test):
                    logging.info(f"Empty test {j})")
                    return
                if isinstance(test.loaded_from, (list, tuple)):
                    for f in test.loaded_from:
                        txt += f"{f}\n"
                else:
                    txt += str(test.loaded_from)

                if not test.mass_given:
                    txt += f" mass for test {j} is not given"
                    txt += f" setting it to {test.mass} mg"
                logging.debug(txt)

                self._make_summary(
                    j,
                    find_ocv=find_ocv,
                    find_ir=find_ir,
                    find_end_voltage=find_end_voltage,
                    use_cellpy_stat_file=use_cellpy_stat_file,
                    ensure_step_table=ensure_step_table,
                    add_normalized_cycle_index=add_normalized_cycle_index,
                    add_c_rate=add_c_rate,
                    normalization_cycles=normalization_cycles,
                    nom_cap=nom_cap,
                )
        else:
            logging.debug("creating summary for only one test")
            dataset_number = self._validate_dataset_number(dataset_number)
            if dataset_number is None:
                self._report_empty_dataset()
                return
            self._make_summary(
                dataset_number,
                find_ocv=find_ocv,
                find_ir=find_ir,
                find_end_voltage=find_end_voltage,
                use_cellpy_stat_file=use_cellpy_stat_file,
                ensure_step_table=ensure_step_table,
                add_normalized_cycle_index=add_normalized_cycle_index,
                add_c_rate=add_c_rate,
                normalization_cycles=normalization_cycles,
                nom_cap=nom_cap,
            )
        return self

    def _make_summary(
        self,
        dataset_number=None,
        mass=None,
        update_it=False,
        select_columns=True,
        find_ocv=False,
        find_ir=False,
        find_end_voltage=False,
        ensure_step_table=True,
        # TODO: @jepe - include option for omitting steps
        sort_my_columns=True,
        use_cellpy_stat_file=False,
        add_normalized_cycle_index=True,
        add_c_rate=False,
        normalization_cycles=None,
        nom_cap=None,
        # capacity_modifier = None,
        # test=None
    ):
        cycle_index_as_index = True

        time_00 = time.time()

        dataset_number = self._validate_dataset_number(dataset_number)

        logging.debug("start making summary")
        if dataset_number is None:
            self._report_empty_dataset()
            return
        dataset = self.cells[dataset_number]
        #        if test.merged == True:
        #            use_cellpy_stat_file=False

        if not mass:
            mass = dataset.mass or 1.0
        else:
            if update_it:
                dataset.mass = mass

        if ensure_step_table and not self.load_only_summary:
            logging.debug("ensuring existence of step-table")
            if not dataset.steps_made:
                logging.debug("dataset.step_table_made is not True")
                logging.info("running make_step_table")
                if nom_cap is not None:
                    dataset.nom_cap = nom_cap
                self.make_step_table(dataset_number=dataset_number)

        # Retrieve the converters etc.
        specific_converter = self.get_converter_to_specific(dataset=dataset, mass=mass)

        hdr_normal = self.headers_normal
        dt_txt = hdr_normal.datetime_txt
        tt_txt = hdr_normal.test_time_txt
        st_txt = hdr_normal.step_time_txt
        c_txt = hdr_normal.cycle_index_txt
        d_txt = hdr_normal.data_point_txt
        s_txt = hdr_normal.step_index_txt
        voltage_header = hdr_normal.voltage_txt
        charge_txt = hdr_normal.charge_capacity_txt
        discharge_txt = hdr_normal.discharge_capacity_txt
        ir_txt = hdr_normal.internal_resistance_txt
        test_id_txt = hdr_normal.test_id_txt
        i_txt = hdr_normal.current_txt

        hdr_summary = self.headers_summary
        discharge_title = hdr_summary.discharge_capacity
        charge_title = hdr_summary.charge_capacity
        cumcharge_title = hdr_summary.cumulated_charge_capacity
        cumdischarge_title = hdr_summary.cumulated_discharge_capacity
        coulomb_title = hdr_summary.coulombic_efficiency
        cumcoulomb_title = hdr_summary.cumulated_coulombic_efficiency
        coulomb_diff_title = hdr_summary.coulombic_difference
        cumcoulomb_diff_title = hdr_summary.cumulated_coulombic_difference
        col_discharge_loss_title = hdr_summary.discharge_capacity_loss
        col_charge_loss_title = hdr_summary.charge_capacity_loss
        dcloss_cumsum_title = hdr_summary.cumulated_discharge_capacity_loss
        closs_cumsum_title = hdr_summary.cumulated_charge_capacity_loss
        endv_charge_title = hdr_summary.end_voltage_charge
        endv_discharge_title = hdr_summary.end_voltage_discharge
        ocv_1_v_min_title = hdr_summary.ocv_first_min
        ocv_1_v_max_title = hdr_summary.ocv_first_max
        ocv_2_v_min_title = hdr_summary.ocv_second_min
        ocv_2_v_max_title = hdr_summary.ocv_second_max
        ir_discharge_title = hdr_summary.ir_discharge
        ir_charge_title = hdr_summary.ir_charge

        ric_disconnect_title = hdr_summary.cumulated_ric_disconnect
        ric_sei_title = hdr_summary.cumulated_ric_sei
        ric_title = hdr_summary.cumulated_ric
        high_level_at_cycle_n_txt = hdr_summary.high_level
        low_level_at_cycle_n_txt = hdr_summary.low_level
        shifted_charge_capacity_title = hdr_summary.shifted_charge_capacity
        shifted_discharge_capacity_title = hdr_summary.shifted_discharge_capacity

        h_normalized_cycle = hdr_summary.normalized_cycle_index

        hdr_steps = self.headers_step_table

        # Here are the two main DataFrames for the test
        # (raw-data and summary-data)
        summary_df = dataset.summary
        if not self.load_only_summary:
            # Can't find summary from raw data if raw data is not loaded.
            raw = dataset.raw
            if use_cellpy_stat_file:
                # This should work even if raw does not
                # contain all data from the test
                try:
                    summary_requirment = raw[d_txt].isin(summary_df[d_txt])
                except KeyError:
                    logging.info("Error in stat_file (?) - using _select_last")
                    summary_requirment = self._select_last(raw)
            else:
                summary_requirment = self._select_last(raw)
            summary = raw[summary_requirment].copy()
        else:
            # summary_requirment = self._reloadrows_raw(summary_df[d_txt])
            summary = summary_df
            dataset.summary = summary
            logging.warning("not implemented yet")
            return

        column_names = summary.columns
        summary_length = len(summary[column_names[0]])
        summary.index = list(range(summary_length))
        # could also index based on Cycle_Index
        # indexes = summary.index

        if select_columns:
            columns_to_keep = [charge_txt, c_txt, d_txt, dt_txt, discharge_txt, tt_txt]
            for cn in column_names:
                if not columns_to_keep.count(cn):
                    summary.pop(cn)

        if not use_cellpy_stat_file:
            logging.debug("not using cellpy statfile")
            # logging.debug("Values obtained from raw:")
            # logging.debug(summary.head(20))

        # logging.debug("Creates summary: specific discharge ('%s')"
        #                   % discharge_title)
        summary[discharge_title] = summary[discharge_txt] * specific_converter

        # logging.debug("Creates summary: specific scharge ('%s')" %
        #                   charge_title)
        summary[charge_title] = summary[charge_txt] * specific_converter

        # logging.debug("Creates summary: cumulated specific charge ('%s')" %
        #                   cumdischarge_title)
        summary[cumdischarge_title] = summary[discharge_title].cumsum()

        # logging.debug("Creates summary: cumulated specific charge ('%s')" %
        #                   cumcharge_title)
        summary[cumcharge_title] = summary[charge_title].cumsum()

        if self.cycle_mode == "anode":
            logging.info(
                "Assuming cycling in anode half-cell (discharge before charge) mode"
            )
            _first_step_txt = discharge_title
            _second_step_txt = charge_title
        else:
            logging.info("Assuming cycling in full-cell / cathode mode")
            _first_step_txt = charge_title
            _second_step_txt = discharge_title

        # logging.debug("Creates summary: coulombic efficiency ('%s')" %
        #                   coulomb_title)
        # logging.debug("100 * ('%s')/('%s)" % (_second_step_txt,
        #                                           _first_step_txt))
        summary[coulomb_title] = (
            100.0 * summary[_second_step_txt] / summary[_first_step_txt]
        )

        # logging.debug("Creates summary: coulombic difference ('%s')" %
        #                   coulomb_diff_title)
        # logging.debug("'%s') - ('%s)" % (_second_step_txt, _first_step_txt))
        summary[coulomb_diff_title] = (
            summary[_second_step_txt] - summary[_first_step_txt]
        )

        # logging.debug("Creates summary: cumulated "
        #                   f"coulombic efficiency ('{cumcoulomb_title}')")
        summary[cumcoulomb_title] = summary[coulomb_title].cumsum()
        # logging.debug("Creates summary: cumulated coulombic difference "
        #                   "f('{cumcoulomb_diff_title}')")
        summary[cumcoulomb_diff_title] = summary[coulomb_diff_title].cumsum()

        # ---------------- discharge loss ---------------------
        # Assume that both charge and discharge is defined as positive.
        # The gain for cycle n (compared to cycle n-1)
        # is then cap[n] - cap[n-1]. The loss is the negative of gain.
        # discharge loss = discharge_cap[n-1] - discharge_cap[n]
        # logging.debug("Creates summary: calculates DL")
        summary[col_discharge_loss_title] = (
            summary[discharge_title].shift(1) - summary[discharge_title]
        )

        summary[dcloss_cumsum_title] = summary[col_discharge_loss_title].cumsum()

        # ---------------- charge loss ------------------------
        # charge loss = charge_cap[n-1] - charge_cap[n]
        summary[col_charge_loss_title] = (
            summary[charge_title].shift(1) - summary[charge_title]
        )

        summary[closs_cumsum_title] = summary[col_charge_loss_title].cumsum()

        # --------------- D.L. --------------------------------
        # NH_n: high level at cycle n. The slope NHn=f(n) is linked to SEI loss
        # NB_n: low level (summation of irreversible capacities) at cycle n
        # Ref_n: sum[i=1 to ref](Q_charge_i - Q_discharge_i) + Q_charge_ref
        # Typically, ref should be a number where the electrode has become
        # stable (i.e. 5).
        # NBn/100 = sum[i=1 to n](Q_charge_i - Q_discharge_i) / Ref_n
        # NHn/100 = Q_charge_n + sum[i=1 to n-1](Q_charge_i - Q_discharge_i)
        #  / Ref_n
        # NH = 100%  ok if NH<120 at n=200
        # NB = 20% stable (or less)

        n = self.daniel_number
        cap_ref = summary.loc[summary[c_txt] == n, _first_step_txt]
        if not cap_ref.empty:
            cap_ref = cap_ref.values[0]

            ref = (
                summary.loc[summary[c_txt] < n, _second_step_txt].sum()
                + summary.loc[summary[c_txt] < n, _first_step_txt].sum()
                + cap_ref
            )

            summary[low_level_at_cycle_n_txt] = (100 / ref) * (
                summary[_first_step_txt].cumsum() - summary[_second_step_txt].cumsum()
            )

            summary[high_level_at_cycle_n_txt] = (100 / ref) * (
                summary[_first_step_txt]
                + summary[_first_step_txt].cumsum()
                - summary[_second_step_txt].cumsum()
            )
        else:
            txt = f"ref cycle number: {n}"
            logging.info(
                "could not extract low-high levels (ref cycle number does not exist)"
            )
            # logging.info(txt)
            summary[low_level_at_cycle_n_txt] = np.nan
            summary[high_level_at_cycle_n_txt] = np.nan

        # --------------relative irreversible capacities
        #  as defined by Gauthier et al.---
        # RIC = discharge_cap[n-1] - charge_cap[n] /  charge_cap[n-1]
        RIC = (summary[_first_step_txt].shift(1) - summary[_second_step_txt]) / summary[
            _second_step_txt
        ].shift(1)
        summary[ric_title] = RIC.cumsum()

        # RIC_SEI = discharge_cap[n] - charge_cap[n-1] / charge_cap[n-1]
        RIC_SEI = (
            summary[_first_step_txt] - summary[_second_step_txt].shift(1)
        ) / summary[_second_step_txt].shift(1)
        summary[ric_sei_title] = RIC_SEI.cumsum()

        # RIC_disconnect = charge_cap[n-1] - charge_cap[n] / charge_cap[n-1]
        RIC_disconnect = (
            summary[_second_step_txt].shift(1) - summary[_second_step_txt]
        ) / summary[_second_step_txt].shift(1)
        summary[ric_disconnect_title] = RIC_disconnect.cumsum()

        # -------------- shifted capacities as defined by J. Dahn et al. -----
        # need to double check this (including checking
        # if it is valid in cathode mode).
        individual_edge_movement = summary[_first_step_txt] - summary[_second_step_txt]

        summary[shifted_charge_capacity_title] = individual_edge_movement.cumsum()
        summary[shifted_discharge_capacity_title] = (
            summary[shifted_charge_capacity_title] + summary[_first_step_txt]
        )

        # if convert_date:
        #     # TODO: should move this to the instrument reader procedure
        #     logging.debug("converting date from xls-type")
        #     summary[date_time_txt_title] = \
        #         summary[dt_txt].apply(xldate_as_datetime)  # , option="to_string")

        if find_ocv and not self.load_only_summary:
            warnings.warn(DeprecationWarning("this option will be removed in v.0.4.0"))
            # should remove this option
            logging.info("CONGRATULATIONS")
            logging.info("-thought this would never be run!")
            logging.info("-find_ocv in make_summary")
            logging.info(
                "  this is a stupid routine that can be implemented much better!"
            )
            do_ocv_1 = True
            do_ocv_2 = True

            ocv1_type = "ocvrlx_up"
            ocv2_type = "ocvrlx_down"

            if not self.cycle_mode == "anode":
                ocv2_type = "ocvrlx_up"
                ocv1_type = "ocvrlx_down"

            ocv_1 = self._get_ocv(
                ocv_steps=dataset.ocv_steps,
                ocv_type=ocv1_type,
                dataset_number=dataset_number,
            )

            ocv_2 = self._get_ocv(
                ocv_steps=dataset.ocv_steps,
                ocv_type=ocv2_type,
                dataset_number=dataset_number,
            )

            if do_ocv_1:
                only_zeros = summary[discharge_txt] * 0.0
                ocv_1_indexes = []
                ocv_1_v_min = []
                ocv_1_v_max = []
                ocvcol_min = only_zeros.copy()
                ocvcol_max = only_zeros.copy()

                for j in ocv_1:
                    cycle = j["Cycle_Index"].values[0]  # jepe fix
                    # try to find inxed
                    index = summary[(summary[c_txt] == cycle)].index
                    # print cycle, index,
                    v_min = j["Voltage"].min()  # jepe fix
                    v_max = j["Voltage"].max()  # jepe fix
                    # print v_min,v_max
                    dv = v_max - v_min
                    ocvcol_min.iloc[index] = v_min
                    ocvcol_max.iloc[index] = v_max

                summary.insert(0, column=ocv_1_v_min_title, value=ocvcol_min)
                summary.insert(0, column=ocv_1_v_max_title, value=ocvcol_max)

            if do_ocv_2:
                only_zeros = summary[discharge_txt] * 0.0
                ocv_2_indexes = []
                ocv_2_v_min = []
                ocv_2_v_max = []
                ocvcol_min = only_zeros.copy()
                ocvcol_max = only_zeros.copy()

                for j in ocv_2:
                    cycle = j["Cycle_Index"].values[0]  # jepe fix
                    # try to find inxed
                    index = summary[(summary[c_txt] == cycle)].index
                    v_min = j["Voltage"].min()  # jepe fix
                    v_max = j["Voltage"].max()  # jepe fix
                    dv = v_max - v_min
                    ocvcol_min.iloc[index] = v_min
                    ocvcol_max.iloc[index] = v_max
                summary.insert(0, column=ocv_2_v_min_title, value=ocvcol_min)
                summary.insert(0, column=ocv_2_v_max_title, value=ocvcol_max)

        if find_end_voltage and not self.load_only_summary:
            # needs to be fixed so that end-voltage also can be extracted
            # from the summary
            ev_t0 = time.time()
            logging.debug("finding end-voltage")
            logging.debug(f"dt: {time.time() - ev_t0}")
            only_zeros_discharge = summary[discharge_txt] * 0.0
            only_zeros_charge = summary[charge_txt] * 0.0
            if not dataset.discharge_steps:
                logging.debug("need to collect discharge steps")
                discharge_steps = self.get_step_numbers(
                    steptype="discharge", allctypes=False, dataset_number=dataset_number
                )
                logging.debug(f"dt: {time.time() - ev_t0}")
            else:
                discharge_steps = dataset.discharge_steps
                logging.debug("  already have discharge_steps")
            if not dataset.charge_steps:
                logging.debug("need to collect charge steps")
                charge_steps = self.get_step_numbers(
                    steptype="charge", allctypes=False, dataset_number=dataset_number
                )
                logging.debug(f"dt: {time.time() - ev_t0}")
            else:
                charge_steps = dataset.charge_steps
                logging.debug("  already have charge_steps")

            endv_indexes = []
            endv_values_dc = []
            endv_values_c = []
            # logging.debug("trying to find end voltage for")
            # logging.debug(dataset.loaded_from)
            # logging.debug("Using the following chargesteps")
            # logging.debug(charge_steps)
            # logging.debug("Using the following dischargesteps")
            # logging.debug(discharge_steps)
            logging.debug("starting iterating through the index")
            for i in summary.index:
                # txt = "index in summary.index: %i" % i
                # logging.debug(txt)
                # selecting the appropriate cycle
                cycle = summary.iloc[i][c_txt]
                # txt = "cycle: %i" % cycle
                # logging.debug(txt)
                step = discharge_steps[cycle]

                # finding end voltage for discharge
                if step[-1]:  # selecting last
                    # TODO: @jepe - use pd.loc[row,column]
                    # for col or pd.loc[(pd.["step"]==1),"x"]
                    end_voltage_dc = raw[
                        (raw[c_txt] == cycle) & (dataset.raw[s_txt] == step[-1])
                    ][voltage_header]
                    # This will not work if there are more than one item in step
                    end_voltage_dc = end_voltage_dc.values[-1]  # selecting
                    # last (could also select amax)
                else:
                    end_voltage_dc = 0  # could also use numpy.nan

                # finding end voltage for charge
                step2 = charge_steps[cycle]
                if step2[-1]:
                    end_voltage_c = raw[
                        (raw[c_txt] == cycle) & (dataset.raw[s_txt] == step2[-1])
                        ][voltage_header]
                    end_voltage_c = end_voltage_c.values[-1]
                    # end_voltage_c = np.amax(end_voltage_c)
                else:
                    end_voltage_c = 0
                endv_indexes.append(i)
                endv_values_dc.append(end_voltage_dc)
                endv_values_c.append(end_voltage_c)
            logging.debug("finished iterating")
            logging.debug(f"find end V took: {time.time() - ev_t0} s")
            ir_frame_dc = only_zeros_discharge + endv_values_dc
            ir_frame_c = only_zeros_charge + endv_values_c
            summary.insert(0, column=endv_discharge_title, value=ir_frame_dc)
            summary.insert(0, column=endv_charge_title, value=ir_frame_c)

        if find_ir and (not self.load_only_summary) and (ir_txt in dataset.raw.columns):
            # should check:  test.charge_steps = None,
            # test.discharge_steps = None
            # THIS DOES NOT WORK PROPERLY!!!!
            # Found a file where it writes IR for cycle n on cycle n+1
            # This only picks out the data on the last IR step before
            logging.debug("finding ir")
            only_zeros = summary[discharge_txt] * 0.0
            if not dataset.discharge_steps:
                discharge_steps = self.get_step_numbers(
                    steptype="discharge", allctypes=False, dataset_number=dataset_number
                )
            else:
                discharge_steps = dataset.discharge_steps
                logging.debug("  already have discharge_steps")
            if not dataset.charge_steps:
                charge_steps = self.get_step_numbers(
                    steptype="charge", allctypes=False, dataset_number=dataset_number
                )
            else:
                charge_steps = dataset.charge_steps
                logging.debug("  already have charge_steps")

            ir_indexes = []
            ir_values = []
            ir_values2 = []
            # logging.debug("trying to find ir for")
            # logging.debug(dataset.loaded_from)
            # logging.debug("Using the following charge_steps")
            # logging.debug(charge_steps)
            # logging.debug("Using the following discharge_steps")
            # logging.debug(discharge_steps)

            for i in summary.index:
                # txt = "index in summary.index: %i" % i
                # logging.debug(txt)
                # selecting the appropriate cycle
                cycle = summary.iloc[i][c_txt]  # "Cycle_Index" = i + 1
                # txt = "cycle: %i" % cycle
                # logging.debug(txt)
                step = discharge_steps[cycle]
                if step[0]:
                    ir = raw.loc[
                        (raw[c_txt] == cycle) & (dataset.raw[s_txt] == step[0]), ir_txt
                    ]
                    # This will not work if there are more than one item in step
                    ir = ir.values[0]
                else:
                    ir = 0
                step2 = charge_steps[cycle]
                if step2[0]:

                    ir2 = raw[(raw[c_txt] == cycle) & (dataset.raw[s_txt] == step2[0])][
                        ir_txt
                    ].values[0]
                else:
                    ir2 = 0
                ir_indexes.append(i)
                ir_values.append(ir)
                ir_values2.append(ir2)

            ir_frame = only_zeros + ir_values
            ir_frame2 = only_zeros + ir_values2
            summary.insert(0, column=ir_discharge_title, value=ir_frame)
            summary.insert(0, column=ir_charge_title, value=ir_frame2)

        if add_normalized_cycle_index:
            if normalization_cycles is not None:
                logging.info(
                    f"Using these cycles for finding the nominal capacity: {normalization_cycles}"
                )
                if not isinstance(normalization_cycles, (list, tuple)):
                    normalization_cycles = [normalization_cycles]

                cap_ref = summary.loc[
                    summary[c_txt].isin(normalization_cycles), _first_step_txt
                ]
                if not cap_ref.empty:
                    nom_cap = cap_ref.mean()
                else:
                    logging.info(f"Empty reference cycle(s)")

            if nom_cap is None:
                logging.debug(f"No nom_cap given")
                nom_cap = self.cell.nom_cap
            logging.info(f"Using the following nominal capacity: {nom_cap}")
            summary[h_normalized_cycle] = summary[cumcharge_title] / nom_cap

        if add_c_rate:
            logging.debug("Extracting C-rates")
            steps = self.cell.steps

            # if hdr_summary.cycle_index not in summary.columns:
            #     summary = summary.reset_index()

            charge_steps = steps.loc[
                steps.type == "charge", [hdr_steps.cycle, "rate_avr"]
            ].rename(columns={"rate_avr": hdr_summary.charge_c_rate})

            summary = summary.merge(
                charge_steps.drop_duplicates(subset=[hdr_steps.cycle], keep="first"),
                left_on=hdr_summary.cycle_index,
                right_on=hdr_steps.cycle,
                how="left",
            ).drop(columns=hdr_steps.cycle)

            discharge_steps = steps.loc[
                steps.type == "discharge", [hdr_steps.cycle, "rate_avr"]
            ].rename(columns={"rate_avr": hdr_summary.discharge_c_rate})

            summary = summary.merge(
                discharge_steps.drop_duplicates(subset=[hdr_steps.cycle], keep="first"),
                left_on=hdr_summary.cycle_index,
                right_on=hdr_steps.cycle,
                how="left",
            ).drop(columns=hdr_steps.cycle)

        if sort_my_columns:
            logging.debug("sorting columns")
            new_first_col_list = [dt_txt, tt_txt, d_txt, c_txt]
            summary = self.set_col_first(summary, new_first_col_list)

        if cycle_index_as_index:
            index_col = hdr_summary.cycle_index
            try:
                summary.set_index(index_col, inplace=True)
            except KeyError:
                logging.debug("Setting cycle_index as index failed")

        dataset.summary = summary
        logging.debug(f"(dt: {(time.time() - time_00):4.2f}s)")

    def inspect_nominal_capacity(self, cycles=None):
        """Method for estimating the nominal capacity

        Args:
            cycles (list of ints): the cycles where it is assumed that the cell reaches nominal capacity.

        Returns:
            Nominal capacity (float).
        """
        logging.debug("inspecting: nominal capacity")
        print("Sorry! This method is still under development.")
        print("Maybe you can plot your data and find the nominal capacity yourself?")
        if cycles is None:
            cycles = [1, 2, 3]

        summary = self.cell.summary

        try:
            nc = summary.loc[
                summary[self.headers_normal.cycle_index_txt].isin(cycles),
                self.headers_summary.discharge_capacity,
            ].mean()
            print("All I can say for now is that the average discharge capacity")
            print(f"for the cycles {cycles} is {nc:0.2f}")
            nc = float(nc)

        except ZeroDivisionError:
            print("zero division error")
            nc = None

        return nc


def get(
    filename=None,
    mass=None,
    instrument=None,
    nominal_capacity=None,
    logging_mode=None,
    cycle_mode=None,
    auto_summary=True,
    **kwargs,
):
    """Create a CellpyData object

    Args:
        filename (str, os.PathLike, or list of raw-file names): path to file(s)
        mass (float): mass of active material (mg) (defaults to mass given in cellpy-file or 1.0)
        instrument (str): instrument to use (defaults to the one in your cellpy config file) (arbin_res, arbin_sql, arbin_sql_csv, arbin_sql_xlxs)
        nominal_capacity (float): nominal capacity for the cell (e.g. used for finding C-rates)
        logging_mode (str): "INFO" or "DEBUG"
        cycle_mode (str): the cycle mode (e.g. "anode" or "full_cell")
        auto_summary (bool): (re-) create summary.
        **kwargs: sent to the loader

    Returns:
        CellpyData object (if successful, None if not)

    """

    from cellpy import log

    log.setup_logging(default_level=logging_mode)
    logging.debug("-------running-get--------")
    cellpy_instance = CellpyData()

    db_readers = ["arbin_sql"]

    if instrument is not None:
        cellpy_instance.set_instrument(instrument=instrument)

    if cellpy_instance.tester in db_readers:
        file_needed = False
    else:
        file_needed = True

    if cycle_mode is not None:
        cellpy_instance.cycle_mode = cycle_mode

    if filename is not None:
        if file_needed:
            if not isinstance(filename, (list, tuple)):
                filename = Path(filename)

                if not filename.is_file():
                    print(f"Could not find {filename}")
                    print("Returning None")
                    return

                if filename.suffix in [".h5", ".hdf5", ".cellpy", ".cpy"]:
                    logging.info(f"Loading cellpy-file: {filename}")
                    cellpy_instance.load(filename, **kwargs)

                    # in case the user wants to give another mass to the cell:
                    if mass is not None:
                        logging.info(f"Setting mass: {mass}")
                        cellpy_instance.set_mass(mass)
                        if auto_summary:
                            logging.info("Creating step table")
                            cellpy_instance.make_step_table()
                            logging.info("Creating summary data")
                            cellpy_instance.make_summary()
                    logging.info("Created CellpyData object")
                    return cellpy_instance

        # raw file
        logging.info(f"Loading raw-file: {filename}")
        cellpy_instance.from_raw(filename, **kwargs)
        if not cellpy_instance:
            print("Could not load file: check log!")
            print("Returning None")
            return

        if mass is not None:
            logging.info(f"Setting mass: {mass}")
            cellpy_instance.set_mass(mass)

        if nominal_capacity is not None:
            logging.info(f"Setting nominal capacity: {nominal_capacity}")
            cellpy_instance.set_nom_cap(nominal_capacity)

        if auto_summary:
            logging.info("Creating step table")
            cellpy_instance.make_step_table()
            logging.info("Creating summary data")
            cellpy_instance.make_summary()
    else:
        if mass:
            prms.Materials["default_mass"] = mass
            prms.Materials["default_mass"] = mass
        if nominal_capacity:
            prms.DataSet["nom_cap"] = nominal_capacity

    logging.info("Created CellpyData object")
    return cellpy_instance


if __name__ == "__main__":
    print("running", end=" ")
    print(sys.argv[0])
    import logging
    from cellpy import log

    log.setup_logging(default_level="DEBUG")

    from cellpy.utils import example_data

    f = example_data.cellpy_file_path()
    print(f)
    print(f.is_file())
    c = CellpyData()
    c.dev_load(f, accept_old=True)
    c.make_step_table()
    c.make_summary()
    print("Here we have it")
    print(c.cell.summary.columns)
    print(c.cell.steps.columns)
    print(c.cell.raw.columns)
