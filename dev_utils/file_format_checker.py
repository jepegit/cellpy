import os
import sys
import pandas as pd
import struct
import numpy as np


def check_biologic():
    mpr_label = b'BIO-LOGIC MODULAR FILE\x1a                         \x00\x00\x00\x00'
    VMPmodule_hdr = np.dtype([('shortname', 'S10'),
                              ('longname', 'S25'),
                              ('length', '<u4'),
                              ('version', '<u4'),
                              ('date', 'S8')])

    test_file = "../cellpy/data_ex/biologic/Bec01_01_1_C20_loop_20170219_01_MB_C02.mpr"
    if not os.path.isfile(test_file):
        print "file not found"
        return

    with open(test_file, mode="rb") as infile:
        # First - checking if it has the correct label
        label = infile.read(len(mpr_label))
        if label != mpr_label:
            raise ValueError('Invalid magic for .mpr file: %s' % label)

        while True:
            # Then - checking if we have reached a module
            module_txt = infile.read(len(b'MODULE'))
            hdr_bytes = infile.read(VMPmodule_hdr.itemsize)

            if module_txt == b'MODULE':
                hdr = np.fromstring(hdr_bytes, dtype=VMPmodule_hdr, count=1)

                hdr_dict = dict(((n, hdr[n][0]) for n in VMPmodule_hdr.names))
                print "\n\nNEW MODULE"
                print hdr

                for key, values in hdr_dict.iteritems():
                    print 30*"="
                    print key
                    print 30*"-"
                    print values
                    print
                hdr_dict['offset'] = infile.tell()

                hdr_dict['data'] = infile.read(hdr_dict['length'])
                print "\nLoaded new set of data"



            if len(module_txt) == 0:  # end of file
                break




    print "OK"



    # print "testing galvani BioLogic.py"
    # mpr1 = MPRfile(test_file)
    #
    # print mpr1

    # eq_(mpt1.dtype.names, ("mode", "ox/red", "error", "control changes",
    #                        "Ns changes", "counter inc.", "time/s",
    #                        "control/V/mA", "Ewe/V", "dQ/mA.h", "P/W",
    #                        "I/mA", "(Q-Qo)/mA.h", "x"))



if __name__ == '__main__':
    check_biologic()
