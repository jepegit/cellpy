import logging

import pytest

from cellpy import log, prms

log.setup_logging(default_level=logging.DEBUG, testing=True)


@pytest.mark.xfail
def test_set_instrument_selecting_default_not_defined(cellpy_data_instance):
    prms.Instruments.custom_instrument_definitions_file = None
    cellpy_data_instance.set_instrument(instrument="custom")


def test_set_instrument_by_filename(cellpy_data_instance, parameters):
    instrument = "maccor_txt"
    cellpy_data_instance.set_instrument(instrument=instrument)


