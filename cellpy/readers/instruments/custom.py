import logging
import os

from cellpy.parameters.internal_settings import get_headers_normal
from cellpy.readers.instruments.mixin import Loader
from cellpy.readers.core import FileID, DataSet, \
    check64bit, humanize_bytes, doc_inherit
from cellpy.parameters import prms


class CustomLoader(Loader):
    """ Class for loading cell data from custom formatted files.

    The file that contains the description of the custom data file
    should be given by issuing the
    pick_definition_file or given in the config file
    (prms.Instruments.custom_instrument_definitions_file)

    The format of the custom data file should be on the form

    ...
        # comment
        # ...
        variable sep value
        variable sep value
        ...
        header1 sep header2 sep ...
        value1  sep value2  sep ...
        ...

    where sep is either defined in the description file or the
    config file.

    The definition file should use the YAML format and it
    must contain

    xxx
    xxx


    """

    def __init__(self):
        """initiates the class"""

        self.logger = logging.getLogger(__name__)
        self.headers_normal = get_headers_normal()
        self.def_file = self.pick_definition_file()

    @staticmethod
    def pick_definition_file():
        return prms.Instruments.custom_instrument_definitions_file

    def parse_definition_file(self):
        # self.settings = parse(self.def_file)
        pass

    @staticmethod
    def get_raw_units():
        raw_units = dict()
        raw_units["current"] = 1.0  # A # = self.settings.xxx.xxx
        raw_units["charge"] = 1.0  # Ah
        raw_units["mass"] = 0.001  # g
        return raw_units

    @staticmethod
    def get_raw_limits(self):
        raw_limits = dict()
        raw_limits["current_hard"] = 0.0000000000001 # self.settings.xxx
        raw_limits["current_soft"] = 0.00001
        raw_limits["stable_current_hard"] = 2.0
        raw_limits["stable_current_soft"] = 4.0
        raw_limits["stable_voltage_hard"] = 2.0
        raw_limits["stable_voltage_soft"] = 4.0
        raw_limits["stable_charge_hard"] = 0.9
        raw_limits["stable_charge_soft"] = 5.0
        raw_limits["ir_change"] = 0.00001
        return raw_limits

    def loader(self, file_name, **kwargs):
        new_tests = []
        if not os.path.isfile(file_name):
            self.logger.info("Missing file_\n   %s" % file_name)
            return
