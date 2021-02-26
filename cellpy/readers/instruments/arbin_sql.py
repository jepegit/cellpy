"""arbin MS SQL Server data"""
import os
import sys
import tempfile
import shutil
import logging
import platform
import warnings
import time
import numpy as np
import pyodbc
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
ALLOW_MULTI_TEST_FILE = prms._allow_multi_test_file
ODBC = prms._odbc
SEARCH_FOR_ODBC_DRIVERS = prms._search_for_odbc_driver


class ArbinSQLLoader(Loader):
    """ Class for loading arbin-data from MS SQL server."""

    def __init__(self):
        """initiates the ArbinSQLLoader class"""

        pass

    def get_raw_units(self):
        """returns a dictionary with unit fractions"""

        raise NotImplemented

    def get_raw_limits(self):
        """returns a dictionary with resolution limits"""

        raise NotImplemented

    def loader(self, file_name):
        """returns a Cell object with loaded data"""

        raise NotImplemented


def test_sql_loader(server: str = None, tests: list = None):
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


if __name__ == "__main__":
    print(" Testing connection to arbin sql server ".center(80, "-"))
    # Made a copy of the db on my local machine
    # remark! used SQL Server Management Studio to restore
    #    the backup, not sure how to connect directly to the backup-files
    server = r"localhost\SQLEXPRESS"
    data_df, stat_df = test_sql_loader(server, ["20201106_HC03B1W_1_cc_01"])
    print(" db loaded and returned as pandas DataFrames ".center(80, "-"))
    print("DATA:")
    print(data_df.columns)
    print(data_df.head())
    print("STATS:")
    print(stat_df.columns)
    print(stat_df.head())
    print(" -OK- ")
