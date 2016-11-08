# -*- coding: utf-8 -*-
"""Datareader for cell testers and potentiostats.

This module is used for loading data and databases created by different cell
testers. Currently it only accepts arbin-type res-files (access) data as
raw data files, but we intend to implement more types soon. It also creates
processed files in the hdf5-format.

Example:
    >>> d = cellpydata()
    >>> d.loadcell(names = [file1.res, file2.res]) # loads and merges the runs
    >>> internal_resistance = d.get_ir()
    >>> d.save_test("mytest.hdf")


Todo:
    * Documentation needed
    * Include functions gradually from old version
    * Rename datastructure
    * Remove mass dependency in summary data
    * use pd.loc[row,column] e.g. pd.loc[:,"charge_cap"] for col or pd.loc[(pd.["step"]==1),"x"]

"""


USE_ADO = False
"""string: set True if using adodbapi"""

if USE_ADO:
    try:
        import adodbapi as dbloader  # http://adodbapi.sourceforge.net/
    except:
        USE_ADO = False

else:
    try:
        import pyodbc as dbloader
    except ImportError:
        dbloader = None

import shutil
import os
import sys
import tempfile
import types
import collections
import time
import warnings
import csv
import itertools
import cProfile
import pstats
import StringIO
from scipy import interpolate
import numpy as np
import pandas as pd
import logging
# import logging.config

warnings.filterwarnings('ignore', category=pd.io.pytables.PerformanceWarning)
pd.set_option('mode.chained_assignment', None)  # "raise" "warn"


# module_logger = logging.getLogger(__name__)

def humanize_bytes(bytes, precision=1):
    """Return a humanized string representation of a number of bytes.

    Assumes `from __future__ import division`.

    >>> humanize_bytes(1)
    '1 byte'
    >>> humanize_bytes(1024)
    '1.0 kB'
    >>> humanize_bytes(1024*123)
    '123.0 kB'
    >>> humanize_bytes(1024*12342)
    '12.1 MB'
    >>> humanize_bytes(1024*12342,2)
    '12.05 MB'
    >>> humanize_bytes(1024*1234,2)
    '1.21 MB'
    >>> humanize_bytes(1024*1234*1111,2)
    '1.31 GB'
    >>> humanize_bytes(1024*1234*1111,1)
    '1.3 GB'
    """
    abbrevs = (
        (1 << 50L, 'PB'),
        (1 << 40L, 'TB'),
        (1 << 30L, 'GB'),
        (1 << 20L, 'MB'),
        (1 << 10L, 'kB'),
        (1, 'bytes')
    )
    if bytes == 1:
        return '1 byte'
    for factor, suffix in abbrevs:
        if bytes >= factor:
            break
    return '%.*f %s' % (precision, bytes / factor, suffix)


def xldate_as_datetime(xldate, datemode=0, option="to_datetime"):
    """Converts a xls date stamp to a more sensible format.

    Args:
        xldate (str): date stamp in Excel format.
        datemode (int): 0 for 1900-based, 1 for 1904-based.
        option (str): option in ("to_datetime", "to_float", "to_string"), return value

    Returns:
        datetime (datetime object, float, or string).

    """

    # This does not work for numpy-arrays
    try:
        test = datetime.time(0, 0)
    except:
        import datetime
    if option == "to_float":
        d = (xldate - 25589) * 86400.0
    elif option == "to_string":
        d = datetime.datetime(1899, 12, 30) + datetime.timedelta(days=xldate + 1462 * datemode)
        # date_format = "%Y-%m-%d %H:%M:%S:%f" # with microseconds, excel cannot cope with this!
        date_format = "%Y-%m-%d %H:%M:%S"  # without microseconds
        d = d.strftime(date_format)
    else:
        d = datetime.datetime(1899, 12, 30) + datetime.timedelta(days=xldate + 1462 * datemode)
    return d


def Convert2mAhg(c, mass=1.0):
    """Converts capacity in Ah to capacity in mAh/g.

    Args:
        c (float or numpy array): capacity in mA.
        mass (float): cmass in mg.

    Returns:
        float: 1000000 * c / mass
    """
    return 1000000 * c / mass


class fileID(object):
    """class for storing information about the raw-data files.

        This class is used for storing and handling raw-data file information. It is important
        to keep track of when the data was extracted from the raw-data files so that it is
        easy to know if the hdf5-files used for storing "treated" data is up-to-date.

        Attributes:
            name (str): Filename of the raw-data file.
            full_name (str): Filename including path of the raw-data file.
            size (float): Size of the raw-data file.
            last_modified (datetime): Last time of modification of the raw-data file.
            last_accessed (datetime): last time of access of the raw-data file.
            last_info_changed (datetime): st_ctime of the raw-data file.
            location (str): Location of the raw-data file.

        """

    def __init__(self, Filename=None):
        make_defaults = True
        if Filename:
            if os.path.isfile(Filename):
                fid_st = os.stat(Filename)
                self.name = os.path.abspath(Filename)
                self.full_name = Filename
                self.size = fid_st.st_size
                self.last_modified = fid_st.st_mtime
                self.last_accessed = fid_st.st_atime
                self.last_info_changed = fid_st.st_ctime
                self.location = os.path.dirname(Filename)
                make_defaults = False

        if make_defaults:
            self.name = None
            self.full_name = None
            self.size = 0
            self.last_modified = None
            self.last_accessed = None
            self.last_info_changed = None
            self.location = None

    def __str__(self):
        txt = "\nfileID information\n"
        txt += "full name: %s\n" % (self.full_name)
        txt += "name: %s\n" % (self.name)
        txt += "modified: %i\n" % (self.last_modified)
        txt += "size: %i\n" % (self.size)
        return txt

    def populate(self, Filename):
        """Finds the file-stats and populates the class with stat values.

        Args:
            Filename (str): name of the file.
        """

        if os.path.isfile(Filename):
            fid_st = os.stat(Filename)
            self.name = os.path.abspath(Filename)
            self.full_name = Filename
            self.size = fid_st.st_size
            self.last_modified = fid_st.st_mtime
            self.last_accessed = fid_st.st_atime
            self.last_info_changed = fid_st.st_ctime
            self.location = os.path.dirname(Filename)

    def get_raw(self):
        """Get a list with information about the file.

        The returned list contains name, size, last_modified and location.
        """
        return [self.name, self.size, self.last_modified, self.location]

    def get_name(self):
        """Get the filename."""
        return self.name

    def get_size(self):
        """Get the size of the file."""
        return self.size

    def get_last(self):
        """Get last modification time of the file."""
        return self.last_modified


class dataset(object):
    """Object to store data for a test.

    This class is used for storing all the relevant data for a 'run', i.e. all the
    data collected by the tester as stored in the raw-files.

    Attributes:
        test_no (int): test number.
        mass (float): mass of electrode [mg].
        dfdata (pandas.DataFrame): contains the experimental data points.
        dfsummary (pandas.DataFrame): contains summary of the data pr. cycle.
        step_table (pandas.DataFrame): information for each step, used for
                                       defining type of step (charge, discharge, etc.)

    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("created dataset instance")
        self.test_no = None
        self.mass = 1.0  # mass of (active) material (in mg)
        self.no_cycles = 0.0
        self.charge_steps = None  # not in use at the moment
        self.discharge_steps = None  # not in use at the moment
        self.ir_steps = None  # dict # not in use at the moment
        self.ocv_steps = None  # dict # not in use at the moment
        self.nom_cap = 3579  # mAh/g (used for finding c-rates)
        self.mass_given = False
        self.c_mode = True
        self.starts_with = "discharge"
        self.material = "noname"
        self.merged = False
        self.file_errors = None  # not in use at the moment
        self.loaded_from = None  # name of the .res file it is loaded from (can be list if merged)
        self.raw_data_files = []
        self.raw_data_files_length = []
        # self.parent_filename = None # name of the .res file it is loaded from (basename) (can be list if merded)
        # self.parent_filename = if listtype, for file in etc,,, os.path.basename(self.loaded_from)
        self.channel_index = None
        self.channel_number = None
        self.creator = None
        self.item_ID = None
        self.schedule_file_name = None
        self.start_datetime = None
        self.test_ID = None
        self.test_name = None
        self.data = collections.OrderedDict()
        self.summary = collections.OrderedDict()
        self.dfdata = None
        self.dfsummary = None
        self.dfsummary_made = False
        self.step_table = collections.OrderedDict()
        self.step_table_made = False
        self.parameter_table = collections.OrderedDict()
        self.summary_version = 2
        self.step_table_version = 2
        self.cellpy_file_version = 3
        self.datapoint_txt = "Data_Point"

    def __str__(self):
        txt = "_cellpy_data_dataset_class_\n"
        txt += "loaded from file\n"
        if isinstance(self.loaded_from, (list, tuple)):
            for f in self.loaded_from:
                txt += f
                txt += "\n"

        else:
            txt += self.loaded_from
            txt += "\n"
        txt += "   GLOBAL\n"
        txt += "test ID:            %i\n" % self.test_ID
        txt += "material:           %s\n" % self.material
        txt += "mass:               %f mg\n" % self.mass
        txt += "channel index:      %i\n" % self.channel_index
        txt += "test name:          %s\n" % self.test_name
        txt += "creator:            %s\n" % self.creator
        txt += "schedule file name: %s\n" % self.schedule_file_name
        try:
            start_datetime_str = xldate_as_datetime(self.start_datetime)
        except:
            start_datetime_str = "NOT READABLE YET"
        txt += "start-date:         %s\n" % start_datetime_str
        txt += "   DATA:\n"
        txt += str(self.dfdata)
        txt += "   \nSUMMARY:\n"
        txt += str(self.dfsummary)

        return txt

    def makeDataFrame(self):
        """Creates a Pandas DataFrame of the data (dfdata and dfsummary)."""

        self.dfdata = pd.DataFrame(self.data)
        self.dfdata.sort_values(by=self.datapoint_txt)
        self.dfsummary = pd.DataFrame(self.summary).sort_values(by=self.datapoint_txt)


class cellpydata(object):
    """Main class for working and storing data.

    This class is the main work-horse for cellpy where all the functions for reading, selecting, and
    tweaking your data is located. It also contains the header definitions, both for the cellpy hdf5
    format, and for the various cell-tester file-formats that can be read. The class can contain
    several tests and each test is stored in a list.

    Attributes:
        tests (list): list of dataset objects.
    """






    def __init__(self, filenames=None,
                 selected_scans=None,
                 verbose=False, # not in use
                 profile=False,
                 filestatuschecker="size",  # "modified"
                 fetch_onliners=False,
                 tester="arbin",
                 ):
        """

        Returns:
            None:
        """
        self.tester = tester
        self.verbose = verbose
        # self._create_logger(self.verbose)
        self.logger = logging.getLogger(__name__)
        self.logger.info("created cellpydata instance")
        self.logger.debug("debug 1")
        self.logger.error("error 1")
        self.profile = profile
        self.max_res_filesize = 150000000
        self.load_only_summary = False
        self.select_minimal = False
        self.minimum_selection = {}
        self.chunk_size = None # 100000
        self.max_chunks = None
        self.last_chunk = None
        self.load_until_error = False
        self.filestatuschecker = filestatuschecker
        self.raw_datadir = None
        self.cellpy_datadir = None
        self.auto_dirs = True  # search in prm-file for res and hdf5 dirs in loadcel
        self.forced_errors = 0
        self.ensure_step_table = False
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

        self.tests = []
        self.tests_status = []
        self.step_table = None
        self.selected_test_number = None
        self.number_of_tests = 0
        self.cellpy_file_version = 3
        self.use_decrp_functions = True
        self.capacity_modifiers = ['reset', ]
        self.cycle_mode = 'anode'
        self.minimum_selection["arbin"] = ["Data_Point","Test_Time","Step_Time",
                                           "DateTime","Step_Index","Cycle_Index",
                                           "Current","Voltage","Charge_Capacity",
                                           "Discharge_Capacity","Internal_Resistance",
                                           ]
        self.list_of_step_types = ['charge', 'discharge',
                                   'cv_charge', 'cv_discharge',
                                   'charge_cv', 'discharge_cv',
                                   'ocvrlx_up', 'ocvrlx_down', 'ir',
                                   'rest', 'not_known']
        # - options
        self.force_step_table_creation = True
        self.force_all = False  # not used yet - should be used when saving
        self.sep = ";"

        # - headers for out-files

        # summary out column headings
        self.summary_txt_discharge_cap = "Discharge_Capacity(mAh/g)"
        self.summary_txt_charge_cap = "Charge_Capacity(mAh/g)"
        self.summary_txt_cum_charge_cap = "Cumulated_Charge_Capacity(mAh/g)"
        self.summary_txt_coul_eff = "Coulombic_Efficiency(percentage)"
        self.summary_txt_coul_diff = "Coulombic_Difference(mAh/g)"
        self.summary_txt_cum_coul_diff = "Cumulated_Coulombic_Difference(mAh/g)"
        self.summary_txt_discharge_cap_loss = "Discharge_Capacity_Loss(mAh/g)"
        self.summary_txt_charge_cap_loss = "Charge_Capacity_Loss(mAh/g)"
        self.summary_txt_cum_discharge_cap_loss = "Cumulated_Discharge_Capacity_Loss(mAh/g)"
        self.summary_txt_cum_charge_cap_loss = "Cumulated_Charge_Capacity_Loss(mAh/g)"
        self.summary_txt_ir_discharge = "ir_discharge"
        self.summary_txt_ir_charge = "ir_charge"
        self.summary_txt_ocv_1_min = "ocv_first_min"
        self.summary_txt_ocv_2_min = "ocv_second_min"
        self.summary_txt_ocv_1_max = "ocv_first_max"
        self.summary_txt_ocv_2_max = "ocv_second_max"
        self.summary_txt_datetime_txt = "date_time_txt"
        self.summary_txt_endv_discharge = "end_voltage_discharge"
        self.summary_txt_endv_charge = "end_voltage_charge"

        # step table column headings
        self.step_table_txt_test = "test"
        self.step_table_txt_cycle = "cycle"
        self.step_table_txt_step = "step"
        self.step_table_txt_type = "type"
        self.step_table_txt_info = "info"
        self.step_table_txt_I_ = "I_"
        self.step_table_txt_V_ = "V_"
        self.step_table_txt_C_ = "Charge_"
        self.step_table_txt_D_ = "Discharge_"
        self.step_table_txt_post_average = "avr"
        self.step_table_txt_post_stdev = "std"
        self.step_table_txt_post_max = "max"
        self.step_table_txt_post_min = "min"
        self.step_table_txt_post_start = "start"
        self.step_table_txt_post_end = "end"
        self.step_table_txt_post_delta = "delta"
        self.step_table_txt_post_rate = "rate"
        self.step_table_txt_ir = "IR"
        self.step_table_txt_ir_change = "IR_pct_change"

        if self.tester == "arbin":
            # - table names
            self.tablename_normal = "Channel_Normal_Table"
            self.tablename_global = "Global_Table"
            self.tablename_statistic = "Channel_Statistic_Table"
            # - global column headings
            self.applications_path_txt = 'Applications_Path'
            self.channel_index_txt = 'Channel_Index'
            self.channel_number_txt = 'Channel_Number'
            self.channel_type_txt = 'Channel_Type'
            self.comments_txt = 'Comments'
            self.creator_txt = 'Creator'
            self.daq_index_txt = 'DAQ_Index'
            self.item_id_txt = 'Item_ID'
            self.log_aux_data_flag_txt = 'Log_Aux_Data_Flag'
            self.log_chanstat_data_flag_txt = 'Log_ChanStat_Data_Flag'
            self.log_event_data_flag_txt = 'Log_Event_Data_Flag'
            self.log_smart_battery_data_flag_txt = 'Log_Smart_Battery_Data_Flag'
            self.mapped_aux_conc_cnumber_txt = 'Mapped_Aux_Conc_CNumber'
            self.mapped_aux_di_cnumber_txt = 'Mapped_Aux_DI_CNumber'
            self.mapped_aux_do_cnumber_txt = 'Mapped_Aux_DO_CNumber'
            self.mapped_aux_flow_rate_cnumber_txt = 'Mapped_Aux_Flow_Rate_CNumber'
            self.mapped_aux_ph_number_txt = 'Mapped_Aux_PH_Number'
            self.mapped_aux_pressure_number_txt = 'Mapped_Aux_Pressure_Number'
            self.mapped_aux_temperature_number_txt = 'Mapped_Aux_Temperature_Number'
            self.mapped_aux_voltage_number_txt = 'Mapped_Aux_Voltage_Number'
            self.schedule_file_name_txt = 'Schedule_File_Name'
            self.start_datetime_txt = 'Start_DateTime'
            self.test_id_txt = 'Test_ID'
            self.test_name_txt = 'Test_Name'

            # - normal table headings
            self.aci_phase_angle_txt = 'ACI_Phase_Angle'
            self.ac_impedance_txt = 'AC_Impedance'
            self.charge_capacity_txt = 'Charge_Capacity'
            self.charge_energy_txt = 'Charge_Energy'
            self.current_txt = 'Current'
            self.cycle_index_txt = 'Cycle_Index'
            self.data_point_txt = 'Data_Point'
            self.datetime_txt = 'DateTime'
            self.discharge_capacity_txt = 'Discharge_Capacity'
            self.discharge_energy_txt = 'Discharge_Energy'
            self.internal_resistance_txt = 'Internal_Resistance'
            self.is_fc_data_txt = 'Is_FC_Data'
            self.step_index_txt = 'Step_Index'
            self.step_time_txt = 'Step_Time'
            self.test_id_txt = 'Test_ID'
            self.test_time_txt = 'Test_Time'
            self.voltage_txt = 'Voltage'
            self.dv_dt_txt = 'dV/dt'
        else:
            print "this option is not implemented yet"

    def _create_logger(self, verbose = False):
        from cellpy import log
        self.logger = logging.getLogger(__name__)
        log.setup_logging(default_level=logging.DEBUG)


    # def _create_logger(self, verbose = False):
    #     from cellpy.parametres import prmreader
    #     prm = prmreader.read()
    #     logdir = prm.filelogdir
    #     # logdir = r"C:\Scripting\Processing\Celldata\cellpylog"
    #     logfile = "cellpylog.log"
    #     logfilename = os.path.join(logdir, logfile)
    #     # logging.config.fileConfig('logging.ini')
    #     logger = logging.getLogger("cellreader")
    #     logger.setLevel(logging.DEBUG)
    #     # create console handler and set level to debug
    #     ch = logging.StreamHandler()
    #     if verbose:
    #         ch.setLevel(logging.DEBUG)
    #     else:
    #         ch.setLevel(logging.INFO)
    #
    #     # create a file handler and set level
    #     fh = logging.FileHandler(logfilename)
    #     fh.setLevel(logging.DEBUG)
    #
    #     # create formatter
    #     formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    #
    #     # add formatter to ch
    #     ch.setFormatter(formatter)
    #
    #     # add formatter to fh
    #     fh.setFormatter(formatter)
    #
    #     # add ch to logger
    #     logger.addHandler(ch)
    #
    #     # add fh to logger
    #     logger.addHandler(fh)
    #
    #     # logging.basicConfig(filename=logfilename, level=logging.DEBUG)
    #     logging = logger

    def set_raw_datadir(self, directory=None):
        """Set the directory containing .res-files.

        Used for setting directory for looking for res-files. A valid directory name is required.

        Args:
            directory (str): path to res-directory

        Example:
            >>> d = cellpydata()
            >>> directory = r"C:\MyData\Arbindata"
            >>> d.set_raw_datadir(directory)

        """

        if directory is None:
            print "no directory name given"
            return
        if not os.path.isdir(directory):
            print directory
            print "directory does not exist"
            return
        self.raw_datadir = directory

    def set_cellpy_datadir(self, directory=None):
        """Set the directory containing .hdf5-files.

        Used for setting directory for looking for hdf5-files. A valid directory name is required.

        Args:
            directory (str): path to hdf5-directory

        Example:
            >>> d = cellpydata()
            >>> directory = r"C:\MyData\HDF5"
            >>> d.set_raw_datadir(directory)

        """

        if directory is None:
            print "no directory name given"
            return
        if not os.path.isdir(directory):
            print "directory does not exist"
            return
        self.cellpy_datadir = directory

    def check_file_ids(self, rawfiles, cellpyfile):
        """Check the stats for the files (raw-data and cellpy hdf5).

        This function checks if the hdf5 file and the res-files have the same
        timestamps etc to find out if we need to bother to load .res -files.

        Args:
            cellpyfile (str): filename of the cellpy hdf5-file.
            rawfiles (list of str): name(s) of raw-data file(s).


        Returns:
            False if the raw files are newer than the cellpy hdf5-file (update needed).
            If return_res is True it also returns list of raw-file_names as second argument.
            """

        txt = "check_file_ids\n  checking file ids - using '%s'" % (self.filestatuschecker)

        self.logger.debug(txt)
        self.logger.info(txt)

        ids_cellpy_file = self._check_cellpy_file(cellpyfile)

        if not ids_cellpy_file:
            self.logger.debug("hdf5 file does not exist - needs updating")
            return False

        ids_raw = self._check_raw(rawfiles)
        similar = self._compare_ids(ids_raw, ids_cellpy_file)

        if not similar:
            self.logger.debug("hdf5 file needs updating")
            return False
        else:
            self.logger.debug("hdf5 file is updated")
            return True

    def _check_raw(self, file_names, abort_on_missing=False):
        """Get the file-ids for the res_files."""

        strip_file_names = True
        check_on = self.filestatuschecker
        if not self._is_listtype(file_names):
            file_names = [file_names, ]

        ids = dict()
        for f in file_names:
            self.logger.debug("checking res file")
            self.logger.debug(f)
            fid = fileID(f)
            self.logger.debug(fid)
            if fid.name is None:
                print "file does not exist:"
                print f
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

        strip_filenames = True
        check_on = self.filestatuschecker
        self.logger.debug("checking cellpy-file")
        self.logger.debug(filename)
        if not os.path.isfile(filename):
            self.logger.debug("cellpy-file does not exist")
            return None

        store = pd.HDFStore(filename)
        try:
            fidtable = store.select("cellpydata/fidtable")
        except:
            print "no fidtable - you should update your hdf5-file"
            fidtable = None
        finally:
            store.close()
        if fidtable is not None:
            raw_data_files, raw_data_files_length = self._convert2fid_list(fidtable)
            txt = "contains %i res-files" % (len(raw_data_files))
            self.logger.debug(txt)
            ids = dict()
            for fid in raw_data_files:
                full_name = fid.full_name
                size = fid.size
                mod = fid.last_modified
                txt = "\nfileID information\nfull name: %s\n" % (full_name)
                txt += "modified: %i\n" % (mod)
                txt += "size: %i\n" % (size)
                self.logger.debug(txt)
                if strip_filenames:
                    name = os.path.basename(full_name)
                else:
                    name = full_name
                if check_on == "size":
                    ids[name] = int(fid.size)
                elif check_on == "modified":
                    ids[name] = int(fid.last_modified)
                else:
                    ids[name] = int(fid.last_accessed)

        else:
            ids = dict()
        return ids

    def _compare_ids(self, ids_res, ids_cellpy_file):
        # Check if the ids are "the same", i.e. if the ids indicates wether new
        # data is likely to be found in the res-files checking length

        similar = True
        l_res = len(ids_res)
        l_cellpy = len(ids_cellpy_file)
        if l_res == l_cellpy and l_cellpy > 0:
            for name, value in ids_res.items():
                if ids_cellpy_file[name] != value:
                    similar = False
        else:
            similar = False

        return similar

    def _find_resfiles_old(self, cellpyfile, counter_min=1, counter_max=10):
        # function to find res files by locating all files of the form
        # (date-label)_(slurry-label)_(el-label)_(cell-type)_*
        # UNDER DEVELOPMENT

        counter_sep = "_"
        counter_digits = 2
        res_extension = ".res"
        res_dir = self.raw_datadir
        resfiles = []
        cellpyfile = os.path.basename(cellpyfile)
        cellpyfile = os.path.splitext(cellpyfile)[0]
        for j in range(counter_min, counter_max + 1):
            lookFor = "%s%s%s%s" % (cellpyfile, counter_sep,
                                    str(j).zfill(counter_digits),
                                    res_extension)

            lookFor = os.path.join(res_dir, lookFor)
            if os.path.isfile(lookFor):
                resfiles.append(lookFor)

        return resfiles

    def loadcell(self, raw_files, cellpy_file=None, mass=None,
                 summary_on_raw=False, summary_ir=True, summary_ocv=False,
                 summary_end_v=True, only_summary=False, only_first=False, force_raw=False):
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
            only_first (bool): only use the first file fitting search criteria
            force_raw (bool): only use raw-files

        Example:

            >>> srnos = my_dbreader.select_batch("testing_new_solvent")
            >>> cell_datas = []
            >>> for srno in srnos:
            >>> ... my_run_name = my_dbreader.get_cell_name(srno)
            >>> ... mass = my_dbreader.get_mass(srno)
            >>> ... rawfiles, cellpyfiles = filefinder.search_for_files(my_run_name)
            >>> ... cell_data = cellreader.cellpydata()
            >>> ... cell_data.loadcell(raw_files = rawfiles, cellpy_file = cellpyfiles)
            >>> ... cell_data.set_mass(mass)
            >>> ... if not cell_data.summary_exists:
            >>> ...     cell_data.make_summary() # etc. etc.
            >>> ... cell_datas.append(cell_data)
            >>>
        """

        # This is a part of a dramatic API change. It will not be possible to
        # load more than one set of tests (i.e. one single cellpy-file or
        # several raw-files that will be automatically merged)
        self.logger.info("started loadcell")
        if cellpy_file is None:
            similar = False
        elif force_raw:
            similar = False
        else:
            similar = self.check_file_ids(raw_files, cellpy_file)

        if only_summary:
            self.load_only_summary = True
        else:
            self.load_only_summary = False

        if not similar:
            self.load_raw(raw_files)
            not_empty = self.tests_status
            if mass:
                self.set_mass(mass)
            if summary_on_raw:
                if not_empty:
                    self.make_summary(all_tests=False, find_ocv=summary_ocv,
                                      find_ir=summary_ir,
                                      find_end_voltage=summary_end_v)
                else:
                    self.logger.debug("Cannot make summary for empty set")

        else:
            self.load(cellpy_file)

    def load_raw(self, file_names=None):
        """Load a raw data-file.

        Args:
            file_names (list of raw-file names:
        """
        if file_names:
            self.file_names = file_names

        if not isinstance(file_names, (list, tuple)):
            self.file_names = [file_names,]

        file_type = self.tester
        if file_type == "arbin":
            raw_file_loader = self._loadres
        else:
            raw_file_loader = self._loadres # only arbin available at the moment

        test_number = 0
        test = None
        for f in self.file_names:
            new_tests = raw_file_loader(f)
            if test is not None:
                new_tests[test_number] = self._append(test[test_number], new_tests[test_number])
                for raw_data_file, file_size in zip(new_tests[test_number].raw_data_files,
                                                    new_tests[test_number].raw_data_files_length):
                    test[test_number].raw_data_files.append(raw_data_file)
                    test[test_number].raw_data_files_length.append(file_size)
            else:
                test = new_tests
        if test:
            self.tests.append(test[test_number])
        else:
            print "no new tests added"
        self.number_of_tests = len(self.tests)
        self.tests_status = self._validate_tests()

    def loadres(self, filenames=None, check_file_type=True):
        """Loads the data into the datastructure."""
        # TODO: use type-checking
        txt = "number of tests: %i" % len(self.file_names)
        self.logger.debug(txt)
        test_number = 0
        counter = 0
        filetype = "res"

        # checking if new file_names is provided or if we should use the stored (self.file_names)
        # values
        if filenames:
            self.file_names = filenames
            if not self._is_listtype(self.file_names):
                self.file_names = [self.file_names]

        # self.file_names is now a list of file_names or list of lists of file_names

        for f in self.file_names:  # iterating through list
            self.logger.debug(f)
            list_type = self._is_listtype(f)
            counter += 1

            if not list_type:  # item contains contains only one filename, f=filename_01, so load it
                if check_file_type:
                    filetype = self._check_file_type(f)
                if filetype == "res":
                    newtests = self._loadres(f)
                elif filetype == "h5":
                    newtests = self._load_hdf5(f)
            else:  # item contains several file_names (sets of data) or is a single valued list
                if not len(f) > 1:  # f = [file_01,] single valued list, so load it
                    if check_file_type:
                        filetype = self._check_file_type(f[0])
                    if filetype == "res":
                        newtests = self._loadres(f[0])

                    elif filetype == "h5":
                        newtests = self._load_hdf5(f[0])
                else:  # f = [file_01, file_02, ....] multiple files, so merge them
                    txt = "multiple files - merging"
                    self.logger.debug(txt)
                    first_test = True
                    newtests = None
                    for f2 in f:
                        txt = "file: %s" % (f2)
                        self.logger.debug(txt)
                        if check_file_type:
                            filetype = self._check_file_type(f2)
                        if filetype == "res":
                            newtests1 = self._loadres(f2)  # loading file

                        # print "loaded file",
                        # print f2

                        if first_test:
                            newtests = newtests1
                            first_test = False
                        else:
                            newtests[test_number] = self._append(newtests[test_number], newtests1[test_number])
                            for raw_data_file, file_size in zip(newtests1[test_number].raw_data_files,
                                                                newtests1[test_number].raw_data_files_length):
                                newtests[test_number].raw_data_files.append(raw_data_file)
                                newtests[test_number].raw_data_files_length.append(file_size)

            if newtests:
                for test in newtests:
                    self.tests.append(test)
            else:
                self.logger.debug("Could not load any files for this set")
                self.logger.debug("Making it an empty test")
                self.tests.append(self._empty_test())

        txt = " ok"
        self.logger.debug(txt)
        self.number_of_tests = len(self.tests)
        txt = "number of tests: %i" % self.number_of_tests
        self.logger.debug(txt)
        # validating tests
        self.tests_status = self._validate_tests()

    #        if separate_datasets:
    #            print "not implemented yet"
    #        else:
    #            if not tests:
    #                tests=range(len(self.tests))
    #            first_test = True
    #            for test_number in tests:
    #                if first_test:
    #                    test = self.tests[test_number]
    #                    first_test = False
    #                else:
    #                    test = self._append(test,self.tests[test_number])
    #            self.tests = [test]
    #            self.number_of_tests=1

    def _validate_tests(self, level=0):
        level = 0
        # simple validation for finding empty tests - should be expanded to
        # find not-complete tests, tests with missing prms etc
        v = []
        if level == 0:
            for test in self.tests:
                v.append(self._is_not_empty_test(test))
        return v

    def _is_not_empty_test(self, test):
        if test is self._empty_test():
            return False
        else:
            return True

    def _report_empty_test(self):
        print "empty set"

    def _empty_test(self):
        return None

    def _check64bit(self, System="python"):
        if System == "python":
            try:
                return sys.maxsize > 2147483647
            except:
                return sys.maxint > 2147483647
        elif System == "os":
            import platform
            pm = platform.machine()
            if pm != ".." and pm.endswith('64'):  # recent Python (not Iron)
                return True
            else:
                if 'PROCESSOR_ARCHITEW6432' in os.environ:
                    return True  # 32 bit program running on 64 bit Windows
                try:
                    return os.environ['PROCESSOR_ARCHITECTURE'].endswith('64')  # 64 bit Windows 64 bit program
                except IndexError:
                    pass  # not Windows
                try:
                    return '64' in platform.architecture()[0]  # this often works in Linux
                except:
                    return False  # is an older version of Python, assume also an older os (best we can guess)

    def load(self,cellpy_file):
        """Loads a cellpy file.
        """

        if self.cellpy_file_version <= 3:
            new_tests = self._load_hdf5(cellpy_file)
        else:
            new_tests = []
            print "This cellpy-file version is not supported by current reader (try to update cellpy)."

        if new_tests:
            for test in new_tests:
                self.tests.append(test)
        else:
            # raise LoadError
            print "Could not load"
            print cellpy_file

        self.number_of_tests = len(self.tests)
        self.tests_status = self._validate_tests()

    def _load_hdf5(self, filename):
        """Load a cellpy-file.

        Args:
            filename (str):

        Returns:
            loaded tests (dataset-object)
        """
        # loads from hdf5 formatted cellpy-file
        if not os.path.isfile(filename):
            print "file does not exist"
            print "  ",
            print filename
            sys.exit()
        print "c",
        store = pd.HDFStore(filename)
        data = dataset()
        data.dfsummary = store.select("cellpydata/dfsummary")
        data.dfdata = store.select("cellpydata/dfdata")
        try:
            data.step_table = store.select("cellpydata/step_table")
            data.step_table_made = True
        except:
            data.step_table = None
            data.step_table_made = False
        infotable = store.select("cellpydata/info")

        try:
            fidtable = store.select("cellpydata/fidtable")
            fidtable_selected = True
        except:
            fidtable = []
            print "no fidtable - you should update your hdf5-file"
            fidtable_selected = False
        self.logger.debug("  h5")
        # this does not yet allow multiple sets
        newtests = []  # but this is ready when that time comes
        data.test_no = self._extract_from_dict(infotable, "test_no")
        data.mass = self._extract_from_dict(infotable, "mass")
        data.mass_given = True
        data.loaded_from = filename
        data.charge_steps = self._extract_from_dict(infotable, "charge_steps")
        data.channel_index = self._extract_from_dict(infotable, "channel_index")
        data.channel_number = self._extract_from_dict(infotable, "channel_number")
        data.creator = self._extract_from_dict(infotable, "creator")
        data.schedule_file_name = self._extract_from_dict(infotable, "schedule_file_name")
        data.start_datetime = self._extract_from_dict(infotable, "start_datetime")
        data.test_ID = self._extract_from_dict(infotable, "test_ID")
        data.test_name = self._extract_from_dict(infotable, "test_name")
        try:
            data.cellpy_file_version = self._extract_from_dict(infotable, "cellpy_file_version")
        except:
            data.cellpy_file_version = None

        try:
            data.step_table_made = self._extract_from_dict(infotable, "step_table_made")
        except:
            data.step_table_made = None

        if fidtable_selected:
            data.raw_data_files, data.raw_data_files_length = self._convert2fid_list(fidtable)
        else:
            data.raw_data_files = None
            data.raw_data_files_length = None
        newtests.append(data)
        store.close()
        # self.tests.append(data)
        print "->"
        return newtests

    def _convert2fid_list(self, tbl):
        self.logger.debug("_convert2fid_list")
        fids = []
        lengths = []
        counter = 0
        for item in tbl["raw_data_name"]:
            fid = fileID()
            fid.name = item
            fid.full_name = tbl["raw_data_full_name"][counter]
            fid.size = tbl["raw_data_size"][counter]
            fid.last_modified = tbl["raw_data_last_modified"][counter]
            fid.last_accessed = tbl["raw_data_last_accessed"][counter]
            fid.last_info_changed = tbl["raw_data_last_info_changed"][counter]
            fid.location = tbl["raw_data_location"][counter]
            l = tbl["raw_data_files_length"][counter]
            counter += 1
            fids.append(fid)
            lengths.append(l)
        return fids, lengths

    def _clean_up_loadres(self, cur, conn, filename):
        if cur is not None:
            cur.close()  # adodbapi
        if conn is not None:
            conn.close()  # adodbapi
        if os.path.isfile(filename):
            try:
                os.remove(filename)
            except WindowsError as e:
                print "could not remove tmp-file"
                print filename
                print e

    def _loadres(self, file_name=None):
        """Loads data from arbin .res files.

        Args:
            file_name (str): path to .res file.

        Returns:
            new_tests (list of data objects), FileError

        """
        new_tests = []
        # -------checking existence of file--------
        if not os.path.isfile(file_name):
            print "Missing file_\n   %s" % (file_name)

        # -------checking file size etc------------
        filesize = os.path.getsize(file_name)
        hfilesize = humanize_bytes(filesize)
        txt = "Filesize: %i (%s)" % (filesize, hfilesize)
        self.logger.debug(txt)
        if filesize > self.max_res_filesize and not self.load_only_summary:
            error_message = "\nERROR (_loadres):\n"
            error_message += "%s > %s - File is too big!\n" % (hfilesize, humanize_bytes(self.max_res_filesize))
            error_message += "(edit self.max_res_filesize)\n"
            print error_message
            return None
            # sys.exit(FileError)

        # ------making temporary file-------------
        temp_dir = tempfile.gettempdir()
        temp_filename = os.path.join(temp_dir, os.path.basename(file_name))
        shutil.copy2(file_name, temp_dir)
        print ".",

        # ------connecting to the .res database----
        constr = self.__get_res_connector(file_name, temp_filename)
        if USE_ADO:
            conn = dbloader.connect(constr)  # adodbapi
        else:
            conn = dbloader.connect(constr, autocommit=True)
        print ".",

        # ------get the global table-----------------
        sql = "select * from %s" % self.tablename_global
        global_data_df = pd.read_sql_query(sql, conn)
        # col_names = list(global_data_df.columns.values)
        tests = global_data_df[self.test_id_txt]
        number_of_sets = len(tests)
        print ".",

        for test_no in range(number_of_sets):
            data = dataset()
            data.test_no = test_no
            data.loaded_from = file_name
            # creating fileID
            fid = fileID(file_name)
            # data.parent_filename = os.path.basename(file_name)# name of the .res file it is loaded from
            data.channel_index = int(global_data_df[self.channel_index_txt][test_no])
            data.channel_number = int(global_data_df[self.channel_number_txt][test_no])
            data.creator = global_data_df[self.creator_txt][test_no]
            data.item_ID = global_data_df[self.item_id_txt][test_no]
            data.schedule_file_name = global_data_df[self.schedule_file_name_txt][test_no]
            data.start_datetime = global_data_df[self.start_datetime_txt][test_no]
            data.test_ID = int(global_data_df[self.test_id_txt][test_no])
            data.test_name = global_data_df[self.test_name_txt][test_no]
            data.raw_data_files.append(fid)

            # ------------------------------------------
            # ---loading-normal-data--------------------
            length_of_test, normal_df = self._load_res_normal_table(conn,data.test_ID)
            # ---loading-statistic-data-----------------
            sql = "select * from %s where %s=%s order by %s" % (self.tablename_statistic,
                                                                self.test_id_txt,
                                                                data.test_ID,
                                                                self.data_point_txt)
            summary_df = pd.read_sql_query(sql, conn)
            data.dfsummary = summary_df
            data.dfdata = normal_df
            data.raw_data_files_length.append(length_of_test)
            new_tests.append(data)
            self._clean_up_loadres(None, conn, temp_filename)
            print ". <-"
        return new_tests

    def _load_res_normal_table(self, conn, test_ID):
        if self.load_only_summary:
            return 0

        if self.select_minimal:
            columns = self.minimum_selection["arbin"]
            columns_txt = ", ".join(["%s"] * len(columns)) % tuple(columns)
        else:
            columns_txt = "*"

        sql_1 = "select %s " % (columns_txt)
        sql_2 = "from %s " % (self.tablename_normal)
        sql_3 = "where %s=%s " % (self.test_id_txt, test_ID)
        sql_4 = "order by %s" % (self.data_point_txt)
        sql = sql_1 + sql_2 + sql_3 + sql_4

        if not self.chunk_size:
            normal_df = pd.read_sql_query(sql, conn)
            length_of_test = normal_df.shape[0]
        else:
            normal_df_reader = pd.read_sql_query(sql, conn, chunksize=self.chunk_size)
            if not self.last_chunk:
                normal_df = normal_df_reader.next()
                chunk_number = 1
            else:
                chunk_number = 0
                for j in range(self.last_chunk):
                    normal_df = normal_df_reader.next()  # TODO: This is SLOW - should use itertools.islice
                    chunk_number += 1

            for chunk in normal_df_reader:

                if self.load_until_error:
                    try:
                        normal_df = pd.concat([normal_df,chunk], ignore_index=True)
                        print "*",
                    except MemoryError:
                        print " - Could not read complete file (MemoryError)."
                        print "Last successfully loaded chunk number:", chunk_number
                        print "Chunk size:", self.chunk_size
                        break
                elif self.max_chunks:
                    if chunk_number < self.max_chunks:
                        normal_df = pd.concat([normal_df,chunk], ignore_index=True)
                        print "*",
                    else:
                        break
                else:
                    normal_df = pd.concat([normal_df, chunk], ignore_index=True)
                chunk_number += 1
            length_of_test = normal_df.shape[0]

        return length_of_test, normal_df

    def __get_res_global_table(self, cur):
        sql = "select * from %s" % self.tablename_global
        cur.execute(sql)  # adodbapi
        col_names = [i[0] for i in cur.description]  # adodbapi
        global_data = collections.OrderedDict()
        for cn in col_names:
            global_data[cn] = []
        self.logger.debug("Starting to load global table from .res file (cur.fetchall())")
        all_data = cur.fetchall()
        self.logger.debug("Finished to load global table from .res file (cur.fetchall())")
        return all_data, col_names, global_data

    def __get_res_connector(self, Filename, temp_filename):
        # -------checking bit and os----------------
        is64bit_python = self._check64bit(System="python")
        # is64bit_os = self._check64bit(System = "os")
        if USE_ADO:
            if is64bit_python:
                print "using 64 bit python"
                constr = 'Provider=Microsoft.ACE.OLEDB.12.0; Data Source=%s' % temp_filename
            else:
                constr = 'Provider=Microsoft.Jet.OLEDB.4.0; Data Source=%s' % temp_filename

        else:
            constr = 'Driver={Microsoft Access Driver (*.mdb, *.accdb)};Dbq=' + temp_filename

        return constr

    def merge(self, tests=None, separate_datasets=False):
        """This function merges datasets into one set."""
        # note: several of the final-test runs contains a first cycle with only delith
        # giving zero as lithiation capacity for that cycle
        print "merging"
        if separate_datasets:
            print "not implemented yet"
        else:
            if tests is None:
                tests = range(len(self.tests))
            first_test = True
            for test_number in tests:
                if first_test:
                    test = self.tests[test_number]
                    first_test = False
                else:
                    test = self._append(test, self.tests[test_number])
                    for raw_data_file, file_size in zip(self.tests[test_number].raw_data_files,
                                                        self.tests[test_number].raw_data_files_length):
                        test.raw_data_files.append(raw_data_file)
                        test.raw_data_files_length.append(file_size)
            self.tests = [test]
            self.number_of_tests = 1

    def _append(self, t1, t2, merge_summary=True, merge_step_table=True):
        test = t1
        # finding diff of time
        start_time_1 = t1.start_datetime
        start_time_2 = t2.start_datetime
        diff_time = xldate_as_datetime(start_time_2) - xldate_as_datetime(start_time_1)
        diff_time = diff_time.total_seconds()
        sort_key = self.datetime_txt  # DateTime
        # mod data points for set 2
        data_point_header = self.data_point_txt
        last_data_point = max(t1.dfdata[data_point_header])
        t2.dfdata[data_point_header] = t2.dfdata[data_point_header] + last_data_point
        # mod cycle index for set 2
        cycle_index_header = self.cycle_index_txt
        last_cycle = max(t1.dfdata[cycle_index_header])
        t2.dfdata[cycle_index_header] = t2.dfdata[cycle_index_header] + last_cycle
        # mod test time for set 2
        test_time_header = self.test_time_txt
        t2.dfdata[test_time_header] = t2.dfdata[test_time_header] + diff_time
        # merging
        dfdata2 = pd.concat([t1.dfdata, t2.dfdata], ignore_index=True)

        # checking if we already have made a summary file of these datasets
        if t1.dfsummary_made and t2.dfsummary_made:
            dfsummary_made = True
        else:
            dfsummary_made = False
        # checking if we already have made step tables for these datasets
        if t1.step_table_made and t2.step_table_made:
            step_table_made = True
        else:
            step_table_made = False

        if merge_summary:
            # check if (self-made) summary exists.
            self_made_summary = True
            try:
                test_it = t1.dfsummary[cycle_index_header]
            except:
                self_made_summary = False
                # print "have not made a summary myself"
            try:
                test_it = t2.dfsummary[cycle_index_header]
            except:
                self_made_summary = False

            if self_made_summary:
                # mod cycle index for set 2
                last_cycle = max(t1.dfsummary[cycle_index_header])
                t2.dfsummary[cycle_index_header] = t2.dfsummary[cycle_index_header] + last_cycle
                # mod test time for set 2
                t2.dfsummary[test_time_header] = t2.dfsummary[test_time_header] + diff_time
                # to-do: mod all the cumsum stuff in the summary (best to make summary after merging)
                # merging
            else:
                t2.dfsummary[data_point_header] = t2.dfsummary[data_point_header] + last_data_point
            dfsummary2 = pd.concat([t1.dfsummary, t2.dfsummary], ignore_index=True)

            test.dfsummary = dfsummary2

        if merge_step_table:
            if step_table_made:
                cycle_index_header = self.cycle_index_txt
                t2.step_table[self.step_table_txt_cycle] = t2.dfdata[self.step_table_txt_cycle] + last_cycle
                step_table2 = pd.concat([t1.step_table, t2.step_table], ignore_index=True)
                test.step_table = step_table2
            else:
                self.logger.debug("could not merge step tables (non-existing) - create them first!")

        # then the rest...
        test.no_cycles = max(dfdata2[cycle_index_header])
        test.dfdata = dfdata2
        test.merged = True
        # to-do:
        #        self.test_no = None
        #        self.charge_steps = None
        #        self.discharge_steps = None
        #        self.ir_steps = None # dict
        #        self.ocv_steps = None # dict
        #        self.loaded_from = None # name of the .res file it is loaded from (can be list if merded)
        #        #self.parent_filename = None # name of the .res file it is loaded from (basename) (can be list if merded)
        #        #self.parent_filename = if listtype, for file in etc,,, os.path.basename(self.loaded_from)
        #        self.channel_index = None
        #        self.channel_number = None
        #        self.creator = None
        #        self.item_ID = None
        #        self.schedule_file_name = None
        #        self.test_ID = None
        #        self.test_name = None

        return test

    # --------------iterate-and-find-in-data----------------------------------------

    def _validate_test_number(self, n, check_for_empty=True):
        # Returns test_number (or None if empty)
        # Remark! _is_not_empty_test returns True or False

        if n != None:
            v = n
        else:
            if self.selected_test_number == None:
                v = 0
            else:
                v = self.selected_test_number
        # check if test is empty
        if check_for_empty:
            not_empty = self._is_not_empty_test(self.tests[v])
            if not_empty:
                return v
            else:
                return None
        else:
            return v

    def _validata_step_table(self, test_number=None, simple=False):
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        step_index_header = self.step_index_txt
        self.logger.debug("*** validating step table")
        d = self.tests[test_number].dfdata
        s = self.tests[test_number].step_table

        if not self.tests[test_number].step_table_made:
            return False

        no_cycles_dfdata = np.amax(d[self.cycle_index_txt])
        no_cycles_step_table = np.amax(s[self.step_table_txt_cycle])

        if simple:
            self.logger.debug("  (simple)")
            if no_cycles_dfdata == no_cycles_step_table:
                return True
            else:
                return False

        else:
            validated = True
            if no_cycles_dfdata != no_cycles_step_table:
                self.logger.debug("  differ in no. of cycles")
                validated = False
            else:
                for j in range(1, no_cycles_dfdata + 1):
                    cycle_number = j
                    no_steps_dfdata = len(np.unique(d[d[self.cycle_index_txt] == cycle_number][self.step_index_txt]))
                    no_steps_step_table = len(s[s[self.step_table_txt_cycle] == cycle_number][self.step_table_txt_step])
                    if no_steps_dfdata != no_steps_step_table:
                        validated = False
                        txt = "Error in step table (cycle: %i) d: %i, s:%i)" % (cycle_number,
                                                                                no_steps_dfdata,
                                                                                no_steps_step_table)

                        self.logger.debug(txt)
            return validated

    def print_step_table(self, test_number=None):
        """Print the step table."""
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        st = self.tests[test_number].step_table
        print st

    def get_step_numbers(self, steptype='charge', allctypes=True, pdtype=False, cycle_number=None, test_number=None):
        """Get the step numbers of selected type.

        Returns the selected step_numbers for the  elected type of step(s).

        Args:
            steptype (string): string identifying type of step.
            allctypes (bool): get all types of charge (or discharge).
            pdtype (bool): return results as pandas.DataFrame
            cycle_number (int): selected cycle, selects all if not set.
            test_number (int): test number (default first) (usually not used).

        Returns:
            List of step numbers corresponding to the selected steptype. Returns a pandas.DataFrame
            instead of a list if pdtype is set to True.

        Example:
            >>> my_charge_steps = cellpydata.get_step_numbers("charge", cycle_number = 3)
            >>> print my_charge_steps
            [5,8]

        """
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return

        # check if step_table is there
        if not self.tests[test_number].step_table_made:
            self.logger.debug("step_table not made")

            if self.force_step_table_creation or self.force_all:
                self.logger.debug("creating step_table for")
                self.logger.debug(self.tests[test_number].loaded_from)
                # print "CREAING STEP-TABLE"
                self.create_step_table(test_number=test_number)

            else:
                print "ERROR! Cannot use get_steps: create step_table first"
                print " you could use find_step_numbers method instead"
                print " (but I don't recommend it)"
                return None

        # check if steptype is valid
        steptype = steptype.lower()
        steptypes = []
        helper_step_types = ['ocv', 'charge_discharge']
        valid_step_type = True
        if steptype in self.list_of_step_types:
            steptypes.append(steptype)
        else:
            txt = "%s is not a valid core steptype" % (steptype)
            if steptype in helper_step_types:
                txt = "but a helper steptype"
                if steptype == 'ocv':
                    steptypes.append('ocvrlx_up')
                    steptypes.append('ocvrlx_down')
                elif steptype == 'charge_discharge':
                    steptypes.append('charge')
                    steptypes.append('discharge')
            else:
                valid_step_type = False
            self.logger.debug(txt)
        if not valid_step_type:
            return None

        # in case of selection allctypes, then modify charge, discharge
        if allctypes:
            add_these = []
            for st in steptypes:
                if st in ['charge', 'discharge']:
                    st1 = st + '_cv'
                    add_these.append(st1)
                    st1 = 'cv_' + st
                    add_these.append(st1)
            for st in add_these:
                steptypes.append(st)

        self.logger.debug("Your steptypes:")
        self.logger.debug(steptypes)

        # retrieving step_table (for convinience)
        st = self.tests[test_number].step_table
        # retrieving cycle numbers
        if cycle_number is None:
            # print "cycle number is none"
            cycle_numbers = self.get_cycle_numbers(test_number)
        else:
            cycle_numbers = [cycle_number, ]

        if pdtype:
            self.logger.debug("out as panda dataframe")
            out = st[st['type'].isin(steptypes) & st['cycle'].isin(cycle_numbers)]
            return out

        # if not pdtype, return a dict instead
        self.logger.debug("out as dict; out[cycle] = [s1,s2,...]")
        self.logger.debug("(same behaviour as find_step_numbers)")
        out = dict()
        for cycle in cycle_numbers:
            steplist = []
            for s in steptypes:
                step = st[(st['type'] == s) & (st['cycle'] == cycle)]['step'].tolist()
                for newstep in step:
                    steplist.append(int(newstep))
                    # int(step.iloc[0])
                    # self.is_empty(steps)
            if not steplist:
                steplist = [0]
            out[cycle] = steplist
        return out

    def _extract_step_values(self, f):
        # ['cycle', 'step',
        # 'I_avr', 'I_std', 'I_max', 'I_min', 'I_start', 'I_end', 'I_delta', 'I_rate',
        # 'V_avr', 'V_std', 'V_max', 'V_min', 'V_start', 'V_end', 'V_delta', 'V_rate',
        # 'type', 'info']

        # --- defining header txts ----
        current_hdtxt = self.current_txt
        voltage_hdtxt = self.voltage_txt
        steptime_hdtxt = self.step_time_txt
        ir_hdtxt = self.internal_resistance_txt
        ir_change_hdtxt = self.step_table_txt_ir_change
        charge_hdtxt = self.charge_capacity_txt
        discharge_hdtxt = self.discharge_capacity_txt

        # print f.head()

        # ---time----
        t_start = f.iloc[0][steptime_hdtxt]
        t_end = f.iloc[-1][steptime_hdtxt]
        t_delta = t_end - t_start  # OBS! will be used as denominator

        # ---current-
        I_avr = f[current_hdtxt].mean()
        I_std = f[current_hdtxt].std()
        I_max = f[current_hdtxt].max()
        I_min = f[current_hdtxt].min()
        I_start = f.iloc[0][current_hdtxt]
        I_end = f.iloc[-1][current_hdtxt]

        # I_delta = I_end-I_start
        I_delta = self._percentage_change(I_start, I_end, default_zero=True)
        I_rate = self._fractional_change(I_delta, t_delta)

        # ---voltage--
        V_avr = f[voltage_hdtxt].mean()
        V_std = f[voltage_hdtxt].std()
        V_max = f[voltage_hdtxt].max()
        V_min = f[voltage_hdtxt].min()
        V_start = f.iloc[0][voltage_hdtxt]
        V_end = f.iloc[-1][voltage_hdtxt]

        # V_delta = V_end-V_start
        V_delta = self._percentage_change(V_start, V_end, default_zero=True)
        V_rate = self._fractional_change(V_delta, t_delta)

        # ---charge---
        C_avr = f[charge_hdtxt].mean()
        C_std = f[charge_hdtxt].std()
        C_max = f[charge_hdtxt].max()
        C_min = f[charge_hdtxt].min()
        C_start = f.iloc[0][charge_hdtxt]
        C_end = f.iloc[-1][charge_hdtxt]

        C_delta = self._percentage_change(C_start, C_end, default_zero=True)
        C_rate = self._fractional_change(C_delta, t_delta)

        # ---discharge---
        D_avr = f[discharge_hdtxt].mean()
        D_std = f[discharge_hdtxt].std()
        D_max = f[discharge_hdtxt].max()
        D_min = f[discharge_hdtxt].min()
        D_start = f.iloc[0][discharge_hdtxt]
        D_end = f.iloc[-1][discharge_hdtxt]

        D_delta = self._percentage_change(D_start, D_end, default_zero=True)
        D_rate = self._fractional_change(D_delta, t_delta)


        # ---internal resistance ----
        IR = f.iloc[0][ir_hdtxt]
        IR_pct_change = f.iloc[0][ir_change_hdtxt]

        # ---output--
        out = [I_avr, I_std, I_max, I_min, I_start, I_end, I_delta, I_rate,
               V_avr, V_std, V_max, V_min, V_start, V_end, V_delta, V_rate,
               C_avr, C_std, C_max, C_min, C_start, C_end, C_delta, C_rate,
               D_avr, D_std, D_max, D_min, D_start, D_end, D_delta, D_rate,
               IR, IR_pct_change, ]
        return out



    def create_step_table(self, test_number=None):
        """ Create a table (v.0.2) that contains summary information for each step.

        This function creates a table containing information about the different steps
        for each cycle and, based on that, decides what type of step it is (e.g. charge)
        for each cycle.

        The format of the step_table is:

            index - cycleno - stepno - \

            Current info (average, stdev, max, min, start, end, delta, rate) - \

            Voltage info (average,  stdev, max, min, start, end, delta, rate) - \

            Type (from pre-defined list) - \

            Info

        Header names (pr. 03.03.2016):

            'cycle', 'step',
            'I_avr', 'I_std', 'I_max', 'I_min', 'I_start', 'I_end', 'I_delta', 'I_rate',
            'V_avr'...,
            'C_avr'...,
            'D_avr'...,
            'IR','IR_pct_change',
            'type', 'info'

        Remark! x_delta is given in percentage.
        """
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return

        cycle_index_header = self.cycle_index_txt
        step_index_header = self.step_index_txt

        step_table_txt_cycle = self.step_table_txt_cycle
        step_table_txt_step = self.step_table_txt_step
        step_table_txt_type = self.step_table_txt_type
        step_table_txt_info = self.step_table_txt_info
        step_table_txt_ir = self.step_table_txt_ir
        step_table_txt_ir_change = self.step_table_txt_ir_change

        # -------------create an "empty" df -----------------------------------

        # --- defining column names ---
        # (should probably migrate this to own function and add to self)

        columns = [step_table_txt_cycle, step_table_txt_step]
        columns_end = [self.step_table_txt_post_average,
                       self.step_table_txt_post_stdev,
                       self.step_table_txt_post_max,
                       self.step_table_txt_post_min,
                       self.step_table_txt_post_start,
                       self.step_table_txt_post_end,
                       self.step_table_txt_post_delta,
                       self.step_table_txt_post_rate,
                       ]
        columns_I = [self.step_table_txt_I_ + x for x in columns_end]
        columns_V = [self.step_table_txt_V_ + x for x in columns_end]
        columns_charge = [self.step_table_txt_C_ + x for x in columns_end]
        columns_discharge = [self.step_table_txt_D_ + x for x in columns_end]
        columns.extend(columns_I)
        columns.extend(columns_V)
        columns.extend(columns_charge)
        columns.extend(columns_discharge)

        columns.append(step_table_txt_ir)
        columns.append(step_table_txt_ir_change)

        columns.append(step_table_txt_type)
        columns.append(step_table_txt_info)

        # --- adding pct change col(s)-----
        df = self.tests[test_number].dfdata
        df[step_table_txt_ir_change] = df[self.internal_resistance_txt].pct_change()

        # --- finding size ------
        df = self.tests[test_number].dfdata
        number_of_rows = df.groupby([cycle_index_header, step_index_header]).size().shape[0]  # smart trick :-)
        # number_of_cols = len(columns)
        # print "number of rows:",
        # print number_of_rows

        # --- creating it ----
        index = np.arange(0, number_of_rows)
        df_steps = pd.DataFrame(index=index, columns=columns)

        # ------------------- finding cycle numbers ---------------------------
        list_of_cycles = df[cycle_index_header].unique()
        # print "list of cycles:"
        # print list_of_cycles

        # ------------------ iterating and populating step_table --------------
        counter = 0
        for cycle in list_of_cycles:
            mask_cycle = df[cycle_index_header] == cycle
            df_cycle = df[mask_cycle]
            steps = df_cycle[step_index_header].unique()
            for step in steps:
                # info = "None"
                mask_step = df_cycle[step_index_header] == step
                df_step = df_cycle[mask_step]
                # print "checking cycle %i - step %i" % (cycle,step)
                result = self._extract_step_values(df_step)

                # inserting into step_table
                df_steps.iloc[counter][step_table_txt_cycle] = cycle
                df_steps.iloc[counter][step_table_txt_step] = step
                # df_steps.iloc[counter]["info"] = info
                df_steps.iloc[counter, 2:-2] = result

                counter += 1

                # ----------chekcing step-type-----------------------------------------
                #
                #        print "checking step-type"
        average_current_txt = self.step_table_txt_I_ + self.step_table_txt_post_average
        min_current_txt = self.step_table_txt_I_ + self.step_table_txt_post_min
        max_current_txt = self.step_table_txt_I_ + self.step_table_txt_post_max
        delta_current_txt = self.step_table_txt_I_ + self.step_table_txt_post_delta
        delta_voltage_txt = self.step_table_txt_V_ + self.step_table_txt_post_delta
        delta_charge_txt = self.step_table_txt_C_ + self.step_table_txt_post_delta
        delta_discharge_txt = self.step_table_txt_D_ + self.step_table_txt_post_delta

        # max_average_current = df_steps[average_current_txt].max()
        #        print "max average current:"
        #        print max_average_current
        #
        current_limit_value_hard = 0.0000000000001
        current_limit_value_soft = 0.00001

        stable_current_limit_hard = 2.0
        stable_current_limit_soft = 4.0

        stable_voltage_limit_hard = 2.0
        stable_voltage_limit_soft = 4.0

        stable_charge_limit_hard = 2.0
        stable_charge_limit_soft = 5.0

        ir_change_limit = 0.00001

        #
        #        minimum_change_limit = 2.0 # percent
        #        minimum_change_limit_voltage_cv = 5.0 # percent
        #        minimum_change_limit_current_cv = 10.0 # percent
        #        minimum_stable_limit = 0.001 # percent
        #        typicall_current_max = 0.001 # A
        #        minimum_ierror_limit = 0.0001 # A

        # --- no current
        # ocv

        # no current - no change in charge and discharge
        mask_no_current_hard = (df_steps[max_current_txt].abs() + df_steps[
            min_current_txt].abs()) < current_limit_value_hard
        mask_no_current_soft = (df_steps[max_current_txt].abs() + df_steps[
            min_current_txt].abs()) < current_limit_value_soft

        mask_voltage_down = df_steps[delta_voltage_txt] < -stable_voltage_limit_hard
        mask_voltage_up = df_steps[delta_voltage_txt] > stable_voltage_limit_hard
        mask_voltage_stable = df_steps[delta_voltage_txt].abs() < stable_voltage_limit_hard

        mask_current_down = df_steps[delta_current_txt] < -stable_current_limit_soft
        mask_current_up = df_steps[delta_current_txt] > stable_current_limit_soft
        mask_current_negative = df_steps[average_current_txt] < -current_limit_value_hard
        mask_current_positive = df_steps[average_current_txt] > current_limit_value_hard
        mask_galvanostatic = df_steps[delta_current_txt].abs() < stable_current_limit_soft

        mask_charge_changed = df_steps[delta_charge_txt].abs() > stable_charge_limit_hard
        mask_discharge_changed = df_steps[delta_discharge_txt].abs() > stable_charge_limit_hard

        mask_ir_changed = df_steps[step_table_txt_ir_change].abs() > ir_change_limit

        mask_no_change = (df_steps[delta_voltage_txt] == 0) & (df_steps[delta_current_txt] == 0) & \
                         (df_steps[delta_charge_txt] == 0) & (df_steps[delta_discharge_txt] == 0)
        #          self.list_of_step_types = ['charge','discharge',
        #                                   'cv_charge','cv_discharge',
        #                                   'charge_cv','discharge_cv',
        #                                   'ocvrlx_up','ocvrlx_down','ir',
        #                                   'rest','not_known']
        # - options

        # --- ocv -------
        df_steps.loc[mask_no_current_hard & mask_voltage_up, step_table_txt_type] = 'ocvrlx_up'
        df_steps.loc[mask_no_current_hard & mask_voltage_down, step_table_txt_type] = 'ocvrlx_down'

        # --- charge and discharge ----
        # df_steps.loc[mask_galvanostatic & mask_current_negative, step_table_txt_type] = 'discharge'
        df_steps.loc[mask_discharge_changed & mask_current_negative, step_table_txt_type] = 'discharge'
        # df_steps.loc[mask_galvanostatic & mask_current_positive, step_table_txt_type] = 'charge'
        df_steps.loc[mask_charge_changed & mask_current_positive, step_table_txt_type] = 'charge'

        df_steps.loc[
            mask_voltage_stable & mask_current_negative & mask_current_down, step_table_txt_type] = 'cv_discharge'
        df_steps.loc[mask_voltage_stable & mask_current_positive & mask_current_down, step_table_txt_type] = 'cv_charge'

        # --- internal resistance ----
        # df_steps.loc[mask_no_change & mask_ir_changed, step_table_txt_type] = 'ir' # assumes that IR is stored in just one row
        df_steps.loc[mask_no_change, step_table_txt_type] = 'ir'  # assumes that IR is stored in just one row

        # --- CV steps ----

        # "voltametry_charge"
        # mask_charge_changed
        # mask_voltage_up
        # (could also include abs-delta-cumsum current)

        # "voltametry_discharge"
        # mask_discharge_changed
        # mask_voltage_down


        # test
        # outfile = r"C:\Scripting\MyFiles\dev_cellpy\tmp\test_new_steptable.csv"
        # df_steps.to_csv(outfile, sep=";", index_label="index")

        # --- finally ------

        self.tests[test_number].step_table = df_steps
        self.tests[test_number].step_table_made = True

    def _percentage_change(self, x0, x1, default_zero=True):
        # calculates the change from x0 to x1 in percentage
        # i.e. returns (x1-x0)*100 / x0
        if x0 == 0.0:
            self.logger.debug("DBZ(_percentage)")  # this will not print anything, set level to 1 to print
            difference = x1 - x0
            if difference != 0.0 and default_zero:
                difference = 0.0
        else:
            difference = (x1 - x0) * 100 / x0

        return difference

    def _fractional_change(self, x0, x1, default_zero=False):
        # calculates the fraction of x0 and x1
        # i.e. returns x1 / x0
        if x1 == 0.0:
            self.logger.debug("DBZ(_fractional)")  # this will not print anything, set level to 1 to print
            if default_zero:
                difference = 0.0
            else:
                difference = np.nan
        else:
            difference = x0 / x1

        return difference

    def select_steps(self, step_dict, append_df=False, test_number=None):
        """Select steps (not documented yet)."""
        # step_dict={1:[1],2:[1],3:[1,2,3]}
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        if not append_df:
            selected = []
            for cycle, step in step_dict.items():
                # print cycle, step
                if len(step) > 1:
                    for s in step:
                        c = self._select_step(cycle, s, test_number)
                        if not self.is_empty(c): selected.append(c)
                else:
                    c = self._select_step(cycle, step, test_number)
                    if not self.is_empty(c): selected.append(c)
        else:
            first = True
            for cycle, step in step_dict.items():
                if len(step) > 1:
                    for s in step:
                        c = self._select_step(cycle, s, test_number)
                        if first:
                            selected = c.copy()
                            first = False
                        else:
                            selected = selected.append(c, ignore_index=True)
                else:
                    c = self._select_step(cycle, step, test_number)
                    if first:
                        selected = c.copy()
                        first = False
                    else:
                        selected = selected.append(c, ignore_index=True)

        return selected

    def _select_step(self, cycle, step, test_number=None):
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        test = self.tests[test_number]
        # test.dfdata

        # check if columns exist
        c_txt = self.cycle_index_txt
        s_txt = self.step_index_txt
        y_txt = self.voltage_txt
        x_txt = self.discharge_capacity_txt  # jepe fix

        # no_cycles=np.amax(test.dfdata[c_txt])
        # print d.columns

        if not any(test.dfdata.columns == c_txt):
            print "error - cannot find %s" % c_txt
            sys.exit(-1)
        if not any(test.dfdata.columns == s_txt):
            print "error - cannot find %s" % s_txt
            sys.exit(-1)

        v = test.dfdata[(test.dfdata[c_txt] == cycle) & (test.dfdata[s_txt] == step)]
        if self.is_empty(v):
            return None
        else:
            return v

    # @print_function
    def populate_step_dict(self, step, test_number=None):
        """Returns a dict with cycle numbers as keys and corresponding steps (list) as values."""
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        step_dict = {}
        cycles = self.tests[test_number].dfdata[self.cycle_index_txt]
        unique_cycles = cycles.unique()
        # number_of_cycles = len(unique_cycles)
        number_of_cycles = np.amax(cycles)
        for cycle in unique_cycles:
            step_dict[cycle] = [step]
        return step_dict

    def find_C_rates(self, steps, mass=None, nom_cap=3579, silent=True, test_number=None):
        """Find the C-rates for the cycles (obs! under development)."""
        self.find_C_rates_old(steps, mass, nom_cap, silent, test_number)

    def find_C_rates_old(self, steps, mass=None, nom_cap=3579, silent=True, test_number=None):
        """Uses old type of step_dict, returns crate_dict.

        crate_dict[cycle] = [step, c-rate]
        """
        self.logger.debug("this is using the old-type step-dict. Could very well be that it does not work")
        c_txt = self.cycle_index_txt
        s_txt = self.step_index_txt
        x_txt = self.current_txt

        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        if not mass:
            mass = self.tests[test_number].mass

        d = self.tests[test_number].dfdata
        c_rates_dict = {}
        for c, s in steps.iteritems():
            v = d[(d[c_txt] == c) & (d[s_txt] == s[0])]
            if not v[x_txt].dropna().empty:
                current = np.average(v[x_txt])
                c_rate = abs(1000000 * current / (nom_cap * mass))
            else:
                c_rate = np.NaN
            c_rates_dict[c] = [s[0], c_rate]
            if not silent:
                print "cycle no %4i (step %3i) has a c-rate of %5.3fC" % (c, s[0], c_rate),
            if c_rate > 0:
                if not silent:
                    print "(=C / %5.1f)" % (1 / c_rate)
            else:
                if not silent:
                    print " --non-positive C-rate!-- "
        return c_rates_dict

    # -------------save-and-export--------------------------------------------------

    def _export_cycles(self, test_number, setname=None, sep=None, outname=None):
        self.logger.debug("exporting cycles")
        lastname = "_cycles.csv"
        if sep is None:
            sep = self.sep
        if outname is None:
            outname = setname + lastname

        list_of_cycles = self.get_cycle_numbers(test_number=test_number)
        number_of_cycles = len(list_of_cycles)
        txt = "you have %i cycles" % (number_of_cycles)
        self.logger.debug(txt)

        out_data = []

        for cycle in list_of_cycles:
            try:
                c, v = self.get_cap(cycle, test_number=test_number)
                c = c.tolist()
                v = v.tolist()
                header_x = "cap cycle_no %i" % cycle
                header_y = "voltage cycle_no %i" % cycle
                c.insert(0, header_x)
                v.insert(0, header_y)
                out_data.append(c)
                out_data.append(v)
            except:
                txt = "could not extract cycle %i" % (cycle)
                self.logger.debug(txt)

        # Saving cycles in one .csv file (x,y,x,y,x,y...)
        # print "saving the file with delimiter '%s' " % (sep)
        self.logger.debug("writing cycles to file")
        with open(outname, "wb") as f:
            writer = csv.writer(f, delimiter=sep)
            writer.writerows(itertools.izip_longest(*out_data))
            # star (or asterix) means transpose (writing cols instead of rows)
        txt = outname
        txt += " OK"
        self.logger.debug(txt)

    def _export_normal(self, data, setname=None, sep=None, outname=None):
        lastname = "_normal.csv"
        if sep is None:
            sep = self.sep
        if outname is None:
            outname = setname + lastname
        txt = outname
        try:
            data.dfdata.to_csv(outname, sep=sep)
            txt += " OK"
        except:
            txt += " Could not save it!"
        self.logger.debug(txt)

    def _export_stats(self, data, setname=None, sep=None, outname=None):
        lastname = "_stats.csv"
        if sep is None:
            sep = self.sep
        if outname is None:
            outname = setname + lastname
        txt = outname
        try:
            data.dfsummary.to_csv(outname, sep=sep)
            txt += " OK"
        except:
            txt += " Could not save it!"
        self.logger.debug(txt)

    def _export_steptable(self, data, setname=None, sep=None, outname=None):
        lastname = "_steps.csv"
        if sep is None:
            sep = self.sep
        if outname is None:
            outname = setname + lastname
        txt = outname
        try:
            data.step_table.to_csv(outname, sep=sep)
            txt += " OK"
        except:
            txt += " Could not save it!"
        self.logger.debug(txt)

    def exportcsv(self, datadir=None, sep=None, cycles=False, raw=True, summary=True):
        """Saves the data as .csv file(s)."""

        if sep is None:
            sep = self.sep
        txt = "\n\n"
        txt += "---------------------------------------------------------------"
        txt += "Saving data"
        txt += "---------------------------------------------------------------"
        self.logger.debug(txt)

        test_number = -1
        for data in self.tests:
            test_number += 1
            if not self._is_not_empty_test(data):
                print "exportcsv -"
                print "empty test [%i]" % (test_number)
                print "not saved!"
            else:
                if isinstance(data.loaded_from,(list, tuple)):
                    txt = "merged file"
                    txt += "using first file as basename"
                    self.logger.debug(txt)
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
                    if data.step_table_made is True:
                        outname_steps = firstname + "_steps.csv"
                        self._export_steptable(data, outname=outname_steps, sep=sep)
                    else:
                        self.logger.debug("step_table_made is not True")

                if summary:
                    outname_stats = firstname + "_stats.csv"
                    self._export_stats(data, outname=outname_stats, sep=sep)

                if cycles:
                    outname_cycles = firstname + "_cycles.csv"
                    self._export_cycles(outname=outname_cycles, test_number=test_number,
                                        sep=sep)

    def save_test(self, filename, test_number=None, force=False, overwrite=True, extension="h5"):
        """Save the data structure using pickle/hdf5."""

        test_number = self._validate_test_number(test_number)
        if test_number is None:
            print "Saving test failed!"
            self._report_empty_test()
            return

        test = self.get_test(test_number)
        dfsummary_made = test.dfsummary_made

        if not dfsummary_made and not force:
            print "You should not save tests without making a summary first!"
            print "If you really want to do it, use save_test with force=True"
        else:
            # check extension
            if not os.path.splitext(filename)[-1]:
                outfile_all = filename + "." + extension
            else:
                outfile_all = filename
            # check if file exists
            write_file = True
            if os.path.isfile(outfile_all):
                self.logger.debug("Outfile exists")
                if overwrite:
                    self.logger.debug("overwrite = True")
                    os.remove(outfile_all)
                else:
                    write_file = False

            if write_file:
                if self.ensure_step_table:
                    self.logger.debug("ensure_step_table is on")
                    if not test.step_table_made:
                        self.logger.debug("save_test: creating step table")
                        self.create_step_table(test_number=test_number)
                self.logger.debug("trying to make infotable")
                infotbl, fidtbl = self._create_infotable(test_number=test_number)  # modify this
                self.logger.debug("trying to save to hdf5")
                txt = "\nHDF5 file: %s" % (outfile_all)
                self.logger.debug(txt)
                store = pd.HDFStore(outfile_all)
                self.logger.debug("trying to put dfdata")
                store.put("cellpydata/dfdata", test.dfdata)  # jepe: fix (get name from class)
                self.logger.debug("trying to put dfsummary")
                store.put("cellpydata/dfsummary", test.dfsummary)

                self.logger.info("trying to put step_table")
                if not test.step_table_made:
                    self.logger.debug(" no step_table made")
                else:
                    store.put("cellpydata/step_table", test.step_table)

                self.logger.debug("trying to put infotbl")
                store.put("cellpydata/info", infotbl)
                self.logger.debug("trying to put fidtable")
                store.put("cellpydata/fidtable", fidtbl)
                store.close()
                # del store
            else:
                print "save_test (hdf5): file exist - did not save",
                print outfile_all

    def _create_infotable(self, test_number=None):
        # needed for saving class/dataset to hdf5
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        test = self.get_test(test_number)

        infotable = collections.OrderedDict()
        infotable["test_no"] = [test.test_no,]
        infotable["mass"] = [test.mass,]
        infotable["charge_steps"] = [test.charge_steps,]
        infotable["discharge_steps"] =[ test.discharge_steps,]
        infotable["ir_steps"] = [test.ir_steps,]
        infotable["ocv_steps"] = [test.ocv_steps,]
        infotable["nom_cap"] = [test.nom_cap,]
        infotable["loaded_from"] = [test.loaded_from,]
        infotable["channel_index"] = [test.channel_index,]
        infotable["channel_number"] = [test.channel_number,]
        infotable["creator"] = [test.creator,]
        infotable["schedule_file_name"] = [test.schedule_file_name,]
        infotable["item_ID"] = [test.item_ID,]
        infotable["test_ID"] = [test.test_ID,]
        infotable["test_name"] = [test.test_name,]
        infotable["start_datetime"] = [test.start_datetime,]
        infotable["dfsummary_made"] = [test.dfsummary_made,]
        infotable["step_table_made"] = [test.step_table_made,]
        infotable["cellpy_file_version"] = [test.cellpy_file_version,]

        infotable = pd.DataFrame(infotable)

        self.logger.debug("_create_infotable: fid")
        fidtable = collections.OrderedDict()
        fidtable["raw_data_name"] = []
        fidtable["raw_data_full_name"] = []
        fidtable["raw_data_size"] = []
        fidtable["raw_data_last_modified"] = []
        fidtable["raw_data_last_accessed"] = []
        fidtable["raw_data_last_info_changed"] = []
        fidtable["raw_data_location"] = []
        fidtable["raw_data_files_length"] = []
        fids = test.raw_data_files
        fidtable["raw_data_fid"] = fids
        for fid, length in zip(fids, test.raw_data_files_length):
            fidtable["raw_data_name"].append(fid.name)
            fidtable["raw_data_full_name"].append(fid.full_name)
            fidtable["raw_data_size"].append(fid.size)
            fidtable["raw_data_last_modified"].append(fid.last_modified)
            fidtable["raw_data_last_accessed"].append(fid.last_accessed)
            fidtable["raw_data_last_info_changed"].append(fid.last_info_changed)
            fidtable["raw_data_location"].append(fid.location)
            fidtable["raw_data_files_length"].append(length)
        fidtable = pd.DataFrame(fidtable)
        return infotable, fidtable

    # --------------helper-functions------------------------------------------------

    def _cap_mod_summary(self, dfsummary, capacity_modifier):
        # modifies the summary table
        discharge_title = self.discharge_capacity_txt
        charge_title = self.charge_capacity_txt
        chargecap = 0.0
        dischargecap = 0.0
        # TODO use pd.loc[row,column] e.g. pd.loc[:,"charge_cap"] for col or pd.loc[(pd.["step"]==1),"x"]
        if capacity_modifier == "reset":

            for index, row in dfsummary.iterrows():
                dischargecap_2 = row[discharge_title]
                dfsummary[discharge_title][index] = dischargecap_2 - dischargecap
                dischargecap = dischargecap_2
                chargecap_2 = row[charge_title]
                dfsummary[charge_title][index] = chargecap_2 - chargecap
                chargecap = chargecap_2

        return dfsummary

    def _cap_mod_normal(self, test_number=None,
                        capacity_modifier="reset",
                        allctypes=True):
        # modifies the normal table
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        cycle_index_header = self.cycle_index_txt
        step_index_header = self.step_index_txt
        discharge_index_header = self.discharge_capacity_txt
        discharge_energy_index_header = self.discharge_energy_txt
        charge_index_header = self.charge_capacity_txt
        charge_energy_index_header = self.charge_energy_txt

        dfdata = self.tests[test_number].dfdata

        chargecap = 0.0
        dischargecap = 0.0

        if capacity_modifier == "reset":
            # discharge cycles
            no_cycles = np.amax(dfdata[cycle_index_header])
            for j in range(1, no_cycles + 1):
                cap_type = "discharge"
                e_header = discharge_energy_index_header
                cap_header = discharge_index_header
                discharge_cycles = self.get_step_numbers(steptype=cap_type, allctypes=allctypes, cycle_number=j,
                                                         test_number=test_number)

                steps = discharge_cycles[j]
                print "----------------------------------------"
                txt = "Cycle  %i (discharge):  " % j
                self.logger.debug(txt)
                # TODO use pd.loc[row,column] e.g. pd.loc[:,"charge_cap"] for col or pd.loc[(pd.["step"]==1),"x"]
                selection = (dfdata[cycle_index_header] == j) & (dfdata[step_index_header].isin(steps))
                c0 = dfdata[selection].iloc[0][cap_header]
                e0 = dfdata[selection].iloc[0][e_header]
                dfdata[cap_header][selection] = (dfdata[selection][cap_header] - c0)
                dfdata[e_header][selection] = (dfdata[selection][e_header] - e0)

                cap_type = "charge"
                e_header = charge_energy_index_header
                cap_header = charge_index_header
                charge_cycles = self.get_step_numbers(steptype=cap_type, allctypes=allctypes, cycle_number=j,
                                                      test_number=test_number)
                steps = charge_cycles[j]
                print "----------------------------------------"
                txt = "Cycle  %i (charge):  " % j
                self.logger.debug(txt)

                selection = (dfdata[cycle_index_header] == j) & (dfdata[step_index_header].isin(steps))
                c0 = dfdata[selection].iloc[0][cap_header]
                e0 = dfdata[selection].iloc[0][e_header]
                dfdata[cap_header][selection] = (dfdata[selection][cap_header] - c0)
                dfdata[e_header][selection] = (dfdata[selection][e_header] - e0)

                # discharge cycles

    def get_number_of_tests(self):
        return self.number_of_tests

    def get_mass(self, test_number=None):
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        if not self.tests[test_number].mass_given:
            print "no mass"
        return self.tests[test_number].mass

    def get_test(self, n=0):
        return self.tests[n]

    def sget_voltage(self, cycle, step, test_number=None):
        """Returns voltage for cycle, step."""

        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        cycle_index_header = self.cycle_index_txt
        voltage_header = self.voltage_txt
        step_index_header = self.step_index_txt
        test = self.tests[test_number].dfdata
        c = test[(test[cycle_index_header] == cycle) & (test[step_index_header] == step)]
        if not self.is_empty(c):
            v = c[voltage_header]
            return v
        else:
            return None

    def get_voltage(self, cycle=None, test_number=None, full=True):
        """Returns voltage (in V)."""

        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        cycle_index_header = self.cycle_index_txt
        voltage_header = self.voltage_txt
        # step_index_header  = self.step_index_txt

        test = self.tests[test_number].dfdata
        if cycle:
            c = test[(test[cycle_index_header] == cycle)]
            if not self.is_empty(c):
                v = c[voltage_header]
                return v
        else:
            if not full:
                self.logger.debug("getting voltage-curves for all cycles")
                v = []
                no_cycles = np.amax(test[cycle_index_header])
                for j in range(1, no_cycles + 1):
                    txt = "Cycle  %i:  " % j
                    self.logger.debug(txt)
                    c = test[(test[cycle_index_header] == j)]
                    v.append(c[voltage_header])
            else:
                v = test[voltage_header]
            return v

    def get_current(self, cycle=None, test_number=None, full=True):
        """Returns current (in mA)."""

        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        cycle_index_header = self.cycle_index_txt
        current_header = self.current_txt
        # step_index_header  = self.step_index_txt

        test = self.tests[test_number].dfdata
        if cycle:
            c = test[(test[cycle_index_header] == cycle)]
            if not self.is_empty(c):
                v = c[current_header]
                return v
        else:
            if not full:
                self.logger.debug("getting voltage-curves for all cycles")
                v = []
                no_cycles = np.amax(test[cycle_index_header])
                for j in range(1, no_cycles + 1):
                    txt = "Cycle  %i:  " % j
                    self.logger.debug(txt)
                    c = test[(test[cycle_index_header] == j)]
                    v.append(c[current_header])
            else:
                v = test[current_header]
            return v

    # @print_function
    def sget_steptime(self, cycle, step, test_number=None):
        """Returns step time for cycle, step."""

        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        cycle_index_header = self.cycle_index_txt
        step_time_header = self.step_time_txt
        step_index_header = self.step_index_txt
        test = self.tests[test_number].dfdata
        c = test[(test[cycle_index_header] == cycle) & (test[step_index_header] == step)]
        if not self.is_empty(c):
            t = c[step_time_header]
            return t
        else:
            return None

    def sget_timestamp(self, cycle, step, test_number=None):
        """Returns timestamp for cycle, step."""

        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        cycle_index_header = self.cycle_index_txt
        timestamp_header = self.test_time_txt
        step_index_header = self.step_index_txt
        test = self.tests[test_number].dfdata
        c = test[(test[cycle_index_header] == cycle) & (test[step_index_header] == step)]
        if not self.is_empty(c):
            t = c[timestamp_header]
            return t
        else:
            return None

    def get_timestamp(self, cycle=None, test_number=None, in_minutes=False, full=True):
        """Returns timestamps (in sec or minutes (if in_minutes==True))."""

        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        cycle_index_header = self.cycle_index_txt
        timestamp_header = self.test_time_txt

        v = None
        test = self.tests[test_number].dfdata
        if cycle:
            c = test[(test[cycle_index_header] == cycle)]
            if not self.is_empty(c):
                v = c[timestamp_header]
        else:
            if not full:
                self.logger.debug("getting voltage-curves for all cycles")
                v = []
                no_cycles = np.amax(test[cycle_index_header])
                for j in range(1, no_cycles + 1):
                    txt = "Cycle  %i:  " % j
                    self.logger.debug(txt)
                    c = test[(test[cycle_index_header] == j)]
                    v.append(c[timestamp_header])
            else:
                self.logger.debug("returning full voltage col")
                v = test[timestamp_header]
                if in_minutes and v is not None:
                    v = v / 60.0
        if in_minutes and v is not None and not full:
            v = v / 60.0
        return v

    def get_dcap(self, cycle=None, test_number=None):
        """Returns discharge_capacity (in mAh/g), and voltage."""

        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        dc, v = self._get_cap(cycle, test_number, "discharge")
        return dc, v

    def get_ccap(self, cycle=None, test_number=None):
        """Returns charge_capacity (in mAh/g), and voltage."""

        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        cc, v = self._get_cap(cycle, test_number, "charge")
        return cc, v

    def get_cap(self, cycle=None, test_number=None,
                polarization=False,
                stepsize=0.2,
                points=None):
        """Gets the capacity for the run.

        For polarization = True: calculates hysteresis.
        For cycle=None: not implemented yet, cycle set to 2.

        Args:
            cycle (int): cycle number.
            polarization (bool): get polarization.
            stepsize (float): used for calculating polarization.
            points (int): used for calculating polarization.
            test_number (int): test number (default first) (usually not used).

        Returns:
            if polarization = False: capacity (mAh/g), voltage
            if polarization = True: capacity (mAh/g), voltage,
               capacity points (mAh/g) [points if given, arranged with stepsize if not],
               polarization (hysteresis)
        """
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        # if cycle is not given, then this function should iterate through cycles
        if not cycle:
            cycle = 2
        cc, cv = self.get_ccap(cycle, test_number)
        dc, dv = self.get_dcap(cycle, test_number)
        last_dc = np.amax(dc)
        cc = last_dc - cc
        c = pd.concat([dc, cc], axis=0)
        v = pd.concat([dv, cv], axis=0)
        if polarization:
            # interpolate cc cv dc dv and find difference
            pv, p = self._polarization(cc, cv, dc, dv, stepsize, points)

            return c, v, pv, p
        else:
            return c, v

    # @print_function
    def _polarization(self, cc, cv, dc, dv, stepsize=0.2, points=None):
        # used when finding the voltage difference in discharge vs charge
        # should probably be labelled "hysteresis" instead of polarization
        # cc = charge cap
        # cv = voltage (during charging)
        # dc = discharge cap
        # vv = voltage (during discharging)
        # stepsize - maybe extend so that the function selects proper stepsize
        # points = [cap1, cap2, cap3, ...] (returns p for given cap points)
        stepsize = 0.2
        cc = self._reverse(cc)
        cv = self._reverse(cv)
        min_dc, max_dc = self._bounds(dc)
        min_cc, max_cc = self._bounds(cc)
        start_cap = max(min_dc, min_cc)
        end_cap = min(max_dc, max_cc)
        #        print min_dc, min_cc, start_cap
        #        print self._roundup(start_cap)
        #        print max_dc, max_cc, end_cap
        #        print self._rounddown(end_cap)
        # TODO check if points are within bounds (implement it later if needed)
        if not points:
            points = np.arange(self._roundup(start_cap), self._rounddown(end_cap), stepsize)
        else:
            if min(points) < start_cap:
                print "ERROR, point %f less than bound (%f)" % (min(points), start_cap)
            if max(points) > end_cap:
                print "ERROR, point %f bigger than bound (%f)" % (max(points), end_cap)
        f1 = interpolate.interp1d(dc, dv)
        f2 = interpolate.interp1d(cc, cv)
        dv_new = f1(points)
        cv_new = f2(points)
        p = cv_new - dv_new
        return points, p

    def _get_cap(self, cycle=None, test_number=None, cap_type="charge"):
        # used when extracting capacities (get_ccap, get_dcap)
        # TODO: does not allow for constant voltage yet
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        test = self.tests[test_number]
        mass = self.get_mass(test_number)
        if cap_type == "charge_capacity":
            cap_type = "charge"
        elif cap_type == "discharge_capacity":
            cap_type = "discharge"
        # cycles = self.find_step_numbers(step_type =cap_type,test_number = test_number)
        self.logger.debug("in _get_cap: finding step numbers")
        if cycle:
            self.logger.debug("for cycle")
            self.logger.debug(cycle)
        cycles = self.get_step_numbers(steptype=cap_type, allctypes=False, cycle_number=cycle,
                                       test_number=test_number)

        self.logger.debug(cycles)
        #        cycles = self.find_step_numbers(step_type ="charge_capacity",test_number = test_number)
        #        self.logger.debug(cycles)
        #        sys.exit(-1)
        c = None
        v = None
        if cap_type == "charge":
            column_txt = self.charge_capacity_txt
        else:
            column_txt = self.discharge_capacity_txt
        if cycle:
            step = cycles[cycle][0]
            selected_step = self._select_step(cycle, step, test_number)
            if not self.is_empty(selected_step):
                v = selected_step[self.voltage_txt]
                c = selected_step[column_txt] * 1000000 / mass
            else:
                self.logger.debug("could not find any steps for this cycle")
                txt = "(c:%i s:%i type:%s)" % (cycle, step, cap_type)
        else:
            # get all the discharge cycles
            # this is a dataframe filtered on step and cycle
            d = self.select_steps(cycles, append_df=True)
            v = d[self.voltage_txt]
            c = d[column_txt] * 1000000 / mass
        return c, v

    def get_ocv(self, cycle_number=None, ocv_type='ocv', test_number=None):
        """Find ocv data in dataset (voltage vs time).

        Args:
            cycle_number (int): find for all cycles if None.
            ocv_type ("ocv", "ocvrlx_up", "ocvrlx_down"):
                     ocv - get up and down (default)
                     ocvrlx_up - get up
                     ocvrlx_down - get down
            test_number (int): test number (default first) (usually not used).
        Returns:
                if cycle_number is not None
                    ocv or [ocv_up, ocv_down]
                    ocv (and ocv_up and ocv_down) are list
                    containg [time,voltage] (that are Series)

                if cycle_number is None
                    [ocv1,ocv2,...ocvN,...] N = cycle
                    ocvN = pandas DataFrame containing the columns
                    cycle inded, step time, step index, data point, datetime, voltage
                    (TODO: check if copy or reference of dfdata is returned)
        """
        # function for getting ocv curves
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        if ocv_type in ['ocvrlx_up', 'ocvrlx_down']:
            ocv = self._get_ocv(test_number=None,
                                ocv_type=ocv_type,
                                select_last=True,
                                select_columns=True,
                                cycle_number=cycle_number,
                                )
            return ocv
        else:
            ocv_up = self._get_ocv(test_number=None,
                                   ocv_type='ocvrlx_up',
                                   select_last=True,
                                   select_columns=True,
                                   cycle_number=cycle_number,
                                   )
            ocv_down = self._get_ocv(test_number=None,
                                     ocv_type='ocvrlx_down',
                                     select_last=True,
                                     select_columns=True,
                                     cycle_number=cycle_number,
                                     )
            return ocv_up, ocv_down

    def _get_ocv(self, ocv_steps=None, test_number=None, ocv_type='ocvrlx_up', select_last=True,
                 select_columns=True, cycle_number=None):
        # find ocv data in dataset
        # (voltage vs time, no current)
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return

        if not ocv_steps:
            if not ocv_type in ['ocvrlx_up', 'ocvrlx_down']:
                self.logger.debug(" ocv_type must be ocvrlx_up or ocvrlx_down ")
                sys.exit(-1)
            else:
                ocv_steps = self.get_step_numbers(steptype=ocv_type, allctypes=False,
                                                  pdtype=False, cycle_number=cycle_number,
                                                  test_number=test_number)

        if cycle_number:
            # check ocv_steps
            ocv_step_exists = True
            #            self.logger.debug(cycle_number)
            #            self.logger.debug(ocv_steps)
            #            self.logger.debug(ocv_steps[cycle_number])
            if not ocv_steps.has_key(cycle_number):
                ocv_step_exists = False
            elif ocv_steps[cycle_number][0] == 0:
                ocv_step_exists = False

            if ocv_step_exists:
                steps = ocv_steps[cycle_number]
                index = 0
                if select_last:
                    index = -1
                step = steps[index]

                c = self._select_step(cycle_number, step)
                t = c[self.step_time_txt]
                o = c[self.voltage_txt]
                return [t, o]
            else:
                txt = "ERROR! cycle %i not found" % (cycle_number)  # jepe fix
                self.logger.debug(txt)
                return [None, None]

        else:
            ocv = []
            for cycle, steps in ocv_steps.items():
                for step in steps:
                    c = self._select_step(cycle, step)
                    # select columns:

                    if select_columns and not self.is_empty(c):
                        column_names = c.columns
                        columns_to_keep = [self.cycle_index_txt,
                                           self.step_time_txt, self.step_index_txt,
                                           self.data_point_txt, self.datetime_txt,
                                           self.voltage_txt,
                                           ]
                        for column_name in column_names:
                            if not columns_to_keep.count(column_name):
                                c.pop(column_name)

                    if not self.is_empty(c):
                        ocv.append(c)
            return ocv

    def get_number_of_cycles(self, test_number=None):
        """Fet the number of cycles in the test."""

        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        d = self.tests[test_number].dfdata
        cycle_index_header = self.cycle_index_txt
        no_cycles = np.amax(d[cycle_index_header])
        return no_cycles

    def get_cycle_numbers(self, test_number=None):
        """Fet a list containing all the cycle numbers in the test."""

        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        d = self.tests[test_number].dfdata
        cycle_index_header = self.cycle_index_txt
        no_cycles = np.amax(d[cycle_index_header])
        # cycles = np.unique(d[cycle_index_header]).values
        cycles = np.unique(d[cycle_index_header])
        return cycles

    def get_ir(self, test_number=None):
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        d = self.tests[test_number].dfdata
        ir_txt = self.internal_resistance_txt
        ir_data = np.unique(d[ir_txt])
        d2 = d.ix[ir_data.index]
        d2 = d2[["Cycle_Index", "DateTime", "Data_Point", "Internal_Resistance"]].sort(
            [self.data_point_txt])  # jepe fix
        # cycles = np.unique(d["Cycle_Index"])  # TODO: jepe fix
        ir_dict = {}
        for i in d2.index:
            cycle = d2.ix[i]["Cycle_Index"]  # TODO: jepe fix
            if not ir_dict.has_key(cycle):
                ir_dict[cycle] = []
            ir_dict[cycle].append(d2.ix[i]["Internal_Resistance"])  # jepe fix
        return ir_dict

    def get_diagnostics_plots(self, test_number=None, scaled=False, ):
        """Gets diagnostics plots.

        Args:
            test_number: test number (default 0).
            scaled (bool): if True, scale by min and max values.

        Returns:
            Returns a dict containing diagnostics plots (keys = 'cycles', 'shifted_discharge_cap',
                'shifted_charge_cap','RIC_cum', 'RIC_disconnect_cum', 'RIC_sei_cum').

        """

        # assuming each cycle consists of one discharge step followed by charge step
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        # print "in get_diagnostics_plots: test_number = %i" % test_number
        cyclenos = self.get_cycle_numbers(test_number=test_number)
        summarydata = self.get_summary(test_number=test_number)
        if summarydata is None:
            print "Warning! no summarydata made yet (get_diagnostics_plots works on summarydata)"
            print "returning None"
            return None

        discharge_txt = self.summary_txt_discharge_cap
        charge_txt = self.summary_txt_charge_cap

        out = None
        dif = []  # difference between charge and discharge
        shifted_discharge_cap = []  # shifted discharge capacity
        shifted_charge_cap = []  # shifted charge capacity

        cycles = []
        RIC_cum = []
        RIC_disconnect_cum = []
        RIC_sei_cum = []

        cn_1 = 0.0
        ric_disconnect_cum = 0.0
        ric_sei_cum = 0.0
        ric_cum = 0.0
        C_n = None
        D_n = None

        for i, cycle in enumerate(cyclenos):
            try:
                D_n = summarydata[discharge_txt][i]
                C_n = summarydata[charge_txt][i]
                dd = C_n - D_n
                ric_n = (D_n - C_n) / C_n
                try:
                    C_n2 = summarydata[charge_txt][i + 1]
                    D_n2 = summarydata[discharge_txt][i + 1]
                    ric_dis_n = (C_n - C_n2) / C_n
                    ric_sei_n = (D_n2 - C_n) / C_n
                except:
                    ric_dis_n = None
                    ric_sei_n = None
                    self.logger.debug("could not get i+1 (probably last point)")

                dn = cn_1 + D_n
                cn = dn - C_n
                shifted_discharge_cap.append(dn)
                shifted_charge_cap.append(cn)
                cn_1 = cn
                dif.append(dd)
                ric_cum += ric_n
                ric_disconnect_cum += ric_dis_n
                ric_sei_cum += ric_sei_n
                cycles.append(cycle)
                RIC_disconnect_cum.append(ric_disconnect_cum)
                RIC_sei_cum.append(ric_sei_cum)
                RIC_cum.append(ric_cum)

            except:
                self.logger.debug("end of summary")
                break
        if scaled is True:
            sdc_min = np.amin(shifted_discharge_cap)
            shifted_discharge_cap = shifted_discharge_cap - sdc_min
            sdc_max = np.amax(shifted_discharge_cap)
            shifted_discharge_cap = shifted_discharge_cap / sdc_max

            scc_min = np.amin(shifted_charge_cap)
            shifted_charge_cap = shifted_charge_cap - scc_min
            scc_max = np.amax(shifted_charge_cap)
            shifted_charge_cap = shifted_charge_cap / scc_max

        out = {}
        out["cycles"] = cycles
        out["shifted_discharge_cap"] = shifted_discharge_cap
        out["shifted_charge_cap"] = shifted_charge_cap
        out["RIC_cum"] = RIC_cum
        out["RIC_disconnect_cum"] = RIC_disconnect_cum
        out["RIC_sei_cum"] = RIC_sei_cum
        return out

    def get_cycle(self, cycle=1, step_type=None, step=None, v=False, test_number=None):
        """Get cycle data.

        Get the cycle data for cycle = cycle (default 1) for step_type or step. The function
        returns a DataFrame filtered on cycle (and optionally step_type or step).
        If neither step_type or step (number) is given, all data for the cycle will be returned
        Warning: TODO - find out if copy or reference is returned
        """
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        mystep = None
        if v:
            print "test number is %i" % test_number
        if step_type:
            # need to find the step-dict
            mystep = self.find_step_numbers(step_type)[cycle][0]
            if v:
                print "selected step number %i" % mystep
                print "all step numbers:"
                print self.find_step_numbers(step_type)
        else:
            if step:
                mystep = step

        dataset = self.tests[test_number]
        cycle_txt = self.cycle_index_txt
        #        test_name = dataset.test_name # nice to get the name of the dataset / experiment as well
        #        sample_mass = dataset.mass # lets also get the sample mass (same as set in d.set_mass(m))

        dfdata = dataset.dfdata
        if mystep:
            if v:
                print "selecting correct step",
                print mystep
            step_txt = self.step_index_txt
            dfdata_cycle = dfdata[(dfdata[cycle_txt] == cycle) & (dfdata[step_txt] == mystep)]
        else:
            if not step and not step_type:
                dfdata_cycle = dfdata[(dfdata[cycle_txt] == cycle)]
            else:
                print "ERROR! This cycle does not have any of your wanted steps"
                dfdata_cycle = None
        return dfdata_cycle

    # @print_function
    def set_mass(self, masses, test_numbers=None, validated=None):
        """Sets the mass (masses) for the test (tests).
        """

        number_of_tests = len(self.tests)
        if not number_of_tests:
            print "no tests have been loaded yet"
            print "cannot set mass before loading tests"
            sys.exit(-1)

        if not test_numbers:
            test_numbers = range(len(self.tests))

        if not self._is_listtype(test_numbers):
            test_numbers = [test_numbers, ]

        if not self._is_listtype(masses):
            masses = [masses, ]
        if validated is None:
            for t, m in zip(test_numbers, masses):
                try:
                    self.tests[t].mass = m
                    self.tests[t].mass_given = True
                except AttributeError as e:
                    print "This test is empty"
                    print e
        else:
            for t, m, v in zip(test_numbers, masses, validated):
                if v:
                    try:
                        self.tests[t].mass = m
                        self.tests[t].mass_given = True
                    except AttributeError as e:
                        print "This test is empty"
                        print e
                else:
                    self.logger.debug("set_mass: this set is empty")

    def set_col_first(self, df, col_names):
        """set selected columns first in a pandas.DataFrame.

        This function sets cols with names given in  col_names (a list) first in the DataFrame.
        The last col in col_name will come first (processed last)
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

    def set_testnumber_force(self, test_number=0):
        """Force to set testnumber.

        Sets the testnumber default (all functions with prm test_number will
        then be run assuming the default set test_number)
        """
        self.selected_test_number = test_number

    def set_testnumber(self, test_number):
        """Set the testnumber.

        Set the test_number that will be used (cellpydata.selected_test_number).
        The class can save several datasets (but its not a frequently used feature),
        the datasets are stored in a list and test_number is the selected index in the list.

        Several options are available:
              n - int in range 0..(len-1) (python uses offset as index, i.e. starts with 0)
              last, end, newest - last (index set to -1)
              first, zero, beinning, default - first (index set to 0)
        """
        self.logger.debug("***set_testnumber(n)")
        test_number_str = test_number
        try:
            if test_number_str.lower() in ["last", "end", "newest"]:
                test_number = -1
            elif test_number_str.lower() in ["first", "zero", "beginning", "default"]:
                test_number = 0
        except:
            self.logger.debug("assuming numeric")

        number_of_tests = len(self.tests)
        if test_number >= number_of_tests:
            test_number = -1
            self.logger.debug("you dont have that many tests, setting to last test")
        elif test_number < -1:
            self.logger.debug("not a valid option, setting to first test")
            test_number = 0
        self.selected_test_number = test_number

    def get_summary(self, test_number=None, use_dfsummary_made=False):
        """Retrieve summary returned as a pandas DataFrame."""
        # TODO: there is something strange with this
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        test = self.get_test(test_number)
        #        print "number of tests:",
        #        print self.get_number_of_tests()
        if use_dfsummary_made:
            dfsummary_made = test.dfsummary_made
        else:
            dfsummary_made = True

        if not dfsummary_made:
            print "Summary is not made yet"
            return None
        else:
            return test.dfsummary

    # -----------internal-helpers---------------------------------------------------

    def is_empty(self, v):
        try:
            if not v:
                return True
            else:
                return False
        except:
            try:
                if v.empty:
                    return True
                else:
                    return False
            except:
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

    def _roundup(self, x):
        n = 1000.0
        x = np.ceil(x * n)
        x = x / n
        return x

    def _rounddown(self, x):
        x = self._roundup(-x)
        x = -x
        return x

    def _reverse(self, x):
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

    def _select_last(self, dfdata):
        # this function gives a set of indexes pointing to the last
        # datapoints for each cycle in the dataset

        # first - select the appropriate column heading to do "find last" on
        c_txt = self.cycle_index_txt  # gives the cycle number
        d_txt = self.data_point_txt  # gives the point number

        steps = []
        max_step = max(dfdata[c_txt])
        for j in range(max_step):
            # TODO use pd.loc[row,column] e.g. pd.loc[:,"charge_cap"] for col or pd.loc[(pd.["step"]==1),"x"]
            last_item = max(dfdata[dfdata[c_txt] == j + 1][d_txt])
            steps.append(last_item)
        last_items = dfdata[d_txt].isin(steps)
        return last_items

    def _extract_from_dict(self, t, x, default_value=None):
        try:
            value = t[x].values
            if value:
                value = value[0]
        except:
            value = default_value
        return value

    def _modify_cycle_number_using_cycle_step(self, from_tuple=[1, 4], to_cycle=44, test_number=None):
        # modify step-cycle tuple to new step-cycle tuple
        # from_tuple = [old cycle_number, old step_number]
        # to_cycle    = new cycle_number

        self.logger.debug("**- _modify_cycle_step")
        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return

        cycle_index_header = self.cycle_index_txt
        step_index_header = self.step_index_txt

        step_table_txt_cycle = self.step_table_txt_cycle
        step_table_txt_step = self.step_table_txt_step

        # modifying step_table
        st = self.tests[test_number].step_table
        st[step_table_txt_cycle][
            (st[step_table_txt_cycle] == from_tuple[0]) & (st[step_table_txt_step] == from_tuple[1])] = to_cycle
        # modifying normal_table
        nt = self.tests[test_number].dfdata
        nt[cycle_index_header][
            (nt[cycle_index_header] == from_tuple[0]) & (nt[step_index_header] == from_tuple[1])] = to_cycle
        # modifying summary_table
        # not implemented yet

    # ----------making-summary------------------------------------------------------
    def make_summary(self, find_ocv=False, find_ir=False, find_end_voltage=False,
                     use_cellpy_stat_file=True, all_tests=True,
                     test_number=0, ensure_step_table=None):
        """Convenience function that makes a summary of the cycling data."""

        if ensure_step_table is None:
            ensure_step_table = self.ensure_step_table
        # Cycle_Index	Test_Time(s)	Test_Time(h)	Date_Time	Current(A)
        # Current(mA)	Voltage(V)	Charge_Capacity(Ah)	Discharge_Capacity(Ah)
        # Charge_Energy(Wh)	Discharge_Energy(Wh)	Internal_Resistance(Ohm)
        # AC_Impedance(Ohm)	ACI_Phase_Angle(Deg)	Charge_Time(s)
        # DisCharge_Time(s)	Vmax_On_Cycle(V)	Coulombic_Efficiency
        if all_tests is True:
            for j in range(len(self.tests)):
                txt = "creating summary for file "
                test = self.tests[j]
                if not self._is_not_empty_test(test):
                    print "empty test %i" % (j)
                    return
                if isinstance(test.loaded_from, (list, tuple)):
                    for f in test.loaded_from:
                        txt += f
                        txt += "\n"
                else:
                    txt += test.loaded_from

                if not test.mass_given:
                    txt += " mass for test %i is not given" % j
                    txt += " setting it to %f mg" % test.mass
                self.logger.debug(txt)

                self._make_summary(j,
                                   find_ocv=find_ocv,
                                   find_ir=find_ir,
                                   find_end_voltage=find_end_voltage,
                                   use_cellpy_stat_file=use_cellpy_stat_file,
                                   ensure_step_table=ensure_step_table,
                                   )
        else:
            self.logger.debug("creating summary for only one test")
            test_number = self._validate_test_number(test_number)
            if test_number is None:
                self._report_empty_test()
                return
            self._make_summary(test_number,
                               find_ocv=find_ocv,
                               find_ir=find_ir,
                               find_end_voltage=find_end_voltage,
                               use_cellpy_stat_file=use_cellpy_stat_file,
                               ensure_step_table=ensure_step_table,
                               )

    def _make_summary(self,
                      test_number=None,
                      mass=None,
                      update_it=False,
                      select_columns=False,
                      find_ocv=False,
                      find_ir=False,
                      find_end_voltage=False,
                      convert_date=True,
                      sort_my_columns=True,
                      use_cellpy_stat_file=True,
                      ensure_step_table=False,
                      # capacity_modifier = None,
                      # test=None
                      ):

        # TODO: insert diagnostics plots
        # TODO: check if cumulated capacity loss is defined correctly

        test_number = self._validate_test_number(test_number)
        if test_number is None:
            self._report_empty_test()
            return
        test = self.tests[test_number]
        #        if test.merged == True:
        #            use_cellpy_stat_file=False

        if not mass:
            mass = test.mass
        else:
            if update_it:
                test.mass = mass

        if ensure_step_table:
            if not test.step_table_made:
                self.create_step_table(test_number=test_number)
        summary_df = test.dfsummary
        dfdata = test.dfdata

        dt_txt = self.datetime_txt
        c_txt = self.cycle_index_txt
        d_txt = self.data_point_txt
        s_txt = self.step_index_txt
        voltage_header = self.voltage_txt
        charge_txt = self.charge_capacity_txt
        discharge_txt = self.discharge_capacity_txt
        if use_cellpy_stat_file:
            summary_requirment = dfdata[d_txt].isin(summary_df[d_txt])
        else:
            summary_requirment = self._select_last(dfdata)
        dfsummary = dfdata[summary_requirment]

        column_names = dfsummary.columns
        summary_length = len(dfsummary[column_names[0]])
        dfsummary.index = range(summary_length)  # could also index based on Cycle_Index
        indexes = dfsummary.index

        if select_columns:
            columns_to_keep = ["Charge_Capacity", "Charge_Energy", "Current", "Cycle_Index",  # TODO jepe fix
                               "Data_Point", "DateTime", "Discharge_Capacity", "Discharge_Energy",
                               "Internal_Resistance", "Step_Index", "Step_Time", "Test_ID", "Test_Time",
                               "Voltage",
                               ]
            for column_name in column_names:
                if not columns_to_keep.count(column_name):
                    dfsummary.pop(column_name)
        if not use_cellpy_stat_file:
            print "values obtained from dfdata:"
            print dfsummary
            print

        discharge_capacity = dfsummary[discharge_txt] * 1000000 / mass
        discharge_title = self.summary_txt_discharge_cap
        dfsummary.insert(0, column=discharge_title, value=discharge_capacity)

        charge_capacity = dfsummary[charge_txt] * 1000000 / mass
        charge_title = self.summary_txt_charge_cap
        dfsummary.insert(0, column=charge_title, value=charge_capacity)

        charge_capacity_cumsum = dfsummary[charge_title].cumsum()
        cumcharge_title = self.summary_txt_cum_charge_cap
        dfsummary.insert(0, column=cumcharge_title, value=charge_capacity_cumsum)

        col_eff = 100.0 * dfsummary[charge_txt] / dfsummary[discharge_txt]
        coloumb_title = self.summary_txt_coul_eff
        dfsummary.insert(0, column=coloumb_title, value=col_eff)

        col_diff = dfsummary[charge_title] - dfsummary[discharge_title]
        coloumb_diff_title = self.summary_txt_coul_diff
        dfsummary.insert(0, column=coloumb_diff_title, value=col_diff)

        col_diff_cumsum = dfsummary[coloumb_diff_title].cumsum()
        cumcoloumb_diff_title = self.summary_txt_cum_coul_diff
        dfsummary.insert(0, column=cumcoloumb_diff_title, value=col_diff_cumsum)

        col_discharge_loss_title = self.summary_txt_discharge_cap_loss
        col_discharge_loss_df = dfsummary[discharge_title].copy()
        dfsummary.insert(0, column=col_discharge_loss_title, value=col_discharge_loss_df)

        for j in col_discharge_loss_df.index:
            if j == 0:
                value = 0.0
            else:
                # value = dfsummary[discharge_title].ix[j-1]-dfsummary[discharge_title].ix[j]
                # value = dfsummary[discharge_title].iloc[j-1]-dfsummary[discharge_title].iloc[j]
                value = dfsummary.loc[j - 1, discharge_title] - dfsummary.loc[j, discharge_title]
            # dfsummary[col_discharge_loss_title].ix[j]=value # TODO change this .iloc
            dfsummary.loc[j, col_discharge_loss_title] = value

        col_charge_loss_title = self.summary_txt_charge_cap_loss
        col_charge_loss_df = dfsummary[charge_title].copy()
        dfsummary.insert(0, column=col_charge_loss_title, value=col_charge_loss_df)

        for j in col_charge_loss_df.index:
            if j == 0:
                value = 0.0
            else:
                # value = dfsummary[charge_title].ix[j-1]-dfsummary[charge_title].ix[j]
                # value = dfsummary[charge_title].iloc[j-1]-dfsummary[charge_title].iloc[j]
                value = dfsummary.loc[j - 1, charge_title] - dfsummary.loc[j, charge_title]
            # dfsummary[col_charge_loss_title].ix[j]=value # TODO change this .iloc
            # dfsummary[col_charge_loss_title].iloc[j]=value
            dfsummary.loc[j, col_charge_loss_title] = value

        col_dcloss_cumsum = dfsummary[col_discharge_loss_title].cumsum()
        dcloss_cumsum_title = self.summary_txt_cum_discharge_cap_loss
        dfsummary.insert(0, column=dcloss_cumsum_title, value=col_dcloss_cumsum)

        col_closs_cumsum = dfsummary[col_charge_loss_title].cumsum()
        closs_cumsum_title = self.summary_txt_cum_charge_cap_loss
        dfsummary.insert(0, column=closs_cumsum_title, value=col_closs_cumsum)

        if convert_date:
            newstamps = []
            for stamp in dfsummary[dt_txt]:
                newstamp = xldate_as_datetime(stamp, option="to_string")
                newstamps.append(newstamp)
            # dfsummary[self.summary_txt_datetime_txt]=newstamps
            dfsummary.loc[:, self.summary_txt_datetime_txt] = newstamps
        newversion = True

        if find_ocv:
            do_ocv_1 = True
            do_ocv_2 = True

            ocv1_type = 'ocvrlx_up'
            ocv2_type = 'ocvrlx_down'

            if not self.cycle_mode == 'anode':
                ocv2_type = 'ocvrlx_up'
                ocv1_type = 'ocvrlx_down'

            ocv_1 = self._get_ocv(ocv_steps=test.ocv_steps,
                                  ocv_type=ocv1_type,
                                  test_number=test_number)

            ocv_2 = self._get_ocv(ocv_steps=test.ocv_steps,
                                  ocv_type=ocv2_type,
                                  test_number=test_number)

            if do_ocv_1:
                only_zeros = dfsummary[discharge_txt] * 0.0
                ocv_1_indexes = []
                ocv_1_v_min = []
                ocv_1_v_max = []
                ocvcol_min = only_zeros.copy()
                ocvcol_max = only_zeros.copy()
                ocv_1_v_min_title = self.summary_txt_ocv_1_min
                ocv_1_v_max_title = self.summary_txt_ocv_1_max

                for j in ocv_1:
                    cycle = j["Cycle_Index"].values[0]  # jepe fix
                    # try to find inxed
                    index = dfsummary[(dfsummary[self.cycle_index_txt] == cycle)].index
                    # print cycle, index,
                    v_min = j["Voltage"].min()  # jepe fix
                    v_max = j["Voltage"].max()  # jepe fix
                    # print v_min,v_max
                    dv = v_max - v_min
                    ocvcol_min.ix[index] = v_min
                    ocvcol_max.ix[index] = v_max

                dfsummary.insert(0, column=ocv_1_v_min_title, value=ocvcol_min)
                dfsummary.insert(0, column=ocv_1_v_max_title, value=ocvcol_max)

            if do_ocv_2:
                only_zeros = dfsummary[discharge_txt] * 0.0
                ocv_2_indexes = []
                ocv_2_v_min = []
                ocv_2_v_max = []
                ocvcol_min = only_zeros.copy()
                ocvcol_max = only_zeros.copy()
                ocv_2_v_min_title = self.summary_txt_ocv_2_min
                ocv_2_v_max_title = self.summary_txt_ocv_2_max

                for j in ocv_2:
                    cycle = j["Cycle_Index"].values[0]  # jepe fix
                    # try to find inxed
                    index = dfsummary[(dfsummary[self.cycle_index_txt] == cycle)].index
                    v_min = j["Voltage"].min()  # jepe fix
                    v_max = j["Voltage"].max()  # jepe fix
                    dv = v_max - v_min
                    ocvcol_min.ix[index] = v_min
                    ocvcol_max.ix[index] = v_max
                dfsummary.insert(0, column=ocv_2_v_min_title, value=ocvcol_min)
                dfsummary.insert(0, column=ocv_2_v_max_title, value=ocvcol_max)

        if find_end_voltage:
            only_zeros_discharge = dfsummary[discharge_txt] * 0.0
            only_zeros_charge = dfsummary[charge_txt] * 0.0
            if not test.discharge_steps:
                # discharge_steps=self.find_step_numbers(test_number=test_number,step_type ="discharge_capacity",only_one=True)
                discharge_steps = self.get_step_numbers(steptype='discharge', allctypes=False, test_number=test_number)
            else:
                discharge_steps = test.discharge_steps
                self.logger.debug("alrady have discharge_steps")
            if not test.charge_steps:
                # charge_steps=self.find_step_numbers(test_number=test_number,step_type ="charge_capacity",only_one=True)
                charge_steps = self.get_step_numbers(steptype='charge', allctypes=False, test_number=test_number)
            else:
                charge_steps = test.charge_steps
                self.logger.debug("already have charge_steps")
            endv_discharge_title = self.summary_txt_endv_discharge
            endv_charge_title = self.summary_txt_endv_charge
            endv_indexes = []
            endv_values_dc = []
            endv_values_c = []
            self.logger.debug("trying to find end voltage for")
            self.logger.debug(test.loaded_from)
            self.logger.debug("Using the following chargesteps")
            self.logger.debug(charge_steps)
            self.logger.debug("Using the following dischargesteps")
            self.logger.debug(discharge_steps)

            for i in dfsummary.index:
                txt = "index in dfsummary.index: %i" % (i)
                self.logger.debug(txt)
                # selecting the appropriate cycle
                cycle = dfsummary.ix[i][self.cycle_index_txt]  # "Cycle_Index" = i + 1
                txt = "cycle: %i" % (cycle)
                self.logger.debug(txt)
                step = discharge_steps[cycle]

                # finding end voltage for discharge
                if step[-1]:  # selecting last
                    # TODO use pd.loc[row,column] e.g. pd.loc[:,"charge_cap"] for col or pd.loc[(pd.["step"]==1),"x"]
                    end_voltage_dc = dfdata[(dfdata[c_txt] == cycle) & (test.dfdata[s_txt] == step[-1])][voltage_header]
                    # This will not work if there are more than one item in step
                    end_voltage_dc = end_voltage_dc.values[-1]  # selecting last (could also select amax)
                else:
                    end_voltage_dc = 0  # could also use numpy.nan

                # finding end voltage for charge
                step2 = charge_steps[cycle]
                if step2[-1]:
                    end_voltage_c = dfdata[(dfdata[c_txt] == cycle) & (test.dfdata[s_txt] == step2[-1])][voltage_header]
                    end_voltage_c = end_voltage_c.values[-1]
                    # end_voltage_c = np.amax(end_voltage_c)
                else:
                    end_voltage_c = 0
                endv_indexes.append(i)
                endv_values_dc.append(end_voltage_dc)
                endv_values_c.append(end_voltage_c)

            ir_frame_dc = only_zeros_discharge + endv_values_dc
            ir_frame_c = only_zeros_charge + endv_values_c
            dfsummary.insert(0, column=endv_discharge_title, value=ir_frame_dc)
            dfsummary.insert(0, column=endv_charge_title, value=ir_frame_c)

        if find_ir:
            # should check:  test.charge_steps = None,   test.discharge_steps = None
            # THIS DOES NOT WORK PROPERLY!!!!
            # Found a file where it writes IR for cycle n on cycle n+1
            # This only picks out the data on the last IR step before the (dis)charge cycle

            # TODO: use self.step_table instead for finding charge/discharge steps
            only_zeros = dfsummary[discharge_txt] * 0.0
            if not test.discharge_steps:
                # discharge_steps=self.find_step_numbers(test_number=test_number,step_type ="discharge_capacity",only_one=True)
                discharge_steps = self.get_step_numbers(steptype='discharge', allctypes=False, test_number=test_number)
            else:
                discharge_steps = test.discharge_steps
                self.logger.debug("alrady have discharge_steps")
            if not test.charge_steps:
                # charge_steps=self.find_step_numbers(test_number=test_number,step_type ="charge_capacity",only_one=True)
                charge_steps = self.get_step_numbers(steptype='charge', allctypes=False, test_number=test_number)
            else:
                charge_steps = test.charge_steps
                self.logger.debug("alrady have charge_steps")
            ir_discharge_title = self.summary_txt_ir_discharge
            ir_charge_title = self.summary_txt_ir_charge
            ir_indexes = []
            ir_values = []
            ir_values2 = []
            self.logger.debug("trying to find ir for")
            self.logger.debug(test.loaded_from)
            self.logger.debug("Using the following chargesteps")
            self.logger.debug(charge_steps)
            self.logger.debug("Using the following dischargesteps")
            self.logger.debug(discharge_steps)

            for i in dfsummary.index:
                txt = "index in dfsummary.index: %i" % (i)
                self.logger.debug(txt)
                # selecting the appropriate cycle
                cycle = dfsummary.ix[i][self.cycle_index_txt]  # "Cycle_Index" = i + 1
                txt = "cycle: %i" % (cycle)
                self.logger.debug(txt)
                step = discharge_steps[cycle]
                if step[0]:
                    # TODO use pd.loc[row,column] e.g. pd.loc[:,"charge_cap"] for col or pd.loc[(pd.["step"]==1),"x"]
                    ir = dfdata[(dfdata[c_txt] == cycle) & (test.dfdata[s_txt] == step[0])][
                        self.internal_resistance_txt]
                    # This will not work if there are more than one item in step
                    ir = ir.values[0]
                else:
                    ir = 0
                step2 = charge_steps[cycle]
                if step2[0]:

                    ir2 = dfdata[(dfdata[c_txt] == cycle) & (test.dfdata[s_txt] == step2[0])][
                        self.internal_resistance_txt].values[0]
                else:
                    ir2 = 0
                ir_indexes.append(i)
                ir_values.append(ir)
                ir_values2.append(ir2)

            ir_frame = only_zeros + ir_values
            ir_frame2 = only_zeros + ir_values2
            dfsummary.insert(0, column=ir_discharge_title, value=ir_frame)
            dfsummary.insert(0, column=ir_charge_title, value=ir_frame2)

        if sort_my_columns:
            if convert_date:
                new_first_col_list = [self.summary_txt_datetime_txt,
                                      self.test_time_txt,
                                      self.data_point_txt,
                                      self.cycle_index_txt]
            else:
                new_first_col_list = [self.datetime_txt,
                                      self.test_time_txt,
                                      self.data_point_txt,
                                      self.cycle_index_txt]

            dfsummary = self.set_col_first(dfsummary, new_first_col_list)

        test.dfsummary = dfsummary
        test.dfsummary_made = True


def setup_cellpy_instance():
    """Prepares for a cellpy session.

    This convenience function creates a cellpy class and sets the parameters
    from your parameters file (using prmreader.read()

    Returns:
        an cellpydata object

    Example:

        >>> celldata = setup_cellpy_instance()
        read prms
        ...
        making class and setting prms

    """
    from cellpy import prmreader
    prms = prmreader.read()
    print "read prms"
    print prms
    print "making class and setting prms"
    cellpy_instance = cellpydata(verbose=True)
    cellpy_instance.set_cellpy_datadir(prms.cellpydatadir)
    cellpy_instance.set_raw_datadir(prms.rawdatadir)
    return cellpy_instance


def just_load_srno(srno, prm_filename=None):
    """Simply load an dataset based on serial number (srno).

    This convenience function reads a dataset based on a serial number. This serial
    number (srno) must then be defined in your database. It is mainly used to check
    that things are set up correctly

    Args:
        srno (int): serial number

    Example:
        >>> srno = 918
        >>> just_load_srno(srno)
        srno: 918
        read prms
        ....

        """
    from cellpy import dbreader, prmreader, filefinder
    print "just_load_srno: srno: %i" % srno

    # ------------reading parametres--------------------------------------------
    print "just_load_srno: read prms"
    prms = prmreader.read(prm_filename)

    print prms

    print "just_load_srno: making class and setting prms"
    d = cellpydata(verbose=True)
    # d.set_cellpy_datadir(prms.cellpydatadir)
    # d.set_raw_datadir(prms.rawdatadir)
    # ------------reading db----------------------------------------------------
    print
    print "just_load_srno: starting to load reader"
    reader = dbreader.reader(prm_filename)
    print "------ok------"

    run_name = reader.get_cell_name(srno)
    print "just_load_srno: run_name:"
    print run_name

    m = reader.get_mass(srno)
    print "just_load_srno: mass: %f" % m
    print

    # ------------loadcell------------------------------------------------------
    print "just_load_srno: getting file_names"
    raw_files, cellpy_file = filefinder.search_for_files(run_name)
    print "raw_files:", raw_files
    print "cellpy_file:", cellpy_file

    print "just_load_srno: running loadcell"
    d.loadcell(raw_files, cellpy_file, mass=m)
    print "------ok------"

    # ------------do stuff------------------------------------------------------
    print "just_load_srno: getting step_numbers for charge"
    v = d.get_step_numbers("charge")
    print v

    print
    print "just_load_srno: finding C-rates"
    d.find_C_rates(v, silent=False)

    print
    print "just_load_srno: OK"
    return True


def load_and_save_resfile(filename, outfile=None, outdir=None, mass=1.00):
    """Load a raw data file and save it as cellpy-file.

    Args:
        mass (float): active material mass [mg].
        outdir (path): optional, path to directory for saving the hdf5-file.
        outfile (str): optional, name of hdf5-file.
        filename (str): name of the resfile.

    Returns:
        out_file_name (str): name of saved file.
    """
    d = cellpydata(verbose=True)

    if not outdir:
        from cellpy import prmreader
        prms = prmreader.read()
        outdir = prms.cellpydatadir

    if not outfile:
        outfile = os.path.basename(filename).split(".")[0] + ".h5"
        outfile = os.path.join(outdir, outfile)

    print "filename:", filename
    print "outfile:", outfile
    print "outdir:", outdir
    print "mass:", mass, "mg"

    d.loadres(filename)
    d.set_mass(mass)
    d.create_step_table()
    d.make_summary()
    d.save_test(filename=outfile)
    d.exportcsv(datadir=outdir, cycles=True, raw=True, summary=True)
    return outfile


def loadcellcheck():
    print "running loadcellcheck"
    out_dir = r"C:\Cell_data\tmp"
    mass = 0.078609164
    rawfile =  r"C:\Cell_data\tmp\large_file_01.res"
    cellpyfile = r"C:\Cell_data\tmp\out\large_file_01.h5"
    cell_data = cellpydata()
    cell_data.select_minimal = True
    cell_data.chunk_size = 100000
    #cell_data.last_chunk = 28
    cell_data.load_until_error = True
    cell_data.max_res_filesize = 400000000
    cell_data.loadcell(raw_files=rawfile, cellpy_file=None, only_summary=False)
    cell_data.set_mass(mass)
    if not cell_data.summary_exists:
        cell_data.make_summary()
    cell_data.save_test(cellpyfile)
    cell_data.exportcsv(datadir=out_dir, cycles=True, raw=True, summary=True)
    print "ok"


def extract_ocvrlx(filename, fileout, mass=1.00):
    """Get the ocvrlx data from dataset.

    Convenience function for extracting ocv relaxation data from runs."""
    import itertools
    import csv
    import matplotlib.pyplot as plt
    type_of_data = "ocvrlx_up"
    d_res = setup_cellpy_instance()
    print filename
    d_res.loadres(filename)
    d_res.set_mass(mass)
    d_res.create_step_table()
    d_res.print_step_table()
    out_data = []
    for cycle in d_res.get_cycle_numbers():
        try:
            if type_of_data == 'ocvrlx_up':
                print "getting ocvrlx up data for cycle %i" % (cycle)
                t, v = d_res.get_ocv(ocv_type='ocvrlx_up', cycle_number=cycle)
            else:
                print "getting ocvrlx down data for cycle %i" % (cycle)
                t, v = d_res.get_ocv(ocv_type='ocvrlx_down', cycle_number=cycle)
            plt.plot(t, v)
            t = t.tolist()
            v = v.tolist()

            header_x = "time (s) cycle_no %i" % cycle
            header_y = "voltage (V) cycle_no %i" % cycle
            t.insert(0, header_x)
            v.insert(0, header_y)
            out_data.append(t)
            out_data.append(v)

        except:
            print "could not extract cycle %i" % (cycle)

    save_to_file = False
    if save_to_file:
        # Saving cycles in one .csv file (x,y,x,y,x,y...)

        endstring = ".csv"
        outfile = fileout + endstring

        delimiter = ";"
        print "saving the file with delimiter '%s' " % (delimiter)
        with open(outfile, "wb") as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerows(itertools.izip_longest(*out_data))
            # star (or asterix) means transpose (writing cols instead of rows)

        print "saved the file",
        print outfile
    plt.show()
    print "bye!"
    return True


# TODO: make option to create step_table when loading file (loadres)
# TODO next:
# 1) new step_table structure [under dev]
# 2) new summary structure
# 3) new overall prms structure (i.e. run summary)
# 4) change name and allow non-arbin type of files
# NOTE
#
#
# PROBLEMS:
# 1. 27.06.2016 new PC with 64bit conda python package:
#              Error opening connection to "Provider=Microsoft.ACE.OLEDB.12.0
#
# FIX:
# 1. 27.06.2016 installed 2007 Office System Driver: Data Connectivity Components
#             (https://www.microsoft.com/en-us/download/confirmation.aspx?id=23734)
#             DID NOT WORK
#    27.06.2016 tried Microsoft Access Database Engine 2010 Redistributable   64x
#             DID NOT INSTALL - my computer has 32bit office, can only be install
#             with 64-bit office
#    27.06.2016 installed Microsoft Access Database Engine 2010 Redistributable   86x
#            DID NOT WORK
#    27.06.2016 uninstalled anaconda 64bit - installed 32 bit
#            WORKED!
#            LESSON LEARNED: dont use 64bit python with 32bit office installed


if __name__ == "__main__":
    print "running",
    print sys.argv[0]
    d = cellpydata()
    just_load_srno(614, r"C:\Scripting\MyFiles\development_cellpy\cellpy\parametres\_cellpy_prms_devel.ini")
    # loadcellcheck()
