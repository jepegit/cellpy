"""This file contains methods for importing Bio-Logic mpr-type files"""

# This is based on the work by Chris Kerr
# (https://github.com/chatcannon/galvani/blob/master/galvani/BioLogic.py)
import datetime
import dateparser
import shutil
import tempfile
import time
import warnings
import logging
import os
from collections import OrderedDict

import numpy as np
import pandas as pd

from cellpy.parameters.internal_settings import get_headers_normal
from cellpy.readers.core import Data, FileID, humanize_bytes
from cellpy.readers.instruments.base import BaseLoader
from cellpy.readers.instruments.loader_specific_modules.biologic_file_format import (
    bl_dtypes,
    bl_flags,
    bl_log_pos_dtype,
    hdr_dtype,
    mpr_label,
)

OLE_TIME_ZERO = datetime.datetime(1899, 12, 30, 0, 0, 0)
SEEK_SET = 0  # from start
SEEK_CUR = 1  # from current position
SEEK_END = 2  # from end of file


def ole2datetime(oledt):
    """converts from ole datetime float to datetime"""
    return OLE_TIME_ZERO + datetime.timedelta(days=float(oledt))


def datetime2ole(dt):
    """converts from datetime object to ole datetime float"""
    delta = dt - OLE_TIME_ZERO
    delta_float = delta / datetime.timedelta(days=1)  # trick from SO
    return delta_float


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


def _read_modules(fileobj):
    module_magic = fileobj.read(len(b"MODULE"))
    logging.debug(f"-")
    hdr_bytes = fileobj.read(hdr_dtype.itemsize)
    hdr = np.fromstring(hdr_bytes, dtype=hdr_dtype, count=1)
    hdr_dict = dict(((n, hdr[n][0]) for n in hdr_dtype.names))
    hdr_dict["offset"] = fileobj.tell()
    hdr_dict["data"] = fileobj.read(hdr_dict["length"])
    fileobj.seek(hdr_dict["offset"] + hdr_dict["length"], SEEK_SET)
    hdr_dict["end"] = fileobj.tell()
    return hdr_dict


class DataLoader(BaseLoader):
    """Class for loading biologics-data from mpr-files."""

    # Note: the class is sub-classing Loader. At the moment, Loader does
    # not really contain anything...
    instrument_name = "biologics_mpr"
    raw_ext = "mpr"

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.headers_normal = get_headers_normal()
        self.current_chunk = 0  # use this to set chunks to load
        self.mpr_data = None
        self.mpr_log = None
        self.mpr_settings = None
        self.cellpy_headers = get_headers_normal()

    @staticmethod
    def get_raw_units():
        """Include the settings for the units used by the instrument.

        The units are defined w.r.t. the SI units ('unit-fractions';
        currently only units that are multiples of
        Si units can be used). For example, for current defined in mA,
        the value for the
        current unit-fraction will be 0.001.

        Returns: dictionary containing the unit-fractions for current, charge,
        and mass

        """

        raw_units = dict()
        raw_units["current"] = "mA"
        raw_units["charge"] = "mAh"
        raw_units["mass"] = "g"
        raw_units["voltage"] = "V"
        return raw_units

    @staticmethod
    def get_raw_limits():
        """Include the settings for how to decide what kind of
        step you are examining here.

        The raw limits are 'epsilons' used to check if the current
        and/or voltage is stable (for example
        for galvanostatic steps, one would expect that the current
        is stable (constant) and non-zero).
        It is expected that different instruments (with different
        resolution etc.) have different
        'epsilons'.

        Returns: the raw limits (dict)

        """
        raw_limits = dict()
        raw_limits["current_hard"] = 0.0000000000001
        raw_limits["current_soft"] = 0.00001
        raw_limits["stable_current_hard"] = 2.0
        raw_limits["stable_current_soft"] = 4.0
        raw_limits["stable_voltage_hard"] = 2.0
        raw_limits["stable_voltage_soft"] = 4.0
        raw_limits["stable_charge_hard"] = 2.0
        raw_limits["stable_charge_soft"] = 5.0
        raw_limits["ir_change"] = 0.00001
        return raw_limits

    def inspect(self, run_data):
        """inspect the file."""
        return run_data

    def repair(self, file_name):
        """try to repair a broken/corrupted file"""
        raise NotImplementedError

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
        raise NotImplementedError

    def loader(self, file_name, bad_steps=None, **kwargs):
        """Loads data from BioLogics mpr files.

        Args:
            file_name (str): path to .res file.
            bad_steps (list of tuples): (c, s) tuples of steps s
             (in cycle c) to skip loading.

        Returns:
            new test
        """
        # print("bad steps: %s" % bad_steps)
        # print(f"kwargs: {kwargs}")
        # self.name = file_name

        # creating temporary file and connection
        # self.copy_to_temporary()
        temp_filename = self.temp_file_path

        filesize = os.path.getsize(self.temp_file_path)
        hfilesize = humanize_bytes(filesize)
        txt = "File size: %i (%s)" % (filesize, hfilesize)
        self.logger.debug(txt)

        self.logger.debug("tmp file: %s" % temp_filename)
        self.logger.debug("HERE WE LOAD THE DATA")

        data = Data()
        self.generate_fid()
        data.raw_data_files.append(self.fid)

        # div parameters and information (probably load this last)
        data.loaded_from = self.name

        # some overall prms
        data.channel_index = None
        data.creator = None
        data.schedule_file_name = None
        data.start_datetime = None
        data.test_ID = None
        data.test_name = None

        # --------- read raw-data (normal-data) -------------------------
        self.logger.debug("reading raw-data")
        self.mpr_data = None
        self.mpr_log = None
        self.mpr_settings = None

        # print(" loading mpr-data ".center(80, "-"))
        self._load_mpr_data(temp_filename, bad_steps)

        length_of_test = self.mpr_data.shape[0]
        logging.debug(f"length of test: {length_of_test}")

        self.logger.debug("renaming columns")
        self._rename_headers()
        # ---------  stats-data (summary-data) -------------------------
        summary_df = self._create_summary_data()

        if summary_df.empty:
            txt = "\nCould not find any summary (stats-file)!"
            txt += " (summary_df.empty = True)"
            txt += "\n -> issue make_summary(use_cellpy_stat_file=False)"
            logging.debug(txt)

        data.summary = summary_df
        data.raw = self.mpr_data

        data.raw_data_files_length.append(length_of_test)
        self._clean_up(temp_filename)
        return data

    def _parse_mpr_log_data(self):
        if not self.mpr_log:
            logging.debug("OBS! No mpr_log!")

        for value in bl_log_pos_dtype:
            # print(value)
            key, start, end, dtype = value
            if key not in self.mpr_log:
                continue
            self.mpr_log[key] = np.frombuffer(  # replaced np.fromstring
                self.mpr_log["data"][start:], dtype=dtype, count=1
            )[0]
            if "a" in dtype:
                self.mpr_log[key] = self.mpr_log[key].decode("utf8")

        # converting dates
        k = "Acquisition started on"
        if k in self.mpr_log:
            date_datetime = ole2datetime(self.mpr_log[k])
        else:
            date_datetime = self.mpr_settings["start_date"]
        self.mpr_log["Start"] = date_datetime

    def _parse_mpr_settings_data(self, settings_mod):
        start_date = dateparser.parse(settings_mod["date"].decode())
        mpr_settings = dict()
        mpr_settings["start_date"] = start_date
        mpr_settings["length"] = settings_mod["length"]
        mpr_settings["end"] = settings_mod["end"]
        mpr_settings["offset"] = settings_mod["offset"]
        mpr_settings["version"] = settings_mod["version"]
        mpr_settings["data"] = settings_mod["data"]
        self.mpr_settings = mpr_settings

    def _get_flag(self, flag_name):
        # TODO: next, find out what where the Ns changes are and Ns
        #  seems to be a method there to get the cycle number as well
        # print(f"flag_name: {flag_name}")
        if flag_name in self.flags_dict:
            mask, dtype = self.flags_dict[flag_name]
            # print(f"flag: {flag_name}, mask: {mask}, dtype: {dtype}")
            bin_str = f"{mask:010b}"
            # print(f"bin_str: {bin_str}")
            # print([int(x) for x in bin_str])
            # print(self.mpr_data["flags"])
            stuff = np.array(
                self.mpr_data["flags"] & mask, dtype=dtype
            )  # need to fix this!
            # print(f"stuff: {stuff}")
            return np.array(
                self.mpr_data["flags"] & mask, dtype=dtype
            )  # need to fix this!
        # elif flag_name in self.flags2_dict:
        #     mask, dtype = self.flags2_dict[flag_name]
        #     return np.array(self.mpr_data['flags2'] & mask, dtype=dtype)
        else:
            # raise AttributeError("Flag '%s' not present" % flag_name)
            logging.info(f"Flag {flag_name} not present")

    def _load_mpr_data(self, filename, bad_steps):
        if bad_steps is not None:
            warnings.warn("Exluding bad steps is not implemented")

        stats_info = os.stat(filename)
        mpr_modules = []

        # VMP LOG: log module
        # VMP data: data module
        # VMP Set: settings module
        with open(filename, mode="rb") as file_obj:
            label = file_obj.read(len(mpr_label))
            self.logger.debug(f"label: {label}")
            counter = 0
            while True:
                counter += 1
                new_module = _read_modules(file_obj)
                position = int(new_module["end"])
                mpr_modules.append(new_module)
                if position >= stats_info.st_size:
                    txt = "-reached end of file"
                    if position == stats_info.st_size:
                        txt += " --exactly at end of file"
                    self.logger.info(txt)
                    break

        # ------------- settings -------------------------------
        settings_mod = None
        for m in mpr_modules:
            if m["shortname"].strip().decode() == "VMP Set":
                settings_mod = m
                break
        if settings_mod is None:
            raise IOError("No settings-module found!")

        self._parse_mpr_settings_data(settings_mod)

        # ------------- data -----------------------------------
        data_module = None
        for i, m in enumerate(mpr_modules):
            if m["shortname"].decode().strip() == "VMP data":
                data_module = m
        if data_module is None:
            raise IOError("No data module!")

        data_version = data_module["version"]
        n_data_points = np.fromstring(data_module["data"][:4], dtype="<u4")
        n_data_points = n_data_points[0]
        n_columns = np.fromstring(data_module["data"][4:5], dtype="u1")
        n_columns = n_columns[0]

        logging.debug(f"data (points, cols): {n_data_points}, {n_columns}")

        if data_version == 0:
            logging.debug("data version 0")
            column_types = np.fromstring(
                data_module["data"][5:], dtype="u1", count=n_columns
            )

            remaining_headers = data_module["data"][5 + n_columns : 100]
            main_data = data_module["data"][100:]

        elif data_version == 2:
            logging.debug("data version 2")
            column_types = np.fromstring(
                data_module["data"][5:], dtype="<u2", count=n_columns
            )
            main_data = data_module["data"][405:]
            remaining_headers = data_module["data"][5 + 2 * n_columns : 405]

        else:
            raise IOError("Unrecognised version for data module: %d" % data_version)

        whats_left = remaining_headers.strip(b"\x00").decode("utf8")
        if whats_left:
            self.logger.debug(" *** UPS! you have some columns left")
            self.logger.debug(whats_left)

        self.cols = []
        dtype_dict = OrderedDict()
        flags_dict = OrderedDict()
        for col in column_types:
            # print(f"col: {col} - {bl_dtypes[col]}")
            self.cols.append(col)
            if col in bl_flags.keys():
                flags_dict[bl_flags[col][0]] = bl_flags[col][1]
            dtype_dict[bl_dtypes[col][1]] = bl_dtypes[col][0]
        self.dtype_dict = dtype_dict
        self.flags_dict = flags_dict

        dtype = np.dtype(list(dtype_dict.items()))
        p = dtype.itemsize
        if not p == (len(main_data) / n_data_points):
            self.logger.info(
                f"WARNING! You have defined {p} bytes, but it seems it should be [{len(main_data) / n_data_points}]"
            )
        bulk = main_data
        bulk_data = np.fromstring(bulk, dtype=dtype)
        mpr_data = pd.DataFrame(bulk_data)

        # ------------- log  -----------------------------------
        log_module = None
        for m in mpr_modules:
            if m["shortname"].strip().decode() == "VMP LOG":
                log_module = m

        mpr_log = dict()
        if log_module is None:
            txt = "WARNING - no log module found!"
            logging.info(txt)
        else:
            end_date = dateparser.parse(log_module["date"].decode())
            mpr_log["end_date"] = end_date
            mpr_log["length2"] = log_module["length"]
            mpr_log["end2"] = log_module["end"]
            mpr_log["offset2"] = log_module["offset"]
            mpr_log["version2"] = log_module["version"]
            mpr_log["data"] = log_module[
                "data"
            ]  # Not sure if I will ever need it, but just in case....
        self.mpr_log = mpr_log
        self._parse_mpr_log_data()
        self.mpr_data = mpr_data
        self._unpack_flags()

        # # temporary export while developing
        # temp = self.mpr_data.copy()
        #
        # temp.to_csv(
        #     r"C:\scripting\cellpy_dev_resources\dev_data\biologic\out\intermediate.csv",
        #     sep=";",
        # )

    def _unpack_flags(self):

        df = self.mpr_data
        flags_dict = self.flags_dict

        for flag_name, (mask, dtype) in flags_dict.items():
            if flag_name in df.columns:
                continue
            df[flag_name] = np.array(df["flags"] & mask, dtype=dtype)
            if dtype == np.bool_:  # bool, but we prefer 0 and 1
                df[flag_name] = df[flag_name].astype(int)
        self.mpr_data = df

    def _rename_header(self, h_old, h_new):
        try:
            self.mpr_data.rename(
                columns={h_new: self.cellpy_headers[h_old]}, inplace=True
            )
        except KeyError as e:
            self.logger.info(f"Problem during conversion to cellpy-format ({e})")

    def _generate_cycle_index(self, cellpy_header_lookup=None, b_header=None):
        if "half_cycle" in self.mpr_data.columns:
            self.mpr_data[self.cellpy_headers["cycle_index_txt"]] = (
                np.floor(self.mpr_data["half_cycle"] + 1) / 2
            ).astype(int) + 1
            return

        if "cycleno" in self.mpr_data.columns:
            self.mpr_data[self.cellpy_headers["cycle_index_txt"]] = (
                np.floor(self.mpr_data["cycleno"] + 1) / 2
            ).astype(int) + 1
            return

        logging.debug("No Ns - must generate from flags")
        flag = "Ns changes"
        self.mpr_data[self.cellpy_headers["cycle_index_txt"]] = 1

        n = self._get_flag(flag)
        if n is None:
            return

        ns_changes = self.mpr_data[n].index.values
        for i in ns_changes:
            self.mpr_data.loc[i:, self.cellpy_headers["cycle_index_txt"]] += 1

    def _generate_datetime(self, cellpy_header_lookup=None, b_header=None):
        if b_header is None:
            b_header = self.cellpy_headers["test_time_txt"]
        start_datetime = self.mpr_log["Start"]
        self.mpr_data[self.cellpy_headers[cellpy_header_lookup]] = [
            start_datetime + datetime.timedelta(seconds=n)
            for n in self.mpr_data[b_header].values
        ]

    def _generate_step_index(self, cellpy_header_lookup=None, b_header=None):

        if b_header in self.mpr_data.columns:
            self.mpr_data[self.cellpy_headers["step_index_txt"]] = (
                self.mpr_data[b_header].astype(int) + 1
            )
            return

        logging.debug("No Ns - must generate from flags")
        self.mpr_data[self.cellpy_headers["step_index_txt"]] = 1
        flag = "Ns changes"

        n = self._get_flag(flag)
        if n is None:
            return

        ns_changes = self.mpr_data[n].index.values
        for i in ns_changes:
            self.mpr_data.loc[i:, self.cellpy_headers["step_index_txt"]] += 1

    def _generate_step_time(self, cellpy_header_lookup=None, b_header=None):

        self.mpr_data[self.cellpy_headers["step_time_txt"]] = np.nan
        if b_header is not None:
            logging.debug("Not implemented yet")
            return

        try:
            g = self.mpr_data.groupby(self.cellpy_headers["step_index_txt"])
            for name, group in g:
                t = group[self.cellpy_headers["test_time_txt"]].values
                t = t - t[0]
                self.mpr_data.loc[group.index, self.cellpy_headers["step_time_txt"]] = t

        except Exception as e:
            logging.debug(f"could not group by step_index_txt: {e}")
            return

    def _generate_capacities(self, cellpy_header_lookup=None, b_header=None):
        if b_header is None:
            b_header = "QChargeDischarge"

        cap_col = self.mpr_data[b_header]
        if cap_col is None:
            return
        self.mpr_data[self.cellpy_headers["discharge_capacity_txt"]] = [
            0.0 if x < 0 else x for x in cap_col
        ]
        self.mpr_data[self.cellpy_headers["charge_capacity_txt"]] = [
            0.0 if x >= 0 else -x for x in cap_col
        ]

    def _rename_headers(self):
        # should ideally use the info from bl_dtypes, will do that later

        protected = [
            "datetime_txt",
            "step_time_txt",
            "step_index_txt",
            "cycle_index_txt",
            "step_time_txt",
            "sub_step_time_txt",
            "charge_capacity_txt",
            "discharge_capacity_txt",
            "data_point_txt",
            # "internal_resistance_txt",
        ]

        # self.mpr_data[self.cellpy_headers["internal_resistance_txt"]] = np.nan
        self.mpr_data[self.cellpy_headers["data_point_txt"]] = np.arange(
            1, self.mpr_data.shape[0] + 1, 1
        )

        cycle_index_made = False
        step_index_made = False
        sub_step_index_made = False
        step_time_made = False
        sub_step_time_made = False
        capacity_made = False
        datetime_made = False

        for key in self.cols:
            cellpy_header_lookup = bl_dtypes[key][-1]
            b_header = bl_dtypes[key][1]

            if cellpy_header_lookup:

                if cellpy_header_lookup not in protected:
                    self._rename_header(cellpy_header_lookup, b_header)

                if cellpy_header_lookup == "charge_capacity_txt":
                    self._generate_capacities(cellpy_header_lookup, b_header)
                    capacity_made = True

                if cellpy_header_lookup == "datetime_txt":
                    self._generate_datetime(cellpy_header_lookup, b_header)
                    datetime_made = True

                if cellpy_header_lookup == "cycle_index_txt":
                    self._generate_cycle_index(cellpy_header_lookup, b_header)
                    cycle_index_made = True

                if cellpy_header_lookup == "step_index_txt":
                    self._generate_step_index(cellpy_header_lookup, b_header)
                    step_index_made = True

                if cellpy_header_lookup == "step_time_txt":
                    self._generate_step_time(cellpy_header_lookup, b_header)
                    step_time_made = True

        if not capacity_made:
            self._generate_capacities()
        if not datetime_made:
            self._generate_datetime("datetime_txt")
        if not cycle_index_made:
            self._generate_cycle_index()
        if not step_index_made:
            self._generate_step_index()

        if not step_time_made:
            self._generate_step_time()

        if not sub_step_time_made:
            self.mpr_data[self.cellpy_headers["sub_step_time_txt"]] = self.mpr_data[
                self.cellpy_headers["step_time_txt"]
            ]
        if not sub_step_index_made:
            self.mpr_data[self.cellpy_headers["sub_step_index_txt"]] = self.mpr_data[
                self.cellpy_headers["step_index_txt"]
            ]

    def _create_summary_data(self):
        # Summary data should contain datapoint-number
        # for last point in the cycle. It must also contain
        # capacity
        df_summary = pd.DataFrame()
        mpr_log = self.mpr_log
        mpr_settings = self.mpr_settings
        # TODO: @jepe - finalise making summary of mpr-files
        # after figuring out steps etc
        logging.debug(
            "Creating summary data for biologics mpr-files" " is not implemented yet"
        )
        self.logger.info(mpr_settings)
        self.logger.info(mpr_log)
        start_date = mpr_settings["start_date"]
        self.logger.info(start_date)
        return df_summary

    def __raw_export(self, filename, df):
        filename_out = os.path.splitext(filename)[0] + "_test_out.csv"
        print("\n--------EXPORTING----------------------------")
        print(filename)
        print("->")
        print(filename_out)
        df.to_csv(filename_out, sep=";")
        print("------OK--------------------------------------")

    def _clean_up(self, tmp_filename):
        if os.path.isfile(tmp_filename):
            try:
                os.remove(tmp_filename)
            except WindowsError as e:
                self.logger.warning(
                    "could not remove tmp-file\n%s %s" % (tmp_filename, e)
                )
        pass


def _main():
    # This is just for testing
    import logging
    import os
    import pathlib
    import sys

    import pandas as pd

    import cellpy
    from cellpy import cellreader, log

    # -------- defining overall path-names etc ----------
    # galvanostatic with steps (but only one cycle): Bec_03_02_formation_20170314_C02.mpr
    # with several cycles (at least one) [VSP]: Mel495_GEIS_cycle4_all_temps.mpr

    mpr_file_path = pathlib.Path(r"C:\scripting\cellpy_dev_resources\dev_data\biologic")
    mpr_file = mpr_file_path / "Bec_03_02_formation_20170314_C02.mpr"

    out_dir = pathlib.Path(r"C:\scripting\cellpy_dev_resources\dev_data\biologic\out")

    print("\n======================mpr-dev===========================")
    print(f"Test-file: {mpr_file}")
    log.setup_logging(default_level="DEBUG")
    instrument = "biologics_mpr"

    c = cellpy.get(mpr_file, instrument=instrument, mass=0.1, area=0.785)
    c.to_csv(out_dir, sep=";")


def _main0():
    # This is just for testing
    import logging
    import os
    import pathlib
    import sys

    import pandas as pd

    import cellpy
    from cellpy import cellreader, log

    # -------- defining overall path-names etc ----------
    # galvanostatic with steps (but only one cycle): Bec_03_02_formation_20170314_C02.mpr
    # with several cycles (at least one) [VSP]: Mel495_GEIS_cycle4_all_temps.mpr

    mpr_file_path = pathlib.Path(r"C:\scripting\cellpy_dev_resources\dev_data\biologic")
    mpr_file = mpr_file_path / "Mel495_GEIS_cycle4_all_temps.mpr"

    out_dir = pathlib.Path(r"C:\scripting\cellpy_dev_resources\dev_data\biologic\out")

    print("\n======================mpr-dev===========================")
    print(f"Test-file: {mpr_file}")
    log.setup_logging(default_level="DEBUG")
    instrument = "biologics_mpr"
    cellpy_data_instance = cellreader.CellpyCell()
    cellpy_data_instance.set_instrument(instrument=instrument)
    print("starting to load the file")
    cellpy_data_instance.from_raw(mpr_file, mass=0.1, area=0.785)
    print("printing cellpy instance:")
    raw = cellpy_data_instance.data.raw
    print(raw.head())
    out_name = f"{mpr_file.stem}_cellpy.csv"
    raw.to_csv(out_dir / out_name, sep=";")

    print("---make step table")
    cellpy_data_instance.make_step_table()
    steps = cellpy_data_instance.data.steps
    out_name = f"{mpr_file.stem}_cellpy_steps.csv"
    steps.to_csv(out_dir / out_name, sep=";")

    print("---make summary")
    cellpy_data_instance.make_summary()
    summary = cellpy_data_instance.data.summary
    out_name = f"{mpr_file.stem}_cellpy_summary.csv"
    summary.to_csv(out_dir / out_name, sep=";")


if __name__ == "__main__":
    _main()
