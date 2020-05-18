"""arbin res-type data files"""
import os
import sys
import tempfile
import shutil
import logging
import platform
import warnings
import time
import numpy as np

import pandas as pd

from cellpy.readers.core import (
    FileID,
    Cell,
    check64bit,
    humanize_bytes,
    xldate_as_datetime,
)
from cellpy.parameters.internal_settings import HeaderDict, get_headers_normal
from cellpy.readers.instruments.mixin import Loader
from cellpy import prms

DEBUG_MODE = prms.Reader.diagnostics
ALLOW_MULTI_TEST_FILE = False

# Select odbc module
ODBC = prms._odbc
SEARCH_FOR_ODBC_DRIVERS = prms._search_for_odbc_driver

use_subprocess = prms.Instruments.Arbin.use_subprocess
detect_subprocess_need = prms.Instruments.Arbin.detect_subprocess_need

# Finding out some stuff about the platform
is_posix = False
is_macos = False
if os.name == "posix":
    is_posix = True
current_platform = platform.system()
if current_platform == "Darwin":
    is_macos = True

if DEBUG_MODE:
    logging.debug("DEBUG_MODE")
    logging.debug(f"ODBC: {ODBC}")
    logging.debug(f"SEARCH_FOR_ODBC_DRIVERS: {SEARCH_FOR_ODBC_DRIVERS}")
    logging.debug(f"use_subprocess: {use_subprocess}")
    logging.debug(f"detect_subprocess_need: {detect_subprocess_need}")
    logging.debug(f"current_platform: {current_platform}")

if detect_subprocess_need:
    logging.debug("detect_subprocess_need is True: checking versions")
    python_version, os_version = platform.architecture()
    if python_version == "64bit" and prms.Instruments.Arbin.office_version == "32bit":
        logging.debug(
            "python 64bit and office 32bit -> " "setting use_subprocess to True"
        )
        use_subprocess = True

if use_subprocess and not is_posix:
    # The windows users most likely have a strange custom path to mdbtools etc.
    logging.debug(
        "using subprocess (most lilkely mdbtools) " "on non-posix (most likely windows)"
    )
    if not prms.Instruments.Arbin.sub_process_path:
        sub_process_path = str(prms._sub_process_path)
    else:
        sub_process_path = str(prms.Instruments.Arbin.sub_process_path)

if is_posix:
    sub_process_path = "mdb-export"

try:
    driver_dll = prms.Instruments.Arbin.odbc_driver
except AttributeError:
    driver_dll = None

use_ado = False

if ODBC == "ado":
    use_ado = True
    logging.debug("Trying to use adodbapi as ado loader")
    try:
        import adodbapi as dbloader  # http://adodbapi.sourceforge.net/
    except ImportError:
        use_ado = False

if not use_ado:
    if ODBC == "pyodbc":
        try:
            import pyodbc as dbloader
        except ImportError:
            warnings.warn("COULD NOT LOAD DBLOADER!", ImportWarning)
            dbloader = None

    elif ODBC == "pypyodbc":
        try:
            import pypyodbc as dbloader
        except ImportError:
            warnings.warn("COULD NOT LOAD DBLOADER!", ImportWarning)
            dbloader = None

if DEBUG_MODE:
    logging.debug(f"dbloader: {dbloader}")

# The columns to choose if minimum selection is selected
MINIMUM_SELECTION = [
    "Data_Point",
    "Test_Time",
    "Step_Time",
    "DateTime",
    "Step_Index",
    "Cycle_Index",
    "Current",
    "Voltage",
    "Charge_Capacity",
    "Discharge_Capacity",
    "Internal_Resistance",
]

# Names of the tables in the .res db that is used by cellpy
TABLE_NAMES = {
    "normal": "Channel_Normal_Table",
    "global": "Global_Table",
    "statistic": "Channel_Statistic_Table",
}

summary_headers_renaming_dict = {
    "test_id_txt": "Test_ID",
    "data_point_txt": "Data_Point",
    "vmax_on_cycle_txt": "Vmax_On_Cycle",
    "charge_time_txt": "Charge_Time",
    "discharge_time_txt": "Discharge_Time",
}


normal_headers_renaming_dict = {
    "aci_phase_angle_txt": "ACI_Phase_Angle",
    "ref_aci_phase_angle_txt": "Reference_ACI_Phase_Angle",
    "ac_impedance_txt": "AC_Impedance",
    "ref_ac_impedance_txt": "Reference_AC_Impedance",
    "charge_capacity_txt": "Charge_Capacity",
    "charge_energy_txt": "Charge_Energy",
    "current_txt": "Current",
    "cycle_index_txt": "Cycle_Index",
    "data_point_txt": "Data_Point",
    "datetime_txt": "DateTime",
    "discharge_capacity_txt": "Discharge_Capacity",
    "discharge_energy_txt": "Discharge_Energy",
    "internal_resistance_txt": "Internal_Resistance",
    "is_fc_data_txt": "Is_FC_Data",
    "step_index_txt": "Step_Index",
    "sub_step_index_txt": "Sub_Step_Index",  # new
    "step_time_txt": "Step_Time",
    "sub_step_time_txt": "Sub_Step_Time",  # new
    "test_id_txt": "Test_ID",
    "test_time_txt": "Test_Time",
    "voltage_txt": "Voltage",
    "ref_voltage_txt": "Reference_Voltage",  # new
    "dv_dt_txt": "dV/dt",
    "frequency_txt": "Frequency",  # new
    "amplitude_txt": "Amplitude",  # new
}


class ArbinLoader(Loader):
    """ Class for loading arbin-data from res-files."""

    def __init__(self):
        """initiates the ArbinLoader class"""
        # could use __init__(self, cellpydata_object) and
        # set self.logger = cellpydata_object.logger etc.
        # then remember to include that as prm in "out of class" functions
        # self.prms = prms
        self.logger = logging.getLogger(__name__)
        # use the following prm to limit to loading only
        # one cycle or from cycle>x to cycle<x+n
        # prms.Reader["limit_loaded_cycles"] = [cycle from, cycle to]

        self.arbin_headers_normal = (
            self.get_headers_normal()
        )  # the column headers defined by Arbin
        self.cellpy_headers_normal = (
            get_headers_normal()
        )  # the column headers defined by cellpy
        self.arbin_headers_global = self.get_headers_global()
        self.current_chunk = 0  # use this to set chunks to load

    @staticmethod
    def get_raw_units():
        raw_units = dict()
        raw_units["current"] = 1.0  # A
        raw_units["charge"] = 1.0  # Ah
        raw_units["mass"] = 0.001  # g
        return raw_units

    @staticmethod
    def get_headers_normal():
        """Defines the so-called normal column headings for Arbin .res-files"""
        headers = HeaderDict()
        # - normal (raw-data) column headings (specific for Arbin)

        headers["aci_phase_angle_txt"] = "ACI_Phase_Angle"
        headers["ref_aci_phase_angle_txt"] = "Reference_ACI_Phase_Angle"

        headers["ac_impedance_txt"] = "AC_Impedance"
        headers["ref_ac_impedance_txt"] = "Reference_AC_Impedance"  # new

        headers["charge_capacity_txt"] = "Charge_Capacity"
        headers["charge_energy_txt"] = "Charge_Energy"
        headers["current_txt"] = "Current"
        headers["cycle_index_txt"] = "Cycle_Index"
        headers["data_point_txt"] = "Data_Point"
        headers["datetime_txt"] = "DateTime"
        headers["discharge_capacity_txt"] = "Discharge_Capacity"
        headers["discharge_energy_txt"] = "Discharge_Energy"
        headers["internal_resistance_txt"] = "Internal_Resistance"

        headers["is_fc_data_txt"] = "Is_FC_Data"
        headers["step_index_txt"] = "Step_Index"
        headers["sub_step_index_txt"] = "Sub_Step_Index"  # new

        headers["step_time_txt"] = "Step_Time"
        headers["sub_step_time_txt"] = "Sub_Step_Time"  # new

        headers["test_id_txt"] = "Test_ID"
        headers["test_time_txt"] = "Test_Time"

        headers["voltage_txt"] = "Voltage"
        headers["ref_voltage_txt"] = "Reference_Voltage"  # new

        headers["dv_dt_txt"] = "dV/dt"
        headers["frequency_txt"] = "Frequency"  # new
        headers["amplitude_txt"] = "Amplitude"  # new

        return headers

    @staticmethod
    def get_headers_global():
        """Defines the so-called global column headings for Arbin .res-files"""
        headers = dict()
        # - global column headings (specific for Arbin)
        headers["applications_path_txt"] = "Applications_Path"
        headers["channel_index_txt"] = "Channel_Index"
        headers["channel_number_txt"] = "Channel_Number"
        headers["channel_type_txt"] = "Channel_Type"
        headers["comments_txt"] = "Comments"
        headers["creator_txt"] = "Creator"
        headers["daq_index_txt"] = "DAQ_Index"
        headers["item_id_txt"] = "Item_ID"
        headers["log_aux_data_flag_txt"] = "Log_Aux_Data_Flag"
        headers["log_chanstat_data_flag_txt"] = "Log_ChanStat_Data_Flag"
        headers["log_event_data_flag_txt"] = "Log_Event_Data_Flag"
        headers["log_smart_battery_data_flag_txt"] = "Log_Smart_Battery_Data_Flag"
        headers["mapped_aux_conc_cnumber_txt"] = "Mapped_Aux_Conc_CNumber"
        headers["mapped_aux_di_cnumber_txt"] = "Mapped_Aux_DI_CNumber"
        headers["mapped_aux_do_cnumber_txt"] = "Mapped_Aux_DO_CNumber"
        headers["mapped_aux_flow_rate_cnumber_txt"] = "Mapped_Aux_Flow_Rate_CNumber"
        headers["mapped_aux_ph_number_txt"] = "Mapped_Aux_PH_Number"
        headers["mapped_aux_pressure_number_txt"] = "Mapped_Aux_Pressure_Number"
        headers["mapped_aux_temperature_number_txt"] = "Mapped_Aux_Temperature_Number"
        headers["mapped_aux_voltage_number_txt"] = "Mapped_Aux_Voltage_Number"
        headers[
            "schedule_file_name_txt"
        ] = "Schedule_File_Name"  # KEEP FOR CELLPY FILE FORMAT
        headers["start_datetime_txt"] = "Start_DateTime"
        headers["test_id_txt"] = "Test_ID"  # KEEP FOR CELLPY FILE FORMAT
        headers["test_name_txt"] = "Test_Name"  # KEEP FOR CELLPY FILE FORMAT
        return headers

    @staticmethod
    def get_raw_limits():
        raw_limits = dict()
        raw_limits["current_hard"] = 0.000_000_000_000_1
        raw_limits["current_soft"] = 0.000_01
        raw_limits["stable_current_hard"] = 2.0
        raw_limits["stable_current_soft"] = 4.0
        raw_limits["stable_voltage_hard"] = 2.0
        raw_limits["stable_voltage_soft"] = 4.0
        raw_limits["stable_charge_hard"] = 0.001
        raw_limits["stable_charge_soft"] = 5.0
        raw_limits["ir_change"] = 0.00001
        return raw_limits

    def _get_res_connector(self, temp_filename):

        if use_ado:
            is64bit_python = check64bit(current_system="python")
            if is64bit_python:
                constr = (
                    "Provider=Microsoft.ACE.OLEDB.12.0; Data Source=%s" % temp_filename
                )
            else:
                constr = (
                    "Provider=Microsoft.Jet.OLEDB.4.0; Data Source=%s" % temp_filename
                )
            return constr

        if SEARCH_FOR_ODBC_DRIVERS:
            logging.debug("Searching for odbc drivers")
            try:
                drivers = [
                    driver
                    for driver in dbloader.drivers()
                    if "Microsoft Access Driver" in driver
                ]
                logging.debug(f"Found these: {drivers}")
                driver = drivers[0]

            except IndexError as e:
                logging.debug(
                    "Unfortunately, it seems the " "list of drivers is emtpy."
                )
                logging.debug("Use driver-name from config (if existing).")
                driver = driver_dll
                if is_macos:
                    driver = "/usr/local/lib/libmdbodbc.dylib"
                else:
                    if not driver:
                        print(
                            "\nCould not find any odbc-drivers suitable "
                            "for .res-type files. "
                            "Check out the homepage of pydobc for info on "
                            "installing drivers"
                        )
                        print(
                            "One solution that might work is downloading "
                            "the Microsoft Access database engine (in correct"
                            " bytes (32 or 64)) "
                            "from:\n"
                            "https://www.microsoft.com/en-us/download/"
                            "details.aspx?id=13255"
                        )
                        print(
                            "Or install mdbtools and set it up "
                            "(check the cellpy docs for help)"
                        )
                        print("\n")
                    else:
                        logging.debug("Using driver dll from config file")
                        logging.debug(f"driver dll: {driver}")

            self.logger.debug(f"odbc constr: {driver}")

        else:
            is64bit_python = check64bit(current_system="python")
            if is64bit_python:
                driver = "{Microsoft Access Driver (*.mdb, *.accdb)}"
            else:
                driver = "Microsoft Access Driver (*.mdb)"
            self.logger.debug("odbc constr: {}".format(driver))
        constr = "Driver=%s;Dbq=%s" % (driver, temp_filename)

        logging.debug(f"constr: {constr}")

        return constr

    def _clean_up_loadres(self, cur, conn, filename):
        if cur is not None:
            cur.close()  # adodbapi
        if conn is not None:
            conn.close()  # adodbapi
        if os.path.isfile(filename):
            try:
                os.remove(filename)
            except WindowsError as e:
                self.logger.warning("could not remove tmp-file\n%s %s" % (filename, e))

    def _post_process(self, data):
        fix_datetime = True
        set_index = True
        rename_headers = True

        # TODO:  insert post-processing and div tests here
        #    - check dtypes

        # Remark that we also set index during saving the file to hdf5 if
        #   it is not set.

        if rename_headers:
            columns = {}
            for key in self.arbin_headers_normal:
                old_header = normal_headers_renaming_dict[key]
                new_header = self.cellpy_headers_normal[key]
                columns[old_header] = new_header

            data.raw.rename(index=str, columns=columns, inplace=True)
            try:
                # TODO: check if summary df is existing (to only check if it is
                #  empty will give an error later!)
                columns = {}
                for key, old_header in summary_headers_renaming_dict.items():
                    try:
                        columns[old_header] = self.cellpy_headers_normal[key]
                    except KeyError:
                        columns[old_header] = old_header.lower()
                data.summary.rename(index=str, columns=columns, inplace=True)
            except Exception as e:
                logging.debug(f"Could not rename summary df ::\n{e}")

        if fix_datetime:
            h_datetime = self.cellpy_headers_normal.datetime_txt
            logging.debug("converting to datetime format")
            # print(data.raw.columns)
            data.raw[h_datetime] = data.raw[h_datetime].apply(
                xldate_as_datetime, option="to_datetime"
            )

            h_datetime = h_datetime
            if h_datetime in data.summary:
                data.summary[h_datetime] = data.summary[h_datetime].apply(
                    xldate_as_datetime, option="to_datetime"
                )

        if set_index:
            hdr_data_point = self.cellpy_headers_normal.data_point_txt
            if data.raw.index.name != hdr_data_point:
                data.raw = data.raw.set_index(hdr_data_point, drop=False)

        return data

    def _inspect(self, run_data):
        """Inspect the file -> reports to log (debug)"""

        if not any([DEBUG_MODE]):
            return run_data

        if DEBUG_MODE:
            checked_rundata = []
            for data in run_data:
                new_cols = data.raw.columns
                for col in self.arbin_headers_normal:
                    if col not in new_cols:
                        logging.debug(f"Missing col: {col}")
                        # data.raw[col] = np.nan
                checked_rundata.append(data)
            return checked_rundata

    def _iterdump(self, file_name, headers=None):
        """
        Function for dumping values from a file.

        Should only be used by developers.

        Args:
            file_name: name of the file
            headers: list of headers to pick
                default:
                ["Discharge_Capacity", "Charge_Capacity"]

        Returns: pandas.DataFrame

        """
        if headers is None:
            headers = ["Discharge_Capacity", "Charge_Capacity"]

        step_txt = self.arbin_headers_normal.step_index_txt
        point_txt = self.arbin_headers_normal.data_point_txt
        cycle_txt = self.arbin_headers_normal.cycle_index_txt

        self.logger.debug("iterating through file: %s" % file_name)
        if not os.path.isfile(file_name):
            print("Missing file_\n   %s" % file_name)

        filesize = os.path.getsize(file_name)
        hfilesize = humanize_bytes(filesize)
        txt = "Filesize: %i (%s)" % (filesize, hfilesize)
        self.logger.info(txt)

        table_name_global = TABLE_NAMES["global"]
        table_name_stats = TABLE_NAMES["statistic"]
        table_name_normal = TABLE_NAMES["normal"]

        # creating temporary file and connection

        temp_dir = tempfile.gettempdir()
        temp_filename = os.path.join(temp_dir, os.path.basename(file_name))
        shutil.copy2(file_name, temp_dir)
        constr = self._get_res_connector(temp_filename)

        if use_ado:
            conn = dbloader.connect(constr)
        else:
            conn = dbloader.connect(constr, autocommit=True)

        self.logger.debug("tmp file: %s" % temp_filename)
        self.logger.debug("constr str: %s" % constr)

        # --------- read global-data ------------------------------------
        self.logger.debug("reading global data table")
        sql = "select * from %s" % table_name_global
        global_data_df = pd.read_sql_query(sql, conn)
        # col_names = list(global_data_df.columns.values)
        self.logger.debug("sql statement: %s" % sql)

        tests = global_data_df[self.arbin_headers_normal.test_id_txt]
        number_of_sets = len(tests)
        self.logger.debug("number of datasets: %i" % number_of_sets)
        self.logger.debug("only selecting first test")
        test_no = 0
        self.logger.debug("setting data for test number %i" % test_no)
        loaded_from = file_name
        # fid = FileID(file_name)
        start_datetime = global_data_df[
            self.arbin_headers_global["start_datetime_txt"]
        ][test_no]
        test_ID = int(
            global_data_df[self.arbin_headers_normal.test_id_txt][test_no]
        )  # OBS
        test_name = global_data_df[self.arbin_headers_global["test_name_txt"]][test_no]

        # --------- read raw-data (normal-data) -------------------------
        self.logger.debug("reading raw-data")

        columns = ["Data_Point", "Step_Index", "Cycle_Index"]
        columns.extend(headers)
        columns_txt = ", ".join(["%s"] * len(columns)) % tuple(columns)

        sql_1 = "select %s " % columns_txt
        sql_2 = "from %s " % table_name_normal
        sql_3 = "where %s=%s " % (self.arbin_headers_normal.test_id_txt, test_ID)
        sql_5 = "order by %s" % self.arbin_headers_normal.data_point_txt
        import time

        info_list = []
        info_header = ["cycle", "row_count", "start_point", "end_point"]
        info_header.extend(headers)
        self.logger.info(" ".join(info_header))
        self.logger.info("-------------------------------------------------")

        for cycle_number in range(1, 2000):
            t1 = time.time()
            self.logger.debug("picking cycle %i" % cycle_number)
            sql_4 = "AND %s=%i " % (cycle_txt, cycle_number)
            sql = sql_1 + sql_2 + sql_3 + sql_4 + sql_5
            self.logger.debug("sql statement: %s" % sql)
            normal_df = pd.read_sql_query(sql, conn)
            t2 = time.time()
            dt = t2 - t1
            self.logger.debug("time: %f" % dt)
            if normal_df.empty:
                self.logger.debug("reached the end")
                break
            row_count, _ = normal_df.shape
            start_point = normal_df[point_txt].min()
            end_point = normal_df[point_txt].max()
            last = normal_df.iloc[-1, :]

            step_list = [cycle_number, row_count, start_point, end_point]
            step_list.extend([last[x] for x in headers])
            info_list.append(step_list)

        self._clean_up_loadres(None, conn, temp_filename)
        info_dict = pd.DataFrame(info_list, columns=info_header)
        return info_dict

    def investigate(self, file_name):
        """Investigate a .res file.

        Args:
            file_name: name of the file

        Returns: dictionary with div. stats and info.

        """
        step_txt = self.arbin_headers_normal.step_index_txt
        point_txt = self.arbin_headers_normal.data_point_txt
        cycle_txt = self.arbin_headers_normal.cycle_index_txt

        self.logger.debug("investigating file: %s" % file_name)
        if not os.path.isfile(file_name):
            print("Missing file_\n   %s" % file_name)

        filesize = os.path.getsize(file_name)
        hfilesize = humanize_bytes(filesize)
        txt = "Filesize: %i (%s)" % (filesize, hfilesize)
        self.logger.info(txt)

        table_name_global = TABLE_NAMES["global"]
        table_name_stats = TABLE_NAMES["statistic"]
        table_name_normal = TABLE_NAMES["normal"]

        # creating temporary file and connection

        temp_dir = tempfile.gettempdir()
        temp_filename = os.path.join(temp_dir, os.path.basename(file_name))
        shutil.copy2(file_name, temp_dir)
        constr = self._get_res_connector(temp_filename)

        if use_ado:
            conn = dbloader.connect(constr)
        else:
            conn = dbloader.connect(constr, autocommit=True)

        self.logger.debug("tmp file: %s" % temp_filename)
        self.logger.debug("constr str: %s" % constr)

        # --------- read global-data ------------------------------------
        self.logger.debug("reading global data table")
        sql = "select * from %s" % table_name_global
        global_data_df = pd.read_sql_query(sql, conn)
        # col_names = list(global_data_df.columns.values)
        self.logger.debug("sql statement: %s" % sql)

        tests = global_data_df[self.arbin_headers_normal.test_id_txt]
        number_of_sets = len(tests)
        self.logger.debug("number of datasets: %i" % number_of_sets)
        self.logger.debug("only selecting first test")
        test_no = 0
        self.logger.debug("setting data for test number %i" % test_no)
        loaded_from = file_name
        # fid = FileID(file_name)
        start_datetime = global_data_df[
            self.arbin_headers_global["start_datetime_txt"]
        ][test_no]
        test_ID = int(
            global_data_df[self.arbin_headers_normal.test_id_txt][test_no]
        )  # OBS
        test_name = global_data_df[self.arbin_headers_global["test_name_txt"]][test_no]

        # --------- read raw-data (normal-data) -------------------------
        self.logger.debug("reading raw-data")

        columns = ["Data_Point", "Step_Index", "Cycle_Index"]
        columns_txt = ", ".join(["%s"] * len(columns)) % tuple(columns)

        sql_1 = "select %s " % columns_txt
        sql_2 = "from %s " % table_name_normal
        sql_3 = "where %s=%s " % (self.arbin_headers_normal.test_id_txt, test_ID)
        sql_5 = "order by %s" % self.arbin_headers_normal.data_point_txt
        import time

        info_list = []
        info_header = ["cycle", "step", "row_count", "start_point", "end_point"]
        self.logger.info(" ".join(info_header))
        self.logger.info("-------------------------------------------------")
        for cycle_number in range(1, 2000):
            t1 = time.time()
            self.logger.debug("picking cycle %i" % cycle_number)
            sql_4 = "AND %s=%i " % (cycle_txt, cycle_number)
            sql = sql_1 + sql_2 + sql_3 + sql_4 + sql_5
            self.logger.debug("sql statement: %s" % sql)
            normal_df = pd.read_sql_query(sql, conn)
            t2 = time.time()
            dt = t2 - t1
            self.logger.debug("time: %f" % dt)
            if normal_df.empty:
                self.logger.debug("reached the end")
                break
            row_count, _ = normal_df.shape
            steps = normal_df[self.arbin_headers_normal.step_index_txt].unique()
            txt = "cycle %i: %i [" % (cycle_number, row_count)
            for step in steps:
                self.logger.debug(" step: %i" % step)
                step_df = normal_df.loc[normal_df[step_txt] == step]
                step_row_count, _ = step_df.shape
                start_point = step_df[point_txt].min()
                end_point = step_df[point_txt].max()
                txt += " %i-(%i)" % (step, step_row_count)
                step_list = [cycle_number, step, step_row_count, start_point, end_point]
                info_list.append(step_list)

            txt += "]"
            self.logger.info(txt)

        self._clean_up_loadres(None, conn, temp_filename)
        info_dict = pd.DataFrame(info_list, columns=info_header)
        return info_dict

    def repair(self, file_name):
        """try to repair a broken/corrupted file"""
        raise NotImplemented

    def dump(self, file_name, path):
        """Dumps the raw file to an intermediate hdf5 file.

        This method can be used if the raw file is too difficult to load and it
        is likely that it is more efficient to convert it to an hdf5 format
        and then load it using the `from_intermediate_file` function.

        Args:
            file_name: name of the raw file
            path: path to where to store the intermediate hdf5 file (optional)

        Returns:
            full path to stored intermediate hdf5 file
            information about the raw file (needed by the
            `from_intermediate_file` function)

        """

        # information = None # contains information needed by the from_
        # intermediate_file reader
        # full_path = None
        # return full_path, information
        raise NotImplemented

    def _loader_win(
        self,
        file_name,
        temp_filename,
        *args,
        bad_steps=None,
        dataset_number=None,
        data_points=None,
        **kwargs,
    ):

        new_tests = []
        conn = None

        table_name_global = TABLE_NAMES["global"]
        table_name_stats = TABLE_NAMES["statistic"]
        table_name_normal = TABLE_NAMES["normal"]

        if DEBUG_MODE:
            time_0 = time.time()

        constr = self._get_res_connector(temp_filename)

        if use_ado:
            conn = dbloader.connect(constr)
        else:
            conn = dbloader.connect(constr, autocommit=True)
        self.logger.debug("constr str: %s" % constr)

        self.logger.debug("reading global data table")
        sql = "select * from %s" % table_name_global
        self.logger.debug("sql statement: %s" % sql)
        global_data_df = pd.read_sql_query(sql, conn)
        # col_names = list(global_data_df.columns.values)
        tests = global_data_df[self.arbin_headers_normal.test_id_txt]

        number_of_sets = len(tests)
        self.logger.debug("number of datasets: %i" % number_of_sets)
        self.logger.debug(f"datasets: {tests}")

        if dataset_number is not None:
            self.logger.info(f"Dataset number given: {dataset_number}")
            self.logger.info(f"Available dataset numbers: {tests}")
            test_nos = [dataset_number]
        else:
            test_nos = range(number_of_sets)

        for counter, test_no in enumerate(test_nos):
            if counter > 0:
                self.logger.warning("** WARNING ** MULTI-TEST-FILE (not recommended)")
                if not ALLOW_MULTI_TEST_FILE:
                    break
            data = self._init_data(file_name, global_data_df, test_no)

            self.logger.debug("reading raw-data")
            # --------- read raw-data (normal-data) ------------------------
            length_of_test, normal_df = self._load_res_normal_table(
                conn, data.test_ID, bad_steps, data_points
            )
            # --------- read stats-data (summary-data) ---------------------
            sql = "select * from %s where %s=%s order by %s" % (
                table_name_stats,
                self.arbin_headers_normal.test_id_txt,
                data.test_ID,
                self.arbin_headers_normal.data_point_txt,
            )
            summary_df = pd.read_sql_query(sql, conn)

            if summary_df.empty and prms.Reader.use_cellpy_stat_file:
                txt = "\nCould not find any summary (stats-file)!"
                txt += "\n -> issue make_summary(use_cellpy_stat_file=False)"
                logging.debug(txt)
                # TODO: Enforce creating a summary df or modify renaming summary df (post process part)
            # normal_df = normal_df.set_index("Data_Point")

            data.summary = summary_df
            if DEBUG_MODE:
                mem_usage = normal_df.memory_usage()
                logging.debug(
                    f"memory usage for "
                    f"loaded data: \n{mem_usage}"
                    f"\ntotal: {humanize_bytes(mem_usage.sum())}"
                )
                logging.debug(f"time used: {(time.time() - time_0):2.4f} s")

            data.raw = normal_df
            data.raw_data_files_length.append(length_of_test)
            data = self._post_process(data)
            data = self.identify_last_data_point(data)
            new_tests.append(data)
        return new_tests

    def _loader_posix(
        self,
        file_name,
        temp_filename,
        temp_dir,
        *args,
        bad_steps=None,
        dataset_number=None,
        data_points=None,
        **kwargs,
    ):

        table_name_global = TABLE_NAMES["global"]
        table_name_stats = TABLE_NAMES["statistic"]
        table_name_normal = TABLE_NAMES["normal"]

        new_tests = []

        if is_posix:
            if is_macos:
                self.logger.debug("\nMAC OSX USING MDBTOOLS")
            else:
                self.logger.debug("\nPOSIX USING MDBTOOLS")
        else:
            self.logger.debug("\nWINDOWS USING MDBTOOLS-WIN")

        if DEBUG_MODE:
            time_0 = time.time()

        tmp_name_global, tmp_name_raw, tmp_name_stats = self._create_tmp_files(
            table_name_global,
            table_name_normal,
            table_name_stats,
            temp_dir,
            temp_filename,
        )

        # use pandas to load in the data
        global_data_df = pd.read_csv(tmp_name_global)
        tests = global_data_df[self.arbin_headers_normal.test_id_txt]

        number_of_sets = len(tests)
        self.logger.debug("number of datasets: %i" % number_of_sets)
        self.logger.debug(f"datasets: {tests}")

        if dataset_number is not None:
            self.logger.info(f"Dataset number given: {dataset_number}")
            self.logger.info(f"Available dataset numbers: {tests}")
            test_nos = [dataset_number]
        else:
            test_nos = range(number_of_sets)

        for counter, test_no in enumerate(test_nos):
            if counter > 0:
                self.logger.warning("** WARNING ** MULTI-TEST-FILE (not recommended)")
                if not ALLOW_MULTI_TEST_FILE:
                    break
            data = self._init_data(file_name, global_data_df, test_no)

            self.logger.debug("reading raw-data")

            length_of_test, normal_df, summary_df = self._load_from_tmp_files(
                data,
                tmp_name_global,
                tmp_name_raw,
                tmp_name_stats,
                temp_filename,
                bad_steps,
                data_points,
            )

            if summary_df.empty and prms.Reader.use_cellpy_stat_file:
                txt = "\nCould not find any summary (stats-file)!"
                txt += "\n -> issue make_summary(use_cellpy_stat_file=False)"
                logging.debug(txt)
            # normal_df = normal_df.set_index("Data_Point")

            data.summary = summary_df
            if DEBUG_MODE:
                mem_usage = normal_df.memory_usage()
                logging.debug(
                    f"memory usage for "
                    f"loaded data: \n{mem_usage}"
                    f"\ntotal: {humanize_bytes(mem_usage.sum())}"
                )
                logging.debug(f"time used: {(time.time() - time_0):2.4f} s")

            data.raw = normal_df
            data.raw_data_files_length.append(length_of_test)
            data = self._post_process(data)
            data = self.identify_last_data_point(data)
            new_tests.append(data)
        return new_tests

    def loader(
        self,
        file_name,
        *args,
        bad_steps=None,
        dataset_number=None,
        data_points=None,
        **kwargs,
    ):
        """Loads data from arbin .res files.

        Args:
            file_name (str): path to .res file.
            bad_steps (list of tuples): (c, s) tuples of steps s (in cycle c)
                to skip loading.
            dataset_number (int): the data set number to select if you are dealing
                with arbin files with more than one data-set.
            data_points (tuple of ints): load only data from data_point[0] to
                    data_point[1] (use None for infinite).

        Returns:
            new_tests (list of data objects)
        """
        # TODO: @jepe - insert kwargs - current chunk, only normal data, etc

        if not os.path.isfile(file_name):
            self.logger.info("Missing file_\n   %s" % file_name)
            return None

        self.logger.debug("in loader")
        self.logger.debug("filename: %s" % file_name)

        filesize = os.path.getsize(file_name)
        hfilesize = humanize_bytes(filesize)
        txt = "Filesize: %i (%s)" % (filesize, hfilesize)
        self.logger.debug(txt)
        if (
            filesize > prms.Instruments.Arbin.max_res_filesize
            and not prms.Reader.load_only_summary
        ):
            error_message = "\nERROR (loader):\n"
            error_message += "%s > %s - File is too big!\n" % (
                hfilesize,
                humanize_bytes(prms.Instruments.Arbin.max_res_filesize),
            )
            error_message += "(edit prms.Instruments.Arbin ['max_res_filesize'])\n"
            print(error_message)
            return None

        temp_dir = tempfile.gettempdir()
        temp_filename = os.path.join(temp_dir, os.path.basename(file_name))
        shutil.copy2(file_name, temp_dir)
        self.logger.debug("tmp file: %s" % temp_filename)

        use_mdbtools = False
        if use_subprocess:
            use_mdbtools = True
        if is_posix:
            use_mdbtools = True

        if use_mdbtools:
            new_tests = self._loader_posix(
                file_name,
                temp_filename,
                temp_dir,
                *args,
                bad_steps=bad_steps,
                dataset_number=dataset_number,
                data_points=data_points,
                **kwargs,
            )
        else:
            new_tests = self._loader_win(
                file_name,
                temp_filename,
                *args,
                bad_steps=bad_steps,
                dataset_number=dataset_number,
                data_points=data_points,
                **kwargs,
            )

        new_tests = self._inspect(new_tests)

        return new_tests

    def _create_tmp_files(
        self,
        table_name_global,
        table_name_normal,
        table_name_stats,
        temp_dir,
        temp_filename,
    ):
        import subprocess

        # creating tmp-filenames
        temp_csv_filename_global = os.path.join(temp_dir, "global_tmp.csv")
        temp_csv_filename_normal = os.path.join(temp_dir, "normal_tmp.csv")
        temp_csv_filename_stats = os.path.join(temp_dir, "stats_tmp.csv")
        # making the cmds
        mdb_prms = [
            (table_name_global, temp_csv_filename_global),
            (table_name_normal, temp_csv_filename_normal),
            (table_name_stats, temp_csv_filename_stats),
        ]
        # executing cmds
        for table_name, tmp_file in mdb_prms:
            with open(tmp_file, "w") as f:
                subprocess.call([sub_process_path, temp_filename, table_name], stdout=f)
                self.logger.debug(f"ran mdb-export {str(f)} {table_name}")
        return (
            temp_csv_filename_global,
            temp_csv_filename_normal,
            temp_csv_filename_stats,
        )

    def _load_from_tmp_files(
        self,
        data,
        temp_csv_filename_global,
        temp_csv_filename_normal,
        temp_csv_filename_stats,
        temp_filename,
        bad_steps,
        data_points,
    ):

        """
        if bad_steps is not None:
            if not isinstance(bad_steps, (list, tuple)):
                bad_steps = [bad_steps]
            for bad_cycle, bad_step in bad_steps:
                self.logger.debug(f"bad_step def: [c={bad_cycle}, s={bad_step}]")
                sql_4 += "AND NOT (%s=%i " % (
                    self.headers_normal.cycle_index_txt,
                    bad_cycle,
                )
                sql_4 += "AND %s=%i) " % (self.headers_normal.step_index_txt, bad_step)



        """
        # should include a more efficient to load the csv (maybe a loop where
        #   we load only chuncks and only keep the parts that fullfill the
        #   filters (e.g. bad_steps, data_points,...)
        normal_df = pd.read_csv(temp_csv_filename_normal)
        # filter on test ID
        normal_df = normal_df[
            normal_df[self.arbin_headers_normal.test_id_txt] == data.test_ID
        ]
        # sort on data point
        if prms._sort_if_subprocess:
            normal_df = normal_df.sort_values(self.arbin_headers_normal.data_point_txt)

        if bad_steps is not None:
            logging.debug("removing bad steps")
            if not isinstance(bad_steps, (list, tuple)):
                bad_steps = [bad_steps]
            if not isinstance(bad_steps[0], (list, tuple)):
                bad_steps = [bad_steps]
            for bad_cycle, bad_step in bad_steps:
                self.logger.debug(f"bad_step def: [c={bad_cycle}, s={bad_step}]")

                selector = (
                    normal_df[self.arbin_headers_normal.cycle_index_txt] == bad_cycle
                ) & (normal_df[self.arbin_headers_normal.step_index_txt] == bad_step)

                normal_df = normal_df.loc[~selector, :]

        if prms.Reader["limit_loaded_cycles"]:
            if len(prms.Reader["limit_loaded_cycles"]) > 1:
                c1, c2 = prms.Reader["limit_loaded_cycles"]
                selector = (
                    normal_df[self.arbin_headers_normal.cycle_index_txt] > c1
                ) & (normal_df[self.arbin_headers_normal.cycle_index_txt] < c2)

            else:
                c1 = prms.Reader["limit_loaded_cycles"][0]
                selector = normal_df[self.arbin_headers_normal.cycle_index_txt] == c1

            normal_df = normal_df.loc[selector, :]

        if data_points is not None:
            logging.debug("selecting data-point range")
            d1, d2 = data_points

            if d1 is not None:
                selector = normal_df[self.arbin_headers_normal.data_point_txt] >= d1
                normal_df = normal_df.loc[selector, :]

            if d2 is not None:
                selector = normal_df[self.arbin_headers_normal.data_point_txt] <= d2
                normal_df = normal_df.loc[selector, :]

        length_of_test = normal_df.shape[0]
        summary_df = pd.read_csv(temp_csv_filename_stats)

        # clean up
        for f in [
            temp_filename,
            temp_csv_filename_stats,
            temp_csv_filename_normal,
            temp_csv_filename_global,
        ]:
            if os.path.isfile(f):
                try:
                    os.remove(f)
                except WindowsError as e:
                    self.logger.warning(f"could not remove tmp-file\n{f} {e}")
        return length_of_test, normal_df, summary_df

    def _init_data(self, file_name, global_data_df, test_no):
        data = Cell()
        data.cell_no = test_no
        data.loaded_from = file_name
        fid = FileID(file_name)
        # name of the .res file it is loaded from:
        # data.parent_filename = os.path.basename(file_name)
        data.channel_index = int(
            global_data_df[self.arbin_headers_global["channel_index_txt"]][test_no]
        )
        data.channel_number = int(
            global_data_df[self.arbin_headers_global["channel_number_txt"]][test_no]
        )
        data.creator = global_data_df[self.arbin_headers_global["creator_txt"]][test_no]
        data.item_ID = global_data_df[self.arbin_headers_global["item_id_txt"]][test_no]
        data.schedule_file_name = global_data_df[
            self.arbin_headers_global["schedule_file_name_txt"]
        ][test_no]
        data.start_datetime = global_data_df[
            self.arbin_headers_global["start_datetime_txt"]
        ][test_no]
        data.test_ID = int(
            global_data_df[self.arbin_headers_normal.test_id_txt][test_no]
        )
        data.test_name = global_data_df[self.arbin_headers_global["test_name_txt"]][
            test_no
        ]
        data.raw_data_files.append(fid)
        return data

    def _normal_table_generator(self, **kwargs):
        pass

    def _load_res_normal_table(self, conn, test_ID, bad_steps, data_points):
        self.logger.debug("starting loading raw-data")
        self.logger.debug(f"connection: {conn} test-ID: {test_ID}")
        self.logger.debug(f"bad steps:  {bad_steps}")

        table_name_normal = TABLE_NAMES["normal"]

        if prms.Reader["load_only_summary"]:  # SETTING
            warnings.warn("not implemented")

        if prms.Reader["select_minimal"]:  # SETTING
            columns = MINIMUM_SELECTION
            columns_txt = ", ".join(["%s"] * len(columns)) % tuple(columns)
        else:
            columns_txt = "*"

        sql_1 = "select %s " % columns_txt
        sql_2 = "from %s " % table_name_normal
        sql_3 = "where %s=%s " % (self.arbin_headers_normal.test_id_txt, test_ID)
        sql_4 = ""

        if bad_steps is not None:
            if not isinstance(bad_steps, (list, tuple)):
                bad_steps = [bad_steps]
            if not isinstance(bad_steps[0], (list, tuple)):
                bad_steps = [bad_steps]
            for bad_cycle, bad_step in bad_steps:
                self.logger.debug(f"bad_step def: [c={bad_cycle}, s={bad_step}]")
                sql_4 += "AND NOT (%s=%i " % (
                    self.arbin_headers_normal.cycle_index_txt,
                    bad_cycle,
                )
                sql_4 += "AND %s=%i) " % (
                    self.arbin_headers_normal.step_index_txt,
                    bad_step,
                )

        if prms.Reader["limit_loaded_cycles"]:
            if len(prms.Reader["limit_loaded_cycles"]) > 1:
                sql_4 += "AND %s>%i " % (
                    self.arbin_headers_normal.cycle_index_txt,
                    prms.Reader["limit_loaded_cycles"][0],
                )
                sql_4 += "AND %s<%i " % (
                    self.arbin_headers_normal.cycle_index_txt,
                    prms.Reader["limit_loaded_cycles"][-1],
                )
            else:
                sql_4 = "AND %s=%i " % (
                    self.arbin_headers_normal.cycle_index_txt,
                    prms.Reader["limit_loaded_cycles"][0],
                )

        if data_points is not None:
            d1, d2 = data_points
            if d1 is not None:
                sql_4 += "AND %s>=%i " % (self.arbin_headers_normal.data_point_txt, d1)
            if d2 is not None:
                sql_4 += "AND %s<=%i " % (self.arbin_headers_normal.data_point_txt, d2)

        sql_5 = "order by %s" % self.arbin_headers_normal.data_point_txt
        sql = sql_1 + sql_2 + sql_3 + sql_4 + sql_5

        self.logger.debug("INFO ABOUT LOAD RES NORMAL")
        self.logger.debug("sql statement: %s" % sql)

        if DEBUG_MODE:
            current_memory_usage = sys.getsizeof(self)

        if not prms.Instruments.Arbin.chunk_size:
            self.logger.debug("no chunk-size given")
            # memory here
            normal_df = pd.read_sql_query(sql, conn)
            # memory here
            length_of_test = normal_df.shape[0]
            self.logger.debug(f"loaded to normal_df (length =  {length_of_test})")
        else:
            self.logger.debug(f"chunk-size: {prms.Instruments.Arbin.chunk_size}")
            self.logger.debug("creating a pd.read_sql_query generator")
            normal_df_reader = pd.read_sql_query(
                sql, conn, chunksize=prms.Instruments.Arbin.chunk_size
            )
            normal_df = None
            chunk_number = 0
            self.logger.debug("created pandas sql reader")
            self.logger.debug("iterating chunk-wise")
            for i, chunk in enumerate(normal_df_reader):
                self.logger.debug(f"iteration number {i}")
                if prms.Instruments.Arbin.max_chunks:
                    self.logger.debug(
                        f"max number of chunks mode "
                        f"({prms.Instruments.Arbin.max_chunks})"
                    )
                    if chunk_number < prms.Instruments.Arbin.max_chunks:
                        normal_df = pd.concat([normal_df, chunk], ignore_index=True)
                        self.logger.debug(
                            f"chunk {i} of {prms.Instruments.Arbin.max_chunks}"
                        )
                    else:
                        break
                else:
                    try:
                        normal_df = pd.concat([normal_df, chunk], ignore_index=True)
                        self.logger.debug("concatenated new chunk")
                    except MemoryError:
                        self.logger.error(
                            " - Could not read complete file (MemoryError)."
                        )
                        self.logger.error(
                            f"Last successfully loaded chunk " f"number: {chunk_number}"
                        )
                        self.logger.error(
                            f"Chunk size: {prms.Instruments.Arbin.chunk_size}"
                        )
                        break
                chunk_number += 1
            length_of_test = normal_df.shape[0]
            self.logger.debug(f"finished iterating (#rows: {length_of_test})")
        return length_of_test, normal_df


if __name__ == "__main__":
    import logging
    from cellpy import log

    log.setup_logging(default_level="DEBUG")
