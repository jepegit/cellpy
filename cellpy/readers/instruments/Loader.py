"""This file contains class for making file loaders"""

from __future__ import division
from __future__ import absolute_import
from __future__ import print_function

import os
import tempfile
import shutil
import logging
import warnings
from six.moves import range  # 'lazy' range (i.e. xrange in Py27)
import numpy as np

import pandas as pd

from cellpy.readers.cellreader import dataset
from cellpy.readers.cellreader import fileID
from cellpy.readers.cellreader import humanize_bytes
from cellpy.readers.cellreader import check64bit
from cellpy.readers.cellreader import get_headers_normal


import warnings
# warnings.warn("not implemented yet")


# The columns to choose if minimum selection is selected
MINIMUM_SELECTION = []


class Loader(object):
    """ Class for loading data from measurement-files."""

    def __init__(self):
        """initiates Loader class"""
        # could use __init__(self, cellpydata_object) and set self.logger = cellpydata_object.logger etc.
        # then remember to include that as prm in "out of class" functions
        self.logger = logging.getLogger()
        self.load_only_summary = False
        self.select_minimal = False
        self.max_filesize = 150000000
        self.position = 0

        self.chunk_size = None  # 100000
        self.max_chunks = None
        self.last_chunk = None
        self.limit_loaded_cycles = None
        self.load_until_error = False

        self.headers_normal = get_headers_normal()

    @staticmethod
    def get_raw_limits():
        """Include the settings for how to decide what kind of step you are examining here.

        The raw limits are 'epsilons' used to check if the current and/or voltage is stable (for example
        for galvanostatic steps, one would expect that the current is stable (constant) and non-zero).
        It is expected that different instruments (with different resolution etc.) have different
        'epsilons'.

        Returns: the raw limits (dict)
        
        """
        raw_limits = dict()
        raw_limits["current_hard"] = 0.0000000000001
        raw_limits["current_soft"] = 0.00001
        raw_limits["stable_current_hard"] = 2.0
        raw_limits["stable_current_soft"] = 4.0
        raw_limits["stable_voltage_hard"] = 2.0
        raw_limits["stable_voltage_soft"] = 4.0
        raw_limits["stable_charge_hard"] = 2.0
        raw_limits["stable_charge_soft"] = 5.0
        raw_limits["ir_change"] = 0.00001
        return raw_limits

    @staticmethod
    def get_raw_units():
        """Include the settings for the units used by the instrument.

        The units are defined w.r.t. the SI units ('unit-fractions'; currently only units that are multiples of
        Si units can be used). For example, for current defined in mA, the value for the
        current unit-fraction will be 0.001.

        OBS! Not properly set yet.

        Returns: dictionary containing the unit-fractions for current, charge, and mass

        """
        raw_units = dict()
        raw_units["current"] = 1.0  # A
        raw_units["charge"] = 1.0  # Ah
        raw_units["mass"] = 0.001  # g
        return raw_units

    @staticmethod
    def loader(file_name=None):
        """Loads data from biologic .? files.

        Args:
            file_name (str): path to .? file.

        Returns:
            new_tests (list of data objects), FileError
        """

        new_tests = []
        if not os.path.isfile(file_name):
            txt = "Missing file_\n   %s" % file_name
            self.logger.error(txt)

        filesize = os.path.getsize(file_name)
        hfilesize = humanize_bytes(filesize)
        txt = "Filesize: %i (%s)" % (filesize, hfilesize)
        self.logger.debug(txt)

        # --- temp-file
        temp_dir = tempfile.gettempdir()
        temp_filename = os.path.join(temp_dir, os.path.basename(file_name))
        shutil.copy2(file_name, temp_dir)
        txt = "."
        self.logger.info(txt)


    def load(self, file_name):
        """Load a raw data-file (convenience function).

        Args:
            file_name (path)

        Returns:
            loaded test
        """

        raw_file_loader = self.loader
        new_rundata = raw_file_loader(file_name)
        new_rundata = self.inspect(new_rundata)
        return new_rundata

    def inspect(self, run_data):
        """inspect the file.

        -adds missing columns (with np.nan)
        """
        checked_rundata = []
        for data in run_data:
            new_cols = data.dfdata.columns
            for col in self.headers_normal:
                if not col in new_cols:
                    data.dfdata[col] = np.nan
            checked_rundata.append(data)
        return checked_rundata

    def repair(self):
        """try to repair a broken/corrupted file"""
        pass

    def get_update(self):
        last_position = self.position
        # self._update(last_position)
        new_position =  last_position
        self.position = new_position

