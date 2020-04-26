"""Tools for getting some data to play with"""
import os
from pathlib import Path
import logging

import cellpy


logging.info("Ready to help you to get some data to play with.")
CURRENT_PATH = Path(os.path.dirname(os.path.realpath(__file__)))
RAW_PATH = CURRENT_PATH / "data" / "raw"
H5_PATH = CURRENT_PATH / "data"


def arbin_file(auto_summary=True):
    """load an example data file (arbin).

    Args:
        auto_summary: run make_summary automatically (defaults to True)

    Returns:
        cellpy.CellpyData object with the arbin data loaded

    """
    file_path = RAW_PATH / "20160805_test001_45_cc_01.res"
    mass = 0.704
    return cellpy.get(filename=file_path, mass=mass, auto_summary=auto_summary)


def cellpy_file():
    """load an example cellpy file."""

    file_path = H5_PATH / "20160805_test001_45_cc.h5"
    return cellpy.get(filename=file_path)


def cellpy_file_path():
    """Get the path to an example cellpy file"""

    return H5_PATH / "20160805_test001_45_cc.h5"
