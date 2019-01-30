# -*- coding: utf-8 -*-
"""simple script for reading .res-files from arbin

This script uses the cellpy.cellreader.CellpyData object.
"""

import os
import sys

import matplotlib.pyplot as plt

from cellpy import cellreader, prmreader

print("still alive so I guess all the needed modules are installed")

rawdir = "../testdata/data"

print(os.getcwd())

if not os.path.isdir(rawdir):
    print("You seem to have given me an invalid path")
    print(rawdir)
    sys.exit(-1)

files = [
    "20160805_test001_45_cc_01.res",
    "20160805_test001_45_cc_02.res",
]

mass = 0.3

rawfiles = [os.path.join(rawdir, f) for f in files]
print("\n", "your files".center(80, "-"))

for f in rawfiles:
    print(f)
print(80*"-")

d = cellreader.CellpyData().from_raw(rawfiles)
d.set_mass(mass)
d.make_step_table()
d.make_summary()

summary = d.dataset.dfsummary
print(summary.head())

fig, ax = plt.subplots(1, 1)
ax.plot(
    summary['Cycle_Index'],
    summary['Cumulated_Coulombic_Difference(mAh/g)']
)
plt.show()

