"""This module is used for loading data using the corresponding local
yaml file with definitions on how the data should be loaded. This loader
is based on the ``TxtLoader`` and can only be used to load csv-type files.
As a "short-cut", this loader will be used if you set the ``instrument``
to the name of the instrument file (with the ``.yml`` extension) e.g.
``c = cellpy.get(rawfile, instrument="instrumentfile.yml")``.
The default instrument file is defined in the cellpy configuration file
(available through ``prms.Instruments.custom_instrument_definitions_file``)."""

from cellpy.readers.instruments.base import TxtLoader
from cellpy.readers.instruments.configurations import (
    register_local_configuration_from_yaml_file,
)


class DataLoader(TxtLoader):
    """Class for loading data from txt files."""

    instrument_name = "local_instrument"
    raw_ext = "*"

    def __init__(self, instrument_file=None, **kwargs):
        """
        Args:
            instrument_file: name of the local instrument file.
            **kwargs: not used.
        """
        self.local_instrument_file = instrument_file
        super().__init__()

    default_model = None
    supported_models = None

    def pre_init(self):
        self.auto_register_config = False
        self.config_params = register_local_configuration_from_yaml_file(
            self.local_instrument_file
        )
