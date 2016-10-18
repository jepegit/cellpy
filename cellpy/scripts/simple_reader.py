# -*- coding: utf-8 -*-
"""simple script for reading .res-files from arbin

This script does not rely on any of the modules in cellpy.
"""

import shutil
import os
import sys
import tempfile
import time
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

try:
    import pyodbc as dbloader
except ImportError:
    print "could not import dbloader (pyodbc)"
    print "this script will not work without"
    sys.exit(0)


def convert2mAhg(d, mass=0.02):
    """

    Args:
        d: capacity
        mass (float): mass in mg

    Returns:
        np.array with capacity in mAh/g
    """
    d = np.array(d)
    return d * 1000000 / mass


def main():
    filename = "my_file.res" # write file name here
    lim_low = 970 # write minimum value for capacity (points less than that will be removed)
    lim_high = 1150 # write maximum value for capacity (points larger than that will be removed)
    mass = 0.02 # mass of (active material of) electrode in mg
    outdir = r"C:\data" # write path to were you want to save the data


    tablename_normal = "Channel_Normal_Table"
    tablename_global = "Global_Table"
    tablename_statistic = "Channel_Statistic_Table"
    fname = os.path.basename(filename)
    fname = os.path.splitext(fname)[0]
    outfile = os.path.join(outdir, fname + "_out.csv")
    outfile2 = os.path.join(outdir, fname + "_cdc.csv")


    print "filename:", filename

    # ------making temporary file-------------
    temp_dir = tempfile.gettempdir()
    temp_filename = os.path.join(temp_dir, os.path.basename(filename))
    print "Copying to tmp-file"
    print "temp_filename:", temp_filename

    shutil.copy2(filename, temp_dir)
    print "Finished to tmp-file"

    constructor = 'Driver={Microsoft Access Driver (*.mdb, *.accdb)};Dbq=' + temp_filename
    conn = dbloader.connect(constructor, autocommit=True)
    cur = conn.cursor()
    sql = "select * from %s" % tablename_normal
    cur.execute(sql)
    col_names = [i[0] for i in cur.description]

    # all_data=cur.fetchall()
    print "COLS:"
    for cname in col_names:
        print cname

    print
    print "reading file",

    # print all_data
    t = time.time()
    state_counter = 0
    limit_counter = 0
    limit = 11213440
    # limit = 100000

    V = []  # "Voltage"
    T = []  # "Test_Time"
    D = []  # "Discharge_Capacity"
    C = []  # "Charge_Capacity"
    I = []  # "Cycle_Index"

    step = 0
    cycle = 0
    v = 0.0
    t = 0.0
    d = 0.0
    c = 0.0

    ofile = open(outfile, 'w')
    header = "time;cycle;step;voltage;discharge_cap;charge_cap\n"
    ofile.write(header)

    for row in cur:
        if not row:
            break

        limit_counter += 1
        if limit_counter >= limit:
            print "x",
            break

        state_counter += 1
        # getting the cycle and step index
        _step = row.Step_Index
        _cycle = row.Cycle_Index
        _v = row.Voltage
        _t = row.Test_Time
        _d = row.Discharge_Capacity
        _c = row.Charge_Capacity
        otxt = "%f;%i;%i;%f;%f;%f\n" % (_t, _cycle, _step, _v, _d, _c)
        ofile.write(otxt)

        # is this a new cycle?
        if _cycle > cycle and cycle >= 1:
            # text = "(%i -> %i)" % (cycle,_cycle)
            # print text,
            print ".",
            if I.count(cycle) == 0:
                # print "s"
                I.append(cycle)
                V.append(v)
                T.append(t)
                D.append(d)
                C.append(c)
            else:
                i = I.index(cycle)
                v2 = V[i]
                t2 = T[i]
                d2 = D[i]
                c2 = C[i]
                update = False
                if d2 > d:
                    D[i] = d2
                    update = True
                if c2 > c:
                    C[i] = c2
                    update = True
                if update:
                    T[i] = t2
                    V[i] = v2

        # print

        # updating variables
        step = _step
        cycle = _cycle
        v = _v
        c = _c
        d = _d
        t = _t

    ofile.close()

    print "finnished reading"
    print
    print "Number of lines:",
    print state_counter
    print "Excecution time:",
    print time.time() - t
    print "Length of data:",
    print len(V)
    print

    if os.path.isfile(temp_filename):
        try:
            print "...removing tmp-file"
            print temp_filename
            os.remove(temp_filename)
        except WindowsError as e:
            print "...could not remove tmp-file"
            print temp_filename
            print e

    print "DATA:"
    print "(I,D)"
    for j, i in zip(I, D):
        if j > 10:
            break
        print "%f %f" % (j, i)

    I = np.array(I)
    D = convert2mAhg(D, mass)
    C = convert2mAhg(C, mass)
    df = pd.DataFrame({'Cycle': I,
                       'Discharge_Capacity': D,
                       'Charge_Capacity': C})

    selection = (df.Charge_Capacity > lim_low) & (df.Charge_Capacity < lim_high)
    df_filtered = df[selection]
    df_filtered.to_csv(outfile2, sep=";", index=False, columns=["Cycle", "Discharge_Capacity", "Charge_Capacity"])

    plt.plot(I, C, '-', label="charge")
    plt.plot(df_filtered.Cycle, df_filtered.Charge_Capacity, 'o', label="filtered-charge")
    plt.xlabel("cycle")
    plt.ylabel("mAh/g")
    plt.legend()
    plt.show()
    # this script is not properly tested yet

if __name__ == "__main__":
    main()
