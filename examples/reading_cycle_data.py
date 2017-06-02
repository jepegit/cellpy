# -*- coding: utf-8 -*-

"""

"""

from cellpy.readers import cellreader
import sys, os, csv, itertools
import matplotlib.pyplot as plt
import numpy as np

__author__ = 'Tor Kristian Vara', 'Jan Petter Maehlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'


def making_csv(filename, outfolder, mass, type_data):
    try:
        os.chdir(outfolder)
        print "Output will be sent to folder:"
        print outfolder
    except:
        print "outfolder does not exits"
        sys.exit(-1)

    # Loading arbin-data
    d = cellreader.CellpyData(filename)
    d.from_res()
    d.set_mass(mass)
    d.make_summary()
    d.make_step_table()

    # Making ocv
    extract_ocvrlx(d, filename=filename, type_data=type_data)

    print "\nexporting raw-data and summary"
    d.to_csv(outfolder)

    # Extracting cycles
    list_of_cycles = d.get_cycle_numbers()
    number_of_cycles = len(list_of_cycles)
    print "you have %i cycles" % (number_of_cycles)

    FileName0 = os.path.basename(filename)
    outfile = "%s_cap_voltage.csv" % (FileName0)
    out_data = []

    for cycle in list_of_cycles:
        try:
            c,v = d.get_cap(cycle)
            c = c.tolist()
            v = v.tolist()
            header_x = "cap cycle_no %i" % cycle
            header_y = "voltage cycle_no %i" % cycle
            c.insert(0,header_x)
            v.insert(0,header_y)
            out_data.append(c)
            out_data.append(v)
        except:
            print "could not extract cycle %i" % (cycle)


    # Saving cycles in one .csv file (x,y,x,y,x,y...)
    delimiter = ";"
    print "saving the file with delimiter '%s' " % (delimiter)
    with open(outfile, "wb") as f:
        writer=csv.writer(f,delimiter=delimiter)
        writer.writerows(itertools.izip_longest(*out_data))
        # star (or asterix) means transpose (writing cols instead of rows)

    print "saved the file",
    print outfile
    print "bye!"


def extract_ocvrlx(d_res, filename, type_data):
    out_data = []
    fileout = filename[:-3] + type_data
    for cycle in d_res.get_cycle_numbers():
        if cycle == d_res.get_cycle_numbers()[-1]:
            break
        else:
            try:
                if type_data == 'ocvrlx_up':
                    print "getting ocvrlx up data for cycle %i" % (cycle)
                    t, v = d_res.get_ocv(ocv_type='ocvrlx_up',
                                         cycle_number=cycle)
                else:
                    print "getting ocvrlx down data for cycle %i" % (cycle)
                    t, v = d_res.get_ocv(ocv_type='ocvrlx_down',
                                         cycle_number=cycle)
                plt.plot(t,v)
                t = t.tolist()
                v = v.tolist()

                header_x = "time (s) cycle_no %i" % cycle
                header_y = "voltage (V) cycle_no %i" % cycle
                t.insert(0, header_x)
                v.insert(0, header_y)
                out_data.append(t)
                out_data.append(v)

            except:
                print "could not extract cycle %i" % (cycle)


    # Saving cycles in one .csv file (x,y,x,y,x,y...)
    endstring = ".csv"
    outfile = fileout + endstring

    delimiter = ";"
    print "saving the file with delimiter '%s' " % (delimiter)
    with open(outfile, "wb") as f:
        writer=csv.writer(f,delimiter=delimiter)
        writer.writerows(itertools.izip_longest(*out_data))
        # star (or asterix) means transpose (writing cols instead of rows)

    print "saved the file",
    print outfile
    print "bye!"


# making_csv()
# extract_ocvrlx("ocvrlx_up")
# extract_ocvrlx("ocvrlx_down")
# plt.show()

# filename = r"C:\Users\torkv\OneDrive - Norwegian University of Life " \
#                r"Sciences\Documents\NMBU\master\ife\python\cellpy\cellpy" \
#                r"\data_ex\20160830_sic006_74_cc_01.res"
# mass = 0.86
# type_of_data = "ocvrlx_up"
# fileout = r"C:\Scripting\MyFiles\dev_cellpy\outdata" \
#           r"\20160805_sic006_74_cc_01_"+type_of_data
# sic006_74 = cellreader.CellpyData()
# sic006_74.from_res(filename)
# sic006_74.set_mass(mass)
# list_of_cycles = sic006_74.get_cycle_numbers()
# print len(list_of_cycles)

