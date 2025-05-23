"""arbin res-type data files"""

import logging
import os
import pathlib
import platform
import shutil
import sys
import tempfile
import time
import warnings

import numpy as np
import pandas as pd
import sqlalchemy as sa

from cellpy import prms
from cellpy.exceptions import NullData
from cellpy.parameters.internal_settings import HeaderDict, get_headers_normal
from cellpy.readers.core import (
    Data,
    FileID,
    check64bit,
    humanize_bytes,
    xldate_as_datetime,
)
from cellpy.readers.instruments.base import MINIMUM_SELECTION, BaseLoader

# TODO: use InstrumentSettings (dataclass) from internal_settings instead of HeaderDict.

DEBUG_MODE = prms.Reader.diagnostics
ALLOW_MULTI_TEST_FILE = False
USE_SQLALCHEMY_ACCESS_ENGINE = True

# Select odbc module
ODBC = prms._odbc
SEARCH_FOR_ODBC_DRIVERS = prms._search_for_odbc_driver

_use_subprocess = prms.Instruments.Arbin.use_subprocess
_detect_subprocess_need = prms.Instruments.Arbin.detect_subprocess_need

_is_posix = False
_is_macos = False
if os.name == "posix":
    _is_posix = True
current_platform = platform.system()
if current_platform == "Darwin":
    _is_macos = True

if DEBUG_MODE:
    logging.debug("DEBUG_MODE")
    logging.debug(f"ODBC: {ODBC}")
    logging.debug(f"SEARCH_FOR_ODBC_DRIVERS: {SEARCH_FOR_ODBC_DRIVERS}")
    logging.debug(f"use_subprocess: {_use_subprocess}")
    logging.debug(f"detect_subprocess_need: {_detect_subprocess_need}")
    logging.debug(f"current_platform: {current_platform}")

if _detect_subprocess_need:
    logging.debug("detect_subprocess_need is True: checking versions")
    python_version, os_version = platform.architecture()
    if python_version == "64bit" and prms.Instruments.Arbin.office_version == "32bit":
        logging.debug("python 64bit and office 32bit -> " "setting use_subprocess to True")
        _use_subprocess = True

if _use_subprocess and not _is_posix:
    # The Windows users most likely have a strange custom path to mdbtools etc.
    logging.debug("using subprocess (most likely mdbtools) on non-posix (most likely windows)")
    if not prms.Instruments.Arbin.sub_process_path:
        _sub_process_path = str(prms.sub_process_path)
    else:
        _sub_process_path = str(prms.Instruments.Arbin.sub_process_path)

if _is_posix:
    _sub_process_path = "mdb-export"

try:
    driver_dll = prms.Instruments.Arbin.odbc_driver
except AttributeError:
    driver_dll = None

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


# Names of the tables in the .res db that is used by cellpy
TABLE_NAMES = {
    "normal": "Channel_Normal_Table",
    "global": "Global_Table",
    "statistic": "Channel_Statistic_Table",
    "aux_global": "Aux_Global_Data_Table",
    "aux": "Auxiliary_Table",
}

SUMMARY_HEADERS_RENAMING_DICT = {
    "test_id_txt": "Test_ID",
    "data_point_txt": "Data_Point",
    "vmax_on_cycle_txt": "Vmax_On_Cycle",
    "charge_time_txt": "Charge_Time",
    "discharge_time_txt": "Discharge_Time",
}

NORMAL_HEADERS_RENAMING_DICT = {
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


class DataLoader(BaseLoader):
    """Class for loading arbin-data from res-files.

    Parameters from configuration (`prms.Instruments.Arbin`)::

        - max_res_filesize: break if file size exceeds this limit.
        - chunk_size: size of chunks to load.
        - max_chunks: max number of chunks to load.
        - use_subprocess: use mdbtools or not.
        - detect_subprocess_need: detect if mdbtools is needed.
        - sub_process_path: path to mdbtools (or similar).
        - office_version: version of office (32 or 64 bit).

    """

    instrument_name = "arbin_res"
    raw_ext = "res"

    def __init__(self, *args, **kwargs):
        # could use __init__(self, cellpydata_object) and
        # set self.logger = cellpydata_object.logger etc.
        # then remember to include that as prm in "out of class" functions
        # self.prms = prms
        self.raw_ext = "res"
        self.logger = logging.getLogger(__name__)
        # use the following prm to limit to loading only
        # one cycle or from cycle>x to cycle<x+n
        # prms.Reader.limit_loaded_cycles = [cycle from, cycle to]

        self.arbin_headers_normal = self.get_headers_normal()  # the column headers defined by Arbin
        self.cellpy_headers_normal = get_headers_normal()  # the column headers defined by cellpy
        self.arbin_headers_global = self.get_headers_global()
        self.arbin_headers_aux_global = self.get_headers_aux_global()
        self.arbin_headers_aux = self.get_headers_aux()
        self.current_chunk = 0  # use this to set chunks to load

    @staticmethod
    def get_raw_units():
        raw_units = dict()
        raw_units["current"] = "A"
        raw_units["charge"] = "Ah"
        raw_units["mass"] = "g"
        raw_units["voltage"] = "V"
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
    def get_headers_aux():
        """Defines the so-called auxiliary table column headings for Arbin .res-files"""
        headers = HeaderDict()
        # - aux column headings (specific for Arbin)
        headers["test_id_txt"] = "Test_ID"
        headers["data_point_txt"] = "Data_Point"
        headers["aux_index_txt"] = "Auxiliary_Index"
        headers["data_type_txt"] = "Data_Type"
        headers["x_value_txt"] = "X"
        headers["x_dt_value"] = "dX_dt"
        return headers

    @staticmethod
    def get_headers_aux_global():
        """Defines the so-called auxiliary global column headings for Arbin .res-files"""
        headers = HeaderDict()
        # - aux global column headings (specific for Arbin)
        headers["channel_index_txt"] = "Channel_Index"
        headers["aux_index_txt"] = "Auxiliary_Index"
        headers["data_type_txt"] = "Data_Type"
        headers["aux_name_txt"] = "Nickname"
        headers["aux_unit_txt"] = "Unit"
        return headers

    @staticmethod
    def get_headers_global():
        """Defines the so-called global column headings for Arbin .res-files"""
        headers = HeaderDict()
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
        headers["schedule_file_name_txt"] = "Schedule_File_Name"  # KEEP FOR CELLPY FILE FORMAT
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
        """Returns a connection to the .res-file"""

        if dbloader is None:
            txt = f"{ODBC=}\n"
            txt += f"{SEARCH_FOR_ODBC_DRIVERS=}\n"
            txt += f"use_subprocess: {_use_subprocess}"
            txt += f"{_detect_subprocess_need=}\n"
            txt += f"{current_platform=}\n"
            raise ValueError(f"Something went seriously wrong." f"dbloader is None.\n{txt}")

        if SEARCH_FOR_ODBC_DRIVERS:
            logging.debug("Searching for odbc drivers")
            try:
                drivers = [driver for driver in dbloader.drivers() if "Microsoft Access Driver" in driver]
                logging.debug(f"Found these: {drivers}")
                driver = drivers[0]

            except AttributeError as e:
                print("ODBC drivers not found.")

            except IndexError as e:
                logging.debug("Unfortunately, it seems the list of drivers is emtpy.")
                logging.debug("Use driver-name from config (if existing).")
                driver = driver_dll
                if _is_macos:
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
                        print("Or install mdbtools and set it up " "(check the cellpy docs for help)")
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
            self.logger.debug(f"odbc constr: {driver}")

        constr = f"Driver={driver};Dbq={temp_filename};ExtendedAnsiSQL=1;"
        logging.debug(f"constr: {constr}")

        return constr

    def _get_connection_or_engine(self, temp_filename):
        # updated to use sqlalchemy - needs sqlalchemy-access
        constr = self._get_res_connector(temp_filename)
        self.logger.debug(f"constr str: {constr}")
        connection_url = sa.engine.URL.create("access+pyodbc", query={"odbc_connect": constr})
        engine = sa.create_engine(connection_url)
        return engine

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
                old_header = NORMAL_HEADERS_RENAMING_DICT[key]
                new_header = self.cellpy_headers_normal[key]
                columns[old_header] = new_header

            data.raw.rename(index=str, columns=columns, inplace=True)
            try:
                # TODO: check if summary df is existing (to only check if it is
                #  empty will give an error later!)
                columns = {}
                for key, old_header in SUMMARY_HEADERS_RENAMING_DICT.items():
                    try:
                        columns[old_header] = self.cellpy_headers_normal[key]
                    except KeyError:
                        columns[old_header] = old_header.lower()
                data.summary.rename(index=str, columns=columns, inplace=True)
            except Exception as e:
                txt = (
                    f"Exception raised ({e})\n"
                    f"key: {key} old_header: {old_header}"
                    f"cellpy headers normal type {type(self.cellpy_headers_normal)}"
                )
                raise Exception(txt)

        if fix_datetime:
            h_datetime = self.cellpy_headers_normal.datetime_txt
            logging.debug("converting to datetime format")
            # print(data.raw.columns)
            data.raw[h_datetime] = data.raw[h_datetime].apply(xldate_as_datetime, option="to_datetime")

            h_datetime = h_datetime
            if h_datetime in data.summary:
                data.summary[h_datetime] = data.summary[h_datetime].apply(xldate_as_datetime, option="to_datetime")

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
            new_cols = run_data.raw.columns
            for col in self.arbin_headers_normal:
                if col not in new_cols:
                    logging.debug(f"Missing col: {col}")
                    # data.raw[col] = np.nan
            return run_data

    def repair(self, file_name):
        """try to repair a broken/corrupted file"""
        raise NotImplemented

    def _query_table(self, table_name, conn, sql=None):
        from sqlalchemy import create_engine, text

        self.logger.debug(f"reading {table_name}")
        if sql is None:
            sql = f"select * from {table_name}"
        self.logger.debug(f"sql statement: {sql}")
        df = pd.read_sql_query(sql=sa.text(sql), con=conn.connect())
        return df

    def _make_name_from_frame(self, df, aux_index, data_type, dx_dt=False):
        df_names = df.loc[
            (df[self.arbin_headers_aux_global.aux_index_txt] == aux_index)
            & (df[self.arbin_headers_aux_global.data_type_txt] == data_type),
            :,
        ]
        unit = df_names[self.arbin_headers_aux_global.aux_unit_txt].values[0]
        nick = df_names[self.arbin_headers_aux_global.aux_name_txt].values[0] or aux_index
        if dx_dt:
            name = f"aux_d_{nick}_dt_u_d{unit}_dt"
        else:
            name = f"aux_{nick}_u_{unit}"
        return name

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
        conn = None

        table_name_global = TABLE_NAMES["global"]
        table_name_aux_global = TABLE_NAMES["aux_global"]
        table_name_aux = TABLE_NAMES["aux"]

        table_name_normal = TABLE_NAMES["normal"]

        if DEBUG_MODE:
            time_0 = time.time()

        conn = self._get_connection_or_engine(temp_filename)

        self.logger.debug("reading global data table")

        global_data_df = self._query_table(table_name=table_name_global, conn=conn)
        tests = global_data_df[self.arbin_headers_normal.test_id_txt]
        number_of_sets = len(tests)
        self.logger.debug(f"number of datasets: {number_of_sets}")

        if dataset_number is not None:
            self.logger.info(f"Dataset number given: {dataset_number}")
            self.logger.info(f"Available dataset numbers: {tests}")
            # check if dataset_number is valid
            #

        else:
            dataset_number = None

        data = self._init_data(file_name, global_data_df, dataset_number)
        self.logger.debug("reading raw-data")
        test_id = data._internal_test_number

        # --------- read stats-data (summary-data) ---------------------

        # --------- read raw-data (normal-data) ------------------------
        length_of_test, normal_df = self._load_res_normal_table(conn, test_id, bad_steps, data_points)
        # --------- read auxiliary data (aux-data) ---------------------
        normal_df = self._load_win_res_auxiliary_table(conn, normal_df, table_name_aux, table_name_aux_global, test_id)
        # FIX: error in order by since datetime is not accurate enough (also need sorting on test-time)
        #   sorting dataframe:
        normal_df = normal_df.sort_values(
            by=[
                self.arbin_headers_normal.datetime_txt,
                self.arbin_headers_normal.test_time_txt,
            ],
            ascending=True,
        )
        # TODO 216: add order by on test_time as well in sql query
        summary_df = self._load_res_summary_table(conn, test_id)
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
                f"memory usage for " f"loaded data: \n{mem_usage}" f"\ntotal: {humanize_bytes(mem_usage.sum())}"
            )
            logging.debug(f"time used: {(time.time() - time_0):2.4f} s")

        data.raw = normal_df
        data.raw_data_files_length.append(length_of_test)
        return data

    def _load_win_res_auxiliary_table(self, conn, normal_df, table_name_aux, table_name_aux_global, test_id):
        aux_global_data_df = self._query_table(table_name_aux_global, conn)
        if not aux_global_data_df.empty:
            aux_df = self._get_aux_df(conn, test_id, table_name_aux)
            aux_df, aux_global_data_df = self._aux_to_wide(aux_df, aux_global_data_df)
            aux_df = self._rename_aux_cols(aux_df, aux_global_data_df)

            if not aux_df.empty:
                normal_df = self._join_aux_to_normal(aux_df, normal_df)
        return normal_df

    def _load_posix_res_auxiliary_table(self, aux_global_data_df, aux_df, normal_df):
        if not aux_global_data_df.empty:
            aux_df, aux_global_data_df = self._aux_to_wide(aux_df, aux_global_data_df)
            aux_df = self._rename_aux_cols(aux_df, aux_global_data_df)

            if not aux_df.empty:
                normal_df = self._join_aux_to_normal(aux_df, normal_df)
        return normal_df

    def _join_aux_to_normal(self, aux_df, normal_df):
        # TODO: clean up setting index (Data_Point). This is currently done in _post_process after
        #    the column names are changed to cellpy-column names ("data_point").
        #    It also keeps a copy of the "data_point"
        #    column. And is that really necessary.
        normal_df.set_index(self.arbin_headers_normal.data_point_txt, inplace=True)
        normal_df = normal_df.join(aux_df, how="left")
        normal_df.reset_index(inplace=True)
        return normal_df

    def _rename_aux_cols(self, aux_df, aux_global_data_df):
        aux_dfs = []
        if self.arbin_headers_aux.x_value_txt in aux_df.columns:
            aux_df_x = aux_df[self.arbin_headers_aux.x_value_txt].copy()
            aux_df_x.columns = [self._make_name_from_frame(aux_global_data_df, z[1], z[0]) for z in aux_df_x.columns]
            aux_dfs.append(aux_df_x)
        if self.arbin_headers_aux.x_dt_value in aux_df.columns:
            aux_df_dx_dt = aux_df[self.arbin_headers_aux.x_dt_value].copy()
            aux_df_dx_dt.columns = [
                self._make_name_from_frame(aux_global_data_df, z[1], z[0], True) for z in aux_df_dx_dt.columns
            ]
            aux_dfs.append(aux_df_dx_dt)
        aux_df = pd.concat(aux_dfs, axis=1)
        return aux_df

    def _aux_to_wide(self, aux_df, aux_global_data_df):
        aux_df = aux_df.drop(self.arbin_headers_aux.test_id_txt, axis=1)
        keys = [
            self.arbin_headers_aux.data_point_txt,
            self.arbin_headers_aux.aux_index_txt,
            self.arbin_headers_aux.data_type_txt,
        ]
        aux_df = aux_df.set_index(keys=keys)
        aux_df = aux_df.unstack(2).unstack(1).dropna(axis=1)
        aux_global_data_df = aux_global_data_df.fillna(0)
        return aux_df, aux_global_data_df

    def _get_aux_df(self, conn, test_id, table_name_aux):
        columns_txt = "*"
        test_numbers = "(" + ",".join([str(tn) for tn in test_id]) + ")"
        sql_1 = "select %s " % columns_txt
        sql_2 = "from %s " % table_name_aux
        sql_3 = f"where {self.arbin_headers_normal.test_id_txt} in {test_numbers}"
        sql_4 = ""
        sql_aux = sql_1 + sql_2 + sql_3 + sql_4
        aux_df = self._query_table(table_name_aux, conn, sql=sql_aux)
        return aux_df

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
        # NOTE: this is the main loader for posix systems (macos and linux), but is also used for windows
        #       if the parameter use_subprocess is set to True (e.g. mdbtools' mdb-export.exe).
        # TODO: auxiliary channels (table)

        table_name_global = TABLE_NAMES["global"]
        table_name_stats = TABLE_NAMES["statistic"]
        table_name_normal = TABLE_NAMES["normal"]
        table_name_aux_global = TABLE_NAMES["aux_global"]
        table_name_aux = TABLE_NAMES["aux"]

        if _is_posix:
            if _is_macos:
                self.logger.debug("MAC OSX USING MDBTOOLS")
            else:
                self.logger.debug("POSIX USING MDBTOOLS")
        else:
            self.logger.debug("WINDOWS USING SUBPROCESS (probably mdb-export.exe)")

        if DEBUG_MODE:
            time_0 = time.time()

        (
            tmp_name_global,
            tmp_name_raw,
            tmp_name_stats,
            tmp_name_aux_global,
            tmp_name_aux,
        ) = self._create_tmp_files(
            table_name_global,
            table_name_normal,
            table_name_stats,
            table_name_aux_global,
            table_name_aux,
            temp_dir,
            temp_filename,
        )

        # use pandas to load in the data
        global_data_df = pd.read_csv(tmp_name_global)
        tests = global_data_df[self.arbin_headers_normal.test_id_txt]
        number_of_sets = len(tests)
        self.logger.debug("number of datasets: %i" % number_of_sets)

        if dataset_number is not None:
            self.logger.info(f"Dataset number given: {dataset_number}")
            self.logger.info(f"Available dataset numbers: {tests}")
        else:
            dataset_number = None

        data = self._init_data(file_name, global_data_df, dataset_number)

        self.logger.debug("reading raw-data")

        (
            length_of_test,
            normal_df,
            summary_df,
            aux_global_data_df,
            aux_df,
        ) = self._load_from_tmp_files(
            data,
            tmp_name_global,
            tmp_name_raw,
            tmp_name_stats,
            tmp_name_aux_global,
            tmp_name_aux,
            temp_filename,
            bad_steps,
            data_points,
        )

        # --------- read auxiliary data (aux-data) ---------------------
        normal_df = self._load_posix_res_auxiliary_table(aux_global_data_df, aux_df, normal_df)

        if summary_df.empty and prms.Reader.use_cellpy_stat_file:
            txt = "\nCould not find any summary (stats-file)!"
            txt += "\n -> issue make_summary(use_cellpy_stat_file=False)"
            logging.debug(txt)
        # normal_df = normal_df.set_index("Data_Point")

        data.summary = summary_df
        if DEBUG_MODE:
            mem_usage = normal_df.memory_usage()
            logging.debug(
                f"memory usage for " f"loaded data: \n{mem_usage}" f"\ntotal: {humanize_bytes(mem_usage.sum())}"
            )
            logging.debug(f"time used: {(time.time() - time_0):2.4f} s")

        data.raw = normal_df
        data.raw_data_files_length.append(length_of_test)
        return data

    def _check_size(self):
        file_size = os.path.getsize(self.temp_file_path)
        hfilesize = humanize_bytes(file_size)
        txt = f"File size: {file_size} ({hfilesize})"
        self.logger.debug(txt)
        if file_size > prms.Instruments.Arbin.max_res_filesize:
            error_message = "\nERROR (loader):\n"
            error_message += (
                f"{hfilesize} > {humanize_bytes(prms.Instruments.Arbin.max_res_filesize)} " f"- File is too big!\n"
            )
            error_message += "(edit prms.Instruments.Arbin ['max_res_filesize'])\n"
            logging.critical(error_message)
            return False
        return True

    def loader(
        self,
        name,
        *args,
        bad_steps=None,
        dataset_number=None,
        data_points=None,
        increment_cycle_index=True,
        **kwargs,
    ):
        """Loads data from arbin .res files.

        Args:
            name (str): path to .res file.
            bad_steps (list of tuples): (c, s) tuples of steps s (in cycle c)
                to skip loading.
            dataset_number (int): the data set number ('Test-ID') to select if you are dealing
                with arbin files with more than one data-set.
                Defaults to selecting all data-sets and merging them.
            data_points (tuple of ints): load only data from data_point[0] to
                    data_point[1] (use None for infinite).
            increment_cycle_index (bool): increment the cycle index if merging several datasets (default True).

        Returns:
            new data (Data)
        """
        # TODO: @jepe - insert kwargs - current chunk, only normal data, etc
        if dataset_number is not None:
            self.logger.info(f"Dataset number given: {dataset_number}")
            merge = False
        else:
            merge = True

        try:
            not_too_big = self._check_size()
            if not not_too_big:
                return None
        except Exception as e:
            self.logger.debug(f"could not get file size: {e}")

        use_mdbtools = False
        if _use_subprocess:
            use_mdbtools = True
        if _is_posix:
            use_mdbtools = True

        if use_mdbtools:
            new_data = self._loader_posix(
                self.name,
                self.temp_file_path,
                self.temp_file_path.parent,
                *args,
                bad_steps=bad_steps,
                dataset_number=dataset_number,
                data_points=data_points,
                **kwargs,
            )
        else:
            new_data = self._loader_win(
                self.name,
                self.temp_file_path,
                *args,
                bad_steps=bad_steps,
                dataset_number=dataset_number,
                data_points=data_points,
                **kwargs,
            )

        new_data = self._post_process(new_data)
        if merge:
            new_data = self._merge(new_data, increment_cycle_index=increment_cycle_index)

        new_data = self.identify_last_data_point(new_data)
        new_data = self._inspect(new_data)

        return new_data

    def _merge(self, data, increment_cycle_index=True):
        """Merge data from different data-sets (Test-ID) into one data-set."""
        test_ids = data._internal_test_number
        if len(test_ids) == 1:
            logging.debug("Only one data-set - no need to merge")
            return data
        if data.raw.empty:
            raise ValueError("No data to merge")

        logging.debug("Merging data (only the normal/raw data)")
        grouped = data.raw.groupby(self.cellpy_headers_normal.test_id_txt)
        groups = []
        last_data_point = 0
        last_test_time = 0.0
        last_cycle_index = 0
        for test_id, df in grouped:
            last = df.iloc[-1]
            df[self.cellpy_headers_normal.data_point_txt] += last_data_point
            df[self.cellpy_headers_normal.test_time_txt] += last_test_time
            if increment_cycle_index:
                df[self.cellpy_headers_normal.cycle_index_txt] += last_cycle_index
            last_data_point = last[self.cellpy_headers_normal.data_point_txt]
            last_test_time = last[self.cellpy_headers_normal.test_time_txt]
            last_cycle_index = last[self.cellpy_headers_normal.cycle_index_txt]
            groups.append(df)
        data.raw = pd.concat(groups, ignore_index=True)
        return data

    @staticmethod
    def _create_tmp_files(
        table_name_global,
        table_name_normal,
        table_name_stats,
        table_name_aux_global,
        table_name_aux,
        temp_dir,
        temp_filename,
    ):
        import subprocess

        # creating tmp-filenames
        temp_csv_filename_global = os.path.join(temp_dir, "global_tmp.csv")
        temp_csv_filename_normal = os.path.join(temp_dir, "normal_tmp.csv")
        temp_csv_filename_stats = os.path.join(temp_dir, "stats_tmp.csv")
        temp_csv_filename_aux_global = os.path.join(temp_dir, "aux_global_tmp.csv")
        temp_csv_filename_aux = os.path.join(temp_dir, "aux_tmp.csv")
        # making the cmds
        mdb_prms = [
            (table_name_global, temp_csv_filename_global),
            (table_name_normal, temp_csv_filename_normal),
            (table_name_stats, temp_csv_filename_stats),
            (table_name_aux_global, temp_csv_filename_aux_global),
            (table_name_aux, temp_csv_filename_aux),
        ]
        # executing cmds
        for table_name, tmp_file in mdb_prms:
            with open(tmp_file, "w") as f:
                try:
                    subprocess.call([_sub_process_path, temp_filename, table_name], stdout=f)
                    logging.debug(f"ran mdb-export {str(f)} {table_name}")
                except FileNotFoundError as e:
                    logging.critical(f"Could not run {_sub_process_path} on {temp_filename}")
                    logging.critical(f"Possible work-around: install mdbtools")
                    raise e
        return (
            temp_csv_filename_global,
            temp_csv_filename_normal,
            temp_csv_filename_stats,
            temp_csv_filename_aux_global,
            temp_csv_filename_aux,
        )

    def _load_from_tmp_files(
        self,
        data,
        temp_csv_filename_global,
        temp_csv_filename_normal,
        temp_csv_filename_stats,
        temp_csv_filename_aux_global,
        temp_csv_filename_aux,
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
        #   we load only chunks and only keep the parts that fulfill the
        #   filters (e.g. bad_steps, data_points,...)
        normal_df = pd.read_csv(temp_csv_filename_normal)
        # filter on test ID
        if data._internal_test_number is not None:
            normal_df = normal_df[normal_df[self.arbin_headers_normal.test_id_txt].isin(data._internal_test_number)]
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

                selector = (normal_df[self.arbin_headers_normal.cycle_index_txt] == bad_cycle) & (
                    normal_df[self.arbin_headers_normal.step_index_txt] == bad_step
                )

                normal_df = normal_df.loc[~selector, :]

        if prms.Reader.limit_loaded_cycles:
            logging.debug("Not yet tested for aux data")
            if len(prms.Reader.limit_loaded_cycles) > 1:
                c1, c2 = prms.Reader.limit_loaded_cycles
                selector = (normal_df[self.arbin_headers_normal.cycle_index_txt] > c1) & (
                    normal_df[self.arbin_headers_normal.cycle_index_txt] < c2
                )

            else:
                c1 = prms.Reader.limit_loaded_cycles[0]
                selector = normal_df[self.arbin_headers_normal.cycle_index_txt] == c1

            normal_df = normal_df.loc[selector, :]

        if data_points is not None:
            logging.debug("selecting data-point range")
            logging.debug("Not yet tested for aux data")
            d1, d2 = data_points

            if d1 is not None:
                selector = normal_df[self.arbin_headers_normal.data_point_txt] >= d1
                normal_df = normal_df.loc[selector, :]

            if d2 is not None:
                selector = normal_df[self.arbin_headers_normal.data_point_txt] <= d2
                normal_df = normal_df.loc[selector, :]

        length_of_test = normal_df.shape[0]
        summary_df = pd.read_csv(temp_csv_filename_stats)
        aux_global_df = pd.read_csv(temp_csv_filename_aux_global)
        aux_df = pd.read_csv(temp_csv_filename_aux)

        # clean up
        for f in [
            temp_filename,
            temp_csv_filename_stats,
            temp_csv_filename_normal,
            temp_csv_filename_global,
            temp_csv_filename_aux_global,
            temp_csv_filename_aux,
        ]:
            if os.path.isfile(f):
                try:
                    os.remove(f)
                except WindowsError as e:
                    logging.warning(f"could not remove tmp-file\n{f} {e}")
        return length_of_test, normal_df, summary_df, aux_global_df, aux_df

    def _init_data(self, file_name, global_data_df, test_no=None):
        data = Data()
        data.loaded_from = file_name
        self.generate_fid()
        # name of the .res file it is loaded from:
        # data.parent_filename = os.path.basename(file_name)

        if test_no is None:
            selected_global_data_df = global_data_df
            data._internal_test_number = selected_global_data_df[self.arbin_headers_global.test_id_txt].values
        else:
            if not isinstance(test_no, (tuple, list)):
                test_no = [test_no]

            selector = global_data_df[self.arbin_headers_global.test_id_txt].isin(test_no)
            selected_global_data_df = global_data_df.loc[selector, :]
            if selected_global_data_df.empty:
                raise NoDataFound(f"Could not find any test with test-ID(s) {test_no}")
            data._internal_test_number = test_no

        # only picking the first entry (assuming only one cell pr file and channel)
        data.channel_index = int(selected_global_data_df[self.arbin_headers_global.channel_index_txt].values[0])
        data.creator = selected_global_data_df[self.arbin_headers_global.creator_txt].values[0]
        data.test_ID = global_data_df[self.arbin_headers_global.item_id_txt].values[0]
        data.schedule_file_name = selected_global_data_df[self.arbin_headers_global.schedule_file_name_txt].values[0]
        # TODO: convert to datetime:
        data.start_datetime = selected_global_data_df[self.arbin_headers_global.start_datetime_txt].values[0]
        data.test_name = selected_global_data_df[self.arbin_headers_global.test_name_txt].values[0]

        data.raw_data_files.append(self.fid)
        return data

    def _normal_table_generator(self, **kwargs):
        pass

    def _load_res_summary_table(self, conn, test_ids):
        table_name_stats = TABLE_NAMES["statistic"]
        test_numbers = "(" + ",".join([str(tn) for tn in test_ids]) + ")"
        sql = (
            f"select * from {table_name_stats} "
            f"where {self.arbin_headers_normal.test_id_txt} in {test_numbers} "
            f"order by {self.arbin_headers_normal.test_id_txt}, {self.arbin_headers_normal.data_point_txt}"
        )
        summary_df = self._query_table(table_name_stats, conn, sql=sql)
        return summary_df

    def _load_res_normal_table(self, conn, test_ids, bad_steps, data_points):
        self.logger.debug("starting loading raw-data")
        self.logger.debug(f"connection: {conn} internal test-ID: {test_ids}")
        self.logger.debug(f"bad steps:  {bad_steps}")

        table_name_normal = TABLE_NAMES["normal"]

        if prms.Reader.select_minimal:  # SETTING
            columns = MINIMUM_SELECTION
            columns_txt = ", ".join(["%s"] * len(columns)) % tuple(columns)
        else:
            columns_txt = "*"

        sql_1 = f"select {columns_txt} "
        sql_2 = f"from {table_name_normal} "
        test_numbers = "(" + ",".join([str(tn) for tn in test_ids]) + ")"
        sql_3 = f"where {self.arbin_headers_normal.test_id_txt} in {test_numbers}"
        sql_4 = " "

        if bad_steps is not None:
            if not isinstance(bad_steps, (list, tuple)):
                bad_steps = [bad_steps]
            if not isinstance(bad_steps[0], (list, tuple)):
                bad_steps = [bad_steps]
            for bad_cycle, bad_step in bad_steps:
                self.logger.debug(f"bad_step def: [c={bad_cycle}, s={bad_step}]")
                sql_4 += f"AND NOT ({self.arbin_headers_normal.cycle_index_txt}={bad_cycle} "
                sql_4 += f"AND {self.arbin_headers_normal.step_index_txt}={bad_step}) "

        if prms.Reader.limit_loaded_cycles:
            if len(prms.Reader.limit_loaded_cycles) > 1:
                sql_4 += "AND %s>%i " % (
                    self.arbin_headers_normal.cycle_index_txt,
                    prms.Reader.limit_loaded_cycles[0],
                )
                sql_4 += "AND %s<%i " % (
                    self.arbin_headers_normal.cycle_index_txt,
                    prms.Reader.limit_loaded_cycles[-1],
                )
            else:
                sql_4 = "AND %s=%i " % (
                    self.arbin_headers_normal.cycle_index_txt,
                    prms.Reader.limit_loaded_cycles[0],
                )

        if data_points is not None:
            d1, d2 = data_points
            if d1 is not None:
                sql_4 += "AND %s>=%i " % (self.arbin_headers_normal.data_point_txt, d1)
            if d2 is not None:
                sql_4 += "AND %s<=%i " % (self.arbin_headers_normal.data_point_txt, d2)

        sql_5 = f"order by {self.arbin_headers_normal.datetime_txt}"
        sql = sql_1 + sql_2 + sql_3 + sql_4 + sql_5

        self.logger.debug("INFO ABOUT LOAD RES NORMAL")
        self.logger.debug("sql statement: %s" % sql)

        if DEBUG_MODE:
            current_memory_usage = sys.getsizeof(self)
            self.logger.debug(f"current memory usage: {current_memory_usage}")

        if not prms.Instruments.Arbin.chunk_size:
            self.logger.debug("no chunk-size given")
            # memory here
            normal_df = pd.read_sql_query(sql=sa.text(sql), con=conn.connect())
            # memory here
            length_of_test = normal_df.shape[0]
        else:
            self.logger.debug(f"chunk-size: {prms.Instruments.Arbin.chunk_size}")
            self.logger.debug("creating a pd.read_sql_query generator")

            normal_df_reader = pd.read_sql_query(
                sql=sa.text(sql),
                con=conn.connect(),
                chunksize=prms.Instruments.Arbin.chunk_size,
            )
            normal_df = None
            chunk_number = 0
            self.logger.debug("created pandas sql reader")
            self.logger.debug("iterating chunk-wise")
            for i, chunk in enumerate(normal_df_reader):
                self.logger.debug(f"iteration number {i}")
                if prms.Instruments.Arbin.max_chunks:
                    self.logger.debug(f"max number of chunks mode " f"({prms.Instruments.Arbin.max_chunks})")
                    if chunk_number < prms.Instruments.Arbin.max_chunks:
                        normal_df = pd.concat([normal_df, chunk], ignore_index=True)
                        self.logger.debug(f"chunk {i} of {prms.Instruments.Arbin.max_chunks}")
                    else:
                        break
                else:
                    try:
                        normal_df = pd.concat([normal_df, chunk], ignore_index=True)
                        self.logger.debug("concatenated new chunk")
                    except MemoryError:
                        self.logger.error(" - Could not read complete file (MemoryError).")
                        self.logger.error(f"Last successfully loaded chunk " f"number: {chunk_number}")
                        self.logger.error(f"Chunk size: {prms.Instruments.Arbin.chunk_size}")
                        break
                chunk_number += 1
            length_of_test = normal_df.shape[0]
            self.logger.debug(f"finished iterating (#rows: {length_of_test})")

        self.logger.debug(f"loaded to normal_df (length =  {length_of_test})")
        self.logger.debug(f"Headers:\n{normal_df.columns}")
        if normal_df is None:
            default_headers = [v for v in self.arbin_headers_normal.values()]
            normal_df = pd.DataFrame(columns=default_headers)
        return length_of_test, normal_df


def _check_loader_aux():
    from pathlib import Path

    from cellpy import log

    log.setup_logging(default_level="CRITICAL")
    p = Path(r"C:\scripts\cellpy_dev_resources\2020_jinpeng_aux_temperature")
    f1 = p / "BIT_LFP5p12s_Pack02_CAP_Cyc200_T25_Nov23.res"
    f2 = p / "BIT_LFP50_12S1P_SOP_0_97_T5_cyc200_3500W_20191231.res"
    f3 = p / "TJP_LR1865SZ_OCV_19_Cyc150_T25_201105.res"

    n = DataLoader().loader(f1)
    print(n[0].raw.tail())


def _check_loader_empty_normal():
    from cellpy import log

    log.setup_logging(default_level="CRITICAL")

    a = DataLoader()
    cols = a.arbin_headers_normal
    df = pd.DataFrame(columns=cols.values())
    print(df)
    print(df.empty)


def _check_multi():
    import pathlib
    import cellpy

    f = r"C:\scripting\cellpy_dev_resources\dev_data\arbin_multi\20230531_NG27_02_cc_01.res"
    out = r"C:\scripting\cellpy_dev_resources\dev_data\arbin_multi\20230531_NG27_02_cc_01.xlsx"
    p = pathlib.Path(f)
    c = cellpy.get(p)
    c.to_excel(out, raw=True)


def _noodle():
    import pandas as pd

    df = pd.DataFrame(
        {
            "a": [1, 2, 3, 4, 5],
            "b": [1, 2, 3, 4, 5],
            "c": [1, 1, 1, 1, 2],
        }
    )
    print(df)

    df2 = df[df["c"].isin([1])]
    print(" new ".center(80, "-"))
    print(df2)


if __name__ == "__main__":
    print(" arbin-res-py ".center(80, "="))
    _noodle()
    print(" finished ".center(80, "="))
