"""biologics mpr-type data files"""

import os
import tempfile
import shutil
import logging
import warnings
import numpy as np
import pandas as pd

import time
from collections import OrderedDict
from datetime import date

from biologic_file_format import bl_dtypes, hdr_dtype, mpr_label

from cellpy.readers.cellreader import DataSet
from cellpy.readers.cellreader import FileID
from cellpy.readers.cellreader import humanize_bytes
from cellpy.readers.cellreader import check64bit
from cellpy.readers.cellreader import get_headers_normal
from cellpy.readers.instruments.mixin import Loader
import cellpy.parameters.prms as prms


SEEK_SET = 0  # from start
SEEK_CUR = 1  # from current position
SEEK_END = 2  # from end of file

# The columns to choose if minimum selection is selected
MINIMUM_SELECTION = ["Data_Point", "Test_Time", "Step_Time", "DateTime", "Step_Index", "Cycle_Index",
                     "Current", "Voltage", "Charge_Capacity", "Discharge_Capacity", "Internal_Resistance"]

# Names of the tables in the .res db that is used by cellpy
TABLE_NAMES = {
    "normal": "Channel_Normal_Table",
    "global": "Global_Table",
    "statistic": "Channel_Statistic_Table",
}


def _read_modules(fileobj):
    module_magic = fileobj.read(len(b'MODULE'))
    hdr_bytes = fileobj.read(hdr_dtype.itemsize)
    hdr = np.fromstring(hdr_bytes, dtype=hdr_dtype, count=1)
    hdr_dict = dict(((n, hdr[n][0]) for n in hdr_dtype.names))
    hdr_dict['offset'] = fileobj.tell()
    hdr_dict['data'] = fileobj.read(hdr_dict['length'])
    fileobj.seek(hdr_dict['offset'] + hdr_dict['length'], SEEK_SET)
    hdr_dict['end'] = fileobj.tell()
    return hdr_dict





class MprLoader(Loader):
    """ Class for loading biologics-data from mpr-files."""

    # Note: the class is sub-classing Loader. At the moment, Loader does not really contain anything...

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.headers_normal = get_headers_normal()
        self.current_chunk = 0  # use this to set chunks to load

    @staticmethod
    def get_raw_units():
        """Include the settings for the units used by the instrument.

        The units are defined w.r.t. the SI units ('unit-fractions'; currently only units that are multiples of
        Si units can be used). For example, for current defined in mA, the value for the
        current unit-fraction will be 0.001.

        Returns: dictionary containing the unit-fractions for current, charge, and mass

        """
        raw_units = dict()
        raw_units["current"] = 1.0  # A
        raw_units["charge"] = 1.0  # Ah
        raw_units["mass"] = 0.001  # g
        return raw_units

    @staticmethod
    def get_raw_limits():
        """Include the settings for how to decide what kind of step you are examining here.

        The raw limits are 'epsilons' used to check if the current and/or voltage is stable (for example
        for galvanostatic steps, one would expect that the current is stable (constant) and non-zero).
        It is expected that different instruments (with different resolution etc.) have different
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
            information about the raw file (needed by the `from_intermediate_file` function)

        """
        raise NotImplementedError


    def loader(self, file_name, bad_steps=None, **kwargs):
        """Loads data from biologics .mpr files.

        Args:
            file_name (str): path to .res file.
            bad_steps (list of tuples): (c, s) tuples of steps s (in cycle c) to skip loading.

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

        table_name_global = TABLE_NAMES["global"]
        table_name_stats = TABLE_NAMES["statistic"]

        # creating temporary file and connection

        temp_dir = tempfile.gettempdir()
        temp_filename = os.path.join(temp_dir, os.path.basename(file_name))
        shutil.copy2(file_name, temp_dir)

        self.logger.debug("tmp file: %s" % temp_filename)
        self.logger.debug("HERE WE LOAD THE DATA")

        data = DataSet()
        fid = FileID(file_name)

        # div parameters and information (probably load this last)
        test_no = 1
        data.test_no = test_no
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
        mpr_data, mpr_log, mpr_settings = self._load_mpr_data(temp_filename, bad_steps)
        # maybe insert tweaking of mpr_data here
        dfdata = mpr_data
        length_of_test = dfdata.shape[0]
        self.logger.debug(f"length of test: {length_of_test}")

        print("----------trying-to-rename-cols--------------------")
        # tname = r"C:\Scripting\MyFiles\development_cellpy\dev_data\tmp\out.xxx"
        # self.__raw_export(tname, dfdata)
        dfdata = self._rename_headers(dfdata)

        # ---------  stats-data (summary-data) ----------------------
        summary_df = self._create_summary_data(mpr_log, mpr_settings)


        if summary_df.empty:
            txt = "\nCould not find any summary (stats-file)!"
            txt += "\n -> issue make_summary(use_cellpy_stat_file=False)"
            warnings.warn(txt)

        data.dfsummary = summary_df
        data.dfdata = dfdata
        data.raw_data_files_length.append(length_of_test)
        new_tests.append(data)

        self._clean_up(temp_filename)
        return new_tests



    def _load_mpr_data(self, filename, bad_steps):
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

        settings_mod = None
        for m in mpr_modules:
            if m["shortname"].strip().decode() == "VMP Set":
                settings_mod = m
        if settings_mod is None:
            print("error - no setting module")

        tm = time.strptime(settings_mod['date'].decode(), '%m.%d.%y')
        startdate = date(tm.tm_year, tm.tm_mon, tm.tm_mday)

        mpr_settings = dict()
        mpr_settings["start_date"] = startdate

        data_module = None
        for m in mpr_modules:
            if m["shortname"].strip().decode() == 'VMP data':
                data_module = m
        if data_module is None:
            print("error - no data module")

        data_version = data_module["version"]

        n_data_points = np.fromstring(data_module['data'][:4], dtype='<u4')[0]
        n_columns = np.fromstring(data_module['data'][4:5], dtype='u1')[0]

        if data_version == 0:
            column_types = np.fromstring(data_module['data'][5:], dtype='u1',
                                         count=n_columns)

            remaining_headers = data_module['data'][5 + n_columns:100]
            main_data = data_module['data'][100:]

        elif data_version == 2:
            column_types = np.fromstring(data_module['data'][5:], dtype='<u2', count=n_columns)
            main_data = data_module['data'][405:]
            remaining_headers = data_module['data'][5 + 2 * n_columns:405]

        else:
            raise ValueError("Unrecognised version for data module: %d" % data_version)


        whats_left = remaining_headers.strip(b'\x00').decode("utf8")
        if whats_left:
            self.logger.debug("UPS! you have some columns left")
            self.logger.debug(whats_left)

        dtype_dict = OrderedDict()
        for col in column_types:
            dtype_dict[bl_dtypes[col][1]] = bl_dtypes[col][0]
        dtype = np.dtype(list(dtype_dict.items()))

        p = dtype.itemsize
        if not p == (len(main_data) / n_data_points):
            self.logger.info("WARNING! You have defined %i bytes, but it seems it should be %i" % (p, len(main_data) /
                                                                                                   n_data_points))
        bulk = main_data
        bulk_data = np.fromstring(bulk, dtype=dtype)
        mpr_data = pd.DataFrame(bulk_data)

        self.logger.debug(mpr_data.columns)
        self.logger.debug(mpr_data.head())
        # TODO: rename headers (use bl_dtypes) to correspond to the cellpy-headers (and do the needed arithmetic)

        return mpr_data, mpr_log, mpr_settings

    def _rename_header(self, dfdata, cellpy_headers, h_old, h_new):
        try:
            #dfdata[cellpy_headers[h_old]] = dfdata[h_new]
            dfdata.rename(columns={h_new: cellpy_headers[h_old]}, inplace=True)
            return dfdata
        except KeyError as e:
            # warnings.warn(f"KeyError {e}")
            self.logger.info(f"Problem during conversion to cellpy-format ({e})")

    def _generate_cycle_index(self, dfdata):
        return 1

    def _generate_datetime(self, dfdata):
        return 1

    def _generate_step_index(self, dfdata, cellpy_headers):
        return self._rename_header(dfdata, cellpy_headers, "step_index_txt", "flags2")

    def _generate_step_time(self, dfdata, cellpy_headers):
        dfdata[cellpy_headers["step_time_txt"]] = np.nan
        return dfdata

    def _generate_sub_step_time(self, dfdata, cellpy_headers):
        dfdata[cellpy_headers["sub_step_time_txt"]] = np.nan
        return dfdata

    def _rename_headers(self, dfdata):
        print(dfdata.columns)
        cellpy_headers = get_headers_normal()
        print(cellpy_headers)

        # should ideally use the info from bl_dtypes, will do that later
        dfdata[cellpy_headers["internal_resistance_txt"]] = np.nan
        dfdata[cellpy_headers["data_point_txt"]] = np.arange(1,dfdata.shape[0]+1,1)
        dfdata[cellpy_headers["cycle_index_txt"]] = self._generate_cycle_index(dfdata)
        dfdata[cellpy_headers["datetime_txt"]] = self._generate_datetime(dfdata)

        dfdata = self._generate_step_time(dfdata, cellpy_headers)
        dfdata = self._generate_sub_step_time(dfdata, cellpy_headers)
        dfdata = self._generate_step_index(dfdata, cellpy_headers)
        dfdata[cellpy_headers["sub_step_index_txt"]] = dfdata[cellpy_headers["step_index_txt"]]

        dfdata[cellpy_headers["datetime_txt"]] = self._generate_datetime(dfdata)

        # simple renaming of column headers for the rest
        self._rename_header(dfdata, cellpy_headers,"frequency_txt", "freq")
        self._rename_header(dfdata, cellpy_headers, "voltage_txt", "Ewe")
        self._rename_header(dfdata, cellpy_headers, "current_txt", "I")
        self._rename_header(dfdata, cellpy_headers, "aci_phase_angle_txt", "phaseZ")
        self._rename_header(dfdata, cellpy_headers, "amplitude_txt", "absZ")
        self._rename_header(dfdata, cellpy_headers, "ref_voltage_txt", "Ece")
        self._rename_header(dfdata, cellpy_headers, "ref_aci_phase_angle_txt", "phaseZce")
        self._rename_header(dfdata, cellpy_headers, "discharge_capacity_txt", "QChargeDischarge")
        self._rename_header(dfdata, cellpy_headers, "charge_capacity_txt", "QChargeDischarge")
        self._rename_header(dfdata, cellpy_headers, "test_time_txt", "time")
        return dfdata

    def _create_summary_data(self, *args):
        raise NotImplementedError


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
                self.logger.warning("could not remove tmp-file\n%s %s" % (tmp_filename, e))
        pass



if __name__ == '__main__':
    import logging
    from cellpy import log
    from cellpy import cellreader
    file_name = 'C:\\Scripting\\MyFiles\\development_cellpy\\testdata\\data\\geis.mpr'
    log.setup_logging(default_level="DEBUG")
    instrument = "biologics_mpr"
    cellpy_data_instance = cellreader.CellpyData()
    cellpy_data_instance.set_instrument(instrument=instrument)
    cellpy_data_instance.from_raw(file_name)
    cellpy_data_instance.make_step_table()
    cellpy_data_instance.make_summary()
    temp_dir = tempfile.mkdtemp()
    cellpy_data_instance.to_csv(datadir=temp_dir)
    shutil.rmtree(temp_dir)
