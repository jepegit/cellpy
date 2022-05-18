import logging
from abc import ABC

import pytest
from cellpy.readers.instruments.configurations import register_configuration_from_module
from cellpy.readers.instruments.base import AutoLoader
from cellpy.readers import core
from cellpy import log, prms

from . import instrument_configuration_module


class MockLoader(AutoLoader, ABC):
    """This is a minimal subclass of AutoLoader that
    reads its configuration from the 'instrument_configuration_module'
    located in the 'tests' directory.
    """
    def pre_init(self):
        self.supported_models = None
        self.default_model = None
        self.auto_register_config = False
        self.config_params = register_configuration_from_module(
            name="test",
            _m=instrument_configuration_module,
        )

    def parse_formatter_parameters(self):
        pass

    def parse_loader_parameters(self):
        pass

    def query_file(self):
        pass

    @staticmethod
    def return_42():
        return 42


log.setup_logging(default_level=logging.DEBUG, testing=True)


@pytest.mark.xfail
def test_set_instrument_selecting_default_not_defined(cellpy_data_instance):
    prms.Instruments.custom_instrument_definitions_file = None
    cellpy_data_instance.set_instrument(instrument="custom")


def test_set_instrument_selecting_default(cellpy_data_instance, parameters):
    prms.Instruments.custom_instrument_definitions_file = parameters.custom_instrument_definitions_file
    cellpy_data_instance.set_instrument(instrument="custom")


def test_set_instrument_and_instrument_file(cellpy_data_instance, parameters):
    cellpy_data_instance.set_instrument(instrument="custom", instrument_file=parameters.custom_instrument_definitions_file)


def test_set_instrument_and_instrument_file_using_sep(cellpy_data_instance, parameters):
    instrument = "custom" + "::" + parameters.custom_instrument_definitions_file
    cellpy_data_instance.set_instrument(instrument=instrument)


@pytest.mark.xfail
def test_set_instrument_missing_file(cellpy_data_instance, parameters):
    prms.Instruments.custom_instrument_definitions_file = "a-file-that-should-not-exist.yml"
    cellpy_data_instance.set_instrument(instrument="custom")


def test_set_instrument_by_filename(cellpy_data_instance, parameters):
    instrument = "maccor_txt"
    cellpy_data_instance.set_instrument(instrument=instrument)


def test_registering_module():
    mloader = MockLoader()
    assert mloader.config_params.unit_labels["resistance"] == "Ohms"
    assert mloader.return_42() == 42


def test_registering_module_post_processors():
    mloader = MockLoader()
    assert mloader.config_params.post_processors["replace"]["one"] == "two"


def test_list_available_instruments():
    pass


@pytest.mark.parametrize('parameter, loader, expected', [
    ("raw_ext", "arbin", "res"),
    ("name", "arbin", "arbin_res"),
    ("raw_ext", "arbin_sql", None),
    ("name", "arbin_sql", "arbin_sql"),
    ("raw_ext", "arbin_sql_csv", "csv"),
    ("name", "arbin_sql_csv", "arbin_sql_csv"),
    ("raw_ext", "arbin_sql_xlsx", "xlsx"),
    ("name", "arbin_sql_xlsx", "arbin_sql_xlsx"),
    ("name", "custom", "custom"),
    ("raw_ext", "custom", "*"),
    ("name", "maccor_txt", "maccor_txt"),
    ("raw_ext", "maccor_txt", "txt"),
    ("name", "pec", "pec_csv"),
    ("raw_ext", "pec", "csv"),
    ("name", "biologics", "biologics_mpr"),
    ("raw_ext", "biologics", "mpr"),
    ("name", "old_custom", "old_custom"),
    ("raw_ext", "old_custom", "*"),
])
def test_query_instrument(parameter, loader, expected):
    assert core.query_instrument(parameter, loader) == expected
