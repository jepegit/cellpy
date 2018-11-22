"""Routines for batch processing of cells (v2)."""

import os
import warnings
import logging
import pandas as pd
import itertools
import time
import csv
import json
import matplotlib.pyplot as plt
import matplotlib as mpl

import cellpy.log
from cellpy import prms
from cellpy.utils.batch_core import CyclingExperiment, CSVExporter

logger = logging.getLogger(__name__)
logging.captureWarnings(True)

cellpy.log.setup_logging(default_level="INFO")
logging.info("If you see this - then logging works")

experiment = CyclingExperiment()
experiment.export_raw = True
experiment.export_cycles = True
experiment.export_ica = True
experiment.journal.project = "experiment"
experiment.journal.name = "test"
experiment.journal.batch_col = 5
experiment.journal.from_db()
experiment.journal.to_file()
print(experiment.journal.pages.head(10))
experiment.update()
exporter = CSVExporter()
exporter.assign(experiment)
exporter.do()


import os

prms.Paths["db_filename"] = "cellpy_db.xlsx"
# These prms works for me on my mac, but probably not for you:
prms.Paths["cellpydatadir"] = "/Users/jepe/scripting/cellpy/testdata/hdf5"
prms.Paths["outdatadir"] = "/Users/jepe/cellpy_data"
prms.Paths["rawdatadir"] = "/Users/jepe/scripting/cellpy/testdata/data"
prms.Paths["db_path"] = "/Users/jepe/scripting/cellpy/testdata/db"
prms.Paths["filelogdir"] = "/Users/jepe/scripting/cellpy/testdata/log"



print(60 * "=")
print("Running main in batch_engines")
print(60 * "-")


print(60 * "-")
