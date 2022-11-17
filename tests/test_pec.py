import logging
import shutil
import tempfile

import pytest

from cellpy import log

from . import fdv

log.setup_logging(default_level=logging.DEBUG, testing=True)


def test_set_instrument(cellpy_data_instance, parameters):
    instrument = "pec_csv"
    cellpy_data_instance.set_instrument(instrument=instrument)
    cellpy_data_instance.from_raw(parameters.pec_file_path)
    cellpy_data_instance.cycle_mode = "cathode"
    cellpy_data_instance.set_mass(50_000)
    cellpy_data_instance.make_step_table()
    cellpy_data_instance.make_summary()
    temp_dir = tempfile.mkdtemp()
    cellpy_data_instance.to_csv(datadir=temp_dir)
    shutil.rmtree(temp_dir)
