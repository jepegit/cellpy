import logging
import os

import pandas as pd

from cellpy import prms
from cellpy.parameters.internal_settings import get_headers_normal
from cellpy.readers.core import (
    Data,
    FileID,
    check64bit,
    humanize_bytes,
    xldate_as_datetime,
)
from cellpy.readers.instruments.base import BaseLoader

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
    return None, None


class DataLoader(BaseLoader):
    """Class for using the NDA loader by Frederik Huld (Beyonder)."""

    instrument_name = "neware_nda"

    def __init__(self, *args, **kwargs):
        """initiates the NdaLoader class"""
        # could use __init__(self, cellpydata_object) and
        # set self.logger = cellpydata_object.logger etc.
        # then remember to include that as prm in "out of class" functions
        # self.prms = prms
        self.logger = logging.getLogger(__name__)

        self.headers_normal = get_headers_normal()
        self.headers_global = self.get_headers_global()
        self.current_chunk = 0  # use this to set chunks to load

    @staticmethod
    def get_params(parameter=None):
        params = dict()
        params["raw_ext"] = "nda"
        if parameter is not None:
            return params[parameter]
        return params

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
        # self.name = file_name
        # self.copy_to_temporary()
        test_no = 1
        channel_index = 1
        creator = "no name"
        schedule_file_name = "no name"
        # TODO: convert to datetime:
        start_datetime = "2020.02.24 14:58:00"
        test_ID = 1
        test_name = "no name"

        self.logger.debug("in loader")
        self.logger.debug("filename: %s" % file_name)

        data = Data()
        data.loaded_from = file_name
        self.generate_fid()
        data.raw_data_files.append(self.fid)
        data.channel_index = channel_index
        data.creator = creator
        data.schedule_file_name = schedule_file_name
        data.start_datetime = start_datetime
        data.test_ID = test_ID
        data.test_name = test_name

        length_of_test, normal_df = load_nda()

        data.summary = pd.DataFrame()

        data.raw = normal_df
        data.raw_data_files_length.append(length_of_test)

        data = self._post_process(data)
        data = self.identify_last_data_point(data)

        return data
