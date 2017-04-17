import os
import time
from collections import OrderedDict
from datetime import date

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

SEEK_SET = 0 # from start
SEEK_CUR = 1 # from current position
SEEK_END = 2 # from end of file



from biologic_file_format import bl_dtypes, hdr_dtype, mpr_label


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

    #So - lets see what we got in this module:
    # for bl_module in mpr_modules:
    #     print 50*":"
    #     for key, v in bl_module.items():
    #         if not key=="data":
    #             print "%s: %s" % (key, v)
    #
    #
    #
    # print "\n"
    # print 50*"-"

    # VMP log -----------------------------------------------
    # Not implemented yet

    # VMP settings ------------------------------------------
    # print 30 * "-"
    # print "parsing the VMP Set module\n"
    settings_mod = None
    for m in mpr_modules:
        if m["shortname"].strip() == "VMP Set":
            settings_mod = m
    if settings_mod is None:
        print "error - no setting module"


    tm = time.strptime(str(settings_mod['date']), '%m.%d.%y')
    startdate = date(tm.tm_year, tm.tm_mon, tm.tm_mday)
    # print "startdate:",
    # print startdate

    mpr_settings = dict()
    mpr_settings["start_date"] = startdate

    # VMP data ---------------------------------------------------
    # print 30 * "-"
    # print "parsing the VMP data module\n"
    data_module = None
    for m in mpr_modules:
        if m["shortname"].strip() == 'VMP data':
            data_module = m
    if data_module is None:
        print "error - no data module"

    data_version = data_module["version"]

    n_data_points = np.fromstring(data_module['data'][:4], dtype='<u4')[0]
    n_columns = np.fromstring(data_module['data'][4:5], dtype='u1')[0]
    # print "v: %i" % data_version
    # print "#points: %i" % n_data_points
    # print "#cols: %i" % n_columns


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
        print "ERROR you have some columns left"

    # now for the tedious bit: find out what each stuff is
    # dtype = VMPdata_dtype_from_colIDsOLD(column_types)
    dtype_dict = OrderedDict()
    for col in column_types:
        txt = "%i: %s" % (col, bl_dtypes[col][1])
        dtype_dict[bl_dtypes[col][1]] = bl_dtypes[col][0]
        print txt
    dtype = np.dtype(list(dtype_dict.items()))
    # print 50*"="
    # print "checking the dtypes"
    # print
    # print dtype.shape
    # print dtype.name
    # print dtype.names
    # print dtype.descr
    # print dtype.itemsize

    p = dtype.itemsize
    if not p == (len(main_data)/n_data_points):
        print "WARNING",
        print "You have defined %i bytes, but it seems it should be %i" % (p,len(main_data)/n_data_points)
    t = []
    # for n in range(20):
    #     #print n
    #     test_line = main_data[n*p:(n+1)*p]
    #     #print repr(test_line)
    #     test_data = np.fromstring(test_line, dtype=dtype)
    #     print test_data['time/s']
    # print t

    print "checking lenght of data"
    len_data = len(main_data)

    # print len_data/n_data_points
    #
    # print "len_data %i " % len_data

    number_of_lines = len_data / p
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

    print "Length of the header line:", hdr_dtype.itemsize
    print "Length of the filestamp line:", len(mpr_label)

    # test_file = "../cellpy/data_ex/biologic/Bec01_01_1_C20_loop_20170219_01_MB_C02.mpr"
    file_name = "../cellpy/data_ex/biologic/Bec_03_02_C20_delith_GEIS_Soc20_steps_C02.mpr"
    if not os.path.isfile(file_name):
        print "file not found"

    statinfo = os.stat(file_name)
    print "size of file:",
    print statinfo.st_size

    mpr_data, mpr_log, mpr_settings = _load_mpr(file_name)
    print mpr_data.head(20)
    print mpr_data.tail(5)

    filename_out = os.path.splitext(file_name)[0] + "_test_out.csv"
    print file_name
    print "->"
    print filename_out
    mpr_data.to_csv(filename_out, sep=";")

    fig, ax = plt.subplots(5)
    ax[0].plot(mpr_data["time"], mpr_data["Ewe"])
    ax[0].plot(mpr_data["time"], mpr_data["Ece"])
    ax[1].plot(mpr_data["time"], mpr_data["flags"], '.')
    ax[2].plot(mpr_data["time"], mpr_data["flags2"], '.')
    ax[3].plot(mpr_data["time"], mpr_data["QChargeDischarge"], '.')
    ax[4].plot(mpr_data["time"], mpr_data["phaseZce"])

    plt.legend()
    plt.show()
