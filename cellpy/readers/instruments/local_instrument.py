"""This module is used for loading data using the corresponding Local
yaml file with definitions on how the data should be loaded. This loader
is based on the TxtLoader and can only be used to load csv-type files"""

from cellpy.readers.instruments.base import TxtLoader
from cellpy.readers.instruments.configurations import (
    register_local_configuration_from_yaml_file,
)


class DataLoader(TxtLoader):
    """Class for loading data from txt files."""

    instrument_name = "local_instrument"
    raw_ext = "*"

    def __init__(self, instrument_file=None, **kwargs):
        self.local_instrument_file = instrument_file
        super().__init__()

    default_model = None
    supported_models = None

    def pre_init(self):
        self.auto_register_config = False
        print("---------------------------")
        print(f"{self.local_instrument_file}")
        print("---------------------------")
        self.config_params = register_local_configuration_from_yaml_file(
            self.local_instrument_file
        )
