"""neware xlsx exported data"""

from dataclasses import dataclass
import datetime
import logging
import pathlib
import sys
import warnings

import pandas as pd
from dateutil.parser import parse

import cellpy.readers.core
from cellpy import prms
from cellpy.exceptions import WrongFileVersion
from cellpy.parameters.internal_settings import HeaderDict, get_headers_normal
from cellpy.readers.core import Data, FileID
from cellpy.readers.core import Q
from cellpy.readers.instruments.base import BaseLoader
from cellpy.readers.instruments.processors import post_processors as pp
from pathlib import Path

DEBUG_MODE = prms.Reader.diagnostics  # not used
ALLOW_MULTI_TEST_FILE = prms._allow_multi_test_file  # not used
DATE_TIME_FORMAT = prms._date_time_format  # not used


@dataclass
class ModelParameters:
    states: dict


def to_datetime(n):
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

    instrument_name = "neware_xlsx"
    raw_ext = "xlsx"

    def __init__(self, *args, **kwargs):
        """initiates the neware xlsx reader class"""
        self.raw_headers_normal = None  # the column headers defined by Neware
        self.cellpy_headers_normal = (
            get_headers_normal()
        )  # the column headers defined by cellpy
        self.normal_headers_renaming_dict = None  # renaming dict for the headers
        self.config_params = None  # configuration parameters

    @staticmethod
    def get_headers_normal():
        """Defines the so-called normal column headings for export"""
        # covered by cellpy at the moment
        return get_headers_normal()

    @staticmethod
    def get_headers_aux(df):
        """Defines the so-called auxiliary table column headings for Neware xlsx export

        Warning: not properly implemented yet

        """
        headers = HeaderDict()
        for col in df.columns:
            if col.startswith("Aux_"):
                ncol = col.replace("/", "_")
                ncol = "".join(ncol.split("(")[0])
                headers[col] = ncol.lower()
            if col.startswith("Step Type"):
                headers[col] = "step_type"

        return headers

    def get_normal_headers_renaming_dict(self):
        units = self.get_raw_units()
        unit_current = units["current"]
        unit_voltage = units["voltage"]
        unit_capacity = units["charge"]
        unit_energy = units["energy"]
        unit_power = units["power"]

        normal_headers_renaming_dict = {
            "test_id_txt": "Test_ID",
            "data_point_txt": "DataPoint",
            "datetime_txt": "Date",
            "test_time_txt": "Total Time",
            "step_time_txt": "Step Time",
            "cycle_index_txt": "Cycle Index",
            "step_index_txt": "Step Index",
            "current_txt": f"Current({unit_current})",
            "voltage_txt": f"Voltage({unit_voltage})",
            "power_txt": f"Power({unit_power})",
            "charge_capacity_txt": f"Capacity({unit_capacity})",
            # "discharge_capacity_txt": f"Capacity({unit_capacity})",
            "charge_energy_txt": f"Energy({unit_energy})",
            # "discharge_energy_txt": f"Energy({unit_energy})",
            "internal_resistance_txt": "Internal_Resistance",
            "ref_voltage_txt": "Aux_Voltage_1",
        }
        return normal_headers_renaming_dict

    def get_raw_units(self):
        raw_units = dict()
        raw_units["current"] = "A"
        raw_units["charge"] = "Ah"
        raw_units["mass"] = "g"
        raw_units["voltage"] = "V"
        raw_units["energy"] = "Wh"
        raw_units["power"] = "W"
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

    # TODO: extract units from the file and link it to the get_raw_units method
    # TODO: extract meta from the file
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
        logging.critical("Experimental loader for neware xlsx files")
        data_df, meta = self._query()

        self.normal_headers_renaming_dict = self.get_normal_headers_renaming_dict()
        data = Data()

        if kwargs.get("config_params"):
            self.config_params = kwargs.get("config_params")
        else:
            self.config_params = ModelParameters(
                {
                    "column_name": "step_type",  # changed from "Step Type" in the _query method
                    "charge_keys": ["CC Chg"],
                    "discharge_keys": ["CC DChg"],
                    "rest_keys": ["Rest"],
                }
            )

        # some metadata is available in the info_df part of the h5 file
        data.loaded_from = self.name

        if meta.keys():
            data.test_name = meta.get(name, "unknown")
            data.custom_info = meta

            if start_time := meta.get("start_time"):
                # TODO: implement conversion to datetime
                logging.debug(f"start_time: {start_time}")

            if end_time := meta.get("end_time"):
                # TODO: implement conversion to datetime
                logging.debug(f"end-time: {end_time}")
            if units := meta.get("units"):
                # TODO: implement handling of units and updating get_raw_units
                logging.debug(f"units: {units}")

            # TODO: implement handling of the rest of the meta data

        # Generating a FileID project:
        self.generate_fid()
        data.raw_data_files.append(self.fid)

        data.raw = data_df
        data.raw_data_files_length.append(len(data_df))
        data.summary = (
            pd.DataFrame()
        )  # creating an empty frame - loading summary is not implemented yet
        data = self._post_process(data)
        data = self.identify_last_data_point(data)

        return data

    def _post_process(self, data):
        set_index = False
        rename_headers = True
        forward_fill_ir = False
        backward_fill_ir = False
        fix_datetime = False
        set_dtypes = False
        time_to_sec = True
        fix_duplicated_rows = True
        split_the_capacity = True
        recalc_capacity = False

        if fix_duplicated_rows:
            data.raw = data.raw.drop_duplicates()

        if rename_headers:
            columns = {}
            for key in self.normal_headers_renaming_dict:
                old_header = self.normal_headers_renaming_dict[key]
                new_header = self.cellpy_headers_normal[key]
                columns[old_header] = new_header

            data.raw.rename(index=str, columns=columns, inplace=True)
            new_aux_headers = self.get_headers_aux(data.raw)
            data.raw.rename(index=str, columns=new_aux_headers, inplace=True)

        if time_to_sec:
            logging.debug("converting time to seconds")
            hdr_step_time = self.cellpy_headers_normal.step_time_txt
            hdr_test_time = self.cellpy_headers_normal.test_time_txt
            if hdr_step_time in data.raw:
                data.raw[hdr_step_time] = pd.to_timedelta(
                    data.raw[hdr_step_time]
                ).dt.total_seconds()
            if hdr_test_time in data.raw:
                data.raw[hdr_test_time] = pd.to_timedelta(
                    data.raw[hdr_test_time]
                ).dt.total_seconds()

        if split_the_capacity:
            logging.debug("splitting capacity")
            data = pp.split_capacity(data, self.config_params)

        if fix_datetime:
            h_datetime = self.cellpy_headers_normal.datetime_txt
            data.raw[h_datetime] = data.raw[h_datetime].apply(to_datetime)
            if h_datetime in data.summary:
                data.summary[h_datetime] = data.summary[h_datetime].apply(to_datetime)

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

        # hdr_date_time = self.arbin_headers_normal.datetime_txt
        # TODO: convert to datetime:
        # start = data.raw[hdr_date_time].iat[0]
        # data.start_datetime = start

        return data

    # noinspection PyTypeChecker
    def _query(self):
        file_name = self.temp_file_path
        file_format = file_name.suffix[1:]
        file_name = pathlib.Path(file_name)
        data_frame = pd.DataFrame()
        meta_dict = dict()

        step_sheet = "step"
        data_sheet = "record"
        unit_sheet = "unit"
        test_sheet = "test"

        hdr_step_step = "Step Type"
        hdr_step_step_number = "Step Number"
        hdr_step_step_index = "Step Index"
        hdr_step_cycle = "Cycle Index"

        hdr_date = "Date"
        hdr_start = "Oneset Date"
        hdr_end = "End Date"
        hdr_cycle = "Cycle Index"
        hdr_step = "Step Type"
        hdr_step_number = "Step Number"
        hdr_step_index = "Step Index"

        if file_format == "xls":
            engine = "xlrd"
            logging.debug(
                f"parsing with pandas.read_excel using {engine} (old format): {self.name}"
            )
            raise WrongFileVersion("reading old xls not implemented yet")

        elif file_format == "xlsx":
            engine = "openpyxl"
            logging.critical(
                f"parsing with pandas.read_excel using {engine}: {self.name}"
            )

        else:
            raise IOError(
                f"Could not read {file_name}, {file_format} not supported yet"
            )

        # -------------- meta data --------------
        try:
            unit_frame = pd.read_excel(
                file_name, engine=engine, sheet_name=unit_sheet, header=None
            )
        except ValueError as e:
            print(f"could not parse {unit_sheet} in file: {e}")
            print(f"most likely this file is not appropriate for cellpy")

        else:
            try:
                meta_dict["name"] = unit_frame.iloc[0, 0]
                meta_dict["device"] = unit_frame.iloc[1, [1, 2, 3]].values

                start_time, end_time = unit_frame.iloc[2, [2, 6]]
                meta_dict["start_time"] = start_time
                meta_dict["end_time"] = end_time

                unit_sub_frame = unit_frame.iloc[5:7, 0:9].T
                unit_sub_frame.columns = ["name", "value"]
                meta_dict["units"] = unit_sub_frame.set_index("name").to_dict()["value"]

            except Exception as e:
                print(f"could not parse unit sheet: {e}")

        try:
            test_frame = pd.read_excel(
                file_name, engine=engine, sheet_name=test_sheet, header=None
            )
        except ValueError as e:
            print(f"could not parse {test_sheet} in file: {e}")
            print(f"It is very likely that this file is not appropriate for cellpy!")
        else:
            try:
                meta_dict["start_step_id"] = test_frame.iloc[1, 2]
                meta_dict["voltage_upper"] = test_frame.iloc[1, 5]
                meta_dict["p_over_n"] = test_frame.iloc[1, 8]

                meta_dict["cycle_count"] = test_frame.iloc[2, 2]
                meta_dict["voltage_lower"] = test_frame.iloc[2, 5]
                meta_dict["builder"] = test_frame.iloc[2, 8]

                meta_dict["record_settings"] = test_frame.iloc[3, 2]
                meta_dict["current_upper"] = test_frame.iloc[3, 5]
                meta_dict["remarks"] = test_frame.iloc[3, 8]

                meta_dict["voltage_range"] = test_frame.iloc[4, 8]
                meta_dict["current_lower"] = test_frame.iloc[4, 5]

                meta_dict["current_range"] = test_frame.iloc[5, 2]
                meta_dict["start_time"] = test_frame.iloc[5, 5]
                meta_dict["barcode"] = test_frame.iloc[5, 8]

                meta_dict["active_material_mass"] = test_frame.iloc[6, 2]
                meta_dict["nominal_capacity"] = test_frame.iloc[6, 5]
                meta_dict["barcode"] = test_frame.iloc[6, 8]

            except Exception as e:
                print(f"could not parse test sheet: {e}")

        # -------------- raw data --------------
        try:
            step_frame = pd.read_excel(file_name, engine=engine, sheet_name=step_sheet)
            data_frame = pd.read_excel(file_name, engine=engine, sheet_name=data_sheet)
        except ValueError as e:
            print(f"could not parse file: {e}")
            raise WrongFileVersion(f"could not parse file: {e}")

        # combining the step and data frames
        data_frame[[hdr_date]] = data_frame[[hdr_date]].apply(pd.to_datetime)
        step_frame[[hdr_start, hdr_end]] = step_frame[[hdr_start, hdr_end]].apply(
            pd.to_datetime
        )

        data_frame[hdr_cycle] = 0
        data_frame[hdr_step_index] = 0
        for index, sub_frame in step_frame.iterrows():
            start_date = sub_frame[hdr_start]
            end_date = sub_frame[hdr_end]
            step = sub_frame[hdr_step_step]
            step_index = sub_frame[hdr_step_step_index]
            cycle = sub_frame[hdr_step_cycle]

            mask = (
                (data_frame[hdr_date] > start_date)
                | (
                    (data_frame[hdr_date] == start_date)
                    & (data_frame[hdr_step] == step)
                )
            ) & (
                (data_frame[hdr_date] < end_date)
                | ((data_frame[hdr_date] == end_date) & (data_frame[hdr_step] == step))
            )
            data_frame.loc[mask, hdr_cycle] = int(cycle)
            data_frame.loc[mask, hdr_step_index] = int(step_index)

        return data_frame, meta_dict


def _check_get():
    import cellpy

    name = r"c:\scripting\tasks\cenate\2023_vajee_neware_excel_dqdv\data\raw\neware_vajee.xlsx"
    c = cellpy.get(
        name,
        instrument="neware_xlsx",
        mass=1.2,
        nominal_capacity=120.0,
        auto_summary=True,
    )
    print(c)


if __name__ == "__main__":
    _check_get()
