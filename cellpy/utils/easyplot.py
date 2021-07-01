# Author: Amund M. Raniseth
# Date: 01.07.2021

import os
from pathlib import Path
import logging
import cellpy
import matplotlib.pyplot as plt


#### WORK IN PROGRESS ####

def plot(files):
    cellpyobjects = []
    for file in files:
        cellpyobjects.append(cellpy.get(filename = file))
    print("plot func is called!")
    print(cellpyobjects)
    print(cellpyobjects[0].get_cycle_numbers())
    curves1 = cellpyobjects[0].get_cap(method="forth-and-forth")
    print(curves1)
    print(type(curves1))
    curves1.plot()