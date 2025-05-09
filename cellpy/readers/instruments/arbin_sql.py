"""arbin MS SQL Server data"""
import datetime
import logging
import os
import platform
import shutil
import sys
import tempfile
import time
import warnings

import numpy as np
import pandas as pd
import pyodbc
from dateutil.parser import parse

from cellpy import prms
from cellpy.parameters.internal_settings import HeaderDict, get_headers_normal
from cellpy.readers.core import (
    Data,
    FileID,
    check64bit,
    humanize_bytes,
    xldate_as_datetime,
)
from cellpy.readers.instruments.base import BaseLoader

# TODO: @muhammad - get more meta data from the SQL db
# TODO: @jepe - update the batch functionality (including filefinder)
# TODO: @muhammad - make routine for "setting up the SQL Server" so that it is accessible and document it

DEBUG_MODE = prms.Reader.diagnostics  # not used
ALLOW_MULTI_TEST_FILE = prms._allow_multi_test_file  # not used
ODBC = prms._odbc
SEARCH_FOR_ODBC_DRIVERS = prms._search_for_odbc_driver  # not used
SQL_SERVER = prms.Instruments.Arbin["SQL_server"]
SQL_UID = prms.Instruments.Arbin["SQL_UID"]
SQL_PWD = prms.Instruments.Arbin["SQL_PWD"]
SQL_DRIVER = prms.Instruments.Arbin["SQL_Driver"]
DATE_TIME_FORMAT = prms._date_time_format

# Names of the tables in the SQL Server db that is used by cellpy

# Not used anymore - maybe use a similar dict for the SQL table names (they are hard-coded at the moment)
TABLE_NAMES = {
    "normal": "Channel_Normal_Table",
    "global": "Global_Table",
    "statistic": "Channel_Statistic_Table",
    "aux_global": "Aux_Global_Data_Table",
    "aux": "Auxiliary_Table",
}

# Contains several headers not encountered yet in the Arbin SQL Server tables
summary_headers_renaming_dict = {
    "test_id_txt": "Test_ID",
    "data_point_txt": "Data_Point",
    "vmax_on_cycle_txt": "Vmax_On_Cycle",
    "charge_time_txt": "Charge_Time",
    "discharge_time_txt": "Discharge_Time",
}

# Contains several headers not encountered yet in the Arbin SQL Server tables
normal_headers_renaming_dict = {
    "aci_phase_angle_txt": "ACI_Phase_Angle",
    "ref_aci_phase_angle_txt": "Reference_ACI_Phase_Angle",
    "ac_impedance_txt": "AC_Impedance",
    "ref_ac_impedance_txt": "Reference_AC_Impedance",
    "charge_capacity_txt": "Charge_Capacity",
    "charge_energy_txt": "Charge_Energy",
    "current_txt": "Current",
    "cycle_index_txt": "Cycle_ID",
    "data_point_txt": "Data_Point",
    "datetime_txt": "Date_Time",
    "discharge_capacity_txt": "Discharge_Capacity",
    "discharge_energy_txt": "Discharge_Energy",
    "internal_resistance_txt": "Internal_Resistance",
    "is_fc_data_txt": "Is_FC_Data",
    "step_index_txt": "Step_ID",
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
    "channel_id_txt": "Channel_ID",  # new Arbin SQL Server
    "data_flag_txt": "Data_Flags",  # new Arbin SQL Server
    "test_name_txt": "Test_Name",  # new Arbin SQL Server
}


# Arbin SQL Server table headers (for both data df and stats df)
# --------------------------------------------------------------
# Test_ID
# Channel_ID
# Date_Time
# Data_Point
# Test_Time
# Step_Time
# Cycle_ID
# Step_ID
# Current
# Voltage
# Charge_Capacity
# Discharge_Capacity
# Charge_Energy
# Discharge_Energy
# Data_Flags
# Test_Name
# (all these headers are now implemented in the internal_settings


def from_arbin_to_datetime(n):
    if isinstance(n, int):
        n = str(n)
    ms_component = n[-7:]
    date_time_component = n[:-7]
    temp = f"{date_time_component}.{ms_component}"
    datetime_object = datetime.datetime.fromtimestamp(float(temp))
    time_in_str = datetime_object.strftime(DATE_TIME_FORMAT)
    return time_in_str


class DataLoader(BaseLoader):
    """Class for loading arbin-data from MS SQL server."""

    instrument_name = "arbin_sql"
    _is_db = True

    def __init__(self, *args, **kwargs):
        """initiates the ArbinSQLLoader class"""
        self.arbin_headers_normal = (
            get_headers_normal()
        )  # the column headers defined by Arbin
        self.cellpy_headers_normal = (
            get_headers_normal()
        )  # the column headers defined by cellpy
        self.arbin_headers_global = self.get_headers_global()
        self.arbin_headers_aux_global = self.get_headers_aux_global()
        self.arbin_headers_aux = self.get_headers_aux()
        self.current_chunk = 0  # use this to set chunks to load
        self.server = SQL_SERVER

    @staticmethod
    def get_headers_normal():
        """Defines the so-called normal column headings for Arbin SQL Server"""
        # covered by cellpy at the moment
        return get_headers_normal()

    @staticmethod
    def get_headers_aux():
        """Defines the so-called auxiliary table column headings for Arbin SQL Server"""
        # not in use (yet)
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
        """Defines the so-called auxiliary global column headings for Arbin SQL Server"""
        # not in use yet
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
        """Defines the so-called global column headings for Arbin SQL Server"""
        # not in use yet
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
        headers[
            "schedule_file_name_txt"
        ] = "Schedule_File_Name"  # KEEP FOR CELLPY FILE FORMAT
        headers["start_datetime_txt"] = "Start_DateTime"
        headers["test_id_txt"] = "Test_ID"  # KEEP FOR CELLPY FILE FORMAT
        headers["test_name_txt"] = "Test_Name"  # KEEP FOR CELLPY FILE FORMAT
        return headers

    @staticmethod
    def get_raw_units():
        raw_units = dict()
        raw_units["current"] = "A"
        raw_units["charge"] = "Ah"
        raw_units["mass"] = "g"
        raw_units["voltage"] = "V"
        return raw_units

    @staticmethod
    def get_raw_limits():
        """returns a dictionary with resolution limits"""
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

    # TODO: rename this (for all instruments) to e.g. load
    # TODO: implement more options (bad_cycles, ...)
    def loader(self, name, **kwargs):
        """returns a Data object with loaded data.

        Loads data from arbin SQL server db.

        Args:
            name (str): name of the test

        Returns:
            new_tests (list of data objects)
        """
        # self.name = name
        self.is_db = True
        data_df, stat_df = self._query_sql(self.name)
        aux_data_df = None  # Needs to be implemented
        meta_data = None  # Should be implemented

        # init data

        # selecting only one value (might implement multi-channel/id use later)
        test_id = data_df["Test_ID"].iloc[0]
        id_name = f"{SQL_SERVER}:{name}:{test_id}"

        channel_id = data_df["Channel_ID"].iloc[0]

        data = Data()
        data.loaded_from = id_name
        data.channel_index = channel_id
        data.test_ID = test_id
        data.test_name = name

        # The following metadata is not implemented yet for SQL loader:
        data.creator = None
        data.schedule_file_name = None
        data.start_datetime = None  # REMARK! convert to datetime when implementing

        # Generating a FileID project:
        self.generate_fid()
        data.raw_data_files.append(self.fid)

        data.raw = data_df
        data.raw_data_files_length.append(len(data_df))
        data.summary = stat_df
        data = self._post_process(data)
        data = self.identify_last_data_point(data)

        return data

    def _post_process(self, data, **kwargs):
        # TODO: move this to parent

        fix_datetime = kwargs.pop("fix_datetime", True)
        set_index = kwargs.pop("set_index", True)
        rename_headers = kwargs.pop("rename_headers", True)
        extract_start_datetime = kwargs.pop("extract_start_datetime", True)
        set_dtypes = kwargs.pop("set_dtypes", True)

        # TODO:  insert post-processing and div tests here
        #    - check dtypes

        # Remark that we also set index during saving the file to hdf5 if
        #   it is not set.
        from pprint import pprint

        if rename_headers:
            columns = {}
            for key in self.arbin_headers_normal:
                old_header = normal_headers_renaming_dict.get(key, None)
                new_header = self.cellpy_headers_normal[key]
                if old_header:
                    columns[old_header] = new_header
                logging.debug(
                    f"processing cellpy normal header key '{key}':"
                    f" old_header='{old_header}' -> new_header='{new_header}'"
                )
            logging.debug(f"renaming dict: {columns}")
            data.raw.rename(index=str, columns=columns, inplace=True)
            try:
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
            data.raw[h_datetime] = data.raw[h_datetime].apply(from_arbin_to_datetime)

            if h_datetime in data.summary:
                data.summary[h_datetime] = data.summary[h_datetime].apply(
                    from_arbin_to_datetime
                )

        if set_index:
            hdr_data_point = self.cellpy_headers_normal.data_point_txt
            if data.raw.index.name != hdr_data_point:
                data.raw = data.raw.set_index(hdr_data_point, drop=False)

        if extract_start_datetime:
            hdr_date_time = self.arbin_headers_normal.datetime_txt
            data.start_datetime = parse(data.raw[hdr_date_time].iat[0][:-7])

        if set_dtypes:
            logging.debug("setting data types")
            # test_time_txt = self.cellpy_headers_normal.test_time_txt
            # step_time_txt = self.cellpy_headers_normal.step_time_txt
            date_time_txt = self.cellpy_headers_normal.datetime_txt
            logging.debug("converting to datetime format")
            try:
                # data.raw[test_time_txt] = pd.to_timedelta(data.raw[test_time_txt])  # cellpy is not ready for this
                # data.raw[step_time_txt] = pd.to_timedelta(data.raw[step_time_txt])  # cellpy is not ready for this
                data.raw[date_time_txt] = pd.to_datetime(
                    data.raw[date_time_txt], format=DATE_TIME_FORMAT
                )
            except ValueError:
                logging.debug("could not convert to datetime format")

        return data

    def _query_sql(self, name):
        # TODO: refactor and include optional SQL arguments
        name_str = f"('{name}', '')"
        con_str = (
            f"Driver={{{SQL_DRIVER}}};" + f"Server={SQL_SERVER};Trusted_Connection=yes;"
        )

        # TODO: use variable for the name of the main db (ArbinPro8....)
        # TODO: consider making a function that searches for correct ArbinPro version
        master_q = (
            "SELECT Database_Name, Test_Name FROM "
            "ArbinPro8MasterInfo.dbo.TestList_Table WHERE "
            f"ArbinPro8MasterInfo.dbo.TestList_Table.Test_Name IN {name_str}"
        )

        conn = pyodbc.connect(con_str)
        sql_query = pd.read_sql_query(master_q, conn)

        datas_df = []
        stats_df = []

        for index, row in sql_query.iterrows():
            # TODO: use variables - see above
            # TODO: consider to use f-strings
            data_query = (
                "SELECT "
                + str(row["Database_Name"])
                + ".dbo.IV_Basic_Table.*, ArbinPro8MasterInfo.dbo.TestList_Table.Test_Name "
                "FROM " + str(row["Database_Name"]) + ".dbo.IV_Basic_Table "
                "JOIN ArbinPro8MasterInfo.dbo.TestList_Table "
                "ON "
                + str(row["Database_Name"])
                + ".dbo.IV_Basic_Table.Test_ID = ArbinPro8MasterInfo.dbo.TestList_Table.Test_ID "
                "WHERE ArbinPro8MasterInfo.dbo.TestList_Table.Test_Name IN "
                + str(name_str)
            )

            stat_query = (
                "SELECT "
                + str(row["Database_Name"])
                + ".dbo.StatisticData_Table.*, ArbinPro8MasterInfo.dbo.TestList_Table.Test_Name "
                "FROM " + str(row["Database_Name"]) + ".dbo.StatisticData_Table "
                "JOIN ArbinPro8MasterInfo.dbo.TestList_Table "
                "ON "
                + str(row["Database_Name"])
                + ".dbo.StatisticData_Table.Test_ID = ArbinPro8MasterInfo.dbo.TestList_Table.Test_ID "
                "WHERE ArbinPro8MasterInfo.dbo.TestList_Table.Test_Name IN "
                + str(name_str)
            )

            datas_df.append(pd.read_sql_query(data_query, conn))
            stats_df.append(pd.read_sql_query(stat_query, conn))

        data_df = pd.concat(datas_df, axis=0)
        stat_df = pd.concat(stats_df, axis=0)

        return data_df, stat_df


def _check_sql_loader(server: str = None, tests: list = None):
    test_name = tuple(tests) + ("",)  # neat trick :-)
    print(f"** test str: {test_name}")
    con_str = "Driver={SQL Server};Server=" + server + ";Trusted_Connection=yes;"
    master_q = (
        "SELECT Database_Name, Test_Name FROM "
        "ArbinPro8MasterInfo.dbo.TestList_Table WHERE "
        f"ArbinPro8MasterInfo.dbo.TestList_Table.Test_Name IN {test_name}"
    )

    conn = pyodbc.connect(con_str)
    print("** connected to server")
    sql_query = pd.read_sql_query(master_q, conn)
    print("** SQL query:")
    print(sql_query)
    for index, row in sql_query.iterrows():
        # Muhammad, why is it a loop here?
        print(f"** index: {index}")
        print(f"** row: {row}")
        data_query = (
            "SELECT "
            + str(row["Database_Name"])
            + ".dbo.IV_Basic_Table.*, ArbinPro8MasterInfo.dbo.TestList_Table.Test_Name "
            "FROM " + str(row["Database_Name"]) + ".dbo.IV_Basic_Table "
            "JOIN ArbinPro8MasterInfo.dbo.TestList_Table "
            "ON "
            + str(row["Database_Name"])
            + ".dbo.IV_Basic_Table.Test_ID = ArbinPro8MasterInfo.dbo.TestList_Table.Test_ID "
            "WHERE ArbinPro8MasterInfo.dbo.TestList_Table.Test_Name IN "
            + str(test_name)
        )

        stat_query = (
            "SELECT "
            + str(row["Database_Name"])
            + ".dbo.StatisticData_Table.*, ArbinPro8MasterInfo.dbo.TestList_Table.Test_Name "
            "FROM " + str(row["Database_Name"]) + ".dbo.StatisticData_Table "
            "JOIN ArbinPro8MasterInfo.dbo.TestList_Table "
            "ON "
            + str(row["Database_Name"])
            + ".dbo.StatisticData_Table.Test_ID = ArbinPro8MasterInfo.dbo.TestList_Table.Test_ID "
            "WHERE ArbinPro8MasterInfo.dbo.TestList_Table.Test_Name IN "
            + str(test_name)
        )
        print(f"** data query: {data_query}")
        print(f"** stat query: {stat_query}")

        # if looping, maybe these should be concatenated?
        data_df = pd.read_sql_query(data_query, conn)
        stat_df = pd.read_sql_query(stat_query, conn)

    return data_df, stat_df


def _check_query():
    import pathlib

    name = ["20201106_HC03B1W_1_cc_01"]
    dd, ds = check_sql_loader(SQL_SERVER, name)
    out = pathlib.Path(r"C:\scripts\notebooks\Div")
    input("x")


def _check_loader():
    print(" Testing connection to arbin sql server ".center(80, "-"))

    sql_loader = DataLoader()
    name = "20201106_HC03B1W_1_cc_01"
    cell = sql_loader.loader(name)

    return cell


def _check_loader_from_outside():
    import matplotlib.pyplot as plt

    from cellpy import cellreader

    name = "20200820_CoFBAT_slurry07B_01_cc_01"
    c = cellreader.CellpyCell()
    c.set_instrument("arbin_sql")
    # print(c)
    c.from_raw(name)
    # print(c)
    c.make_step_table()
    c.make_summary()
    # print(c)
    raw = c.data.raw
    steps = c.data.steps
    summary = c.data.summary
    raw.to_csv(r"C:\scripting\trash\raw.csv", sep=";")
    steps.to_csv(r"C:\scripting\trash\steps.csv", sep=";")
    summary.to_csv(r"C:\scripting\trash\summary.csv", sep=";")

    n = c.get_number_of_cycles()
    print(f"number of cycles: {n}")

    cycle = c.get_cap(1, method="forth")
    print(cycle.head())
    cycle.plot(x="capacity", y="voltage")
    plt.show()


def _check_get():
    import cellpy

    name = "20200820_CoFBAT_slurry07B_01_cc_01"
    c = cellpy.get(name, instrument="arbin_sql")
    print(c)


if __name__ == "__main__":
    # test_query()
    # cell = test_loader()
    _check_get()
