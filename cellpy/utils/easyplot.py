# Author: Amund M. Raniseth
# Date: 01.07.2021

import os
from pathlib import Path
import logging

import cellpy

def plot(files):
    cellpyobjects = []
    for file in files:
        cellpyobjects.append(cellpy.get(filename = file))
    print("plot func is called!")