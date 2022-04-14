"""This module is used for loading data using the corresponding Local
yaml file with definitions on how the data should be loaded."""

from cellpy.readers.instruments.base import TxtLoader
from cellpy.readers.instruments.configurations import (
    register_local_configuration_from_yaml_file,
)


class LocalTxtLoader(TxtLoader):
    """Class for loading data from txt files."""

    def __init__(self, local_instrument_file=None):
        self.local_instrument_file = local_instrument_file
        super().__init__()

    default_model = None
    supported_models = None

    def pre_init(self):
        self.auto_register_config = False
        self.config_params = register_local_configuration_from_yaml_file(
            self.local_instrument_file
        )
