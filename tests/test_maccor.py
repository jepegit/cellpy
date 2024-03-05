import logging
import shutil
import tempfile

import pytest

from cellpy import get, log, prms

log.setup_logging(default_level=logging.DEBUG, testing=True)


@pytest.fixture
def maccor_cell(cellpy_data_instance, parameters):
    return cellpy_data_instance.load(parameters.mpr_cellpy_file_path)


def test_set_instrument(cellpy_data_instance, parameters):
    import os

    instrument = "maccor_txt"
    cellpy_data_instance.set_instrument(instrument=instrument)
    cellpy_data_instance.from_raw(parameters.mcc_file_path, model="one", sep="\t")
    cellpy_data_instance.make_step_table()
    cellpy_data_instance.make_summary()
    assert len(cellpy_data_instance.data.raw) == 6704
    temp_dir = tempfile.mkdtemp()
    logging.debug(f"created a temporary directory and dumping csv there ({temp_dir})")
    cellpy_data_instance.to_csv(datadir=temp_dir)
    assert len(os.listdir(temp_dir)) > 0
    shutil.rmtree(temp_dir)


def test_cellpy_get_model_one(parameters):
    instrument = "maccor_txt"
    c = get(
        filename=parameters.mcc_file_path,
        instrument=instrument,
        model="one",
        mass=1.0,
        testing=True,
    )
    assert len(c.data.raw) == 6704


def test_load_custom_yaml_file(parameters):
    definitions_file = parameters.custom_instrument_path
    from pprint import pprint

    from ruamel import yaml

    yml = yaml.YAML()
    with open(definitions_file, "r") as ff:
        settings = yml.load(ff.read())
    pprint(settings)


def test_cellpy_get_model_one_custom_instrument_file(parameters):
    """Use default location of user instrument files"""
    # uses local_instrument.py as loader
    # TODO: create defaults for missing parameters in the custom instrument file.

    instrument = parameters.custom_instrument
    prms.Paths.instrumentdir = parameters.instrument_dir
    logging.debug(f"directory: {parameters.instrument_dir}")
    logging.debug(f"instrument file: {parameters.custom_instrument}")
    c = get(
        filename=parameters.mcc_file_path, instrument=instrument, mass=1.0, testing=True
    )
    assert len(c.data.raw) == 6704


def test_cellpy_get(parameters):
    instrument = "maccor_txt"
    c = get(
        parameters.mcc_file_path,
        instrument=instrument,
        sep="\t",
        logging_mode="DEBUG",
        testing=True,
    )
    assert len(c.data.raw) == 6704


# def test_cellpy_get_2(parameters):
#     from cellpy import prms
#
#     prms.Instruments.Maccor.format_params = "two"
#     instrument = "maccor_txt"
#     c = get(parameters.mcc_file_path2, instrument=instrument)
#     assert len(c.data.raw) == 6704
