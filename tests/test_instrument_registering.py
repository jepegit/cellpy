import logging

import pytest

from cellpy import log, prms

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


