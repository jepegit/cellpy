print("hello")
from cellpy import  cellreader, prmreader
import pandas
import matplotlib.pyplot as plt
import os
print("still alive")

rawdir = r"C:\Scripting\Processing\Test\raw"
outdir = r"C:\Scripting\Processing\Test\out"

files = ["20170922_bec04_31_cc_01.res",
        "20170922_bec04_31_cc_02.res",
        "20170922_bec04_31_cc_03.res",
        "20170922_bec04_31_cc_04.res",
        "20170922_bec04_31_cc_05.res",
        "20170922_bec04_31_cc_06.res",
        "20170922_bec04_31_cc_07.res"
        ]

mass = 0.3

rawfiles = [os.path.join(rawdir, f) for f in files]
print(rawfiles)

d = cellreader.CellpyData()
d.from_raw(rawfiles)
d.set_mass(mass)

