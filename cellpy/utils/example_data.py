"""Tools for getting some data to play with"""

import logging
import os
from pathlib import Path

import cellpy

logging.info("Ready to help you to get some data to play with.")
CURRENT_PATH = Path(os.path.dirname(os.path.realpath(__file__)))
RAW_PATH = CURRENT_PATH / "data" / "raw"
H5_PATH = CURRENT_PATH / "data"


def _download_example_data(filename):
    """Download example data from the cellpy-data repository.

    Args:
        filename (str): the name of the file to download

    Returns:
        None

    """
    # Should download file from e.g. GitHub and save it in the data folder (RAW_PATH)
    raise NotImplementedError("Downloading example data is not implemented yet.")


def raw_file(auto_summary=True, testing=False):
    """load an example data file (arbin).

    Args:
        auto_summary (bool): run make_summary automatically (defaults to True)
        testing (bool): run in test mode

    Returns:
        cellpy.CellpyCell object with the data loaded

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
        cellpy.CellpyCell object with the data loaded
    """

    file_path = H5_PATH / "20180418_sf033_4_cc.h5"
    return cellpy.get(filename=file_path, testing=testing)


def rate_file(testing=False):
    """load an example cellpy file.

    Args:
        testing (bool): run in test mode

    Returns:
        cellpy.CellpyCell object with the rate data loaded
    """

    file_path = H5_PATH / "20231115_rate_cc.h5"
    return cellpy.get(filename=file_path, testing=testing)


def cellpy_file_path():
    """Get the path to an example cellpy file"""

    return H5_PATH / "20180418_sf033_4_cc.h5"


def arbin_file_path():
    """Get the path to an example arbin res file"""

    return RAW_PATH / "20160805_test001_45_cc_01.res"


def arbin_multi_file_path():
    """Get the path to an example arbin res file"""
    r = "aux_multi_x.res"
    p = RAW_PATH / r
    if not p.is_file():
        _download_example_data(r)
    return p


def maccor_file_path():
    """Get the path to an example maccor txt file"""
    r = "maccor.txt"
    p = RAW_PATH / r
    if not p.is_file():
        _download_example_data(r)
    return p


def neware_file_path():
    """Get the path to an example neware csv file"""
    r = "neware.csv"
    p = RAW_PATH / r
    if not p.is_file():
        _download_example_data(r)
    return p


def pec_file_path():
    """Get the path to an example pec csv file"""
    r = "pec.csv"
    p = RAW_PATH / r
    if not p.is_file():
        _download_example_data(r)
    return p


def biologics_file_path():
    """Get the path to an example biologics mpr file"""
    r = "biol.mpr"
    p = RAW_PATH / r
    if not p.is_file():
        _download_example_data(r)
    return p


if __name__ == "__main__":
    _a = raw_file()
    print("Saving new version of the cellpy file!")
    _a.save(cellpy_file_path())
