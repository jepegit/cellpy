"""Tools for getting some data to play with"""

from enum import Enum
import logging
import os
from pathlib import Path

import requests
from tqdm.auto import tqdm

import cellpy
from cellpy import prms

logging.info("Ready to help you to get some data to play with.")
CURRENT_PATH = Path(os.path.dirname(os.path.realpath(__file__)))
DATA_PATH = CURRENT_PATH / "data"
DO_NOT_REMOVE_THESE_FILES = [".gitkeep"]


class ExampleData(Enum):
    """Enum for example data files"""

    ARBIN = "20160805_test001_45_cc_01.res"
    CELLPY = "20180418_sf033_4_cc.h5"
    OLD_CELLPY = "20160805_test001_45_cc.h5"
    RATE = "20231115_rate_cc.h5"
    AUX_MULTI_X = "aux_multi_x.res"
    # BIOL_MPR = "biol.mpr"
    # MACCOR_TXT = "maccor.txt"
    # NEWARE_CSV = "neware.csv"
    PEC_CSV = "pec.csv"


def download_file(url, local_filename):
    """Download a file from the web.

    Args:
        url (str): URL of the file to download
        local_filename (str): Local filename to save the file to

    """
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            if prms._url_example_data_download_with_progressbar:
                pbar = tqdm(
                    total=int(r.headers["Content-Length"]), unit="B", unit_scale=True
                )
            for chunk in r.iter_content(chunk_size=8192):
                if chunk and prms._url_example_data_download_with_progressbar:
                    pbar.update(len(chunk))
                f.write(chunk)


def _download_if_missing(filename: str) -> Path:
    p = DATA_PATH / filename
    if not p.is_file():
        _download_example_data(filename)
    return p


def _remove_file(filename: str):
    p = DATA_PATH / filename
    logging.debug(f"Removing file: {p}")
    p.unlink(missing_ok=False)


def _remove_all_files():
    for f in DATA_PATH.glob("*"):
        logging.debug(f"Removing file: {f}")
        if f.name not in DO_NOT_REMOVE_THESE_FILES:
            f.unlink(missing_ok=True)
            logging.debug(f"{f.name} removed")
        else:
            logging.debug(f"{f.name} not removed (protected)")


def _is_downloaded(filename: str) -> bool:
    p = DATA_PATH / filename
    return p.is_file()


def _download_all_files():
    for f in ExampleData:
        _download_example_data(f.value)


def _download_example_data(filename: str):
    """Download example data from the cellpy-data repository.

    Args:
        filename (str): the name of the file to download

    Returns:
        None

    """
    logging.info(f"{filename} not found. Trying to access it from GitHub...")
    base_url = prms._url_example_data
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Could not find {DATA_PATH}")

    logging.debug(f"Downloading {filename} from {base_url} to {DATA_PATH}")
    download_file(base_url + filename, os.path.join(DATA_PATH, filename))

    logging.debug("File downloaded successfully.")


def download_all_files():
    """Download all example data files from the cellpy-data repository."""
    _download_all_files()


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


def rate_file():
    """Get the path to an example cellpy file with rate data"""
    return _download_if_missing(ExampleData.RATE.value)


def cellpy_file_path() -> Path:
    """Get the path to an example cellpy file"""

    return _download_if_missing(ExampleData.CELLPY.value)


def old_cellpy_file_path() -> Path:
    """Get the path to an example cellpy file"""
    return _download_if_missing(ExampleData.OLD_CELLPY.value)


def arbin_file_path() -> Path:
    """Get the path to an example arbin res file"""

    return _download_if_missing(ExampleData.ARBIN.value)


def arbin_multi_file_path() -> Path:
    """Get the path to an example arbin res file"""
    return _download_if_missing(ExampleData.AUX_MULTI_X.value)


def maccor_file_path() -> Path:
    """Get the path to an example maccor txt file"""
    return _download_if_missing(ExampleData.MACCOR_TXT.value)


def neware_file_path() -> Path:
    """Get the path to an example neware csv file"""
    return _download_if_missing(ExampleData.NEWARE_CSV.value)


def pec_file_path() -> Path:
    """Get the path to an example pec csv file"""
    return _download_if_missing(ExampleData.PEC_CSV.value)


def biologics_file_path() -> Path:
    """Get the path to an example biologics mpr file"""
    return _download_if_missing(ExampleData.BIOL_MPR.value)


if __name__ == "__main__":
    # This is used for making a new version of the cellpy file
    _a = raw_file()
    print("Saving new version of the cellpy file!")
    _a.save(cellpy_file_path())
