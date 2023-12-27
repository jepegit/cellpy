"""arbin MS SQL Server exported h5 data"""
import datetime
import logging
import pathlib
import sys
import warnings

import pandas as pd
from dateutil.parser import parse

from cellpy import prms
from cellpy.exceptions import WrongFileVersion
from cellpy.parameters.internal_settings import HeaderDict, get_headers_normal
from cellpy.readers.core import Data, FileID
from cellpy.readers.instruments.base import BaseLoader
from pathlib import Path

DEBUG_MODE = prms.Reader.diagnostics  # not used
ALLOW_MULTI_TEST_FILE = prms._allow_multi_test_file  # not used
DATE_TIME_FORMAT = prms._date_time_format  # not used

normal_headers_renaming_dict = {
    "test_id_txt": "Test_ID",
    "data_point_txt": "Data_Point",
    "datetime_txt": "Date_Time",
    "test_time_txt": "Test_Time",
    "step_time_txt": "Step_Time",
    "cycle_index_txt": "Cycle_Index",
    "step_index_txt": "Step_Index",
    "current_txt": "Current",
    "voltage_txt": "Voltage",
    "power_txt": "Power",
    "charge_capacity_txt": "Charge_Capacity",
    "discharge_capacity_txt": "Discharge_Capacity",
    "charge_energy_txt": "Charge_Energy",
    "discharge_energy_txt": "Discharge_Energy",
    "internal_resistance_txt": "Internal_Resistance",
    "ref_voltage_txt": "Aux_Voltage_1",
}


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

    instrument_name = "arbin_sql_h5"
    raw_ext = "h5"

    def __init__(self, *args, **kwargs):
        """initiates the ArbinSQLLoader class"""
        self.arbin_headers_normal = (
            self.get_headers_normal()
        )  # the column headers defined by Arbin
        self.cellpy_headers_normal = (
            get_headers_normal()
        )  # the column headers defined by cellpy

    @staticmethod
    def get_headers_normal():
        """Defines the so-called normal column headings for Arbin SQL Server h5 export"""
        # covered by cellpy at the moment
        return get_headers_normal()

    @staticmethod
    def get_headers_aux(df):
        """Defines the so-called auxiliary table column headings for Arbin SQL Server h5 export"""
        headers = HeaderDict()
        for col in df.columns:
            if col.startswith("Aux_"):
                ncol = col.replace("/", "_")
                ncol = "".join(ncol.split("(")[0])
                headers[col] = ncol.lower()

        return headers

    @staticmethod
    def get_raw_units():
        raw_units = dict()
        raw_units["current"] = "A"
        raw_units["charge"] = "Ah"
        raw_units["mass"] = "g"
        raw_units["voltage"] = "V"
        raw_units["nominal_capacity"] = "Ah/g"
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

        Loads data from arbin SQL server h5 export.

        Args:
            name (str): name of the file

        Returns:
            data object
        """
        # self.name = name
        # self.copy_to_temporary()
        data_dfs = self._parse_h5_data()
        data = Data()

        # some metadata is available in the info_df part of the h5 file
        data.loaded_from = self.name
        data.channel_index = data_dfs["info_df"]["IV_Ch_ID"].iloc[0]
        data.test_ID = data_dfs["info_df"]["Test_ID"].iloc[0]
        data.test_name = self.name.name
        data.creator = None
        data.schedule_file_name = data_dfs["info_df"]["Schedule_File_Name"].iloc[0]
        # TODO: convert to datetime (note that this seems to be set also in the postprocessing)
        data.start_datetime = data_dfs["info_df"]["First_Start_DateTime"].iloc[0]
        data.mass = data_dfs["info_df"]["SpecificMASS"].iloc[0]
        data.nom_cap = data_dfs["info_df"]["SpecificCapacity"].iloc[0]

        # Generating a FileID project:
        self.generate_fid()
        data.raw_data_files.append(self.fid)

        data.raw = data_dfs["data_df"]
        data.raw_data_files_length.append(len(data_dfs["data_df"]))
        data.summary = (
            pd.DataFrame()
        )  # creating an empty frame - loading summary is not implemented yet
        data = self._post_process(data)
        data = self.identify_last_data_point(data)
        return data

    def _post_process(self, data):
        set_index = True
        rename_headers = True
        forward_fill_ir = True
        backward_fill_ir = True
        fix_datetime = True
        set_dtypes = True
        fix_duplicated_rows = True
        recalc_capacity = False

        if fix_duplicated_rows:
            data.raw = data.raw.drop_duplicates()

        if rename_headers:
            columns = {}
            for key in normal_headers_renaming_dict:
                old_header = normal_headers_renaming_dict[key]
                new_header = self.cellpy_headers_normal[key]
                columns[old_header] = new_header

            data.raw.rename(index=str, columns=columns, inplace=True)
            new_aux_headers = self.get_headers_aux(data.raw)
            data.raw.rename(index=str, columns=new_aux_headers, inplace=True)

        if fix_datetime:
            h_datetime = self.cellpy_headers_normal.datetime_txt
            data.raw[h_datetime] = data.raw[h_datetime].apply(from_arbin_to_datetime)
            if h_datetime in data.summary:
                data.summary[h_datetime] = data.summary[h_datetime].apply(
                    from_arbin_to_datetime
                )

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

        if set_index:
            hdr_data_point = self.cellpy_headers_normal.data_point_txt
            if data.raw.index.name != hdr_data_point:
                data.raw = data.raw.set_index(
                    hdr_data_point, drop=False
                )  # TODO: check if this is standard

        if forward_fill_ir:
            logging.debug("forward filling ir")
            hdr_ir = self.cellpy_headers_normal.internal_resistance_txt
            data.raw[hdr_ir] = data.raw[hdr_ir].fillna(method="ffill")

        if backward_fill_ir:
            logging.debug("forward filling ir")
            hdr_ir = self.cellpy_headers_normal.internal_resistance_txt
            data.raw[hdr_ir] = data.raw[hdr_ir].fillna(method="bfill")

        if recalc_capacity:
            print("Not implemented yet - do it yourself")
            print("recalculating capacity: cap = current * time")

        hdr_date_time = self.arbin_headers_normal.datetime_txt
        start = data.raw[hdr_date_time].iat[0]
        # TODO: convert to datetime:
        data.start_datetime = start

        return data

    def _parse_h5_data(self):
        file_name = self.temp_file_path
        date_time_col = normal_headers_renaming_dict["datetime_txt"]
        file_name = pathlib.Path(file_name)

        raw_frames = {}
        with pd.HDFStore(file_name) as h5_file:
            for key in ["data_df", "info_df", "stat_df"]:
                raw_frames[key] = h5_file.select(key)

        return raw_frames


def check_get():
    import cellpy

    name = r"c:\Data\Electrochemical\Projects-raw\LongLife\20220607_SiCx_slurry-04b_1_cc_01.h5"
    c = cellpy.get(name, instrument="arbin_sql_h5")
    print(c)


if __name__ == "__main__":
    check_get()
