"""This file contains methods for importing Bio-Logic files"""
# This is based on the work by Chris Kerr
# (https://github.com/chatcannon/galvani/blob/master/galvani/BioLogic.py)

import os
import tempfile
import shutil
import logging
import warnings
import numpy as np
import pandas as pd

import os
import time
from collections import OrderedDict
from datetime import date

from .biologic_file_format import bl_dtypes, hdr_dtype, mpr_label

from cellpy.readers.cellreader import DataSet
from cellpy.readers.cellreader import FileID
from cellpy.readers.cellreader import humanize_bytes
from cellpy.readers.cellreader import check64bit
from cellpy.readers.cellreader import get_headers_normal


import warnings
warnings.warn("not fully implemented yet")

SEEK_SET = 0 # from start
SEEK_CUR = 1 # from current position
SEEK_END = 2 # from end of file
# The columns to choose if minimum selection is selected
MINIMUM_SELECTION = []


class BioLogicLoader(object):
    """ Class for loading biologic-data from ?-files."""

    def __init__(self):
        """initiates the BioLogicLoader class"""
        # could use __init__(self, cellpydata_object) and set self.logger = cellpydata_object.logger etc.
        # then remember to include that as prm in "out of class" functions
        self.logger = logging.getLogger()
        self.load_only_summary = False
        self.select_minimal = False
        self.max_filesize = 150000000
        self.position = 0

        self.chunk_size = None  # 100000
        self.max_chunks = None
        self.last_chunk = None
        self.limit_loaded_cycles = None

        self.headers_normal = get_headers_normal()

    @staticmethod
    def get_raw_limits():
        """Include the settings for how to decide what kind of step you are examining here.

        The raw limits are 'epsilons' used to check if the current and/or voltage is stable (for example
        for galvanostatic steps, one would expect that the current is stable (constant) and non-zero).
        It is expected that different instruments (with different resolution etc.) have different
        'epsilons'.

        OBS! Not properly set yet.

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

    @staticmethod
    def get_raw_units():
        """Include the settings for the units used by the instrument.

        The units are defined w.r.t. the SI units ('unit-fractions'; currently only units that are multiples of
        Si units can be used). For example, for current defined in mA, the value for the
        current unit-fraction will be 0.001.

        OBS! Not properly set yet.

        Returns: dictionary containing the unit-fractions for current, charge, and mass

        """
        raw_units = dict()
        raw_units["current"] = 1.0  # A (should be in mA, think it is 0.001)
        raw_units["charge"] = 1.0  # Ah (should be in mAh, think it is 0.001)
        raw_units["mass"] = 0.001  # g
        return raw_units

    def loader(self,file_name=None):
        """Loads data from biologic .? files.

        Args:
            file_name (str): path to .? file.

        Returns:
            new_tests (list of data objects), FileError

        """

        new_tests = []
        if not os.path.isfile(file_name):
            print("Missing file_\n   %s" % file_name)

        filesize = os.path.getsize(file_name)
        hfilesize = humanize_bytes(filesize)
        txt = "Filesize: %i (%s)" % (filesize, hfilesize)
        self.logger.debug(txt)

        # --- temp-file
        temp_dir = tempfile.gettempdir()
        temp_filename = os.path.join(temp_dir, os.path.basename(file_name))
        shutil.copy2(file_name, temp_dir)
        print(".", end=' ')


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

        -adds missing columns (with np.nan)
        """
        checked_rundata = []
        for data in run_data:
            new_cols = data.dfdata.columns
            for col in self.headers_normal:
                if not col in new_cols:
                    data.dfdata[col] = np.nan
            checked_rundata.append(data)
        return checked_rundata

    def repair(self):
        """try to repair a broken/corrupted file"""
        pass

    def get_update(self):
        last_position = self.position
        # self._update(last_position)
        new_position =  last_position
        self.position = new_position


def simple_check(filename):
    """Load a raw data file """
    print("1")
    a = BioLogicLoader()
    a.load(filename)
    print("2")


def simple_load_and_save(file_name):
    """Load a raw data BioLogic mpr file """
    import logging
    from cellpy import log
    log.setup_logging(default_level=logging.DEBUG)

    print("Length of the header line:", hdr_dtype.itemsize)
    print("Length of the filestamp line:", len(mpr_label))

    if not os.path.isfile(file_name):
        print("file not found")

    statinfo = os.stat(file_name)
    print("size of file:", end=" ")
    print(statinfo.st_size)

    mpr_data, mpr_log, mpr_settings = _load_mpr(file_name)

    print(50*"-")
    print("\nhead:")
    print(mpr_data.head(20))
    print("\ntail:")
    print(mpr_data.tail(5))

    print(50 * "-")
    print("\nsettings:")
    print(mpr_settings)

    filename_out = os.path.splitext(file_name)[0] + "_test_out.csv"
    print(50 * "-")
    print(file_name)
    print("->")
    print(filename_out)
    print(50 * "-")
    mpr_data.to_csv(filename_out, sep=";")
    print("OK")



def _read_modules(fileobj):
    module_magic = fileobj.read(len(b'MODULE'))
    # print repr(module_magic)
    hdr_bytes = fileobj.read(hdr_dtype.itemsize)  # this contains the headers
    # print repr(hdr_bytes)
    hdr = np.fromstring(hdr_bytes, dtype=hdr_dtype, count=1)  # converting the headers from bytes
    hdr_dict = dict(((n, hdr[n][0]) for n in hdr_dtype.names))
    hdr_dict['offset'] = fileobj.tell()  # saving the position in the file
    # so - lets read all the stuff until we have reached 'length'
    hdr_dict['data'] = fileobj.read(hdr_dict['length'])
    # Setting the position in the file (why?, isnt this already where we are?)
    fileobj.seek(hdr_dict['offset'] + hdr_dict['length'], SEEK_SET)
    hdr_dict['end'] = fileobj.tell()
    # Maybe due to the "speed-up" tweak in Python 2.7 for .read()?
    # No, it seems that you can set the file position "further" than the actual size of the file
    # That is maybe strange.
    return hdr_dict


def _load_mpr(file_name):
    mpr_modules = []

    mpr_log = None
    mpr_data = None
    mpr_settings = None

    file_obj = open(file_name, mode="rb")

    # Starting with reading the "first line"
    label = file_obj.read(len(mpr_label))  # this is the file-stamp

    # Then, lets iterate through the file and get the modules
    counter = 0
    while True:
        counter += 1
        txt =  "try %i\n" % (counter)
        new_module = _read_modules(file_obj)
        position = int(new_module["end"])
        mpr_modules.append(new_module)
        # write to log
        if position >= statinfo.st_size:
            txt =  "-reached end of file\n"
            if position == statinfo.st_size:
                txt += "--- exactly at end of file\n"
            # write to log
            break

    # closing the file
    file_obj.close()

    # VMP log -----------------------------------------------
    # Not implemented yet

    # VMP settings ------------------------------------------
    settings_mod = None
    for m in mpr_modules:
        if m["shortname"].strip() == "VMP Set":
            settings_mod = m
    if settings_mod is None:
        print("error - no setting module")

    tm = time.strptime(str(settings_mod['date']), '%m.%d.%y')
    startdate = date(tm.tm_year, tm.tm_mon, tm.tm_mday)

    mpr_settings = dict()
    mpr_settings["start_date"] = startdate
    mpr_settings["column_types"] = list()
    mpr_settings["n_data_points"] = 0
    mpr_settings["n_columns"] = 0
    mpr_settings["data_version"] = None
    mpr_settings["module_items"] = list()

    for bl_module in mpr_modules:
        for key, v in bl_module.items():
            if not key=="data":
                mpr_settings["module_items"].append((key,v))


    # VMP data ---------------------------------------------------
    data_module = None
    for m in mpr_modules:
        if m["shortname"].strip() == 'VMP data':
            data_module = m
    if data_module is None:
        print("error - no data module")

    data_version = data_module["version"]
    mpr_settings["data_version"] = data_version

    n_data_points = np.fromstring(data_module['data'][:4], dtype='<u4')[0]
    n_columns = np.fromstring(data_module['data'][4:5], dtype='u1')[0]
    mpr_settings["n_data_points"] = n_data_points
    mpr_settings["n_columns"] = n_columns

    if data_version == 0:
        column_types = np.fromstring(data_module['data'][5:], dtype='u1',
                                     count=n_columns)

        remaining_headers = data_module['data'][5 + n_columns:100]
        main_data = data_module['data'][100:]

    elif data_version == 2:
        column_types = np.fromstring(data_module['data'][5:], dtype='<u2', count=n_columns)
        main_data = data_module['data'][405:]

        ## There is 405 bytes of data before the main array starts
        remaining_headers = data_module['data'][5 + 2 * n_columns:405]

    else:
        raise ValueError("Unrecognised version for data module: %d" % data_version)

    whats_left = "%s" % str(remaining_headers).strip('\x00')
    if whats_left:
        print("ERROR you have some columns left")

    dtype_dict = OrderedDict()
    for col in column_types:
        mpr_settings["column_types"].append([col,bl_dtypes[col][1]])
        dtype_dict[bl_dtypes[col][1]] = bl_dtypes[col][0]

    dtype = np.dtype(list(dtype_dict.items()))

    p = dtype.itemsize
    if not p == (len(main_data)/n_data_points):
        print("WARNING")
        print("You have defined %i bytes, but it seems it should be %i" % (p,len(main_data)/n_data_points))


    # print("checking lenght of data")
    len_data = len(main_data)

    # print len_data/n_data_points
    #
    # print "len_data %i " % len_data

    # number_of_lines = len_data / p
    # print "length of lines %i " % p
    # print "number of lines %i " % number_of_lines
    #
    # print "multiplied %i" % (number_of_lines * p)
    # print "error %i" % (len_data - (number_of_lines*p))
    reminders = []
    for j in range(1,100):
        if not (len_data % j):
            reminders.append(j)

    # print reminders

    # bulk_size = 100
    # print "checking bulk of total size: %i" % (bulk_size*p)
    # print "remaining data: %fi" % (len_data - bulk_size*p)

    # bulk = main_data[0:bulk_size*p]
    bulk = main_data
    bulk_data = np.fromstring(bulk, dtype=dtype)
    #print bulk_data
    mpr_data = pd.DataFrame(bulk_data)

    return mpr_data, mpr_log, mpr_settings


    #print "dtype" # [('flags', 'u1'), ('flags2', '<u2'), ('I Range', '<u2'), ('time/s', '<f8'), ('NotKnown_20', '<f4'), ('Ewe/V', '<f4'), ('I/mA', '<f4'), ('NotKnown_13', '<f4'), ('NotKnown_74', '<f4'), ('NotKnown_467', '<f4'), ('NotKnown_468', '<f4'), ('NotKnown_9', '<f4')]
    #print dtype
    #print "flags_dict" # OrderedDict([('mode', (3, <type 'numpy.uint8'>)), ('ox/red', (4, <type 'numpy.bool_'>)), ('error', (8, <type 'numpy.bool_'>)), ('control changes', (16, <type 'numpy.bool_'>)), ('Ns changes', (32, <type 'numpy.bool_'>)), ('counter inc.', (128, <type 'numpy.bool_'>))])
    #print "flags2_dict" # OrderedDict([('??', (1, <type 'numpy.bool_'>))])



    # for line in lines_data[1:10]:
    #     print repr(line)

    #print repr(main_data)

    #data = np.fromstring(main_data, dtype=dtype)


if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import logging
    from cellpy import log
    log.setup_logging(default_level=logging.DEBUG)

    print("Length of the header line:", hdr_dtype.itemsize)
    print("Length of the filestamp line:", len(mpr_label))

    file_name = "../../data_ex/biologic/Bec01_01_1_C20_loop_20170219_01_MB_C02.mpr"
    # file_name = "../../data_ex/biologic/Bec_03_02_C20_delith_GEIS_Soc20_steps_C02.mpr"
    if not os.path.isfile(file_name):
        print("file not found")

    statinfo = os.stat(file_name)
    print("size of file:", end=" ")
    print(statinfo.st_size)

    mpr_data, mpr_log, mpr_settings = _load_mpr(file_name)
    print(mpr_data.head(20))
    print(mpr_data.tail(5))

    print(mpr_settings)


    filename_out = os.path.splitext(file_name)[0] + "_test_out.csv"
    print(file_name)
    print("->")
    print(filename_out)
    mpr_data.to_csv(filename_out, sep=";")

    fig, ax = plt.subplots(4)
    ax[0].plot(mpr_data["time"], mpr_data["Ewe"])
    ax[0].plot(mpr_data["time"], mpr_data["Ece"])
    ax[1].plot(mpr_data["time"], mpr_data["flags"], '.')
    ax[2].plot(mpr_data["time"], mpr_data["flags2"], '.')
    ax[3].plot(mpr_data["time"], mpr_data["QChargeDischarge"], '.')

    plt.legend()
    plt.show()

