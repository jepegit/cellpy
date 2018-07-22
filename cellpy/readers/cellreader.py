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


Todo:
    * Documentation needed
    * Include functions gradually from old version
    * Rename datastructure
    * Remove mass dependency in summary data
    * use pd.loc[row,column] e.g. pd.loc[:,"charge_cap"] for col or
        pd.loc[(pd.["step"]==1),"x"]

"""

import os
import sys
import datetime
import collections
import warnings
import csv
import itertools
from scipy import interpolate
import numpy as np
import pandas as pd
import logging
import cellpy.parameters.prms as prms
from cellpy.exceptions import WrongFileVersion, DeprecatedFeature

CELLPY_FILE_VERSION = 3
MINIMUM_CELLPY_FILE_VERSION = 1
STEP_TABLE_VERSION = 3
NORMAL_TABLE_VERSION = 3
SUMMARY_TABLE_VERSION = 3

# TODO: fix chained assignments and performance warnings (comment below and fix)
warnings.filterwarnings('ignore', category=pd.io.pytables.PerformanceWarning)
pd.set_option('mode.chained_assignment', None)  # "raise" "warn"

# module_logger = logging.getLogger(__name__)


def get_headers_summary():
    """Returns a dictionary containing the header-strings for the summary
    (used as column headers for the summary pandas DataFrames)"""

    # - headers for out-files
    # 08.12.2016: added temperature_last, temperature_mean, aux_
    headers_summary = dict()
    headers_summary["discharge_capacity"] = "Discharge_Capacity(mAh/g)"
    headers_summary["charge_capacity"] = "Charge_Capacity(mAh/g)"
    headers_summary["cumulated_charge_capacity"] = \
        "Cumulated_Charge_Capacity(mAh/g)"
    headers_summary["cumulated_discharge_capacity"] = \
        "Cumulated_Discharge_Capacity(mAh/g)"
    headers_summary["coulombic_efficiency"] = \
        "Coulombic_Efficiency(percentage)"
    headers_summary["cumulated_coulombic_efficiency"] = \
        "Cumulated_Coulombic_Efficiency(percentage)"
    headers_summary["coulombic_difference"] = "Coulombic_Difference(mAh/g)"
    headers_summary["cumulated_coulombic_difference"] = \
        "Cumulated_Coulombic_Difference(mAh/g)"
    headers_summary["discharge_capacity_loss"] = \
        "Discharge_Capacity_Loss(mAh/g)"
    headers_summary["charge_capacity_loss"] = "Charge_Capacity_Loss(mAh/g)"
    headers_summary["cumulated_discharge_capacity_loss"] = \
        "Cumulated_Discharge_Capacity_Loss(mAh/g)"
    headers_summary["cumulated_charge_capacity_loss"] = \
        "Cumulated_Charge_Capacity_Loss(mAh/g)"
    headers_summary["ir_discharge"] = "IR_Discharge(Ohms)"
    headers_summary["ir_charge"] = "IR_Charge(Ohms)"
    headers_summary["ocv_first_min"] = "OCV_First_Min(V)"
    headers_summary["ocv_second_min"] = "OCV_Second_Min(V)"
    headers_summary["ocv_first_max"] = "OCV_First_Max(V)"
    headers_summary["ocv_second_max"] = "OCV_Second_Max(V)"
    headers_summary["date_time_txt"] = "Date_Time_Txt(str)"
    headers_summary["end_voltage_discharge"] = "End_Voltage_Discharge(V)"
    headers_summary["end_voltage_charge"] = "End_Voltage_Charge(V)"
    headers_summary["cumulated_ric_disconnect"] = "RIC_Disconnect(none)"
    headers_summary["cumulated_ric_sei"] = "RIC_SEI(none)"
    headers_summary["cumulated_ric"] = "RIC(none)"
    # Sum of irreversible capacity:
    headers_summary["low_level"] = "Low_Level(percentage)"
    # SEI loss:
    headers_summary["high_level"] = "High_Level(percentage)"
    headers_summary["shifted_charge_capacity"] = \
        "Charge_Endpoint_Slippage(mAh/g)"
    headers_summary["shifted_discharge_capacity"] = \
        "Discharge_Endpoint_Slippage(mAh/g)"
    headers_summary["temperature_last"] = "Last_Temperature(C)"
    headers_summary["temperature_mean"] = "Average_Temperature(C)"
    headers_summary["pre_aux"] = "Aux_"
    return headers_summary


def get_cellpy_units():
    """Returns a dictionary with units"""

    cellpy_units = dict()
    cellpy_units["current"] = 0.001  # mA
    cellpy_units["charge"] = 0.001  # Ah
    cellpy_units["mass"] = 0.001  # mg (used for input of mass)
    cellpy_units["specific"] = 1.0  # g (used for calc. of e.g. spec. capacity)
    return cellpy_units


def get_headers_normal():
    """Returns a dictionary containing the header-strings for the normal data
        (used as column headers for the main data pandas DataFrames)"""
    headers_normal = dict()
    headers_normal['aci_phase_angle_txt'] = 'ACI_Phase_Angle'
    headers_normal['ref_aci_phase_angle_txt'] = 'Reference_ACI_Phase_Angle'

    headers_normal['ac_impedance_txt'] = 'AC_Impedance'
    headers_normal['ref_ac_impedance_txt'] = 'Reference_AC_Impedance'  # new

    headers_normal['charge_capacity_txt'] = 'Charge_Capacity'
    headers_normal['charge_energy_txt'] = 'Charge_Energy'
    headers_normal['current_txt'] = 'Current'
    headers_normal['cycle_index_txt'] = 'Cycle_Index'
    headers_normal['data_point_txt'] = 'Data_Point'
    headers_normal['datetime_txt'] = 'DateTime'
    headers_normal['discharge_capacity_txt'] = 'Discharge_Capacity'
    headers_normal['discharge_energy_txt'] = 'Discharge_Energy'
    headers_normal['internal_resistance_txt'] = 'Internal_Resistance'

    headers_normal['is_fc_data_txt'] = 'Is_FC_Data'
    headers_normal['step_index_txt'] = 'Step_Index'
    headers_normal['sub_step_index_txt'] = 'Sub_Step_Index'  # new

    headers_normal['step_time_txt'] = 'Step_Time'
    headers_normal['sub_step_time_txt'] = 'Sub_Step_Time'  # new

    headers_normal['test_id_txt'] = 'Test_ID'
    headers_normal['test_time_txt'] = 'Test_Time'

    headers_normal['voltage_txt'] = 'Voltage'
    headers_normal['ref_voltage_txt'] = 'Reference_Voltage'  # new

    headers_normal['dv_dt_txt'] = 'dV/dt'
    headers_normal['frequency_txt'] = 'Frequency'  # new
    headers_normal['amplitude_txt'] = 'Amplitude'  # new

    return headers_normal


def get_headers_step_table():
    """Returns a dictionary containing the header-strings for the steps table
        (used as column headers for the steps pandas DataFrames)"""
    # 08.12.2016: added sub_step, sub_type, and pre_time
    headers_step_table = dict()
    headers_step_table["test"] = "test"
    headers_step_table["cycle"] = "cycle"
    headers_step_table["step"] = "step"
    headers_step_table["sub_step"] = "sub_step"
    headers_step_table["type"] = "type"
    headers_step_table["sub_type"] = "sub_type"
    headers_step_table["info"] = "info"
    headers_step_table["pre_current"] = "I_"
    headers_step_table["pre_voltage"] = "V_"
    headers_step_table["pre_charge"] = "Charge_"
    headers_step_table["pre_discharge"] = "Discharge_"
    headers_step_table["pre_point"] = "datapoint_"
    headers_step_table["pre_time"] = "time_"
    headers_step_table["post_mean"] = "avr"
    headers_step_table["post_std"] = "std"
    headers_step_table["post_max"] = "max"
    headers_step_table["post_min"] = "min"
    headers_step_table["post_start"] = "start"
    headers_step_table["post_end"] = "end"
    headers_step_table["post_delta"] = "delta"
    headers_step_table["post_rate"] = "rate"
    headers_step_table["internal_resistance"] = "IR"
    headers_step_table["internal_resistance_change"] = "IR_pct_change"
    return headers_step_table


def check64bit(current_system="python"):
    """checks if you are on a 64 bit platform"""
    if current_system == "python":
        return sys.maxsize > 2147483647
    elif current_system == "os":
        import platform
        pm = platform.machine()
        if pm != ".." and pm.endswith('64'):  # recent Python (not Iron)
            return True
        else:
            if 'PROCESSOR_ARCHITEW6432' in os.environ:
                return True  # 32 bit program running on 64 bit Windows
            try:
                # 64 bit Windows 64 bit program
                return os.environ['PROCESSOR_ARCHITECTURE'].endswith('64')
            except IndexError:
                pass  # not Windows
            try:
                # this often works in Linux
                return '64' in platform.architecture()[0]
            except Exception:
                # is an older version of Python, assume also an older os@
                # (best we can guess)
                return False


def humanize_bytes(b, precision=1):
    """Return a humanized string representation of a number of b.

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
    # abbrevs = (
    #     (1 << 50L, 'PB'),
    #     (1 << 40L, 'TB'),
    #     (1 << 30L, 'GB'),
    #     (1 << 20L, 'MB'),
    #     (1 << 10L, 'kB'),
    #     (1, 'b')
    # )
    abbrevs = (
        (1 << 50, 'PB'),
        (1 << 40, 'TB'),
        (1 << 30, 'GB'),
        (1 << 20, 'MB'),
        (1 << 10, 'kB'),
        (1, 'b')
    )
    if b == 1:
        return '1 byte'
    for factor, suffix in abbrevs:
        if b >= factor:
            break
    # return '%.*f %s' % (precision, old_div(b, factor), suffix)
    return '%.*f %s' % (precision, b // factor, suffix)


def xldate_as_datetime(xldate, datemode=0, option="to_datetime"):
    """Converts a xls date stamp to a more sensible format.

    Args:
        xldate (str): date stamp in Excel format.
        datemode (int): 0 for 1900-based, 1 for 1904-based.
        option (str): option in ("to_datetime", "to_float", "to_string"),
            return value

    Returns:
        datetime (datetime object, float, or string).

    """

    # This does not work for numpy-arrays

    if option == "to_float":
        d = (xldate - 25589) * 86400.0
    else:
        try:
            d = datetime.datetime(1899, 12, 30) + \
                datetime.timedelta(days=xldate + 1462 * datemode)
            # date_format = "%Y-%m-%d %H:%M:%S:%f" # with microseconds,
            # excel cannot cope with this!
            if option == "to_string":
                date_format = "%Y-%m-%d %H:%M:%S"  # without microseconds
                d = d.strftime(date_format)
        except TypeError:
            warnings.warn(f'The date is not of correct type [{xldate}]')
            d = xldate
    return d


# noinspection PyPep8Naming
def Convert2mAhg(c, mass=1.0):
    """Converts capacity in Ah to capacity in mAh/g.

    Args:
        c (float or numpy array): capacity in mA.
        mass (float): mass in mg.

    Returns:
        float: 1000000 * c / mass
    """
    return 1000000 * c / mass


# noinspection PyPep8Naming
class FileID(object):
    """class for storing information about the raw-data files.

        This class is used for storing and handling raw-data file information.
        It is important to keep track of when the data was extracted from the
        raw-data files so that it is easy to know if the hdf5-files used for
        @storing "treated" data is up-to-date.

        Attributes:
            name (str): Filename of the raw-data file.
            full_name (str): Filename including path of the raw-data file.
            size (float): Size of the raw-data file.
            last_modified (datetime): Last time of modification of the raw-data
                file.
            last_accessed (datetime): last time of access of the raw-data file.
            last_info_changed (datetime): st_ctime of the raw-data file.
            location (str): Location of the raw-data file.

        """

    def __init__(self, filename=None):
        make_defaults = True
        if filename:
            if os.path.isfile(filename):
                fid_st = os.stat(filename)
                self.name = os.path.abspath(filename)
                self.full_name = filename
                self.size = fid_st.st_size
                self.last_modified = fid_st.st_mtime
                self.last_accessed = fid_st.st_atime
                self.last_info_changed = fid_st.st_ctime
                self.location = os.path.dirname(filename)
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
        txt += "full name: %s\n" % self.full_name
        txt += "name: %s\n" % self.name
        if self.last_modified is not None:
            txt += f"modified: {self.last_modified}\n"
        else:
            txt += "modified: NAN\n"
        if self.size is not None:
            txt += f"size: {self.size}\n"
        else:
            txt += "size: NAN\n"
        return txt

    def populate(self, filename):
        """Finds the file-stats and populates the class with stat values.

        Args:
            filename (str): name of the file.
        """

        if os.path.isfile(filename):
            fid_st = os.stat(filename)
            self.name = os.path.abspath(filename)
            self.full_name = filename
            self.size = fid_st.st_size
            self.last_modified = fid_st.st_mtime
            self.last_accessed = fid_st.st_atime
            self.last_info_changed = fid_st.st_ctime
            self.location = os.path.dirname(filename)

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


# noinspection PyPep8Naming
class DataSet(object):
    """Object to store data for a test.

    This class is used for storing all the relevant data for a 'run', i.e. all
    the data collected by the tester as stored in the raw-files.

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
        self.logger.debug("created DataSet instance")

        self.test_no = None
        self.mass = prms.Materials["default_mass"]  # active material (in mg)
        self.tot_mass = prms.Materials["default_mass"]  # total material (in mg)
        self.no_cycles = 0.0
        self.charge_steps = None  # not in use at the moment
        self.discharge_steps = None  # not in use at the moment
        self.ir_steps = None  # dict # not in use at the moment
        self.ocv_steps = None  # dict # not in use at the moment
        self.nom_cap = prms.DataSet["nom_cap"]  # mAh/g (for finding c-rates)
        self.mass_given = False
        self.material = prms.Materials["default_material"]
        self.merged = False
        self.file_errors = None  # not in use at the moment
        self.loaded_from = None  # loaded from (can be list if merged)
        self.raw_data_files = []
        self.raw_data_files_length = []
        self.channel_index = None
        self.channel_number = None
        self.creator = None
        self.item_ID = None
        self.schedule_file_name = None
        self.start_datetime = None
        self.test_ID = None
        self.name = None
        # methods in CellpyData to update if adding new attributes:
        #  _load_infotable()
        # _create_infotable()

        self.data = collections.OrderedDict()  # not used
        self.summary = collections.OrderedDict()  # not used

        self.dfdata = None
        self.dfsummary = None
        self.dfsummary_made = False
        self.step_table = collections.OrderedDict()
        self.step_table_made = False
        self.parameter_table = collections.OrderedDict()
        self.summary_version = SUMMARY_TABLE_VERSION
        self.step_table_version = STEP_TABLE_VERSION
        self.cellpy_file_version = CELLPY_FILE_VERSION
        self.normal_table_version = NORMAL_TABLE_VERSION
        # ready for use if implementing loading units
        # (will probably never happen).
        self.raw_units = dict()  # units used for raw_data

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
        txt += f"material:            {self.material}\n"
        txt += f"mass (active):       {self.mass}\n"
        txt += f"test ID:             {self.test_ID}\n"
        txt += f"mass (total):        {self.tot_mass}\n"
        txt += f"nominal capacity:    {self.nom_cap}\n"
        txt += f"channel index:       {self.channel_index}\n"
        txt += f"DataSet name:        {self.name}\n"
        txt += f"creator:             {self.creator}\n"
        txt += f"schedule file name:  {self.schedule_file_name}\n"

        try:
            start_datetime_str = xldate_as_datetime(self.start_datetime)
        except Exception:
            start_datetime_str = "NOT READABLE YET"
        txt += f"start-date:         {start_datetime_str}\n"

        txt += "   DATA:\n"
        try:
            txt += str(self.dfdata.head())
        except AttributeError:
            txt += "EMPTY (Not processed yet)\n"

        txt += "   \nSUMMARY:\n"
        try:
            txt += str(self.dfsummary.head())
        except AttributeError:
            txt += "EMPTY (Not processed yet)\n"

        txt += "   \nPARAMETERS:\n"
        try:
            txt += str(self.parameter_table.head())
        except AttributeError:
            txt += "EMPTY (Not processed yet)\n"

        txt += "raw units:"
        txt += "     Currently defined in the CellpyData-object"
        return txt


class CellpyData(object):
    """Main class for working and storing data.

    This class is the main work-horse for cellpy where all the functions for
    reading, selecting, and tweaking your data is located. It also contains the
    header definitions, both for the cellpy hdf5 format, and for the various
    cell-tester file-formats that can be read. The class can contain
    several tests and each test is stored in a list. If you see what I mean...

    Attributes:
        datasets (list): list of DataSet objects.
    """

    def __init__(self, filenames=None,
                 selected_scans=None,
                 profile=False,
                 filestatuschecker=None,  # "modified"
                 fetch_one_liners=False,
                 tester=None,
                 ):
        """

        Returns:
            None:
        """

        if tester is None:
            self.tester = prms.Instruments["tester"]
        else:
            self.tester = tester
        self.loader = None  # this will be set in the function set_instrument
        self.logger = logging.getLogger(__name__)
        self.logger.info("created CellpyData instance")
        self.profile = profile
        self.minimum_selection = {}
        if filestatuschecker is None:
            self.filestatuschecker = prms.Reader["filestatuschecker"]
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

        self.datasets = []
        self.status_datasets = []
        self.step_table = None
        self.selected_dataset_number = 0
        self.number_of_datasets = 0

        self.capacity_modifiers = ['reset', ]

        self.list_of_step_types = ['charge', 'discharge',
                                   'cv_charge', 'cv_discharge',
                                   'charge_cv', 'discharge_cv',
                                   'ocvrlx_up', 'ocvrlx_down', 'ir',
                                   'rest', 'not_known']
        # - options
        self.force_step_table_creation = \
            prms.Reader["force_step_table_creation"]
        self.force_all = prms.Reader["force_all"]
        self.sep = prms.Reader["sep"]
        self.cycle_mode = prms.Reader["cycle_mode"]
        # self.max_res_filesize = prms.Reader["max_res_filesize"]
        self.load_only_summary = prms.Reader["load_only_summary"]
        self.select_minimal = prms.Reader["select_minimal"]
        # self.chunk_size = prms.Reader["chunk_size"]  # 100000
        # self.max_chunks = prms.Reader["max_chunks"]
        # self.last_chunk = prms.Reader["last_chunk"]
        self.limit_loaded_cycles = prms.Reader["limit_loaded_cycles"]
        # self.load_until_error = prms.Reader["load_until_error"]
        self.ensure_step_table = prms.Reader["ensure_step_table"]
        self.daniel_number = prms.Reader["daniel_number"]
        self.raw_datadir = prms.Reader["raw_datadir"]
        self.cellpy_datadir = prms.Reader["cellpy_datadir"]
        # search in prm-file for res and hdf5 dirs in loadcell:
        self.auto_dirs = prms.Reader["auto_dirs"]

        # - headers and instruments
        self.headers_normal = get_headers_normal()
        self.headers_summary = get_headers_summary()
        self.headers_step_table = get_headers_step_table()

        self.table_names = None  # dictionary defined in set_instruments
        self.set_instrument()

        # - units used by cellpy
        self.cellpy_units = get_cellpy_units()

    @property
    def dataset(self):
        """returns the DataSet instance"""
        return self.datasets[self.selected_dataset_number]

    def set_instrument(self, instrument=None):
        """Set the instrument (i.e. tell cellpy the file-type you use).

        Args:
            instrument: (str) in ["arbin", "bio-logic-csv", "bio-logic-bin",...]

        Sets the instrument used for obtaining the data (i.e. sets fileformat)

        """
        if instrument is None:
            instrument = self.tester

        if instrument in ["arbin", "arbin_res"]:
            self._set_arbin()

        elif instrument == "arbin_experimental":
            self._set_arbin_experimental()

        elif instrument in ["biologics", "biologics_mpr"]:
            self._set_biologic()

        else:
            raise Exception(f"option does not exist: '{instrument}'")

    def _set_biologic(self):
        warnings.warn("Experimental! Not ready for production!")
        from cellpy.readers.instruments import biologics_mpr as instr

        self.loader_class = instr.MprLoader()
        # get information
        self.raw_units = self.loader_class.get_raw_units()
        self.raw_limits = self.loader_class.get_raw_limits()
        # create loader
        self.loader = self.loader_class.loader

    def _set_pec(self):
        warnings.warn("not implemented")

    def _set_maccor(self):
        warnings.warn("not implemented")

    def _set_arbin(self):
        # Note! All these _set_instrument methods can be generalized to one
        # method. At the moment, I find it more transparent to separate them
        # into respective methods pr instrument.

        from cellpy.readers.instruments import arbin as instr
        self.loader_class = instr.ArbinLoader()
        # get information
        self.raw_units = self.loader_class.get_raw_units()
        self.raw_limits = self.loader_class.get_raw_limits()
        # send information (should improve this later)
        # loader_class.load_only_summary = self.load_only_summary
        # loader_class.select_minimal = self.select_minimal
        # loader_class.max_res_filesize = self.max_res_filesize
        # loader_class.chunk_size = self.chunk_size
        # loader_class.max_chunks = self.max_chunks
        # loader_class.last_chunk = self.last_chunk
        # loader_class.limit_loaded_cycles = self.limit_loaded_cycles
        # loader_class.load_until_error = self.load_until_error

        # create loader
        self.loader = self.loader_class.loader

    # def _set_arbin_experimental(self):
    #     # Note! All these _set_instrument methods can be generalized to one
    #     # method. At the moment, I find it
    #     # more transparent to separate them into respective methods pr
    #     # instrument.
    #     from .instruments import arbin_experimental as instr
    #     self.loader_class = instr.ArbinLoader()
    #     # get information
    #     self.raw_units = self.loader_class.get_raw_units()
    #     self.raw_limits = self.loader_class.get_raw_limits()
    #     # send information (should improve this later)
    #     # loader_class.load_only_summary = self.load_only_summary
    #     # loader_class.select_minimal = self.select_minimal
    #     # loader_class.max_res_filesize = self.max_res_filesize
    #     # loader_class.chunk_size = self.chunk_size
    #     # loader_class.max_chunks = self.max_chunks
    #     # loader_class.last_chunk = self.last_chunk
    #     # loader_class.limit_loaded_cycles = self.limit_loaded_cycles
    #     # loader_class.load_until_error = self.load_until_error
    #
    #     # create loader
    #     self.loader = self.loader_class.loader

    def _create_logger(self):
        from cellpy import log
        self.logger = logging.getLogger(__name__)
        log.setup_logging(default_level="DEBUG")

    def set_cycle_mode(self, cycle_mode):
        """set the cycle mode.

        (will be deprecated soon - use prms.Reader.cycle_mode = "anode" etc.)"""
        # should use proper python 'setting' (decorator etc)
        self.cycle_mode = cycle_mode

    def set_raw_datadir(self, directory=None):
        """Set the directory containing .res-files.

        Used for setting directory for looking for res-files.@
        A valid directory name is required.

        Args:
            directory (str): path to res-directory

        Example:
            >>> d = CellpyData()
            >>> directory = r"C:\MyData\Arbindata"
            >>> d.set_raw_datadir(directory)

        """

        if directory is None:
            print("no directory name given")
            return
        if not os.path.isdir(directory):
            print(directory)
            print("directory does not exist")
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
            >>> directory = r"C:\MyData\HDF5"
            >>> d.set_raw_datadir(directory)

        """

        if directory is None:
            print("no directory name given")
            return
        if not os.path.isdir(directory):
            print("directory does not exist")
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
            False if the raw files are newer than the cellpy hdf5-file
                (update needed).
            If return_res is True it also returns list of raw-file_names as
                second argument.
            """

        txt = "check_file_ids\n  checking file ids - using '%s'" \
              % self.filestatuschecker

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
            fid = FileID(f)
            self.logger.debug(fid)
            if fid.name is None:
                print("file does not exist:")
                print(f)
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
            fidtable = store.select("CellpyData/fidtable")
        except Exception:
            self.logger.warning("no fidtable -"
                                " you should update your hdf5-file")
            fidtable = None
        finally:
            store.close()
        if fidtable is not None:
            raw_data_files, raw_data_files_length = \
                self._convert2fid_list(fidtable)
            txt = "contains %i res-files" % (len(raw_data_files))
            self.logger.debug(txt)
            ids = dict()
            for fid in raw_data_files:
                full_name = fid.full_name
                size = fid.size
                mod = fid.last_modified
                txt = "\nfileID information\nfull name: %s\n" % full_name
                txt += f"modified: {mod}\n"
                txt += "size: {size}\n"
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

    @staticmethod
    def _compare_ids(ids_res, ids_cellpy_file):
        similar = True
        l_res = len(ids_res)
        l_cellpy = len(ids_cellpy_file)
        if l_res == l_cellpy and l_cellpy > 0:
            for name, value in list(ids_res.items()):
                if ids_cellpy_file[name] != value:
                    similar = False
        else:
            similar = False

        return similar

    def loadcell(self, raw_files, cellpy_file=None, mass=None,
                 summary_on_raw=False, summary_ir=True, summary_ocv=False,
                 summary_end_v=True, only_summary=False, only_first=False,
                 force_raw=False,
                 use_cellpy_stat_file=None):

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
            use_cellpy_stat_file (bool): use stat file if creating summary
                from raw

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
        self.logger.info("started loadcell")
        if cellpy_file is None:
            similar = False
        elif force_raw:
            similar = False
        else:
            similar = self.check_file_ids(raw_files, cellpy_file)
        self.logger.debug("checked if the files were similar")

        if only_summary:
            self.load_only_summary = True
        else:
            self.load_only_summary = False

        if not similar:
            self.logger.info("cellpy file(s) needs updating - loading raw")
            self.logger.debug(raw_files)
            self.from_raw(raw_files)
            self.logger.debug("loaded files")
            # Check if the run was loaded ([] if empty)
            if self.status_datasets:
                if mass:
                    self.set_mass(mass)
                if summary_on_raw:
                    self.make_summary(all_tests=False, find_ocv=summary_ocv,
                                      find_ir=summary_ir,
                                      find_end_voltage=summary_end_v,
                                      use_cellpy_stat_file=use_cellpy_stat_file)
            else:
                self.logger.warning("Empty run!")
        else:
            self.load(cellpy_file)

    def from_raw(self, file_names=None, **kwargs):
        """Load a raw data-file.

        Args:
            file_names (list of raw-file names): uses CellpyData.file_names if
                None. If the list contains more than one file name, then the
                runs will be merged together.
        """
        # This function only loads one test at a time (but could contain several
        # files). The function from_res() also implements loading several
        # datasets (using list of lists as input).

        if file_names:
            self.file_names = file_names

        if not isinstance(file_names, (list, tuple)):
            self.file_names = [file_names, ]

        # file_type = self.tester
        raw_file_loader = self.loader
        set_number = 0
        test = None
        counter = 0
        for f in self.file_names:
            self.logger.debug("loading raw file: {}".format(f))
            new_tests = raw_file_loader(f, **kwargs)  # this should now work
            if test is not None:
                test[set_number] = self._append(test[set_number],
                                                new_tests[set_number])
                self.logger.debug("added this test - starting merging")
                self.logger.debug(new_tests[set_number].raw_data_files)
                self.logger.debug(new_tests[set_number].raw_data_files_length)
                for raw_data_file, file_size in zip(new_tests[set_number].raw_data_files,
                                                    new_tests[set_number].raw_data_files_length):
                    self.logger.debug(raw_data_file)

                    test[set_number].raw_data_files.append(raw_data_file)
                    test[set_number].raw_data_files_length.append(file_size)
                    counter += 1
                    if counter > 10:
                        self.logger.debug("ERROR? Too many files to merge")
                        raise ValueError("Too many files to merge - "
                                         "could be a p2-p3 zip thing")
            else:
                test = new_tests
        self.logger.debug("finished loading the raw-files")
        if test:
            self.datasets.append(test[set_number])
        else:
            self.logger.warning("No new datasets added!")
        self.number_of_datasets = len(self.datasets)
        self.status_datasets = self._validate_datasets()

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
        self.logger.debug("validating test")
        level = 0
        # simple validation for finding empty datasets - should be expanded to
        # find not-complete datasets, datasets with missing prms etc
        v = []
        if level == 0:
            for test in self.datasets:
                # check that it contains all the necessary headers (and add missing ones)
                # test = self._clean_up_normal_table(test)
                # check that the test is not empty
                v.append(self._is_not_empty_dataset(test))
        return v

    def check(self):
        """Returns False if no datasets exists or if one or more of the datasets
        are empty"""

        if len(self.status_datasets) == 0:
            return False
        if all(self.status_datasets):
            return True
        return False

    def _is_not_empty_dataset(self, dataset):
        if dataset is self._empty_dataset():
            return False
        else:
            return True

    def _clean_up_normal_table(self, test=None, dataset_number=None):
        # check that test contains all the necessary headers (and add missing
        # ones)
        raise NotImplementedError

    def _report_empty_dataset(self):
        self.logger.info("empty set")

    @staticmethod
    def _empty_dataset():
        return None

    def load(self, cellpy_file, parent_level="CellpyData"):
        """Loads a cellpy file.

        Args:
            cellpy_file (path, str): Full path to the cellpy file.
            parent_level (str, optional): Parent level

        """
        try:
            self.logger.info("loading hdf5")
            self.logger.info(cellpy_file)
            new_datasets = self._load_hdf5(cellpy_file, parent_level)
            self.logger.info("file loaded")
        except AttributeError:
            new_datasets = []
            self.logger.warning("This cellpy-file version is not supported by"
                                "current reader (try to update cellpy).")

        if new_datasets:
            for dataset in new_datasets:
                self.datasets.append(dataset)
        else:
            # raise LoadError
            self.logger.warning("Could not load")
            self.logger.warning(str(cellpy_file))

        self.number_of_datasets = len(self.datasets)
        self.status_datasets = self._validate_datasets()

    def _load_hdf5(self, filename, parent_level="CellpyData"):
        """Load a cellpy-file.

        Args:
            filename (str): Name of the cellpy file.
            parent_level (str) (optional): name of the parent level
                (defaults to "CellpyData")

        Returns:
            loaded datasets (DataSet-object)
        """

        if not os.path.isfile(filename):
            self.logger.info(f"file does not exist: {filename}")
            raise IOError
        self.logger.info("-from cellpy-file")
        store = pd.HDFStore(filename)

        # required_keys = ['dfdata', 'dfsummary', 'fidtable', 'info']
        required_keys = ['dfdata', 'dfsummary', 'info']
        required_keys = ["/" + parent_level + "/" + _ for _ in required_keys]

        for key in required_keys:
            if key not in store.keys():
                self.logger.info(f"This hdf-file is not good enough - "
                                 f"at least one key is missing: {key}")
                raise Exception(f"OH MY GOD! At least one crucial key"
                                f"is missing {key}!")

        self.logger.debug(f"Keys in current hdf5-file: {store.keys()}")
        data = DataSet()

        if parent_level != "CellpyData":
            self.logger.debug("Using non-default parent label for the "
                              "hdf-store: {}".format(parent_level))

        infotable = store.select(parent_level + "/info")  # remark! changed
        # spelling from lower letter to camel-case!

        try:
            data.cellpy_file_version = \
                self._extract_from_dict(infotable, "cellpy_file_version")
        except Exception:
            data.cellpy_file_version = 0

        # if data.cellpy_file_version < MINIMUM_CELLPY_FILE_VERSION:
        #     raise AttributeError

        if data.cellpy_file_version > CELLPY_FILE_VERSION:
            raise WrongFileVersion

        data.dfsummary = store.select(parent_level + "/dfsummary")
        data.dfdata = store.select(parent_level + "/dfdata")

        try:
            data.step_table = store.select(parent_level + "/step_table")
            data.step_table_made = True
        except Exception:
            data.step_table = None
            data.step_table_made = False
        try:
            fidtable = store.select(
                parent_level + "/fidtable")  # remark! changed spelling from
            # lower letter to camel-case!
            fidtable_selected = True
        except Exception:
            fidtable = []
            self.logger.warning("no fidtable - you should update your hdf5-file")
            fidtable_selected = False
        self.logger.debug("  h5")
        # this does not yet allow multiple sets

        newtests = []  # but this is ready when that time comes

        # The infotable stores "meta-data". The follwing statements loads the
        # content of infotable and updates div. DataSet attributes.
        # Maybe better use it as dict?

        data = self._load_infotable(data, infotable, filename)

        if fidtable_selected:
            data.raw_data_files, data.raw_data_files_length = \
                self._convert2fid_list(fidtable)
        else:
            data.raw_data_files = None
            data.raw_data_files_length = None
        newtests.append(data)
        store.close()
        # self.datasets.append(data)
        return newtests

    def _load_infotable(self, data, infotable, filename):
        # get attributes from infotable
        data.test_no = self._extract_from_dict(infotable, "test_no")
        data.mass = self._extract_from_dict(infotable, "mass")
        data.mass_given = True
        data.loaded_from = filename
        data.charge_steps = self._extract_from_dict(infotable, "charge_steps")
        data.channel_index = self._extract_from_dict(infotable, "channel_index")
        data.channel_number = \
            self._extract_from_dict(infotable, "channel_number")
        data.creator = self._extract_from_dict(infotable, "creator")
        data.schedule_file_name = \
            self._extract_from_dict(infotable, "schedule_file_name")
        data.start_datetime = \
            self._extract_from_dict(infotable, "start_datetime")
        data.test_ID = self._extract_from_dict(infotable, "test_ID")
        # hack to allow the renaming of tests to datasets
        try:
            data.name = self._extract_from_dict_hard(infotable, "name")
        except Exception:
            warnings.warn("OLD TYPE STYLE FOUND!")
            data.name = self._extract_from_dict(infotable, "test_name")

        try:
            data.step_table_made = \
                self._extract_from_dict(infotable, "step_table_made")
        except Exception:  # not needed?
            data.step_table_made = None
        return data

    @staticmethod
    def _extract_from_dict(t, x, default_value=None):
        try:
            value = t[x].values
            if value:
                value = value[0]
        except Exception:
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
        test = self.get_dataset(dataset_number)

        infotable = collections.OrderedDict()
        infotable["test_no"] = [test.test_no, ]
        infotable["mass"] = [test.mass, ]
        infotable["charge_steps"] = [test.charge_steps, ]
        infotable["discharge_steps"] = [test.discharge_steps, ]
        infotable["ir_steps"] = [test.ir_steps, ]
        infotable["ocv_steps"] = [test.ocv_steps, ]
        infotable["nom_cap"] = [test.nom_cap, ]
        infotable["loaded_from"] = [test.loaded_from, ]
        infotable["channel_index"] = [test.channel_index, ]
        infotable["channel_number"] = [test.channel_number, ]
        infotable["creator"] = [test.creator, ]
        infotable["schedule_file_name"] = [test.schedule_file_name, ]
        infotable["item_ID"] = [test.item_ID, ]
        infotable["test_ID"] = [test.test_ID, ]
        infotable["name"] = [test.name, ]
        infotable["start_datetime"] = [test.start_datetime, ]
        infotable["dfsummary_made"] = [test.dfsummary_made, ]
        infotable["step_table_made"] = [test.step_table_made, ]
        infotable["cellpy_file_version"] = [test.cellpy_file_version, ]

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

    def _convert2fid_list(self, tbl):
        self.logger.debug("_convert2fid_list")
        fids = []
        lengths = []
        counter = 0
        for item in tbl["raw_data_name"]:
            fid = FileID()
            fid.name = item
            fid.full_name = tbl["raw_data_full_name"][counter]
            fid.size = tbl["raw_data_size"][counter]
            fid.last_modified = tbl["raw_data_last_modified"][counter]
            fid.last_accessed = tbl["raw_data_last_accessed"][counter]
            fid.last_info_changed = tbl["raw_data_last_info_changed"][counter]
            fid.location = tbl["raw_data_location"][counter]
            length = tbl["raw_data_files_length"][counter]
            counter += 1
            fids.append(fid)
            lengths.append(length)
        return fids, lengths

    def merge(self, datasets=None, separate_datasets=False):
        """This function merges datasets into one set."""
        print("merging")
        if separate_datasets:
            print("not implemented yet")
        else:
            if datasets is None:
                datasets = list(range(len(self.datasets)))
            first = True
            for dataset_number in datasets:
                if first:
                    dataset = self.datasets[dataset_number]
                    first = False
                else:
                    dataset = self._append(dataset, self.datasets[dataset_number])
                    for raw_data_file, file_size in zip(self.datasets[dataset_number].raw_data_files,
                                                        self.datasets[dataset_number].raw_data_files_length):
                        dataset.raw_data_files.append(raw_data_file)
                        dataset.raw_data_files_length.append(file_size)
            self.datasets = [dataset]
            self.number_of_datasets = 1

    def _append(self, t1, t2, merge_summary=True, merge_step_table=True):
        test = t1
        # finding diff of time
        start_time_1 = t1.start_datetime
        start_time_2 = t2.start_datetime
        diff_time = xldate_as_datetime(start_time_2) - \
                    xldate_as_datetime(start_time_1)
        diff_time = diff_time.total_seconds()
        sort_key = self.headers_normal['datetime_txt']  # DateTime
        # mod data points for set 2
        data_point_header = self.headers_normal['data_point_txt']
        last_data_point = max(t1.dfdata[data_point_header])
        t2.dfdata[data_point_header] = t2.dfdata[data_point_header] + \
                                       last_data_point
        # mod cycle index for set 2
        cycle_index_header = self.headers_normal['cycle_index_txt']
        last_cycle = max(t1.dfdata[cycle_index_header])
        t2.dfdata[cycle_index_header] = t2.dfdata[cycle_index_header] + \
                                        last_cycle
        # mod test time for set 2
        test_time_header = self.headers_normal['test_time_txt']
        t2.dfdata[test_time_header] = t2.dfdata[test_time_header] + diff_time
        # merging
        dfdata2 = pd.concat([t1.dfdata, t2.dfdata], ignore_index=True)

        # checking if we already have made a summary file of these datasets
        # (to be used if merging summaries (but not properly implemented yet))
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
            except Exception:
                self_made_summary = False
                # print "have not made a summary myself"
            try:
                test_it = t2.dfsummary[cycle_index_header]
            except Exception:
                self_made_summary = False

            if self_made_summary:
                # mod cycle index for set 2
                last_cycle = max(t1.dfsummary[cycle_index_header])
                t2.dfsummary[cycle_index_header] = t2.dfsummary[cycle_index_header] \
                                                   + last_cycle
                # mod test time for set 2
                t2.dfsummary[test_time_header] = t2.dfsummary[test_time_header] \
                                                 + diff_time
                # to-do: mod all the cumsum stuff in the summary (best to make
                # summary after merging) merging
            else:
                t2.dfsummary[data_point_header] = t2.dfsummary[data_point_header] + last_data_point
            dfsummary2 = pd.concat([t1.dfsummary, t2.dfsummary], ignore_index=True)

            test.dfsummary = dfsummary2

        if merge_step_table:
            if step_table_made:
                cycle_index_header = self.headers_normal['cycle_index_txt']
                t2.step_table[self.headers_step_table["cycle"]] = t2.dfdata[
                                                                      self.headers_step_table["cycle"]] + last_cycle
                step_table2 = pd.concat([t1.step_table, t2.step_table],
                                        ignore_index=True)
                test.step_table = step_table2
            else:
                self.logger.debug("could not merge step tables (non-existing) -"
                                  "create them first!")

        # then the rest...
        test.no_cycles = max(dfdata2[cycle_index_header])
        test.dfdata = dfdata2
        test.merged = True
        # TODO (jepe) update merging for more variables
        #        self.test_no = None
        #        self.charge_steps = None
        #        self.discharge_steps = None
        #        self.ir_steps = None # dict
        #        self.ocv_steps = None # dict
        #        self.loaded_from = None # name of the .res file it is loaded from (can be list if merged)
        #        self.parent_filename = None # name of the .res file it is loaded from (basename)(can be list if merged)
        #        self.parent_filename = if listtype, for file in etc,,, os.path.basename(self.loaded_from)
        #        self.channel_index = None
        #        self.channel_number = None
        #        self.creator = None
        #        self.item_ID = None
        #        self.schedule_file_name = None
        #        self.test_ID = None
        #        self.name = None

        return test

    # --------------iterate-and-find-in-data-----------------------------------

    def _validate_dataset_number(self, n, check_for_empty=True):
        # Returns dataset_number (or None if empty)
        # Remark! _is_not_empty_dataset returns True or False

        if n is not None:
            v = n
        else:
            if self.selected_dataset_number is None:
                v = 0
            else:
                v = self.selected_dataset_number
        # check if test is empty
        if check_for_empty:
            not_empty = self._is_not_empty_dataset(self.datasets[v])
            if not_empty:
                return v
            else:
                return None
        else:
            return v

    def _validate_step_table(self, dataset_number=None, simple=False):
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return

        step_index_header = self.headers_normal['step_index_txt']
        self.logger.debug("*** validating step table")
        d = self.datasets[dataset_number].dfdata
        s = self.datasets[dataset_number].step_table

        if not self.datasets[dataset_number].step_table_made:
            return False

        no_cycles_dfdata = np.amax(d[self.headers_normal['cycle_index_txt']])
        headers_step_table = self.headers_step_table
        no_cycles_step_table = np.amax(s[headers_step_table["cycle"]])

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
                    no_steps_dfdata = len(np.unique(d.loc[d[self.headers_normal['cycle_index_txt']] == cycle_number,
                                                          self.headers_normal['step_index_txt']]))
                    no_steps_step_table = len(s.loc[s[headers_step_table["cycle"]] == cycle_number,
                                                    headers_step_table["step"]])
                    if no_steps_dfdata != no_steps_step_table:
                        validated = False
                        txt = "Error in step table (cycle: %i) d: %i, s:%i)" % (cycle_number,
                                                                                no_steps_dfdata,
                                                                                no_steps_step_table)

                        self.logger.debug(txt)
            return validated

    def print_step_table(self, dataset_number=None):
        """Print the step table."""
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        st = self.datasets[dataset_number].step_table
        print(st)

    def get_step_numbers(self, steptype='charge', allctypes=True, pdtype=False,
                         cycle_number=None, dataset_number=None):
        # TODO: include sub_steps here
        """Get the step numbers of selected type.

        Returns the selected step_numbers for the  elected type of step(s).

        Args:
            steptype (string): string identifying type of step.
            allctypes (bool): get all types of charge (or discharge).
            pdtype (bool): return results as pandas.DataFrame
            cycle_number (int): selected cycle, selects all if not set.
            dataset_number (int): test number (default first)
                (usually not used).

        Returns:
            List of step numbers corresponding to the selected steptype.
                Returns a pandas.DataFrame
            instead of a list if pdtype is set to True.

        Example:
            >>> my_charge_steps = CellpyData.get_step_numbers("charge", cycle_number = 3)
            >>> print my_charge_steps
            [5,8]

        """
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return

        # check if step_table is there
        if not self.datasets[dataset_number].step_table_made:
            self.logger.debug("step_table not made")

            if self.force_step_table_creation or self.force_all:
                self.logger.debug("creating step_table for")
                self.logger.debug(self.datasets[dataset_number].loaded_from)
                # print "CREAING STEP-TABLE"
                self.make_step_table(dataset_number=dataset_number)

            else:
                print("ERROR! Cannot use get_steps: create step_table first")
                print(" you could use find_step_numbers method instead")
                print(" (but I don't recommend it)")
                return None

        # check if steptype is valid
        steptype = steptype.lower()
        steptypes = []
        helper_step_types = ['ocv', 'charge_discharge']
        valid_step_type = True
        if steptype in self.list_of_step_types:
            steptypes.append(steptype)
        else:
            txt = "%s is not a valid core steptype" % steptype
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
        st = self.datasets[dataset_number].step_table
        # retrieving cycle numbers
        if cycle_number is None:
            # print "cycle number is none"
            cycle_numbers = self.get_cycle_numbers(dataset_number)
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

    # noinspection PyPep8Naming
    def _extract_step_values(self, f):
        # ['cycle', 'step',
        # 'I_avr', 'I_std', 'I_max', 'I_min', 'I_start', 'I_end', 'I_delta',
        #  'I_rate',
        # 'V_avr', 'V_std', 'V_max', 'V_min', 'V_start', 'V_end', 'V_delta',
        # 'V_rate',
        # 'type', 'info']

        # --- defining header txts ----
        current_hdtxt = self.headers_normal['current_txt']
        voltage_hdtxt = self.headers_normal['voltage_txt']
        steptime_hdtxt = self.headers_normal['step_time_txt']
        ir_hdtxt = self.headers_normal['internal_resistance_txt']
        ir_change_hdtxt = self.headers_step_table["internal_resistance_change"]
        charge_hdtxt = self.headers_normal['charge_capacity_txt']
        discharge_hdtxt = self.headers_normal['discharge_capacity_txt']

        # print f.head()

        # ---time----
        t_start = f.iloc[0][steptime_hdtxt]
        t_end = f.iloc[-1][steptime_hdtxt]
        t_delta = t_end - t_start  # OBS! will be used as denominator

        # ---current-
        I_avr = f[current_hdtxt].mean()
        I_std = f[current_hdtxt].std()
        # noinspection PyPep8Naming
        I_max = f[current_hdtxt].max()
        # noinspection PyPep8Naming
        I_min = f[current_hdtxt].min()
        # noinspection PyPep8Naming
        I_start = f.iloc[0][current_hdtxt]
        # noinspection PyPep8Naming
        I_end = f.iloc[-1][current_hdtxt]

        # I_delta = I_end-I_start
        # noinspection PyPep8Naming
        I_delta = self._percentage_change(I_start, I_end, default_zero=True)
        # noinspection PyPep8Naming
        I_rate = self._fractional_change(I_delta, t_delta)

        # ---voltage--
        # noinspection PyPep8Naming
        V_avr = f[voltage_hdtxt].mean()
        # noinspection PyPep8Naming
        V_std = f[voltage_hdtxt].std()
        # noinspection PyPep8Naming
        V_max = f[voltage_hdtxt].max()
        # noinspection PyPep8Naming
        V_min = f[voltage_hdtxt].min()
        # noinspection PyPep8Naming
        V_start = f.iloc[0][voltage_hdtxt]
        # noinspection PyPep8Naming
        V_end = f.iloc[-1][voltage_hdtxt]

        # V_delta = V_end-V_start
        # noinspection PyPep8Naming
        V_delta = self._percentage_change(V_start, V_end, default_zero=True)
        # noinspection PyPep8Naming
        V_rate = self._fractional_change(V_delta, t_delta)

        # ---charge---
        # noinspection PyPep8Naming
        C_avr = f[charge_hdtxt].mean()
        # noinspection PyPep8Naming
        C_std = f[charge_hdtxt].std()
        # noinspection PyPep8Naming
        C_max = f[charge_hdtxt].max()
        # noinspection PyPep8Naming
        C_min = f[charge_hdtxt].min()
        # noinspection PyPep8Naming
        C_start = f.iloc[0][charge_hdtxt]
        # noinspection PyPep8Naming
        C_end = f.iloc[-1][charge_hdtxt]

        # noinspection PyPep8Naming
        C_delta = self._percentage_change(C_start, C_end, default_zero=True)
        # noinspection PyPep8Naming
        C_rate = self._fractional_change(C_delta, t_delta)

        # ---discharge---
        # noinspection PyPep8Naming
        D_avr = f[discharge_hdtxt].mean()
        # noinspection PyPep8Naming
        D_std = f[discharge_hdtxt].std()
        # noinspection PyPep8Naming
        D_max = f[discharge_hdtxt].max()
        # noinspection PyPep8Naming
        D_min = f[discharge_hdtxt].min()
        # noinspection PyPep8Naming
        D_start = f.iloc[0][discharge_hdtxt]
        # noinspection PyPep8Naming
        D_end = f.iloc[-1][discharge_hdtxt]

        # noinspection PyPep8Naming
        D_delta = self._percentage_change(D_start, D_end, default_zero=True)
        # noinspection PyPep8Naming
        D_rate = self._fractional_change(D_delta, t_delta)

        # ---internal resistance ----
        # noinspection PyPep8Naming
        IR = f.iloc[0][ir_hdtxt]
        # noinspection PyPep8Naming
        IR_pct_change = f.iloc[0][ir_change_hdtxt]

        # ---output--
        out = [I_avr, I_std, I_max, I_min, I_start, I_end, I_delta, I_rate,
               V_avr, V_std, V_max, V_min, V_start, V_end, V_delta, V_rate,
               C_avr, C_std, C_max, C_min, C_start, C_end, C_delta, C_rate,
               D_avr, D_std, D_max, D_min, D_start, D_end, D_delta, D_rate,
               IR, IR_pct_change, ]
        return out

    def load_step_specifications(self, file_name, short=False,
                                 dataset_number=None):
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
            self.logger.info("step col is missing")
            raise IOError

        if "type" not in step_specs.columns:
            self.logger.info("type col is missing")
            raise IOError

        if not short and "cycle" not in step_specs.columns:
            self.logger.info("cycle col is missing")
            raise IOError

        self.make_step_table(custom_step_definition=True,
                             step_specifications=step_specs,
                             short=short)

    def make_step_table(self, custom_step_definition=False,
                        step_specifications=None,
                        short=False,
                        dataset_number=None):

        """ Create a table (v.3) that contains summary information for each step.

        This function creates a table containing information about the
        different steps for each cycle and, based on that, decides what type of
        step it is (e.g. charge) for each cycle.

        The format of the step_table is:

            index - cycleno - stepno -
            Current info (average, stdev, max, min, start, end, delta, rate) -
            Voltage info (average,  stdev, max, min, start, end, delta, rate) -
            Type (from pre-defined list) -
            Info

        Header names (pr. 03.03.2016):

            'cycle', 'step',
            'I_avr', 'I_std', 'I_max', 'I_min',
                 'I_start', 'I_end', 'I_delta', 'I_rate',
            'V_avr'...,
            'C_avr'...,
            'D_avr'...,
            'IR','IR_pct_change',
            'type', 'info'

        8.12.2016: added sub_step, sub_type, and pre_time, pre_point
        Remark! x_delta is given in percentage.
        """
        # TODO: need to implement newly added columns
        # (strategy: work with empty cols first)

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return

        cycle_index_header = self.headers_normal['cycle_index_txt']
        step_index_header = self.headers_normal['step_index_txt']
        internal_resistance_txt = self.headers_normal['internal_resistance_txt']

        headers_step_table = self.headers_step_table

        step_table_txt_cycle = headers_step_table["cycle"]
        step_table_txt_step = headers_step_table["step"]
        step_table_txt_sub_step = headers_step_table["sub_step"]

        step_table_txt_type = headers_step_table["type"]
        step_table_txt_sub_type = headers_step_table["sub_type"]

        step_table_txt_info = headers_step_table["info"]
        step_table_txt_ir = headers_step_table["internal_resistance"]
        step_table_txt_ir_change = \
            headers_step_table["internal_resistance_change"]

        # -------------create an "empty" df -----------------------------------

        # --- defining column names ---
        # (should probably migrate this to own function and add to self)
        columns = [step_table_txt_cycle, step_table_txt_step]

        columns_end = [headers_step_table["post_mean"],
                       headers_step_table["post_std"],
                       headers_step_table["post_max"],
                       headers_step_table["post_min"],
                       headers_step_table["post_start"],
                       headers_step_table["post_end"],
                       headers_step_table["post_delta"],
                       headers_step_table["post_rate"],
                       ]

        columns_end_limited = [headers_step_table["post_start"],
                               headers_step_table["post_end"],
                               headers_step_table["post_delta"], ]

        # noinspection PyPep8Naming
        columns_I = [headers_step_table["pre_current"] + x for x in columns_end]
        # noinspection PyPep8Naming
        columns_V = [headers_step_table["pre_voltage"] + x for x in columns_end]
        columns_charge = [headers_step_table["pre_charge"] +
                          x for x in columns_end]
        columns_discharge = [headers_step_table["pre_discharge"] +
                             x for x in columns_end]

        columns_point = [headers_step_table["pre_point"] +
                         x for x in columns_end_limited]
        columns_time = [headers_step_table["pre_time"] +
                        x for x in columns_end_limited]

        columns.extend(columns_I)
        columns.extend(columns_V)
        columns.extend(columns_charge)
        columns.extend(columns_discharge)

        columns.append(step_table_txt_ir)
        columns.append(step_table_txt_ir_change)

        columns.append(step_table_txt_type)
        columns.append(step_table_txt_info)

        # CONTINUE FROM HERE:
        # columns.extend(columns_point)
        # columns.extend(columns_time)
        # columns.append(step_table_txt_sub_step)
        # columns.append(step_table_txt_sub_type)

        # --- adding pct change col(s)-----
        df = self.datasets[dataset_number].dfdata
        df[step_table_txt_ir_change] = df[internal_resistance_txt].pct_change()

        # --- finding size ------
        df = self.datasets[dataset_number].dfdata
        number_of_rows = df.groupby([cycle_index_header,
                                     step_index_header]).size().shape[0]
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

        average_current_txt = headers_step_table["pre_current"] + \
                              headers_step_table["post_mean"]
        min_current_txt = headers_step_table["pre_current"] + \
                          headers_step_table["post_min"]
        max_current_txt = headers_step_table["pre_current"] + \
                          headers_step_table["post_max"]
        delta_current_txt = headers_step_table["pre_current"] + \
                            headers_step_table["post_delta"]
        delta_voltage_txt = headers_step_table["pre_voltage"] + \
                            headers_step_table["post_delta"]
        delta_charge_txt = headers_step_table["pre_charge"] + \
                           headers_step_table["post_delta"]
        delta_discharge_txt = headers_step_table["pre_discharge"] + \
                              headers_step_table["post_delta"]

        # max_average_current = df_steps[average_current_txt].max()
        #        print "max average current:"
        #        print max_average_current
        #

        # - setting limits
        current_limit_value_hard = self.raw_limits["current_hard"]
        current_limit_value_soft = self.raw_limits["current_soft"]
        stable_current_limit_hard = self.raw_limits["stable_current_hard"]
        stable_current_limit_soft = self.raw_limits["stable_current_soft"]
        stable_voltage_limit_hard = self.raw_limits["stable_voltage_hard"]
        stable_voltage_limit_soft = self.raw_limits["stable_voltage_soft"]
        stable_charge_limit_hard = self.raw_limits["stable_charge_hard"]
        stable_charge_limit_soft = self.raw_limits["stable_charge_soft"]
        ir_change_limit = self.raw_limits["ir_change"]

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

        mask_voltage_down = df_steps[delta_voltage_txt] < \
                            -stable_voltage_limit_hard
        mask_voltage_up = df_steps[delta_voltage_txt] > \
                          stable_voltage_limit_hard
        mask_voltage_stable = df_steps[delta_voltage_txt].abs() < \
                              stable_voltage_limit_hard

        mask_current_down = df_steps[delta_current_txt] < \
                            -stable_current_limit_soft
        mask_current_up = df_steps[delta_current_txt] > \
                          stable_current_limit_soft
        mask_current_negative = df_steps[average_current_txt] < \
                                -current_limit_value_hard
        mask_current_positive = df_steps[average_current_txt] > \
                                current_limit_value_hard
        mask_galvanostatic = df_steps[delta_current_txt].abs() < \
                             stable_current_limit_soft

        mask_charge_changed = df_steps[delta_charge_txt].abs() > \
                              stable_charge_limit_hard
        mask_discharge_changed = df_steps[delta_discharge_txt].abs() > \
                                 stable_charge_limit_hard

        mask_ir_changed = df_steps[step_table_txt_ir_change].abs() > \
                          ir_change_limit

        mask_no_change = (df_steps[delta_voltage_txt] == 0) & \
                         (df_steps[delta_current_txt] == 0) & \
                         (df_steps[delta_charge_txt] == 0) & \
                         (df_steps[delta_discharge_txt] == 0)

        if custom_step_definition:
            self.logger.debug("parsing custom step definition")
            if not short:
                self.logger.debug("using long format (cycle,step)")
                for row in step_specifications.itertuples():
                    self.logger.debug(f"cycle: {row.cycle} step: {row.step}"
                                      f" type: {row.type}")
                    df_steps.loc[(df_steps[step_table_txt_step] == row.step) &
                                 (df_steps[step_table_txt_cycle] == row.cycle),
                                 "type"] = row.type
                    df_steps.loc[(df_steps[step_table_txt_step] == row.step) &
                                 (df_steps[step_table_txt_cycle] == row.cycle),
                                 "info"] = row.info
            else:
                self.logger.debug("using short format (step)")
                for row in step_specifications.itertuples():
                    self.logger.debug(f"step: {row.step} "
                                      f"type: {row.type}"
                                      f"info: {row.info}")
                    df_steps.loc[df_steps[step_table_txt_step] == row.step,
                                 "type"] = row.type
                    df_steps.loc[df_steps[step_table_txt_step] == row.step,
                                 "info"] = row.info

        else:
            # --- ocv -------
            df_steps.loc[mask_no_current_hard & mask_voltage_up,
                         step_table_txt_type] = 'ocvrlx_up'
            df_steps.loc[mask_no_current_hard & mask_voltage_down,
                         step_table_txt_type] = 'ocvrlx_down'

            # --- charge and discharge ----
            # df_steps.loc[mask_galvanostatic & mask_current_negative,
            # step_table_txt_type] = 'discharge'
            df_steps.loc[mask_discharge_changed & mask_current_negative,
                         step_table_txt_type] = 'discharge'
            # df_steps.loc[mask_galvanostatic & mask_current_positive,
            # step_table_txt_type] = 'charge'
            df_steps.loc[mask_charge_changed & mask_current_positive,
                         step_table_txt_type] = 'charge'

            df_steps.loc[
                mask_voltage_stable & mask_current_negative & mask_current_down,
                step_table_txt_type] = 'cv_discharge'
            df_steps.loc[mask_voltage_stable & mask_current_positive &
                         mask_current_down, step_table_txt_type] = 'cv_charge'

            # --- internal resistance ----
            df_steps.loc[mask_no_change, step_table_txt_type] = 'ir'
            # assumes that IR is stored in just one row

            # --- CV steps ----

            # "voltametry_charge"
            # mask_charge_changed
            # mask_voltage_up
            # (could also include abs-delta-cumsum current)

            # "voltametry_discharge"
            # mask_discharge_changed
            # mask_voltage_down

        # --- finally ------

        self.datasets[dataset_number].step_table = df_steps
        self.datasets[dataset_number].step_table_made = True

    @staticmethod
    def _percentage_change(x0, x1, default_zero=True):
        # calculates the change from x0 to x1 in percentage
        # i.e. returns (x1-x0)*100 / x0
        if x0 == 0.0:
            # self.logger.debug("DBZ(_percentage)")
            # this will not print anything, set level to 1 to print
            difference = x1 - x0
            if difference != 0.0 and default_zero:
                difference = 0.0
        else:
            difference = (x1 - x0) * 100 / x0

        return difference

    @staticmethod
    def _fractional_change(x0, x1, default_zero=False):
        # calculates the fraction of x0 and x1
        # i.e. returns x1 / x0
        if x1 == 0.0:
            # self.logger.debug("DBZ(_fractional)")
            # this will not print anything, set level to 1 to print
            if default_zero:
                difference = 0.0
            else:
                difference = np.nan
        else:
            difference = x0 / x1
        return difference

    def select_steps(self, step_dict, append_df=False, dataset_number=None):
        """Select steps (not documented yet)."""
        raise DeprecatedFeature

    def _select_step(self, cycle, step, dataset_number=None):
        # TODO: insert sub_step here
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        test = self.datasets[dataset_number]
        # test.dfdata

        # check if columns exist
        c_txt = self.headers_normal['cycle_index_txt']
        s_txt = self.headers_normal['step_index_txt']
        y_txt = self.headers_normal['voltage_txt']
        x_txt = self.headers_normal['discharge_capacity_txt']  # jepe fix

        # no_cycles=np.amax(test.dfdata[c_txt])
        # print d.columns

        if not any(test.dfdata.columns == c_txt):
            print("error - cannot find %s" % c_txt)
            sys.exit(-1)
        if not any(test.dfdata.columns == s_txt):
            print("error - cannot find %s" % s_txt)
            sys.exit(-1)

        v = test.dfdata[(test.dfdata[c_txt] == cycle) & (test.dfdata[s_txt] == step)]
        if self.is_empty(v):
            return None
        else:
            return v

    def populate_step_dict(self, step, dataset_number=None):
        """Returns a dict with cycle numbers as keys
        and corresponding steps (list) as values."""
        raise DeprecatedFeature

    def _export_cycles(self, dataset_number, setname=None,
                       sep=None, outname=None, shifted=False, method=None,
                       shift=0.0):
        # export voltage - capacity curves to .csv file

        self.logger.debug("exporting cycles")
        lastname = "_cycles.csv"
        if sep is None:
            sep = self.sep
        if outname is None:
            outname = setname + lastname

        list_of_cycles = self.get_cycle_numbers(dataset_number=dataset_number)
        number_of_cycles = len(list_of_cycles)
        txt = "you have %i cycles" % number_of_cycles
        self.logger.debug(txt)

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
                c, v = self.get_cap(cycle, dataset_number=dataset_number,
                                    method=method,
                                    shift=shift,
                                    )
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
                txt = "extracted cycle %i" % cycle
                self.logger.info(txt)
            except ImportError as e:
                txt = "could not extract cycle %i" % cycle
                self.logger.info(txt)
                self.logger.debug(e)

        # Saving cycles in one .csv file (x,y,x,y,x,y...)
        # print "saving the file with delimiter '%s' " % (sep)
        self.logger.debug("writing cycles to file")
        with open(outname, "w") as f:
            writer = csv.writer(f, delimiter=sep)
            writer.writerows(itertools.zip_longest(*out_data))
            # star (or asterix) means transpose (writing cols instead of rows)
        txt = outname
        txt += " exported."
        self.logger.info(txt)

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
        except Exception as e:
            txt += " Could not save it!"
            self.logger.debug(e)
        self.logger.info(txt)

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
        except Exception as e:
            txt += " Could not save it!"
            self.logger.debug(e)
        self.logger.info(txt)

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
        except Exception as e:
            txt += " Could not save it!"
            self.logger.debug(e)
        self.logger.info(txt)

    def to_csv(self, datadir=None, sep=None, cycles=False, raw=True,
               summary=True, shifted=False,
               method=None, shift=0.0):
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

        Returns: Nothing

        """

        if sep is None:
            sep = self.sep
        txt = "\n\n"
        txt += "---------------------------------------------------------------"
        txt += "Saving data"
        txt += "---------------------------------------------------------------"
        self.logger.info(txt)

        dataset_number = -1
        for data in self.datasets:
            dataset_number += 1
            if not self._is_not_empty_dataset(data):
                print("to_csv -")
                print("empty test [%i]" % dataset_number)
                print("not saved!")
            else:
                if isinstance(data.loaded_from, (list, tuple)):
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
                    firstname = os.path.join(datadir,
                                             os.path.basename(firstname))

                if raw:
                    outname_normal = firstname + "_normal.csv"
                    self._export_normal(data, outname=outname_normal, sep=sep)
                    if data.step_table_made is True:
                        outname_steps = firstname + "_steps.csv"
                        self._export_steptable(data, outname=outname_steps,
                                               sep=sep)
                    else:
                        self.logger.debug("step_table_made is not True")

                if summary:
                    outname_stats = firstname + "_stats.csv"
                    self._export_stats(data, outname=outname_stats, sep=sep)

                if cycles:
                    outname_cycles = firstname + "_cycles.csv"
                    self._export_cycles(outname=outname_cycles,
                                        dataset_number=dataset_number,
                                        sep=sep, shifted=shifted,
                                        method=method, shift=shift)

    def save(self, filename, dataset_number=None, force=False, overwrite=True,
             extension="h5"):
        """Save the data structure to cellpy-format.

        Args:
            filename: (str) the name you want to give the file
            dataset_number: (int) if you have several datasets, chose the one
                you want (probably leave this untouched)
            force: (bool) save a file even if the summary is not made yet
                (not recommended)
            overwrite: (bool) save the new version of the file even if old one
                exists.
            extension: (str) filename extension.

        Returns: Nothing at all.
        """

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            print("Saving test failed!")
            self._report_empty_dataset()
            return

        test = self.get_dataset(dataset_number)
        dfsummary_made = test.dfsummary_made  #

        if not dfsummary_made and not force:
            print("You should not save datasets without making a "
                  "summary first!")
            print("If you really want to do it, use save with force=True")
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
                        self.logger.debug("save: creating step table")
                        self.make_step_table(dataset_number=dataset_number)
                self.logger.debug("trying to make infotable")
                # modify this:
                infotbl, fidtbl = \
                    self._create_infotable(dataset_number=dataset_number)
                self.logger.debug("trying to save to hdf5")
                txt = "\nHDF5 file: %s" % outfile_all
                self.logger.debug(txt)
                store = pd.HDFStore(outfile_all)
                self.logger.debug("trying to put dfdata")
                # jepe: fix (get name from class):
                store.put("CellpyData/dfdata", test.dfdata)
                self.logger.debug("trying to put dfsummary")
                store.put("CellpyData/dfsummary", test.dfsummary)

                self.logger.info("trying to put step_table")
                if not test.step_table_made:
                    self.logger.debug(" no step_table made")
                else:
                    store.put("CellpyData/step_table", test.step_table)

                self.logger.debug("trying to put infotbl")
                store.put("CellpyData/info", infotbl)
                self.logger.debug("trying to put fidtable")
                store.put("CellpyData/fidtable", fidtbl)
                store.close()
                # del store
            else:
                print("save (hdf5): file exist - did not save", end=' ')
                print(outfile_all)

    # --------------helper-functions--------------------------------------------

    def _cap_mod_summary(self, dfsummary, capacity_modifier="reset"):
        # modifies the summary table
        discharge_title = self.headers_normal['discharge_capacity_txt']
        charge_title = self.headers_normal['charge_capacity_txt']
        chargecap = 0.0
        dischargecap = 0.0
        # TODO use pd.loc[row,column] e.g. pd.loc[:,"charge_cap"] for col or
        # pd.loc[(pd.["step"]==1),"x"]
        if capacity_modifier == "reset":

            for index, row in dfsummary.iterrows():
                dischargecap_2 = row[discharge_title]
                dfsummary[discharge_title][index] = dischargecap_2 - \
                                                    dischargecap
                dischargecap = dischargecap_2
                chargecap_2 = row[charge_title]
                dfsummary[charge_title][index] = chargecap_2 - chargecap
                chargecap = chargecap_2
        else:
            raise NotImplementedError

        return dfsummary

    def _cap_mod_normal(self, dataset_number=None,
                        capacity_modifier="reset",
                        allctypes=True):
        # modifies the normal table
        self.logger.debug("Not properly checked yet! Use with caution!")
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        cycle_index_header = self.headers_normal['cycle_index_txt']
        step_index_header = self.headers_normal['step_index_txt']
        discharge_index_header = self.headers_normal['discharge_capacity_txt']
        discharge_energy_index_header = \
            self.headers_normal['discharge_energy_txt']
        charge_index_header = self.headers_normal['charge_capacity_txt']
        charge_energy_index_header = self.headers_normal['charge_energy_txt']

        dfdata = self.datasets[dataset_number].dfdata

        chargecap = 0.0
        dischargecap = 0.0

        if capacity_modifier == "reset":
            # discharge cycles
            no_cycles = np.amax(dfdata[cycle_index_header])
            for j in range(1, no_cycles + 1):
                cap_type = "discharge"
                e_header = discharge_energy_index_header
                cap_header = discharge_index_header
                discharge_cycles = self.get_step_numbers(steptype=cap_type,
                                                         allctypes=allctypes,
                                                         cycle_number=j,
                                                         dataset_number=dataset_number)

                steps = discharge_cycles[j]
                txt = "Cycle  %i (discharge):  " % j
                self.logger.debug(txt)
                # TODO use pd.loc[row,column] e.g. pd.loc[:,"charge_cap"]
                # for col or pd.loc[(pd.["step"]==1),"x"]
                selection = (dfdata[cycle_index_header] == j) & \
                            (dfdata[step_index_header].isin(steps))
                c0 = dfdata[selection].iloc[0][cap_header]
                e0 = dfdata[selection].iloc[0][e_header]
                dfdata[cap_header][selection] = (dfdata[selection][cap_header]
                                                 - c0)
                dfdata[e_header][selection] = (dfdata[selection][e_header] - e0)

                cap_type = "charge"
                e_header = charge_energy_index_header
                cap_header = charge_index_header
                charge_cycles = self.get_step_numbers(steptype=cap_type,
                                                      allctypes=allctypes,
                                                      cycle_number=j,
                                                      dataset_number=dataset_number)
                steps = charge_cycles[j]
                txt = "Cycle  %i (charge):  " % j
                self.logger.debug(txt)

                selection = (dfdata[cycle_index_header] == j) & \
                            (dfdata[step_index_header].isin(steps))

                if any(selection):
                    c0 = dfdata[selection].iloc[0][cap_header]
                    e0 = dfdata[selection].iloc[0][e_header]
                    dfdata[cap_header][selection] = (dfdata[selection][cap_header]
                                                     - c0)
                    dfdata[e_header][selection] = (dfdata[selection][e_header] - e0)

    def get_number_of_tests(self):
        return self.number_of_datasets

    def get_mass(self, set_number=None):
        set_number = self._validate_dataset_number(set_number)
        if set_number is None:
            self._report_empty_dataset()
            return
        if not self.datasets[set_number].mass_given:
            print("no mass")
        return self.datasets[set_number].mass

    def get_dataset(self, n=0):
        return self.datasets[n]

    def sget_voltage(self, cycle, step, set_number=None):
        """Returns voltage for cycle, step.

        Convinience function; same as issuing
           dfdata[(dfdata[cycle_index_header] == cycle) &
                 (dfdata[step_index_header] == step)][voltage_header]

        Args:
            cycle: cycle number
            step: step number
            set_number: the dataset number (automatic selection if None)

        Returns:
            pandas.Series or None if empty
        """

        set_number = self._validate_dataset_number(set_number)
        if set_number is None:
            self._report_empty_dataset()
            return
        cycle_index_header = self.headers_normal['cycle_index_txt']
        voltage_header = self.headers_normal['voltage_txt']
        step_index_header = self.headers_normal['step_index_txt']
        test = self.datasets[set_number].dfdata
        c = test[(test[cycle_index_header] == cycle) &
                 (test[step_index_header] == step)]
        if not self.is_empty(c):
            v = c[voltage_header]
            return v
        else:
            return None

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
        cycle_index_header = self.headers_normal['cycle_index_txt']
        voltage_header = self.headers_normal['voltage_txt']
        # step_index_header  = self.headers_normal['step_index_txt']

        test = self.datasets[dataset_number].dfdata
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
        cycle_index_header = self.headers_normal['cycle_index_txt']
        current_header = self.headers_normal['current_txt']
        # step_index_header  = self.headers_normal['step_index_txt']

        test = self.datasets[dataset_number].dfdata
        if cycle:
            c = test[(test[cycle_index_header] == cycle)]
            if not self.is_empty(c):
                v = c[current_header]
                return v
        else:
            if not full:
                self.logger.debug("getting current-curves for all cycles")
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

    def sget_steptime(self, cycle, step, dataset_number=None):
        """Returns step time for cycle, step.

        Convinience function; same as issuing
           dfdata[(dfdata[cycle_index_header] == cycle) &
                 (dfdata[step_index_header] == step)][step_time_header]

        Args:
            cycle: cycle number
            step: step number
            dataset_number: the dataset number (automatic selection if None)

        Returns:
            pandas.Series or None if empty
        """

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        cycle_index_header = self.headers_normal['cycle_index_txt']
        step_time_header = self.headers_normal['step_time_txt']
        step_index_header = self.headers_normal['step_index_txt']
        test = self.datasets[dataset_number].dfdata
        c = test[(test[cycle_index_header] == cycle) &
                 (test[step_index_header] == step)]
        if not self.is_empty(c):
            t = c[step_time_header]
            return t
        else:
            return None

    def sget_timestamp(self, cycle, step, dataset_number=None):
        """Returns timestamp for cycle, step.

        Convinience function; same as issuing
           dfdata[(dfdata[cycle_index_header] == cycle) &
                 (dfdata[step_index_header] == step)][timestamp_header]

        Args:
            cycle: cycle number
            step: step number
            dataset_number: the dataset number (automatic selection if None)

        Returns:
            pandas.Series
        """

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        cycle_index_header = self.headers_normal['cycle_index_txt']
        timestamp_header = self.headers_normal['test_time_txt']
        step_index_header = self.headers_normal['step_index_txt']
        test = self.datasets[dataset_number].dfdata
        c = test[(test[cycle_index_header] == cycle) &
                 (test[step_index_header] == step)]
        if not self.is_empty(c):
            t = c[timestamp_header]
            return t
        else:
            return pd.Series()

    def get_timestamp(self, cycle=None, dataset_number=None,
                      in_minutes=False, full=True):
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
        cycle_index_header = self.headers_normal['cycle_index_txt']
        timestamp_header = self.headers_normal['test_time_txt']

        v = pd.Series()
        test = self.datasets[dataset_number].dfdata
        if cycle:
            c = test[(test[cycle_index_header] == cycle)]
            if not self.is_empty(c):
                v = c[timestamp_header]

        else:
            if not full:
                self.logger.debug("getting timestapm for all cycles")
                v = []
                no_cycles = np.amax(test[cycle_index_header])
                for j in range(1, no_cycles + 1):
                    txt = "Cycle  %i:  " % j
                    self.logger.debug(txt)
                    c = test[(test[cycle_index_header] == j)]
                    v.append(c[timestamp_header])
            else:
                self.logger.debug("returning full timestamp col")
                v = test[timestamp_header]
                if in_minutes and v is not None:
                    v /= 60.0
        if in_minutes and v is not None:
            v /= 60.0
        return v

    def get_dcap(self, cycle=None, dataset_number=None):
        """Returns discharge_capacity (in mAh/g), and voltage."""

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        dc, v = self._get_cap(cycle, dataset_number, "discharge")
        return dc, v

    def get_ccap(self, cycle=None, dataset_number=None):
        """Returns charge_capacity (in mAh/g), and voltage."""

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        cc, v = self._get_cap(cycle, dataset_number, "charge")
        return cc, v

    def get_cap(self, cycle=None, dataset_number=None,
                method="back-and-forth",
                shift=0.0, ):
        """Gets the capacity for the run.
        For cycle=None: not implemented yet, cycle set to 1.

        Args:
            cycle (int): cycle number.
            method (string): how the curves are given
                "back-and-forth" - standard back and forth; discharge
                    (or charge) reversed from where charge (or discharge) ends.
                "forth" - discharge (or charge) continues along x-axis.
                "forth-and-forth" - discharge (or charge) also starts at 0
                    (or shift if not shift=0.0)
            shift: start-value for charge (or discharge) (typically used when
                plotting shifted-capacity).
            dataset_number (int): test number (default first)
                (usually not used).

        Returns: capacity (mAh/g), voltage
        """
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return

        # if cycle is not given, then this function should
        # iterate through cycles
        if not cycle:
            cycle = self.get_cycle_numbers()

        if not isinstance(cycle, (collections.Iterable,)):
            cycle = [cycle]

        method = method.lower()
        if method not in ["back-and-forth", "forth", "forth-and-forth"]:
            warnings.warn(f"method '{method}' is not a valid option "
                          f"- setting to 'back-and-forth'")
            method = "back-and-forth"

        capacity = None
        voltage = None

        initial = True
        for current_cycle in cycle:
            self.logger.debug(f"processing cycle {current_cycle}")

            cc, cv = self.get_ccap(current_cycle, dataset_number)
            dc, dv = self.get_dcap(current_cycle, dataset_number)

            if initial:
                self.logger.debug("(initial cycle)")
                prev_end = shift
                initial = False

            if self.cycle_mode.lower() == "anode":
                _first_step_c = dc
                _first_step_v = dv
                _last_step_c = cc
                _last_step_v = cv
            else:
                _first_step_c = cc
                _first_step_v = cv
                _last_step_c = dc
                _last_step_v = dv

            if method == "back-and-forth":
                _last = np.amax(_first_step_c)
                # should change amax to last point
                if _last_step_c is not None:
                    _last_step_c = _last - _last_step_c + prev_end
                else:
                    self.logger.debug("no last charge step found")
                if _first_step_c is not None:
                    _first = _first_step_c.iat[0]
                    _first_step_c += prev_end
                    _new_first = _first_step_c.iat[0]
                else:
                    self.logger.debug("no first charge step found")
                self.logger.debug(f"current shifts used: prev_end = {prev_end}")
                self.logger.debug(f"shifting start from {_first} to "
                                  f"{_new_first}")

                prev_end = np.amin(_last_step_c)
                # should change amin to last point

            elif method == "forth":
                _last = np.amax(_first_step_c)
                # should change amax to last point
                if _last_step_c is not None:
                    _last_step_c += _last + prev_end
                else:
                    self.logger.debug("no last charge step found")
                if _first_step_c is not None:
                    _first_step_c += prev_end
                else:
                    self.logger.debug("no first charge step found")

                prev_end = np.amax(_last_step_c)
                # should change amin to last point

            elif method == "forth-and-forth":
                if _last_step_c is not None:
                    _last_step_c += shift
                else:
                    self.logger.debug("no last charge step found")
                if _first_step_c is not None:
                    _first_step_c += shift
                else:
                    self.logger.debug("no first charge step found")

            c = pd.concat([_first_step_c, _last_step_c], axis=0)
            v = pd.concat([_first_step_v, _last_step_v], axis=0)

            capacity = pd.concat([capacity, c], axis=0)
            voltage = pd.concat([voltage, v], axis=0)

        return capacity, voltage

    def _get_cap(self, cycle=None, dataset_number=None, cap_type="charge"):
        # used when extracting capacities (get_ccap, get_dcap)
        # TODO: does not allow for constant voltage yet?
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        test = self.datasets[dataset_number]
        mass = self.get_mass(dataset_number)
        if cap_type == "charge_capacity":
            cap_type = "charge"
        elif cap_type == "discharge_capacity":
            cap_type = "discharge"
        # cycles = self.find_step_numbers(step_type =cap_type,
        # dataset_number = dataset_number)
        self.logger.debug("in _get_cap: finding step numbers")
        if cycle:
            self.logger.debug("for cycle")
            self.logger.debug(cycle)
        cycles = self.get_step_numbers(steptype=cap_type, allctypes=False,
                                       cycle_number=cycle,
                                       dataset_number=dataset_number)

        self.logger.debug(cycles)
        c = pd.Series()
        v = pd.Series()
        if cap_type == "charge":
            column_txt = self.headers_normal['charge_capacity_txt']
        else:
            column_txt = self.headers_normal['discharge_capacity_txt']
        if cycle:
            step = cycles[cycle][0]
            selected_step = self._select_step(cycle, step, dataset_number)
            if not self.is_empty(selected_step):
                v = selected_step[self.headers_normal['voltage_txt']]
                c = selected_step[column_txt] * 1000000 / mass
            else:
                self.logger.debug("could not find any steps for this cycle")
                txt = "(c:%i s:%i type:%s)" % (cycle, step, cap_type)
        else:
            # get all the discharge cycles
            # this is a dataframe filtered on step and cycle
            raise NotImplementedError
            # TODO: fix this now!
            # d = self.select_steps(cycles, append_df=True)
            # v = d[self.headers_normal['voltage_txt']]
            # c = d[column_txt] * 1000000 / mass
        return c, v

    def get_ocv(self, cycle_number=None, ocv_type='ocv', dataset_number=None):
        """Find ocv data in DataSet (voltage vs time).

        Args:
            cycle_number (int): find for all cycles if None.
            ocv_type ("ocv", "ocvrlx_up", "ocvrlx_down"):
                     ocv - get up and down (default)
                     ocvrlx_up - get up
                     ocvrlx_down - get down
            dataset_number (int): test number (default first)
                (usually not used).
        Returns:
                if cycle_number is not None
                    ocv or [ocv_up, ocv_down]
                    ocv (and ocv_up and ocv_down) are list
                    containg [time,voltage] (that are Series)

                if cycle_number is None
                    [ocv1,ocv2,...ocvN,...] N = cycle
                    ocvN = pandas DataFrame containing the columns
                    cycle inded, step time, step index, data point, datetime,
                        voltage
                    (TODO: check if copy or reference of dfdata is returned)
        """
        # function for getting ocv curves
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        if ocv_type in ['ocvrlx_up', 'ocvrlx_down']:
            ocv = self._get_ocv(dataset_number=None,
                                ocv_type=ocv_type,
                                select_last=True,
                                select_columns=True,
                                cycle_number=cycle_number,
                                )
            return ocv
        else:
            ocv_up = self._get_ocv(dataset_number=None,
                                   ocv_type='ocvrlx_up',
                                   select_last=True,
                                   select_columns=True,
                                   cycle_number=cycle_number,
                                   )
            ocv_down = self._get_ocv(dataset_number=None,
                                     ocv_type='ocvrlx_down',
                                     select_last=True,
                                     select_columns=True,
                                     cycle_number=cycle_number,
                                     )
            return ocv_up, ocv_down

    def _get_ocv(self, ocv_steps=None, dataset_number=None,
                 ocv_type='ocvrlx_up', select_last=True,
                 select_columns=True, cycle_number=None):
        # find ocv data in DataSet
        # (voltage vs time, no current)
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return

        if not ocv_steps:
            if not ocv_type in ['ocvrlx_up', 'ocvrlx_down']:
                self.logger.debug(" ocv_type must be ocvrlx_up or ocvrlx_down ")
                sys.exit(-1)
            else:
                ocv_steps = self.get_step_numbers(steptype=ocv_type,
                                                  allctypes=False,
                                                  pdtype=False,
                                                  cycle_number=cycle_number,
                                                  dataset_number=dataset_number)

        if cycle_number:
            # check ocv_steps
            ocv_step_exists = True
            #            self.logger.debug(cycle_number)
            #            self.logger.debug(ocv_steps)
            #            self.logger.debug(ocv_steps[cycle_number])
            if cycle_number not in ocv_steps:
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
                t = c[self.headers_normal['step_time_txt']]
                o = c[self.headers_normal['voltage_txt']]
                return [t, o]
            else:
                txt = "ERROR! cycle %i not found" % cycle_number  # jepe fix
                self.logger.debug(txt)
                return [None, None]

        else:
            ocv = []
            for cycle, steps in list(ocv_steps.items()):
                for step in steps:
                    c = self._select_step(cycle, step)
                    # select columns:

                    if select_columns and not self.is_empty(c):
                        column_names = c.columns
                        columns_to_keep = [self.headers_normal['cycle_index_txt'],
                                           self.headers_normal['step_time_txt'],
                                           self.headers_normal['step_index_txt'],
                                           self.headers_normal['data_point_txt'],
                                           self.headers_normal['datetime_txt'],
                                           self.headers_normal['voltage_txt'],
                                           ]
                        for column_name in column_names:
                            if not columns_to_keep.count(column_name):
                                c.pop(column_name)

                    if not self.is_empty(c):
                        ocv.append(c)
            return ocv

    def get_number_of_cycles(self, dataset_number=None):
        """Get the number of cycles in the test."""

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        d = self.datasets[dataset_number].dfdata
        cycle_index_header = self.headers_normal['cycle_index_txt']
        no_cycles = np.amax(d[cycle_index_header])
        return no_cycles

    def get_cycle_numbers(self, dataset_number=None):
        """Get a list containing all the cycle numbers in the test."""

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        d = self.datasets[dataset_number].dfdata
        cycle_index_header = self.headers_normal['cycle_index_txt']
        no_cycles = np.amax(d[cycle_index_header])
        # cycles = np.unique(d[cycle_index_header]).values
        cycles = np.unique(d[cycle_index_header])
        return cycles

    def get_ir(self, dataset_number=None):
        """Get the IR data (Deprecated)."""

        raise DeprecatedFeature

    def get_converter_to_specific(self, dataset=None, mass=None,
                                  to_unit=None, from_unit=None):
        """get the convertion values

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
            dataset = self.datasets[dataset_number]

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
        # Remove this later
        # assert float(from_unit / to_unit) == 1000000.0
        return from_unit / to_unit / mass

    def get_diagnostics_plots(self, dataset_number=None, scaled=False):
        """Gets diagnostics plots.

        Args:
            dataset_number: test number (default 0).
            scaled (bool): if True, scale by min and max values.

        Returns:
            Returns a dict containing diagnostics plots (keys = 'cycles',
                'shifted_discharge_cap',
                'shifted_charge_cap','RIC_cum',
                'RIC_disconnect_cum', 'RIC_sei_cum').

        """

        # assuming each cycle consists of one discharge step followed by
        # charge step
        warnings.warn("This feature will be deprecated soon. Extract"
                      " diagnostics from the summary instead.",
                      DeprecationWarning)
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        # print "in get_diagnostics_plots: dataset_number = %i" % dataset_number
        cyclenos = self.get_cycle_numbers(dataset_number=dataset_number)
        summarydata = self.get_summary(dataset_number=dataset_number)
        if summarydata is None:
            print("Warning! no summarydata made yet (get_diagnostics_plots "
                  "works on summarydata)")
            print("returning None")
            return None

        discharge_txt = self.headers_summary["discharge_capacity"]
        charge_txt = self.headers_summary["charge_capacity"]

        out = None
        dif = []  # difference between charge and discharge
        shifted_discharge_cap = []  # shifted discharge capacity
        shifted_charge_cap = []  # shifted charge capacity

        cycles = []
        # noinspection PyPep8Naming
        RIC_cum = []
        # noinspection PyPep8Naming
        RIC_disconnect_cum = []
        # noinspection PyPep8Naming
        RIC_sei_cum = []

        cn_1 = 0.0
        ric_disconnect_cum = 0.0
        ric_sei_cum = 0.0
        ric_cum = 0.0
        # noinspection PyPep8Naming
        C_n = None
        # noinspection PyPep8Naming
        D_n = None

        for i, cycle in enumerate(cyclenos):
            try:
                # noinspection PyPep8Naming
                D_n = summarydata[discharge_txt][i]
                # noinspection PyPep8Naming
                C_n = summarydata[charge_txt][i]
                dd = C_n - D_n
                ric_n = (D_n - C_n) / C_n
                try:
                    # noinspection PyPep8Naming
                    C_n2 = summarydata[charge_txt][i + 1]
                    # noinspection PyPep8Naming
                    D_n2 = summarydata[discharge_txt][i + 1]
                    ric_dis_n = (C_n - C_n2) / C_n
                    ric_sei_n = (D_n2 - C_n) / C_n
                except Exception:
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

            except Exception:
                self.logger.debug("end of summary")
                break
        if scaled is True:
            sdc_min = np.amin(shifted_discharge_cap)
            shifted_discharge_cap -= sdc_min
            sdc_max = np.amax(shifted_discharge_cap)
            shifted_discharge_cap /= sdc_max

            scc_min = np.amin(shifted_charge_cap)
            shifted_charge_cap -= scc_min
            scc_max = np.amax(shifted_charge_cap)
            shifted_charge_cap /= scc_max

        out = dict()
        out["cycles"] = cycles
        out["shifted_discharge_cap"] = shifted_discharge_cap
        out["shifted_charge_cap"] = shifted_charge_cap
        out["RIC_cum"] = RIC_cum
        out["RIC_disconnect_cum"] = RIC_disconnect_cum
        out["RIC_sei_cum"] = RIC_sei_cum
        return out

    def _set_mass(self, dataset_number, value):
        try:
            self.datasets[dataset_number].mass = value
            self.datasets[dataset_number].mass_given = True
        except AttributeError as e:
            print("This test is empty")
            print(e)

    def _set_tot_mass(self, dataset_number, value):
        try:
            self.datasets[dataset_number].tot_mass = value
        except AttributeError as e:
            print("This test is empty")
            print(e)

    def _set_nom_cap(self, dataset_number, value):
        try:
            self.datasets[dataset_number].nom_cap = value
        except AttributeError as e:
            print("This test is empty")
            print(e)

    def _set_run_attribute(self, attr, vals, dataset_number=None,
                           validated=None):
        # Sets the val (vals) for the test (datasets).
        if attr == "mass":
            setter = self._set_mass
        elif attr == "tot_mass":
            setter = self._set_tot_mass
        elif attr == "nom_cap":
            setter = self._set_nom_cap

        number_of_tests = len(self.datasets)
        if not number_of_tests:
            print("no datasets have been loaded yet")
            print("cannot set mass before loading datasets")
            sys.exit(-1)

        if not dataset_number:
            dataset_number = list(range(len(self.datasets)))

        if not self._is_listtype(dataset_number):
            dataset_number = [dataset_number, ]

        if not self._is_listtype(vals):
            vals = [vals, ]
        if validated is None:
            for t, m in zip(dataset_number, vals):
                setter(t, m)
        else:
            for t, m, v in zip(dataset_number, vals, validated):
                if v:
                    setter(t, m)
                else:
                    self.logger.debug("_set_run_attribute: this set is empty")

    def set_mass(self, masses, dataset_number=None, validated=None):
        """Sets the mass (masses) for the test (datasets).
        """
        self._set_run_attribute("mass", masses, dataset_number=dataset_number,
                                validated=validated)

    def set_tot_mass(self, masses, dataset_number=None, validated=None):
        """Sets the mass (masses) for the test (datasets).
        """
        self._set_run_attribute("tot_mass", masses,
                                dataset_number=dataset_number,
                                validated=validated)

    def set_nom_cap(self, nom_caps, dataset_number=None, validated=None):
        """Sets the mass (masses) for the test (datasets).
        """
        self._set_run_attribute("nom_cap", nom_caps,
                                dataset_number=dataset_number,
                                validated=validated)

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
        self.selected_dataset_number = dataset_number

    def set_testnumber(self, dataset_number):
        """Set the DataSet number.

        Set the dataset_number that will be used
        (CellpyData.selected_dataset_number).
        The class can save several datasets (but its not a frequently used
        feature), the datasets are stored in a list and dataset_number is the
        selected index in the list.

        Several options are available:
              n - int in range 0..(len-1) (python uses offset as index, i.e.
                  starts with 0)
              last, end, newest - last (index set to -1)
              first, zero, beinning, default - first (index set to 0)
        """
        self.logger.debug("***set_testnumber(n)")
        dataset_number_txt = dataset_number
        try:
            if dataset_number_txt.lower() in ["last", "end", "newest"]:
                dataset_number = -1
            elif dataset_number_txt.lower() in ["first", "zero", "beginning",
                                                "default"]:
                dataset_number = 0
        except Exception:
            self.logger.debug("assuming numeric")

        number_of_tests = len(self.datasets)
        if dataset_number >= number_of_tests:
            dataset_number = -1
            self.logger.debug("you dont have that many datasets, setting to "
                              "last test")
        elif dataset_number < -1:
            self.logger.debug("not a valid option, setting to first test")
            dataset_number = 0
        self.selected_dataset_number = dataset_number

    def get_summary(self, dataset_number=None, use_dfsummary_made=False):
        """Retrieve summary returned as a pandas DataFrame."""
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return None

        test = self.get_dataset(dataset_number)

        # This is a bit convoluted; in the old days, we used an attribute
        # called dfsummary_made,
        # that was set to True when the summary was made successfully.
        # It is most likely never
        # used anymore. And will most probably be deleted.
        if use_dfsummary_made:
            dfsummary_made = test.dfsummary_made
        else:
            dfsummary_made = True

        if not dfsummary_made:
            warnings.warn("Summary is not made yet")
            return None
        else:
            self.logger.info("returning datasets[test_no].dfsummary")
            return test.dfsummary

    # -----------internal-helpers-----------------------------------------------

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

    def _select_last(self, dfdata):
        # this function gives a set of indexes pointing to the last
        # datapoints for each cycle in the dataset

        c_txt = self.headers_normal['cycle_index_txt']
        d_txt = self.headers_normal['data_point_txt']

        steps = []
        max_step = max(dfdata[c_txt])
        for j in range(max_step):
            last_item = max(dfdata.loc[dfdata[c_txt] == j + 1, d_txt])
            steps.append(last_item)
        last_items = dfdata[d_txt].isin(steps)
        return last_items

    def _modify_cycle_number_using_cycle_step(self, from_tuple=None,
                                              to_cycle=44, dataset_number=None):
        # modify step-cycle tuple to new step-cycle tuple
        # from_tuple = [old cycle_number, old step_number]
        # to_cycle    = new cycle_number

        if from_tuple is None:
            from_tuple = [1, 4]
        self.logger.debug("**- _modify_cycle_step")
        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return

        cycle_index_header = self.headers_normal['cycle_index_txt']
        step_index_header = self.headers_normal['step_index_txt']

        step_table_txt_cycle = self.headers_step_table["cycle"]
        step_table_txt_step = self.headers_step_table["step"]

        # modifying step_table
        st = self.datasets[dataset_number].step_table
        st[step_table_txt_cycle][
            (st[step_table_txt_cycle] == from_tuple[0]) &
            (st[step_table_txt_step] == from_tuple[1])] = to_cycle
        # modifying normal_table
        nt = self.datasets[dataset_number].dfdata
        nt[cycle_index_header][
            (nt[cycle_index_header] == from_tuple[0]) &
            (nt[step_index_header] == from_tuple[1])] = to_cycle
        # modifying summary_table
        # not implemented yet

    # ----------making-summary------------------------------------------------------
    def make_summary(self, find_ocv=False, find_ir=False,
                     find_end_voltage=False,
                     use_cellpy_stat_file=None, all_tests=True,
                     dataset_number=0, ensure_step_table=None,
                     convert_date=True):
        """Convenience function that makes a summary of the cycling data."""

        if ensure_step_table is None:
            ensure_step_table = self.ensure_step_table
        # Cycle_Index	Test_Time(s)	Test_Time(h)	Date_Time	Current(A)
        # Current(mA)	Voltage(V)	Charge_Capacity(Ah)	Discharge_Capacity(Ah)
        # Charge_Energy(Wh)	Discharge_Energy(Wh)	Internal_Resistance(Ohm)
        # AC_Impedance(Ohm)	ACI_Phase_Angle(Deg)	Charge_Time(s)
        # DisCharge_Time(s)	Vmax_On_Cycle(V)	Coulombic_Efficiency
        if use_cellpy_stat_file is None:
            use_cellpy_stat_file = prms.Reader.use_cellpy_stat_file
            self.logger.debug("using use_cellpy_stat_file from prms")
            self.logger.debug(f"use_cellpy_stat_file: {use_cellpy_stat_file}")

        if all_tests is True:
            for j in range(len(self.datasets)):
                txt = "creating summary for file "
                test = self.datasets[j]
                if not self._is_not_empty_dataset(test):
                    print("empty test %i" % j)
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
                                   convert_date=convert_date,
                                   )
        else:
            self.logger.debug("creating summary for only one test")
            dataset_number = self._validate_dataset_number(dataset_number)
            if dataset_number is None:
                self._report_empty_dataset()
                return
            self._make_summary(dataset_number,
                               find_ocv=find_ocv,
                               find_ir=find_ir,
                               find_end_voltage=find_end_voltage,
                               use_cellpy_stat_file=use_cellpy_stat_file,
                               ensure_step_table=ensure_step_table,
                               convert_date=convert_date,
                               )

    def _make_summary(self,
                      dataset_number=None,
                      mass=None,
                      update_it=False,
                      select_columns=True,
                      find_ocv=False,
                      find_ir=False,
                      find_end_voltage=False,
                      # TODO: this is only needed for arbin-data:
                      convert_date=True,
                      sort_my_columns=True,
                      use_cellpy_stat_file=False,
                      ensure_step_table=False,
                      # capacity_modifier = None,
                      # test=None
                      ):

        dataset_number = self._validate_dataset_number(dataset_number)
        if dataset_number is None:
            self._report_empty_dataset()
            return
        dataset = self.datasets[dataset_number]
        #        if test.merged == True:
        #            use_cellpy_stat_file=False

        if not mass:
            mass = dataset.mass
        else:
            if update_it:
                dataset.mass = mass

        if ensure_step_table and not self.load_only_summary:
            if not dataset.step_table_made:
                self.make_step_table(dataset_number=dataset_number)

        # Retrieve the converters etc.
        specific_converter = self.get_converter_to_specific(dataset=dataset,
                                                            mass=mass)

        # Retrieving the column header names for raw-data (dfdata)
        dt_txt = self.headers_normal['datetime_txt']
        tt_txt = self.headers_normal['test_time_txt']
        st_txt = self.headers_normal['step_time_txt']
        c_txt = self.headers_normal['cycle_index_txt']
        d_txt = self.headers_normal['data_point_txt']
        s_txt = self.headers_normal['step_index_txt']
        voltage_header = self.headers_normal['voltage_txt']
        charge_txt = self.headers_normal['charge_capacity_txt']
        discharge_txt = self.headers_normal['discharge_capacity_txt']
        ir_txt = self.headers_normal['internal_resistance_txt']
        test_id_txt = self.headers_normal['test_id_txt']
        i_txt = self.headers_normal['current_txt']

        # Retrieving the column header names for summary-data (dfsummary)
        headers_summary = self.headers_summary

        discharge_title = headers_summary["discharge_capacity"]
        charge_title = headers_summary["charge_capacity"]
        cumcharge_title = headers_summary["cumulated_charge_capacity"]
        cumdischarge_title = headers_summary["cumulated_discharge_capacity"]
        coulomb_title = headers_summary["coulombic_efficiency"]
        cumcoulomb_title = headers_summary["cumulated_coulombic_efficiency"]
        coulomb_diff_title = headers_summary["coulombic_difference"]
        cumcoulomb_diff_title = \
            headers_summary["cumulated_coulombic_difference"]
        col_discharge_loss_title = headers_summary["discharge_capacity_loss"]
        col_charge_loss_title = headers_summary["charge_capacity_loss"]
        dcloss_cumsum_title = \
            headers_summary["cumulated_discharge_capacity_loss"]
        closs_cumsum_title = headers_summary["cumulated_charge_capacity_loss"]
        endv_charge_title = headers_summary["end_voltage_charge"]
        endv_discharge_title = headers_summary["end_voltage_discharge"]
        date_time_txt_title = headers_summary["date_time_txt"]
        ocv_1_v_min_title = headers_summary["ocv_first_min"]
        ocv_1_v_max_title = headers_summary["ocv_first_max"]
        ocv_2_v_min_title = headers_summary["ocv_second_min"]
        ocv_2_v_max_title = headers_summary["ocv_second_max"]
        ir_discharge_title = headers_summary["ir_discharge"]
        ir_charge_title = headers_summary["ir_charge"]

        ric_disconnect_title = headers_summary["cumulated_ric_disconnect"]
        ric_sei_title = headers_summary["cumulated_ric_sei"]
        ric_title = headers_summary["cumulated_ric"]
        high_level_at_cycle_n_txt = headers_summary["high_level"]
        low_level_at_cycle_n_txt = headers_summary["low_level"]
        shifted_charge_capacity_title = \
            headers_summary["shifted_charge_capacity"]
        shifted_discharge_capacity_title = \
            headers_summary["shifted_discharge_capacity"]

        # Here are the two main DataFrames for the test
        # (raw-data and summary-data)
        summary_df = dataset.dfsummary
        if not self.load_only_summary:
            # Can't find summary from raw data if raw data is not loaded.
            dfdata = dataset.dfdata
            if use_cellpy_stat_file:
                # This should work even if dfdata does not
                # contain all data from the test
                try:
                    summary_requirment = dfdata[d_txt].isin(summary_df[d_txt])
                except KeyError:
                    self.logger.info("error in stat_file (?) - "
                                     "using _select_last")
                    summary_requirment = self._select_last(dfdata)
            else:
                summary_requirment = self._select_last(dfdata)
            dfsummary = dfdata[summary_requirment]
        else:
            # summary_requirment = self._reloadrows_raw(summary_df[d_txt])
            dfsummary = summary_df
            dataset.dfsummary = dfsummary
            dataset.dfsummary_made = True
            self.logger.warning("not implemented yet")
            return

        column_names = dfsummary.columns
        summary_length = len(dfsummary[column_names[0]])
        dfsummary.index = list(range(summary_length))
        # could also index based on Cycle_Index
        # indexes = dfsummary.index

        if select_columns:
            columns_to_keep = [charge_txt, c_txt, d_txt, dt_txt,
                               discharge_txt, tt_txt,
                               ]
            for column_name in column_names:
                if not columns_to_keep.count(column_name):
                    dfsummary.pop(column_name)

        if not use_cellpy_stat_file:
            self.logger.debug("Not using cellpy statfile!")
            self.logger.debug("Values obtained from dfdata:")
            self.logger.debug(dfsummary.head(20))

        self.logger.debug("Creates summary: specific discharge ('%s')"
                          % discharge_title)
        dfsummary[discharge_title] = dfsummary[discharge_txt] * \
                                     specific_converter

        self.logger.debug("Creates summary: specific scharge ('%s')" %
                          charge_title)
        dfsummary[charge_title] = dfsummary[charge_txt] * specific_converter

        self.logger.debug("Creates summary: cumulated specific charge ('%s')" %
                          cumdischarge_title)
        dfsummary[cumdischarge_title] = dfsummary[discharge_title].cumsum()

        self.logger.debug("Creates summary: cumulated specific charge ('%s')" %
                          cumcharge_title)
        dfsummary[cumcharge_title] = dfsummary[charge_title].cumsum()

        if self.cycle_mode.lower() == "anode":
            self.logger.info("assuming cycling anode half-cell (discharge "
                             "before charge)")
            _first_step_txt = discharge_title
            _second_step_txt = charge_title
        else:
            _first_step_txt = charge_title
            _second_step_txt = discharge_title

        self.logger.debug("Creates summary: coulombic efficiency ('%s')" %
                          coulomb_title)
        self.logger.debug("100 * ('%s')/('%s)" % (_second_step_txt,
                                                  _first_step_txt))
        dfsummary[coulomb_title] = 100.0 * dfsummary[_second_step_txt] / \
                                   dfsummary[_first_step_txt]

        self.logger.debug("Creates summary: coulombic difference ('%s')" %
                          coulomb_diff_title)
        self.logger.debug("'%s') - ('%s)" % (_second_step_txt, _first_step_txt))
        dfsummary[coulomb_diff_title] = dfsummary[_second_step_txt] - \
                                        dfsummary[_first_step_txt]

        self.logger.debug("Creates summary: cumulated coulombic efficiency ('%s')" % cumcoulomb_title)
        dfsummary[cumcoulomb_title] = dfsummary[coulomb_title].cumsum()
        self.logger.debug("Creates summary: cumulated coulombic difference ('%s')" % cumcoulomb_diff_title)
        dfsummary[cumcoulomb_diff_title] = dfsummary[coulomb_diff_title].cumsum()

        # ---------------- discharge loss ---------------------
        # Assume that both charge and discharge is defined as positive.
        # The gain for cycle n (compared to cycle n-1)
        # is then cap[n] - cap[n-1]. The loss is the negative of gain.
        # discharge loss = discharge_cap[n-1] - discharge_cap[n]
        self.logger.debug("Creates summary: calculates DL")
        dfsummary[col_discharge_loss_title] = dfsummary[discharge_title].shift(1) - \
                                              dfsummary[discharge_title]
        dfsummary[dcloss_cumsum_title] = dfsummary[col_discharge_loss_title].cumsum()

        # ---------------- charge loss ------------------------
        # charge loss = charge_cap[n-1] - charge_cap[n]
        dfsummary[col_charge_loss_title] = dfsummary[charge_title].shift(1) - \
                                           dfsummary[charge_title]
        dfsummary[closs_cumsum_title] = dfsummary[col_charge_loss_title].cumsum()

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
        cap_ref = dfsummary.loc[dfsummary[c_txt] == n, _first_step_txt]
        if not cap_ref.empty:
            cap_ref = cap_ref.values[0]
            ref = dfsummary.loc[dfsummary[c_txt] < n, _second_step_txt].sum() \
                  + dfsummary.loc[dfsummary[c_txt] < n, _first_step_txt].sum() + cap_ref
            dfsummary[low_level_at_cycle_n_txt] = (100 / ref) * (dfsummary[_first_step_txt].cumsum()
                                                                 - dfsummary[_second_step_txt].cumsum())
            dfsummary[high_level_at_cycle_n_txt] = (100 / ref) * (dfsummary[_first_step_txt]
                                                                  + dfsummary[_first_step_txt].cumsum()
                                                                  - dfsummary[_second_step_txt].cumsum())
        else:
            txt = "ref cycle number: %i" % n
            self.logger.info("could not extract low-high levels (ref cycle "
                             "number does not exist)")
            self.logger.info(txt)
            dfsummary[low_level_at_cycle_n_txt] = np.nan
            dfsummary[high_level_at_cycle_n_txt] = np.nan

        # --------------relative irreversible capacities as defined by Gauthier et al.---
        # RIC = discharge_cap[n-1] - charge_cap[n] /  charge_cap[n-1]
        # noinspection PyPep8Naming
        RIC = (dfsummary[_first_step_txt].shift(1) -
               dfsummary[_second_step_txt]) / \
              dfsummary[_second_step_txt].shift(1)
        dfsummary[ric_title] = RIC.cumsum()

        # RIC_SEI = discharge_cap[n] - charge_cap[n-1] / charge_cap[n-1]
        # noinspection PyPep8Naming
        RIC_SEI = (dfsummary[_first_step_txt] -
                   dfsummary[_second_step_txt].shift(1)) / \
                   dfsummary[_second_step_txt].shift(1)
        dfsummary[ric_sei_title] = RIC_SEI.cumsum()

        # RIC_disconnect = charge_cap[n-1] - charge_cap[n] / charge_cap[n-1]
        # noinspection PyPep8Naming
        RIC_disconnect = (dfsummary[_second_step_txt].shift(1) -
                          dfsummary[_second_step_txt]) / dfsummary[
            _second_step_txt].shift(1)
        dfsummary[ric_disconnect_title] = RIC_disconnect.cumsum()

        # -------------- shifted capacities as defined by J. Dahn et al. -----
        # need to double check this (including checking if it is valid in cathode mode).
        individual_edge_movement = dfsummary[_first_step_txt] - \
                                   dfsummary[_second_step_txt]
        dfsummary[shifted_charge_capacity_title] = \
            individual_edge_movement.cumsum()
        dfsummary[shifted_discharge_capacity_title] = \
            dfsummary[shifted_charge_capacity_title] + dfsummary[
            _first_step_txt]

        if convert_date:
            self.logger.debug("converting date from xls-type")
            dfsummary[date_time_txt_title] = \
                dfsummary[dt_txt].apply(xldate_as_datetime, option="to_string")

        if find_ocv and not self.load_only_summary:
            # should remove this option
            print(20 * "*")
            print("CONGRATULATIONS")
            print("-though this would never be run!")
            print("-find_ocv in make_summary")
            print("  this is a stupid routine that can be implemented "
                  "much better!")
            print(20 * "*")
            do_ocv_1 = True
            do_ocv_2 = True

            ocv1_type = 'ocvrlx_up'
            ocv2_type = 'ocvrlx_down'

            if not self.cycle_mode == 'anode':
                ocv2_type = 'ocvrlx_up'
                ocv1_type = 'ocvrlx_down'

            ocv_1 = self._get_ocv(ocv_steps=dataset.ocv_steps,
                                  ocv_type=ocv1_type,
                                  dataset_number=dataset_number)

            ocv_2 = self._get_ocv(ocv_steps=dataset.ocv_steps,
                                  ocv_type=ocv2_type,
                                  dataset_number=dataset_number)

            if do_ocv_1:
                only_zeros = dfsummary[discharge_txt] * 0.0
                ocv_1_indexes = []
                ocv_1_v_min = []
                ocv_1_v_max = []
                ocvcol_min = only_zeros.copy()
                ocvcol_max = only_zeros.copy()

                for j in ocv_1:
                    cycle = j["Cycle_Index"].values[0]  # jepe fix
                    # try to find inxed
                    index = dfsummary[(dfsummary[c_txt] == cycle)].index
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

                for j in ocv_2:
                    cycle = j["Cycle_Index"].values[0]  # jepe fix
                    # try to find inxed
                    index = dfsummary[(dfsummary[c_txt] == cycle)].index
                    v_min = j["Voltage"].min()  # jepe fix
                    v_max = j["Voltage"].max()  # jepe fix
                    dv = v_max - v_min
                    ocvcol_min.ix[index] = v_min
                    ocvcol_max.ix[index] = v_max
                dfsummary.insert(0, column=ocv_2_v_min_title, value=ocvcol_min)
                dfsummary.insert(0, column=ocv_2_v_max_title, value=ocvcol_max)

        if find_end_voltage and not self.load_only_summary:
            # needs to be fixed so that end-voltage also can be extracted
            # from the summary
            only_zeros_discharge = dfsummary[discharge_txt] * 0.0
            only_zeros_charge = dfsummary[charge_txt] * 0.0
            if not dataset.discharge_steps:
                discharge_steps = self.get_step_numbers(steptype='discharge',
                                                        allctypes=False,
                                                        dataset_number=dataset_number)
            else:
                discharge_steps = dataset.discharge_steps
                self.logger.debug("alrady have discharge_steps")
            if not dataset.charge_steps:
                charge_steps = self.get_step_numbers(steptype='charge',
                                                     allctypes=False,
                                                     dataset_number=dataset_number)
            else:
                charge_steps = dataset.charge_steps
                self.logger.debug("already have charge_steps")

            endv_indexes = []
            endv_values_dc = []
            endv_values_c = []
            self.logger.debug("trying to find end voltage for")
            self.logger.debug(dataset.loaded_from)
            self.logger.debug("Using the following chargesteps")
            self.logger.debug(charge_steps)
            self.logger.debug("Using the following dischargesteps")
            self.logger.debug(discharge_steps)

            for i in dfsummary.index:
                txt = "index in dfsummary.index: %i" % i
                self.logger.debug(txt)
                # selecting the appropriate cycle
                cycle = dfsummary.ix[i][c_txt]  # "Cycle_Index" = i + 1
                txt = "cycle: %i" % cycle
                self.logger.debug(txt)
                step = discharge_steps[cycle]

                # finding end voltage for discharge
                if step[-1]:  # selecting last
                    # TODO use pd.loc[row,column] e.g. pd.loc[:,"charge_cap"]
                    # for col or pd.loc[(pd.["step"]==1),"x"]
                    end_voltage_dc = dfdata[(dfdata[c_txt] == cycle) &
                                            (dataset.dfdata[s_txt] == step[-1])][
                        voltage_header]
                    # This will not work if there are more than one item in step
                    end_voltage_dc = end_voltage_dc.values[-1]  # selecting
                    # last (could also select amax)
                else:
                    end_voltage_dc = 0  # could also use numpy.nan

                # finding end voltage for charge
                step2 = charge_steps[cycle]
                if step2[-1]:
                    end_voltage_c = dfdata[(dfdata[c_txt] == cycle) &
                                           (dataset.dfdata[s_txt] ==
                                            step2[-1])][voltage_header]
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

        if find_ir and not self.load_only_summary:
            # should check:  test.charge_steps = None,
            # test.discharge_steps = None
            # THIS DOES NOT WORK PROPERLY!!!!
            # Found a file where it writes IR for cycle n on cycle n+1
            # This only picks out the data on the last IR step before
            # @the (dis)charge cycle

            # TODO: use self.step_table instead for
            # finding charge/discharge steps
            only_zeros = dfsummary[discharge_txt] * 0.0
            if not dataset.discharge_steps:
                discharge_steps = self.get_step_numbers(steptype='discharge',
                                                        allctypes=False,
                                                        dataset_number=dataset_number)
            else:
                discharge_steps = dataset.discharge_steps
                self.logger.debug("already have discharge_steps")
            if not dataset.charge_steps:
                charge_steps = self.get_step_numbers(steptype='charge',
                                                     allctypes=False,
                                                     dataset_number=dataset_number)
            else:
                charge_steps = dataset.charge_steps
                self.logger.debug("already have charge_steps")

            ir_indexes = []
            ir_values = []
            ir_values2 = []
            self.logger.debug("trying to find ir for")
            self.logger.debug(dataset.loaded_from)
            self.logger.debug("Using the following charge_steps")
            self.logger.debug(charge_steps)
            self.logger.debug("Using the following discharge_steps")
            self.logger.debug(discharge_steps)

            for i in dfsummary.index:
                txt = "index in dfsummary.index: %i" % i
                self.logger.debug(txt)
                # selecting the appropriate cycle
                cycle = dfsummary.ix[i][c_txt]  # "Cycle_Index" = i + 1
                txt = "cycle: %i" % cycle
                self.logger.debug(txt)
                step = discharge_steps[cycle]
                if step[0]:
                    ir = dfdata.loc[(dfdata[c_txt] == cycle) &
                                    (dataset.dfdata[s_txt] == step[0]), ir_txt]
                    # This will not work if there are more than one item in step
                    ir = ir.values[0]
                else:
                    ir = 0
                step2 = charge_steps[cycle]
                if step2[0]:

                    ir2 = dfdata[(dfdata[c_txt] == cycle) &
                                 (dataset.dfdata[s_txt] == step2[0])][
                        ir_txt].values[0]
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
                new_first_col_list = [date_time_txt_title, tt_txt, d_txt, c_txt]
            else:
                new_first_col_list = [dt_txt, tt_txt, d_txt, c_txt]
            dfsummary = self.set_col_first(dfsummary, new_first_col_list)

        dataset.dfsummary = dfsummary
        dataset.dfsummary_made = True


def setup_cellpy_instance():
    """Prepares for a cellpy session.

    This convenience function creates a cellpy class and sets the parameters
    from your parameters file (using prmreader.read()

    Returns:
        an CellpyData object

    Example:

        >>> celldata = setup_cellpy_instance()
        read prms
        ...
        making class and setting prms

    """
    print("making class and setting prms")
    cellpy_instance = CellpyData()
    return cellpy_instance


def just_load_srno(srno, prm_filename=None):
    """Simply load an dataset based on serial number (srno).

    This convenience function reads a dataset based on a serial number. This
    serial number (srno) must then be defined in your database. It is mainly
    used to check that things are set up correctly.

    Args:
        prm_filename: name of parameter file (optional).
        srno (int): serial number

    Example:
        >>> srno = 918
        >>> just_load_srno(srno)
        srno: 918
        read prms
        ....

        """
    from cellpy import dbreader, prmreader, filefinder
    print("just_load_srno: srno: %i" % srno)

    # ------------reading parameters--------------------------------------------
    # print "just_load_srno: read prms"
    # prm = prmreader.read(prm_filename)
    #
    # print prm

    print("just_load_srno: making class and setting prms")
    d = CellpyData()

    # ------------reading db----------------------------------------------------
    print()
    print("just_load_srno: starting to load reader")
    # reader = dbreader.reader(prm_filename)
    reader = dbreader.Reader()
    print("------ok------")

    run_name = reader.get_cell_name(srno)
    print("just_load_srno: run_name:")
    print(run_name)

    m = reader.get_mass(srno)
    print("just_load_srno: mass: %f" % m)
    print()

    # ------------loadcell------------------------------------------------------
    print("just_load_srno: getting file_names")
    raw_files, cellpy_file = filefinder.search_for_files(run_name)
    print("raw_files:", raw_files)
    print("cellpy_file:", cellpy_file)

    print("just_load_srno: running loadcell")
    d.loadcell(raw_files, cellpy_file, mass=m)
    print("------ok------")

    # ------------do stuff------------------------------------------------------
    print("just_load_srno: getting step_numbers for charge")
    v = d.get_step_numbers("charge")
    print(v)

    print()
    print("just_load_srno: finding C-rates")
    d.find_C_rates(v, silent=False)

    print()
    print("just_load_srno: OK")
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
    d = CellpyData()

    if not outdir:
        outdir = prms.Paths["cellpydatadir"]

    if not outfile:
        outfile = os.path.basename(filename).split(".")[0] + ".h5"
        outfile = os.path.join(outdir, outfile)

    print("filename:", filename)
    print("outfile:", outfile)
    print("outdir:", outdir)
    print("mass:", mass, "mg")

    d.from_raw(filename)
    d.set_mass(mass)
    d.make_step_table()
    d.make_summary()
    d.save(filename=outfile)
    d.to_csv(datadir=outdir, cycles=True, raw=True, summary=True)
    return outfile


def load_and_print_resfile(filename, info_dict=None):
    """Load a raw data file and print information.

    Args:
        filename (str): name of the resfile.
        info_dict (dict):

    Returns:
        info (str): string describing something.
    """

    # self.test_no = None
    # self.mass = 1.0  # mass of (active) material (in mg)
    # self.no_cycles = 0.0
    # self.charge_steps = None  # not in use at the moment
    # self.discharge_steps = None  # not in use at the moment
    # self.ir_steps = None  # dict # not in use at the moment
    # self.ocv_steps = None  # dict # not in use at the moment
    # self.nom_cap = 3579  # mAh/g (used for finding c-rates)
    # self.mass_given = False
    # self.c_mode = True
    # self.starts_with = "discharge"
    # self.material = "noname"
    # self.merged = False
    # self.file_errors = None  # not in use at the moment
    # self.loaded_from = None  # name of the .res file it is loaded from
    # (can be list if merged)
    # self.raw_data_files = []
    # self.raw_data_files_length = []
    # # self.parent_filename = None # name of the .res file it is loaded from
    # (basename) (can be list if merded)
    # # self.parent_filename = if listtype, for file in etc,,,
    # os.path.basename(self.loaded_from)
    # self.channel_index = None
    # self.channel_number = None
    # self.creator = None
    # self.item_ID = None
    # self.schedule_file_name = None
    # self.start_datetime = None
    # self.test_ID = None
    # self.name = None

    # NEXT: include nom_cap, tot_mass and  parameters table in save/load hdf5
    if info_dict is None:
        info_dict = dict()
        info_dict["mass"] = 1.23  # mg
        info_dict["nom_cap"] = 3600  # mAh/g (active material)
        info_dict["tot_mass"] = 2.33  # mAh/g (total mass of material)

    d = CellpyData()

    print("filename:", filename)
    print("info_dict in:", end=' ')
    print(info_dict)

    d.from_raw(filename)
    d.set_mass(info_dict["mass"])
    d.make_step_table()
    d.make_summary()

    for test in d.datasets:
        print("newtest")
        print(test)

    return info_dict


def loadcell_check():
    print("running loadcell_check")
    out_dir = r"C:\Cell_data\tmp"
    mass = 0.078609164
    rawfile = r"C:\Cell_data\tmp\large_file_01.res"
    cellpyfile = r"C:\Cell_data\tmp\out\large_file_01.h5"
    cell_data = CellpyData()
    cell_data.select_minimal = True
    # cell_data.load_until_error = True
    cell_data.loadcell(raw_files=rawfile, cellpy_file=None, only_summary=False)
    cell_data.set_mass(mass)
    if not cell_data.summary_exists:
        cell_data.make_summary()
    cell_data.save(cellpyfile)
    cell_data.to_csv(datadir=out_dir, cycles=True, raw=True, summary=True)
    print("ok")


def extract_ocvrlx(filename, fileout, mass=1.00):
    """Get the ocvrlx data from dataset.

    Convenience function for extracting ocv relaxation data from runs."""
    import itertools
    import csv
    import matplotlib.pyplot as plt
    type_of_data = "ocvrlx_up"
    d_res = setup_cellpy_instance()
    print(filename)
    # d_res.from_res(filename)
    d_res.from_raw(filename)
    d_res.set_mass(mass)
    d_res.make_step_table()
    d_res.print_step_table()
    out_data = []
    for cycle in d_res.get_cycle_numbers():
        try:
            if type_of_data == 'ocvrlx_up':
                print("getting ocvrlx up data for cycle %i" % cycle)
                t, v = d_res.get_ocv(ocv_type='ocvrlx_up', cycle_number=cycle)
            else:
                print("getting ocvrlx down data for cycle %i" % cycle)
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

        except Exception:
            print("could not extract cycle %i" % cycle)

    save_to_file = False
    if save_to_file:
        # Saving cycles in one .csv file (x,y,x,y,x,y...)

        endstring = ".csv"
        outfile = fileout + endstring

        delimiter = ";"
        print("saving the file with delimiter '%s' " % delimiter)
        with open(outfile, "w") as f:
            writer = csv.writer(f, delimiter=delimiter)
            writer.writerows(itertools.zip_longest(*out_data))
            # star (or asterix) means transpose (writing cols instead of rows)

        print("saved the file", end=' ')
        print(outfile)
    plt.show()
    print("bye!")
    return True


# PROBLEMS:
# 1. 27.06.2016 new PC with 64bit conda python package:
#              Error opening connection to "Provider=Microsoft.ACE.OLEDB.12.0
#
# FIX:
# 1. 27.06.2016 installed 2007 Office System Driver: Data Connectivity
#             Components
#             (https://www.microsoft.com/en-us/download/confirmation.aspx?id=23734)
#             DID NOT WORK
#    27.06.2016 tried Microsoft Access Database Engine 2010 Redistributable
#             64x DID NOT INSTALL - my computer has 32bit office,
#             can only be install with 64-bit office
#    27.06.2016 installed Microsoft Access Database Engine 2010 Redistributable
#            86x DID NOT WORK
#    27.06.2016 uninstalled anaconda 64bit - installed 32 bit
#            WORKED!
#            LESSON LEARNED: dont use 64bit python with 32bit office installed


if __name__ == "__main__":
    print("running", end=' ')
    print(sys.argv[0])
    import logging
    from cellpy import log

    log.setup_logging(default_level="DEBUG")
    testfile = "../../testdata/data/20160805_test001_45_cc_01.res"
    load_and_print_resfile(testfile)
