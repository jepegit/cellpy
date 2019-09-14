"""This file contains methods for importing Bio-Logic mpr-type files"""
# This is based on the work by Chris Kerr
# (https://github.com/chatcannon/galvani/blob/master/galvani/BioLogic.py)
import os
import tempfile
import shutil
import logging
import warnings
import time
from collections import OrderedDict
import datetime
import pandas as pd
import numpy as np

from cellpy.readers.instruments.biologic_file_format import (
    bl_dtypes,
    hdr_dtype,
    mpr_label,
    bl_log_pos_dtype,
    bl_flags,
)
from cellpy.readers.core import FileID, Cell, check64bit, humanize_bytes
from cellpy.parameters.internal_settings import get_headers_normal
from cellpy.readers.instruments.mixin import Loader
from cellpy.parameters import prms

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
    hdr_bytes = fileobj.read(hdr_dtype.itemsize)
    hdr = np.fromstring(
        hdr_bytes, dtype=hdr_dtype, count=1
    )  # TODO: change to frombuffer
    hdr_dict = dict(((n, hdr[n][0]) for n in hdr_dtype.names))
    hdr_dict["offset"] = fileobj.tell()
    hdr_dict["data"] = fileobj.read(hdr_dict["length"])
    fileobj.seek(hdr_dict["offset"] + hdr_dict["length"], SEEK_SET)
    hdr_dict["end"] = fileobj.tell()
    return hdr_dict


class MprLoader(Loader):
    """ Class for loading biologics-data from mpr-files."""

    # Note: the class is sub-classing Loader. At the moment, Loader does
    # not really contain anything...

    def __init__(self):
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
        raw_units["current"] = 1.0  # A
        raw_units["charge"] = 1.0  # Ah
        raw_units["mass"] = 0.001  # g
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

    def load(self, file_name):
        """Load a raw data-file

        Args:
            file_name (path)

        Returns:
            loaded test
        """
        raw_file_loader = self.loader
        new_rundata = raw_file_loader(file_name)
        new_rundata = self.inspect(new_rundata)
        return new_rundata

    def inspect(self, run_data):
        """inspect the file.
        """
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
        """Loads data from biologics .mpr files.

        Args:
            file_name (str): path to .res file.
            bad_steps (list of tuples): (c, s) tuples of steps s
             (in cycle c) to skip loading.

        Returns:
            new_tests (list of data objects)
        """
        new_tests = []
        if not os.path.isfile(file_name):
            self.logger.info("Missing file_\n   %s" % file_name)
            return None

        filesize = os.path.getsize(file_name)
        hfilesize = humanize_bytes(filesize)
        txt = "Filesize: %i (%s)" % (filesize, hfilesize)
        self.logger.debug(txt)

        # creating temporary file and connection
        temp_dir = tempfile.gettempdir()
        temp_filename = os.path.join(temp_dir, os.path.basename(file_name))
        shutil.copy2(file_name, temp_dir)

        self.logger.debug("tmp file: %s" % temp_filename)
        self.logger.debug("HERE WE LOAD THE DATA")

        data = Cell()
        fid = FileID(file_name)

        # div parameters and information (probably load this last)
        test_no = 1
        data.cell_no = test_no
        data.loaded_from = file_name

        # some overall prms
        data.channel_index = None
        data.channel_number = None
        data.creator = None
        data.item_ID = None
        data.schedule_file_name = None
        data.start_datetime = None
        data.test_ID = None
        data.test_name = None
        data.raw_data_files.append(fid)

        # --------- read raw-data (normal-data) -------------------------
        self.logger.debug("reading raw-data")
        self.mpr_data = None
        self.mpr_log = None
        self.mpr_settings = None

        self._load_mpr_data(temp_filename, bad_steps)
        length_of_test = self.mpr_data.shape[0]
        self.logger.debug(f"length of test: {length_of_test}")

        self.logger.debug("renaming columns")
        self._rename_headers()
        # ---------  stats-data (summary-data) -------------------------
        summary_df = self._create_summary_data()

        if summary_df.empty:
            txt = "\nCould not find any summary (stats-file)!"
            txt += " (summary_df.empty = True)"
            txt += "\n -> issue make_summary(use_cellpy_stat_file=False)"
            warnings.warn(txt)

        data.summary = summary_df
        data.raw = self.mpr_data

        data.raw_data_files_length.append(length_of_test)
        new_tests.append(data)

        self._clean_up(temp_filename)
        return new_tests

    def _parse_mpr_log_data(self):
        for value in bl_log_pos_dtype:
            key, start, end, dtype = value
            self.mpr_log[key] = np.frombuffer(  # replaced np.fromstring
                self.mpr_log["data"][start:], dtype=dtype, count=1
            )[0]
            if "a" in dtype:
                self.mpr_log[key] = self.mpr_log[key].decode("utf8")

        # converting dates
        date_datetime = ole2datetime(self.mpr_log["Acquisition started on"])
        self.mpr_log["Start"] = date_datetime

    def _parse_mpr_settings_data(self, settings_mod):

        tm = time.strptime(settings_mod["date"].decode(), "%m.%d.%y")
        startdate = datetime.date(tm.tm_year, tm.tm_mon, tm.tm_mday)

        mpr_settings = dict()
        mpr_settings["start_date"] = startdate
        mpr_settings["length"] = settings_mod["length"]
        mpr_settings["end"] = settings_mod["end"]
        mpr_settings["offset"] = settings_mod["offset"]
        mpr_settings["version"] = settings_mod["version"]
        mpr_settings["data"] = settings_mod["data"]
        self.mpr_settings = mpr_settings
        return None

    def _get_flag(self, flag_name):
        if flag_name in self.flags_dict:
            mask, dtype = self.flags_dict[flag_name]
            # print(f"flag: {flag_name}, mask: {mask}, dtype: {dtype}")
            return np.array(self.mpr_data["flags"] & mask, dtype=dtype)
        # elif flag_name in self.flags2_dict:
        #     mask, dtype = self.flags2_dict[flag_name]
        #     return np.array(self.mpr_data['flags2'] & mask, dtype=dtype)
        else:
            raise AttributeError("Flag '%s' not present" % flag_name)

    def _load_mpr_data(self, filename, bad_steps):
        if bad_steps is not None:
            warnings.warn("Exluding bad steps is not implemented")

        stats_info = os.stat(filename)
        mpr_modules = []

        mpr_log = None
        mpr_data = None
        mpr_settings = None

        file_obj = open(filename, mode="rb")
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

        file_obj.close()

        # ------------- set -----------------------------------
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
        for m in mpr_modules:
            if m["shortname"].strip().decode() == "VMP data":
                data_module = m
        if data_module is None:
            raise IOError("No data module!")

        data_version = data_module["version"]
        n_data_points = np.fromstring(data_module["data"][:4], dtype="<u4")[0]
        n_columns = np.fromstring(data_module["data"][4:5], dtype="u1")[0]
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
            self.logger.debug("UPS! you have some columns left")
            self.logger.debug(whats_left)

        dtype_dict = OrderedDict()
        flags_dict = OrderedDict()

        for col in column_types:
            if col in bl_flags.keys():
                flags_dict[bl_flags[col][0]] = bl_flags[col][1]

            dtype_dict[bl_dtypes[col][1]] = bl_dtypes[col][0]

        self.dtype_dict = dtype_dict
        self.flags_dict = flags_dict

        dtype = np.dtype(list(dtype_dict.items()))

        p = dtype.itemsize
        if not p == (len(main_data) / n_data_points):
            self.logger.info(
                "WARNING! You have defined %i bytes, "
                "but it seems it should be %i" % (p, len(main_data) / n_data_points)
            )
        bulk = main_data
        bulk_data = np.fromstring(bulk, dtype=dtype)
        mpr_data = pd.DataFrame(bulk_data)

        self.logger.debug(mpr_data.columns)
        self.logger.debug(mpr_data.head())

        # ------------- log  -----------------------------------
        log_module = None
        for m in mpr_modules:
            if m["shortname"].strip().decode() == "VMP LOG":
                log_module = m
        if log_module is None:
            txt = "error - no log module"
            raise IOError(txt)

        tm = time.strptime(log_module["date"].decode(), "%m.%d.%y")
        enddate = datetime.date(tm.tm_year, tm.tm_mon, tm.tm_mday)

        mpr_log = dict()
        mpr_log["end_date"] = enddate
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

    def _rename_header(self, h_old, h_new):
        try:
            self.mpr_data.rename(
                columns={h_new: self.cellpy_headers[h_old]}, inplace=True
            )
        except KeyError as e:
            # warnings.warn(f"KeyError {e}")
            self.logger.info(f"Problem during conversion to cellpy-format ({e})")

    def _generate_cycle_index(self):
        flag = "Ns changes"
        n = self._get_flag(flag)
        self.mpr_data[self.cellpy_headers["cycle_index_txt"]] = 1
        ns_changes = self.mpr_data[n].index.values
        for i in ns_changes:
            self.mpr_data.loc[i:, self.cellpy_headers["cycle_index_txt"]] += 1

    def _generate_datetime(self):
        start_date = self.mpr_settings["start_date"]
        start_datetime = self.mpr_log["Start"]
        cellpy_header_txt = "datetime_txt"
        date_format = "%Y-%m-%d %H:%M:%S"  # without microseconds
        self.mpr_data[self.cellpy_headers[cellpy_header_txt]] = [
            start_datetime + datetime.timedelta(seconds=n)
            for n in self.mpr_data["time"].values
        ]
        # self.mpr_data[self.cellpy_headers[cellpy_header_txt]]
        # .start_date.strftime(date_format)
        # TODO: @jepe - currently storing as datetime object
        # (while for arbindata it is stored as str)

    def _generate_step_index(self):
        # TODO: @jepe - check and optionally fix me
        cellpy_header_txt = "step_index_txt"
        biologics_header_txt = "flags2"
        self._rename_header(cellpy_header_txt, biologics_header_txt)
        self.mpr_data[self.cellpy_headers[cellpy_header_txt]] += 1

    def _generate_step_time(self):
        # TODO: @jepe - fix me
        self.mpr_data[self.cellpy_headers["step_time_txt"]] = np.nan

    def _generate_sub_step_time(self):
        # TODO: @jepe - fix me
        self.mpr_data[self.cellpy_headers["sub_step_time_txt"]] = np.nan

    def _generate_capacities(self):
        cap_col = self.mpr_data["QChargeDischarge"]
        self.mpr_data[self.cellpy_headers["discharge_capacity_txt"]] = [
            0.0 if x < 0 else x for x in cap_col
        ]
        self.mpr_data[self.cellpy_headers["charge_capacity_txt"]] = [
            0.0 if x >= 0 else x for x in cap_col
        ]

    def _rename_headers(self):
        # should ideally use the info from bl_dtypes, will do that later

        self.mpr_data[self.cellpy_headers["internal_resistance_txt"]] = np.nan
        self.mpr_data[self.cellpy_headers["data_point_txt"]] = np.arange(
            1, self.mpr_data.shape[0] + 1, 1
        )
        self._generate_datetime()
        self._generate_cycle_index()

        self._generate_step_time()
        self._generate_sub_step_time()
        self._generate_step_index()
        self._generate_capacities()

        # simple renaming of column headers for the rest
        self._rename_header("frequency_txt", "freq")
        self._rename_header("voltage_txt", "Ewe")
        self._rename_header("current_txt", "I")
        self._rename_header("aci_phase_angle_txt", "phaseZ")
        self._rename_header("amplitude_txt", "absZ")
        self._rename_header("ref_voltage_txt", "Ece")
        self._rename_header("ref_aci_phase_angle_txt", "phaseZce")
        self._rename_header("test_time_txt", "time")

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
        warnings.warn(
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


if __name__ == "__main__":
    import logging
    import sys
    import os
    from cellpy import log
    from cellpy import cellreader

    # -------- defining overall path-names etc ----------
    current_file_path = os.path.dirname(os.path.realpath(__file__))
    # relative_test_data_dir = "../cellpy/data_ex"
    relative_test_data_dir = "../../../testdata"
    relative_out_data_dir = "../../../dev_data"
    test_data_dir = os.path.abspath(
        os.path.join(current_file_path, relative_test_data_dir)
    )
    test_data_dir_out = os.path.abspath(
        os.path.join(current_file_path, relative_out_data_dir)
    )
    test_data_dir_raw = os.path.join(test_data_dir, "data")
    if not os.path.isdir(test_data_dir_raw):
        print(f"Could not find {test_data_dir_raw}")
        sys.exit(-23)
    if not os.path.isdir(test_data_dir_out):
        sys.exit(-24)

    if not os.path.isdir(os.path.join(test_data_dir_out, "out")):
        os.mkdir(os.path.join(test_data_dir_out, "out"))
    test_data_dir_out = os.path.join(test_data_dir_out, "out")

    test_raw_file = "biol.mpr"
    test_raw_file_full = os.path.join(test_data_dir_raw, test_raw_file)

    test_data_dir_cellpy = os.path.join(test_data_dir, "hdf5")
    test_cellpy_file = "geis.h5"
    test_cellpy_file_tmp = "tmpfile.h5"
    test_cellpy_file_full = os.path.join(test_data_dir_cellpy, test_cellpy_file)
    test_cellpy_file_tmp_full = os.path.join(test_data_dir_cellpy, test_cellpy_file_tmp)

    raw_file_name = test_raw_file_full
    print("\n======================mpr-dev===========================")
    print(f"Test-file: {raw_file_name}")
    log.setup_logging(default_level="DEBUG")
    instrument = "biologics_mpr"
    cellpy_data_instance = cellreader.CellpyData()
    cellpy_data_instance.set_instrument(instrument=instrument)
    print("starting to load the file")
    cellpy_data_instance.from_raw(raw_file_name)
    print("printing cellpy instance:")
    print(cellpy_data_instance)

    print("---make step table")
    cellpy_data_instance.make_step_table()

    print("---make summary")
    cellpy_data_instance.make_summary()

    print("---saving to csv")
    try:
        temp_dir = tempfile.mkdtemp()
        cellpy_data_instance.to_csv(datadir=temp_dir)
        cellpy_data_instance.to_csv(datadir=test_data_dir_out)
        print("---saving to hdf5")
        print("NOT YET")
    finally:
        shutil.rmtree(temp_dir)


# dtype = dtype([('flags', 'u1'), ('time/s', '<f8'), ('Ewe/V', '<f4'), ('dQ/mA.h', '<f8'),
#        ('I/mA', '<f4'), ('Ece/V', '<f4'), ('(Q-Qo)/mA.h', '<f8'), ('20', '<f8'),
#        ('freq/Hz', '<f4'), ('Phase(Z)/deg', '<f4'), ('|Z|/Ohm', '<f4'),
#        ('I Range', '<u2'), ('74', '<f8'), ('96', '<f8'), ('98', '<f8'),
#        ('99', '<f8'), ('100', '<f8'), ('101', '<f8'), ('123', '<f8'),
#        ('124', '<f8'), ('Capacitance charge/µF', '<f8'), ('Capacitance discharge/µF', '<f8'),
#        ('Ns', '<u2'), ('430', '<f8'), ('431', '<f8'), ('432', '<f8'), ('433', '<f8'),
#        ('Q charge/discharge/mA.h', '<f8'), ('half cycle', '<u4'), ('469', '<f8'),
#        ('471', '<f8')])
#
# flags = OrderedDict(
#     [
#         ('mode', (3, <class 'numpy.uint8'>)),('ox/red', (4, <class 'numpy.bool_'>)),
#         ('error', (8, <class 'numpy.bool_'>)), ('control changes', (16, <class 'numpy.bool_'>)),
#         ('Ns changes', (32, <class 'numpy.bool_'>)), ('counter inc.', (128, <class 'numpy.bool_'>))]
# )
# flags2 = OrderedDict()
