"""arbin MS SQL Server data"""
import os
import sys
import tempfile
import shutil
import logging
import platform
import warnings
import time
import numpy as np

import pandas as pd

from cellpy.readers.core import (
    FileID,
    Cell,
    check64bit,
    humanize_bytes,
    xldate_as_datetime,
)
from cellpy.parameters.internal_settings import HeaderDict, get_headers_normal
from cellpy.readers.instruments.mixin import Loader
from cellpy import prms

DEBUG_MODE = prms.Reader.diagnostics
ALLOW_MULTI_TEST_FILE = prms._allow_multi_test_file
ODBC = prms._odbc
SEARCH_FOR_ODBC_DRIVERS = prms._search_for_odbc_driver


class ArbinSQLLoader(Loader):
    """ Class for loading arbin-data from MS SQL server."""

    def __init__(self):
        """initiates the ArbinSQLLoader class"""

        pass

    def get_raw_units(self):
        """returns a dictionary with unit fractions"""

        raise NotImplemented

    def get_raw_limits(self):
        """returns a dictionary with resolution limits"""

        raise NotImplemented

    def loader(self, file_name):
        """returns a Cell object with loaded data"""

        raise NotImplemented


if __name__ == "__main__":
    print("hei")
