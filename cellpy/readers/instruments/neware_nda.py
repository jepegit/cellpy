import logging
from datetime import datetime, timezone
import pandas as pd
import sys
import pathlib

from cellpy.readers.instruments.base import BaseLoader
from cellpy import prms
from cellpy.parameters.internal_settings import HeaderDict, get_headers_normal
from cellpy.readers.core import Data

"""Neware NDA (or NDAX) data"""



# How can we propagate kwargs from cellpy.get to the loader?



# TODO: rename columns
# TODO: check if data is loaded correctly
# TODO: override fastnda (need to provide it with the correct aux dict) (monkey patch)


""" Index(['index', 'voltage_V', 'current_mA', 'unix_time_s', 'step_time_s',
       'total_time_s', 'cycle_count', 'step_count', 'step_index', 'step_type',
       'capacity_mAh', 'energy_mWh', 'aux1_?', 'aux1_temperature_degC',
       'aux1_?_right'],
      dtype='str')"""

DEBUG_MODE = prms.Reader.diagnostics  # not used
ALLOW_MULTI_TEST_FILE = prms._allow_multi_test_file  # not used
DATE_TIME_FORMAT = prms._date_time_format  # not used
USE_LOCAL_FASTNDA = prms._use_local_fastnda
CUSTOM_AUX_MAPPING = {
    102: "aux_102",
    # 103: "temperature_degC",
    103: "aux_103",
    335: "temperature_setpoint_degC",
    345: "humidity_%",
    1122: "my_custom_channel",  # your addition
}

normal_headers_renaming_dict = {
    "test_id_txt": "Test_ID",
    "data_point_txt": "index",
    "datetime_txt": "unix_time_s",
    "test_time_txt": "total_time_s",
    "step_time_txt": "step_time_s",
    "cycle_index_txt": "cycle_count",
    "step_index_txt": "step_index",
    "current_txt": "current_mA",
    "voltage_txt": "voltage_V",
    "power_txt": "power_mW",
    "charge_capacity_txt": "charge_mAh",
    # "charge_capacity_txt": "capacity_mAh",
    "discharge_capacity_txt": "discharge_mAh",
    "charge_energy_txt": "charge_mWh",
    # "charge_energy_txt": "energy_mWh",
    "discharge_energy_txt": "discharge_mWh",
    "internal_resistance_txt": "internal_resistance_mOhm",
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


def unix_time_s_to_datetime(unix_time_s: float | pd.Series, utc: bool = True) -> datetime | pd.Series:
    """Convert Unix time in seconds (e.g. Neware/fastnda unix_time_s) to datetime.

    Args:
        unix_time_s: Seconds since Unix epoch (scalar or pandas Series).
        utc: If True, return timezone-aware UTC; if False, return naive local time.

    Returns:
        datetime (or Series of datetime) for the given Unix timestamp(s).
    """
    if isinstance(unix_time_s, pd.Series):
        out = pd.to_datetime(unix_time_s.astype(float), unit="s")
        if utc:
            out = out.dt.tz_localize("UTC")
        return out
    t = float(unix_time_s)
    if utc:
        return datetime.fromtimestamp(t, tz=timezone.utc)
    return datetime.fromtimestamp(t)


class DataLoader(BaseLoader):
    """Class for loading data from Neware NDA files using the `fastnda` library."""

    instrument_name = "neware_nda"
    raw_ext = "nda*"

    # override this if needed
    def __init__(self, *args, **kwargs):
        self.fastnda_headers_normal = (
            self.get_headers_normal()
        )  # the column headers defined by fastnda
        self.cellpy_headers_normal = (
            get_headers_normal()
        )  # the column headers defined by cellpy

    @staticmethod
    def get_headers_normal():
        """Defines the so-called normal column headings"""
        # covered by cellpy at the moment
        return get_headers_normal()

    @staticmethod
    def get_headers_aux(df):
        """Defines the so-called auxiliary table column headings"""
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

        Loads data from Neware NDA (or NDAX) file using the `fastnda` library.

        Args:
            name (str): name of the file

        Returns:
            data object
        """
        # self.name = name
        # self.copy_to_temporary()
        raw_data = self._run_fastnda()
        data = Data()

        # # some metadata is available in the info_df part of the h5 file
        # data.loaded_from = self.name
        # data.channel_index = data_dfs["info_df"]["IV_Ch_ID"].iloc[0]
        # data.test_ID = data_dfs["info_df"]["Test_ID"].iloc[0]
        # data.test_name = self.name.name
        # data.creator = None
        # data.schedule_file_name = data_dfs["info_df"]["Schedule_File_Name"].iloc[0]
        # # TODO: convert to datetime (note that this seems to be set also in the postprocessing)
        # data.start_datetime = data_dfs["info_df"]["First_Start_DateTime"].iloc[0]
        # data.mass = data_dfs["info_df"]["SpecificMASS"].iloc[0]
        # data.nom_cap = data_dfs["info_df"]["SpecificCapacity"].iloc[0]

        # Generating a FileID project:
        self.generate_fid()
        data.raw_data_files.append(self.fid)

        data.raw = raw_data
        data.raw_data_files_length.append(len(raw_data))
        data.summary = (
            pd.DataFrame()
        )  # creating an empty frame - loading summary is not implemented yet
        data = self._post_process(data)
        with pd.option_context("display.max_columns", None):
            print(data.raw.head())
            print(data.raw.tail())
        print(data.raw.columns)

        data = self.identify_last_data_point(data)
        # sys.exit()
        return data

    def _post_process(self, data):
        set_index = False
        rename_headers = True
        split_capacity = True
        set_dtypes = True
        fix_duplicated_rows = True

        if fix_duplicated_rows:
            data.raw = data.raw.drop_duplicates()

        if split_capacity:
            print("splitting capacity is not implemented yet")

        if rename_headers:
            columns = {}
            for key in normal_headers_renaming_dict:
                old_header = normal_headers_renaming_dict[key]
                new_header = self.cellpy_headers_normal[key]
                columns[old_header] = new_header

            data.raw.rename(index=str, columns=columns, inplace=True)
            new_aux_headers = self.get_headers_aux(data.raw)
            data.raw.rename(index=str, columns=new_aux_headers, inplace=True)

        if set_dtypes:
            logging.debug("setting data types")
            # test_time_txt = self.cellpy_headers_normal.test_time_txt
            # step_time_txt = self.cellpy_headers_normal.step_time_txt
            date_time_txt = self.cellpy_headers_normal.datetime_txt
            logging.debug("converting to datetime format")
            try:
                # data.raw[test_time_txt] = pd.to_timedelta(data.raw[test_time_txt])  # cellpy is not ready for this
                # data.raw[step_time_txt] = pd.to_timedelta(data.raw[step_time_txt])  # cellpy is not ready for this
                data.raw[date_time_txt] = unix_time_s_to_datetime(
                    data.raw[date_time_txt], utc=True
                )

            except ValueError:
                logging.debug("could not convert to datetime format")

        if set_index:
            hdr_data_point = self.cellpy_headers_normal.data_point_txt
            if data.raw.index.name != hdr_data_point:
                data.raw = data.raw.set_index(
                    hdr_data_point, drop=False
                )  # TODO: check if this is standard


        hdr_date_time = self.cellpy_headers_normal.datetime_txt
        start = data.raw[hdr_date_time].iat[0]
        # TODO: convert to datetime:
        data.start_datetime = start

        return data

    def _run_fastnda(self, **kwargs):
        if USE_LOCAL_FASTNDA:
            from cellpy.libs import local_fastnda as fnda
        else:
            try:
                if CUSTOM_AUX_MAPPING is not None:
                    from types import MappingProxyType
                    import fastnda.ndax as _ndax
                    _ndax.AUX_CHL_MAP = MappingProxyType(CUSTOM_AUX_MAPPING)
                import fastnda as fnda
            except ImportError:
                raise ImportError("fastnda is not installed. Please install it using `pip install fastnda`.")

        file_name = self.temp_file_path
        file_name = pathlib.Path(file_name)

        raw_data = fnda.read(file_name, **kwargs)
        raw_data = raw_data.to_pandas()
        # save to local directory for debugging
        local_dir = pathlib.Path(r"C:\scripting\cellpy\local")
        raw_data.to_csv(local_dir / "raw_data.csv")

        if not USE_LOCAL_FASTNDA:
            raw_data = _process_fastnda_data(raw_data)
        return raw_data


def _process_fastnda_data(raw_data):
    print("PROCESSING FASTNDA DATA".center(100, "="))
    return raw_data


def _check_get():
    import cellpy

    name = r"C:\scripting\cellpy\testdata\data\20260302_IFE_BTS85_2_9_8_1.ndax"
    c = cellpy.get(name, instrument="neware_nda", random_keyword="test-random-keyword")
    print(c)


if __name__ == "__main__":
    _check_get()
