# -*- coding: utf-8 -*-
"""simple script for reading .res-files from arbin

This script does not rely on any of the modules in cellpy.
"""

import os
import shutil
import sys
import tempfile
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    import pyodbc as dbloader
except ImportError:
    print("could not import dbloader (pyodbc)")
    print("this script will not work without")
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
    # This script relies on using Microsoft Access Driver.
    # If you are on a non-Microsoft OS, this will not work.
    # Even on a Windows machine, you will need to make sure that
    # the appropriate driver is installed (same bit as your python)

    # write file name here:
    filename = r"..\testdata\data\20160805_test001_45_cc_01.res"
    # write min value for capacity (points less than that will be removed):
    lim_low = 10
    # write max value for capacity (points larger than that will be removed):
    lim_high = 6050
    # mass of (active material of) electrode in mg:
    mass = 0.8369
    # write path to were you want to save the data:
    outdir = r"..\.."

    tablename_normal = "Channel_Normal_Table"
    tablename_global = "Global_Table"
    tablename_statistic = "Channel_Statistic_Table"
    fname = os.path.basename(filename)
    fname = os.path.splitext(fname)[0]
    outfile = os.path.join(outdir, fname + "_out.csv")
    outfile2 = os.path.join(outdir, fname + "_cdc.csv")

    print("filename:"), filename

    # ------making temporary file-------------
    temp_dir = tempfile.gettempdir()
    temp_filename = os.path.join(temp_dir, os.path.basename(filename))
    print("Copying to tmp-file")
    print("temp_filename:"), temp_filename

    shutil.copy2(filename, temp_dir)
    print("Finished to tmp-file")

    constructor = (
        "Driver={Microsoft Access Driver (*.mdb, *.accdb)};Dbq=" + temp_filename
    )
    conn = dbloader.connect(constructor, autocommit=True)
    cur = conn.cursor()
    sql = "select * from %s ORDER BY Test_Time" % tablename_normal
    cur.execute(sql)
    col_names = [i[0] for i in cur.description]

    # all_data=cur.fetchall()
    print("COLS:")
    for cname in col_names:
        print(cname)

    print("\nreading file")

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

    ofile = open(outfile, "w")
    header = "time;cycle;step;voltage;discharge_cap;charge_cap\n"
    ofile.write(header)

    for row in cur:
        if not row:
            break

        limit_counter += 1
        if limit_counter >= limit:
            print("x"),
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
            print(".", end=" ")
            if I.count(cycle) == 0:
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

        step = _step
        cycle = _cycle
        v = _v
        c = _c
        d = _d
        t = _t

    ofile.close()

    print(f"finnished reading\nNumber of lines: {state_counter}")
    print(f"Excecution time: {time.time() - t}\nLength of data: {V}")

    if os.path.isfile(temp_filename):
        try:
            print(f"...removing tmp-file {temp_filename}")
            os.remove(temp_filename)
        except WindowsError as e:
            print(f"...could not remove tmp-file {temp_filename} - {e}")

    print("DATA:")
    print("(I,D)")
    for j, i in zip(I, D):
        if j > 10:
            break
        print("%f %f") % (j, i)

    I = np.array(I)
    D = convert2mAhg(D, mass)
    C = convert2mAhg(C, mass)
    df = pd.DataFrame({"Cycle": I, "Discharge_Capacity": D, "Charge_Capacity": C})

    selection = (df.Charge_Capacity > lim_low) & (df.Charge_Capacity < lim_high)
    df_filtered = df[selection]
    df_filtered.to_csv(
        outfile2,
        sep=";",
        index=False,
        columns=["Cycle", "Discharge_Capacity", "Charge_Capacity"],
    )

    plt.plot(I, C, "-", label="charge")
    plt.plot(
        df_filtered.Cycle, df_filtered.Charge_Capacity, "o", label="filtered-charge"
    )
    plt.xlabel("cycle")
    plt.ylabel("mAh/g")
    plt.legend()
    print(" nice figure ".center(80, "-"))
    plt.show()

    # PS! This script is not properly tested yet. Because I never need it.
    # The most likely reasons for failure is that the files or folders
    # you have stated does not exist, or that the odbc driver (Access)
    # is missing or is of the wrong bit (64bit when using 32bit Python).


if __name__ == "__main__":
    main()
