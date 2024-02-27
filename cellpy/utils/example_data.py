"""Tools for getting some data to play with"""

import logging
import os
from pathlib import Path

import requests

import cellpy
from cellpy import prms

logging.info("Ready to help you to get some data to play with.")
CURRENT_PATH = Path(os.path.dirname(os.path.realpath(__file__)))
DATA_PATH = CURRENT_PATH / "data"


def download_file(url, local_filename):
    """Download a file from the web.

    Args:
        url (str): URL of the file to download
        local_filename (str): Local filename to save the file to

    """
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)


def _download_if_missing(filename: str) -> Path:
    p = DATA_PATH / filename
    if not p.is_file():
        _download_example_data(filename)
    return p


def _download_example_data(filename: str):
    """Download example data from the cellpy-data repository.

    Args:
        filename (str): the name of the file to download

    Returns:
        None

    """
    logging.info(f"{filename} not found. Trying to access it from GitHub...")
    base_url = prms._url_example_cellpy_data
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Could not find {DATA_PATH}")

    logging.debug(f"Downloading {filename} from {base_url} to {DATA_PATH}")
    download_file(base_url + filename, os.path.join(DATA_PATH, filename))

    logging.debug("File downloaded successfully.")


def raw_file(
    auto_summary: bool = True, testing: bool = False
) -> cellpy.cellreader.CellpyCell:
    """load an example data file (arbin).

    Args:
        auto_summary (bool): run make_summary automatically (defaults to True)
        testing (bool): run in test mode

    Returns:
        cellpy.CellpyCell object with the data loaded

    """
    file_path = arbin_file_path()
    mass = 0.704
    return cellpy.get(
        filename=file_path, mass=mass, auto_summary=auto_summary, testing=testing
    )


def cellpy_file(testing: bool = False) -> cellpy.cellreader.CellpyCell:
    """load an example cellpy file.

    Args:
        testing (bool): run in test mode

    Returns:
        cellpy.CellpyCell object with the data loaded
    """

    file_path = cellpy_file_path()
    return cellpy.get(filename=file_path, testing=testing)


@property
def rate_file():
    """Get the path to an example cellpy file with rate data"""
    return _download_if_missing("20231115_rate_cc.h5")


@property
def cellpy_file_path() -> Path:
    """Get the path to an example cellpy file"""

    return _download_if_missing("20180418_sf033_4_cc.h5")


def old_cellpy_file_path() -> Path:
    """Get the path to an example cellpy file"""
    return _download_if_missing("20160805_test001_45_cc.h5")


@property
def arbin_file_path() -> Path:
    """Get the path to an example arbin res file"""

    return _download_if_missing("20160805_test001_45_cc_01.res")


@property
def arbin_multi_file_path() -> Path:
    """Get the path to an example arbin res file"""
    return _download_if_missing("aux_multi_x.res")


@property
def maccor_file_path() -> Path:
    """Get the path to an example maccor txt file"""
    return _download_if_missing("maccor.txt")


@property
def neware_file_path() -> Path:
    """Get the path to an example neware csv file"""
    return _download_if_missing("neware.csv")


@property
def pec_file_path() -> Path:
    """Get the path to an example pec csv file"""
    return _download_if_missing("pec.csv")


@property
def biologics_file_path() -> Path:
    """Get the path to an example biologics mpr file"""
    return _download_if_missing("biol.mpr")


if __name__ == "__main__":
    # This is used for making a new version of the cellpy file
    _a = raw_file()
    print("Saving new version of the cellpy file!")
    _a.save(cellpy_file_path())
