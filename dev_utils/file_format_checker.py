import os
import sys
import pandas as pd
import struct
import numpy as np
import sys
import re
from datetime import date, datetime, timedelta
import time
from collections import OrderedDict
import matplotlib.pyplot as plt


SEEK_SET = 0 # from start
SEEK_CUR = 1 # from current position
SEEK_END = 2 # from end of file

mpr_label = b'BIO-LOGIC MODULAR FILE\x1a                         \x00\x00\x00\x00'

hdr_dtype = np.dtype([('shortname', 'S10'),('longname', 'S25'),('length', '<u4'),
                          ('version', '<u4'),('date', 'S8')])


from biologic_file_format import bl_dtypes

print bl_dtypes

def VMPdata_dtype_from_colIDsOLD(colIDs):
    dtype_dict = OrderedDict()
    for colID in colIDs:
        print "checking colID %i" % colID
        if colID in (1, 2, 3, 21, 31, 65):
            print "u1"
            dtype_dict['flags'] = 'u1'

        elif colID in (131,):
            dtype_dict['flags2'] = '<u2'
            print "u2"

        elif colID == 4:
            dtype_dict['time/s'] = '<f8'
            print "f8"
        elif colID == 5:
            dtype_dict['control/V/mA'] = '<f4'
        # 6 is Ewe, 77 is <Ewe>, I don't see the difference
        elif colID in (6, 77):
            dtype_dict['Ewe/V'] = '<f4'
        # Can't see any difference between 7 and 23
        elif colID in (7, 23):
            dtype_dict['dQ/mA.h'] = '<f8'
        # 76 is <I>, 8 is either I or <I> ??
        elif colID in (8, 76):
            dtype_dict['I/mA'] = '<f4' # changed to f8 from f4
        elif colID == 11:
            dtype_dict['I/mA'] = '<f8'
        elif colID == 19:
            dtype_dict['control/V'] = '<f4' # change to f8 from f4?
        elif colID == 24:
            dtype_dict['cycle number'] = '<f8'
        elif colID == 32:
            dtype_dict['freq/Hz'] = '<f4'
        elif colID == 33:
            dtype_dict['|Ewe|/V'] = '<f4'
        elif colID == 34:
            dtype_dict['|I|/A'] = '<f4'
        elif colID == 35:
            dtype_dict['Phase(Z)/deg'] = '<f4'
        elif colID == 36:
            dtype_dict['|Z|/Ohm'] = '<f4'
        elif colID == 37:
            dtype_dict['Re(Z)/Ohm'] = '<f4'
        elif colID == 38:
            dtype_dict['-Im(Z)/Ohm'] = '<f4'
        elif colID == 39:
            dtype_dict['I Range'] = '<u2'
            print "u2"

        elif colID == 70:
            dtype_dict['P/W'] = '<f4'
        elif colID == 434:
            dtype_dict['(Q-Qo)/C'] = '<f4'
        elif colID == 435:
            dtype_dict['dQ/C'] = '<f4'

        elif colID == 20:
            dtype_dict['NotKnown_20'] = '<f4'
        elif colID == 13:
            dtype_dict['NotKnown_13'] = '<f8'
        elif colID == 74:
            dtype_dict['NotKnown_74'] = '<f8'
        elif colID == 467:
            dtype_dict['NotKnown_467'] = '<f8'
        elif colID == 468:
            dtype_dict['NotKnown_468'] = '<f4'
        elif colID == 9:
            dtype_dict['NotKnown_9'] = '<f4'

        else:
            print "column type %d not implemented" % colID

            #raise NotImplementedError("column type %d not implemented" % colID)

    return np.dtype(list(dtype_dict.items()))




def read_module_1(fileobj):
    module_magic = fileobj.read(len(b'MODULE'))
    print repr(module_magic)


    hdr_bytes = fileobj.read(hdr_dtype.itemsize)  # this contains the headers
    print repr(hdr_bytes)
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


def check_biologic():


    mpr_modules = []


    print "Length of the header line:", hdr_dtype.itemsize
    print "Length of the filestamp line:", len(mpr_label)

    # test_file = "../cellpy/data_ex/biologic/Bec01_01_1_C20_loop_20170219_01_MB_C02.mpr"
    test_file = "../cellpy/data_ex/biologic/Bec_03_02_C20_delith_GEIS_Soc20_steps_C02.mpr"
    if not os.path.isfile(test_file):
        print "file not found"
        return

    statinfo = os.stat(test_file)
    print "size of file:",
    print statinfo.st_size
    fileobj = open(test_file, mode="rb")

    # Starting with reading the "first line"
    label = fileobj.read(len(mpr_label))  # this is the file-stamp
    print repr(mpr_label)
    print repr(label)

    # Then, lets try this
    for j in range(1000):
        print "try %i" % (j+1)
        new_module = read_module_1(fileobj)
        position = int(new_module["end"])
        mpr_modules.append(new_module)
        if position >= statinfo.st_size:
            print "-reached end of file"
            if position == statinfo.st_size:
                print "--- exactly at end of file"
            break

    # closing the file
    fileobj.close()


    # So - lets see what we got in this module:
    for bl_module in mpr_modules:
        print 50*":"
        for key, v in bl_module.items():
            if not key=="data":
                print "%s: %s" % (key, v)



    print "\n"
    print 50*"-"
    # data = mpr_modules[1]["data"]
    # print len(data)
    #print repr(data)


    # VMP settings ------------------------------------------
    print 30 * "-"
    print "parsing the VMP Set module\n"
    settings_mod = None
    for m in mpr_modules:
        if m["shortname"].strip() == "VMP Set":
            settings_mod = m
    if settings_mod is None:
        print "error - no setting module"


    tm = time.strptime(str(settings_mod['date']), '%m.%d.%y')
    startdate = date(tm.tm_year, tm.tm_mon, tm.tm_mday)
    print "startdate:",
    print startdate

    # VMP data ---------------------------------------------------
    print 30 * "-"
    print "parsing the VMP data module\n"
    data_module = None
    for m in mpr_modules:
        if m["shortname"].strip() == 'VMP data':
            data_module = m
    if data_module is None:
        print "error - no data module"

    data_version = data_module["version"]
    n_data_points = int(np.fromstring(data_module['data'][:4], dtype='<u4'))
    n_columns = int(np.fromstring(data_module['data'][4:5], dtype='u1'))
    print "v: %i" % data_version
    print "#points: %i" % n_data_points
    print "#cols: %i" % n_columns


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
        raise ValueError("Unrecognised version for data module: %d" %
                         data_version)

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
    print 50*"="
    print "checking the dtypes"
    print
    print dtype.shape
    print dtype.name
    print dtype.names
    print dtype.descr
    print dtype.itemsize

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

    print len_data/n_data_points

    print "len_data %i " % len_data

    number_of_lines = len_data / p
    print "length of lines %i " % p
    print "number of lines %i " % number_of_lines

    print "multiplied %i" % (number_of_lines * p)
    print "error %i" % (len_data - (number_of_lines*p))
    reminders = []
    for j in range(1,100):
        if not (len_data % j):
            reminders.append(j)

    print reminders

    bulk_size = 100
    print "checking bulk of total size: %i" % (bulk_size*p)
    print "remaining data: %fi" % (len_data - bulk_size*p)

    bulk = main_data[0:bulk_size*p]
    bulk = main_data
    bulk_data = np.fromstring(bulk, dtype=dtype)
    #print bulk_data
    df = pd.DataFrame(bulk_data)
    print df.head(20)
    print df.tail(5)
    filename_out = os.path.splitext(test_file)[0]+"_test_out.csv"
    print test_file
    print "->"
    print filename_out
    df.to_csv(filename_out, sep=";")
    #df.plot(x="time/s", y=["Ewe/V", "I/mA"])
    fig, ax = plt.subplots(5)
    ax[0].plot(df["time"], df["Ewe"])
    ax[0].plot(df["time"], df["Ece"])
    ax[1].plot(df["time"], df["flags"], '.')
    ax[2].plot(df["time"], df["flags2"], '.')
    ax[3].plot(df["time"], df["QChargeDischarge"], '.')
    ax[4].plot(df["time"], df["phaseZce"])

    plt.legend()

    plt.show()

    #print "dtype" # [('flags', 'u1'), ('flags2', '<u2'), ('I Range', '<u2'), ('time/s', '<f8'), ('NotKnown_20', '<f4'), ('Ewe/V', '<f4'), ('I/mA', '<f4'), ('NotKnown_13', '<f4'), ('NotKnown_74', '<f4'), ('NotKnown_467', '<f4'), ('NotKnown_468', '<f4'), ('NotKnown_9', '<f4')]
    #print dtype
    #print "flags_dict" # OrderedDict([('mode', (3, <type 'numpy.uint8'>)), ('ox/red', (4, <type 'numpy.bool_'>)), ('error', (8, <type 'numpy.bool_'>)), ('control changes', (16, <type 'numpy.bool_'>)), ('Ns changes', (32, <type 'numpy.bool_'>)), ('counter inc.', (128, <type 'numpy.bool_'>))])
    #print "flags2_dict" # OrderedDict([('??', (1, <type 'numpy.bool_'>))])



    # for line in lines_data[1:10]:
    #     print repr(line)

    #print repr(main_data)

    #data = np.fromstring(main_data, dtype=dtype)


if __name__ == '__main__':
    check_biologic()
