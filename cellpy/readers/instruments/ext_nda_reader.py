import os
import logging

import pandas as pd

from cellpy.readers.core import (
    FileID,
    Cell,
    check64bit,
    humanize_bytes,
    xldate_as_datetime,
)
from cellpy.parameters.internal_settings import get_headers_normal
from cellpy.readers.instruments.mixin import Loader
from cellpy import prms

try:
    from nda_reader import nda_reader
except ImportError:
    logging.warn("Could not load nda reader")


# import nda_reader
# read_nda
# fix headers etc
# check


def load_nda(*args, **kwargs):
    print("dummy function (mock)")
    print(args)
    print(kwargs)


class NdaLoader(Loader):
    """ Class for using the NDA loader by Frederik Huld (Beyonder)."""

    def __init__(self):
        """initiates the NdaLoader class"""
        # could use __init__(self, cellpydata_object) and
        # set self.logger = cellpydata_object.logger etc.
        # then remember to include that as prm in "out of class" functions
        # self.prms = prms
        self.logger = logging.getLogger(__name__)

        self.headers_normal = get_headers_normal()
        self.headers_global = self.get_headers_global()
        self.current_chunk = 0  # use this to set chunks to load

    def get_raw_units(self):
        """Include the settings for the units used by the instrument.

        The units are defined w.r.t. the SI units ('unit-fractions'; currently only units that are multiples of
        Si units can be used). For example, for current defined in mA, the value for the
        current unit-fraction will be 0.001.

        Returns: dictionary containing the unit-fractions for current, charge, and mass

        """
        raise NotImplementedError

    def get_raw_limits(self):
        """Include the settings for how to decide what kind of step you are examining here.

        The raw limits are 'epsilons' used to check if the current and/or voltage is stable (for example
        for galvanostatic steps, one would expect that the current is stable (constant) and non-zero).
        It is expected that different instruments (with different resolution etc.) have different
        'epsilons'.

        Returns: the raw limits (dict)

        """
        raise NotImplementedError

    def loader(self, file_name, *args, **kwargs):
        """Loads data into a DataSet object and returns it"""

        new_tests = []

        test_no = 1
        channel_index = 1
        channel_number = 1
        creator = "no name"
        item_ID = 1
        schedule_file_name = "no name"
        start_datetime = "2020.02.24 14:58:00"
        test_ID = 1
        test_name = "no name"

        if not os.path.isfile(file_name):
            self.logger.info("Missing file_\n   %s" % file_name)
            return None

        self.logger.debug("in loader")
        self.logger.debug("filename: %s" % file_name)

        filesize = os.path.getsize(file_name)
        hfilesize = humanize_bytes(filesize)
        txt = "Filesize: %i (%s)" % (filesize, hfilesize)
        self.logger.debug(txt)

        data = Cell()
        data.cell_no = test_no
        data.loaded_from = file_name
        fid = FileID(file_name)
        data.channel_index = channel_index
        data.channel_number = channel_number
        data.creator = creator
        data.item_ID = item_ID
        data.schedule_file_name = schedule_file_name
        data.start_datetime = start_datetime
        data.test_ID = test_ID
        data.test_name = test_name
        data.raw_data_files.append(fid)

        length_of_test, normal_df = load_nda()

        data.summary = empty_df

        data.raw = normal_df
        data.raw_data_files_length.append(length_of_test)

        data = self._post_process(data)
        data = self.identify_last_data_point(data)

        new_tests.append(data)

        return new_tests
