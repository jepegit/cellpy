"""Tools for getting some data to play with"""

import warnings
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
_DATA_PATH = CURRENT_PATH / "data"
DO_NOT_REMOVE_THESE_FILES = [".gitkeep"]
CHUNK_SIZE = 8192

_example_data_download_help = """
You don't have any accessible example directory set in your configurations so
cellpy will try to download the example data to the folder where the cellpy
package is installed.

"""
_example_data_download_error_help = """
Unfortunately, cellpy could not find / failed to download the example data.
It might be that you have not set up the example data directory in your configurations
while you are not allowed to download the data to the folder where cellpy is
installed (cellpy's backup option when it can't find any example data directory).

You can set up cellpy through the command line interface:

    cellpy setup

or you can set the path to the example data directory manually in your script:

    >>> from cellpy import prms
    >>> prms.Paths.examplesdir = "/path/to/your/example/data"

"""


def _user_examples_dir():
    """Get the path to the user's examples directory"""
    examples_dir = Path(prms.Paths.examplesdir)
    if not examples_dir.is_dir():
        warnings.warn(f"Could not find {examples_dir}")
        print(_example_data_download_help)
        return None
    return examples_dir / "data"


if prms._example_data_in_example_folder_if_available:
    DATA_PATH = _user_examples_dir() or _DATA_PATH


# TODO: add more example data files
#  (here and in the examples folder and make tests)
class ExampleData(Enum):
    """Enum for example data files"""

    CELLPY = "20180418_sf033_4_cc.h5"
    OLD_CELLPY = "20160805_test001_45_cc.h5"
    RATE = "20231115_rate_cc.h5"
    # GITT = "gitt.h5"
    # COMMERCIAL = "commercial.h5"
    # CV = "cv.h5"
    # EIS = "eis.h5"
    # BUGGY_FILE = "buggy.h5"
    # PLATING = "plating.h5"
    ARBIN = "20160805_test001_45_cc_01.res"
    AUX_MULTI_X = "aux_multi_x.res"
    PEC_CSV = "pec.csv"
    # CUSTOM = "custom.csv"
    # CUSTOM_EXCEL = "custom.xlsx"
    # BIOL_MPR = "biol.mpr"
    # MACCOR_TXT = "maccor.txt"
    # NEWARE_CSV = "neware.csv"
    # --------------------------------
    # DB = "cellpy_db.sqlite"
    # SIMPLE_DB = "simple_db.xlsx"
    # STEPS = "steps.csv"
    # STEPS_SHORT = "steps_short.csv"


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
            for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                if chunk and prms._url_example_data_download_with_progressbar:
                    pbar.update(len(chunk))
                f.write(chunk)


def _download_if_missing(filename: str) -> Path:
    p = DATA_PATH / filename
    if not p.is_file():
        try:
            _download_example_data(filename)
        except requests.HTTPError as e:
            warnings.warn(f"Could not download {filename}: {e}")
            raise e
        except Exception as e:
            warnings.warn(f"Could not download {filename}: {e}")
            print(_example_data_download_error_help)
            raise e
    return p


def _remove_file(filename: str):
    p = DATA_PATH / filename
    logging.debug(f"Removing file: {p}")
    p.unlink(missing_ok=True)


def _remove_all_files():
    for f in ExampleData:
        _remove_file(f.value)


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
        try:
            os.makedirs(DATA_PATH)
        except Exception:  # noqa
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
