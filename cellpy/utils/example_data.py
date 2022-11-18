"""Tools for getting some data to play with"""
import logging
import os
from pathlib import Path

import cellpy

logging.info("Ready to help you to get some data to play with.")
CURRENT_PATH = Path(os.path.dirname(os.path.realpath(__file__)))
RAW_PATH = CURRENT_PATH / "data" / "raw"
H5_PATH = CURRENT_PATH / "data"


def arbin_file(auto_summary=True, testing=False):
    """load an example data file (arbin).

    Args:
        auto_summary (bool): run make_summary automatically (defaults to True)
        testing (bool): run in test mode

    Returns:
        cellpy.CellpyCell object with the arbin data loaded

    """
    file_path = RAW_PATH / "20160805_test001_45_cc_01.res"
    mass = 0.704
    return cellpy.get(
        filename=file_path, mass=mass, auto_summary=auto_summary, testing=testing
    )


def cellpy_file(testing=False):
    """load an example cellpy file.

    Args:
        testing (bool): run in test mode

    Returns:
        cellpy.CellpyCell object with the arbin data loaded
    """

    file_path = H5_PATH / "20160805_test001_45_cc.h5"
    return cellpy.get(filename=file_path, testing=testing)


def cellpy_file_path():
    """Get the path to an example cellpy file"""

    return H5_PATH / "20160805_test001_45_cc.h5"


def arbin_file_path():
    """Get the path to an example arbin res file"""

    return RAW_PATH / "20160805_test001_45_cc_01.res"


if __name__ == "__main__":
    a = arbin_file()
    print("Saving new version of the cellpy file!")
    a.save(cellpy_file_path())
