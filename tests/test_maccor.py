import tempfile
import shutil
import pytest
import logging
from cellpy import log, get


log.setup_logging(default_level=logging.DEBUG, testing=True)


@pytest.fixture
def maccor_cell(cellpy_data_instance, parameters):
    return cellpy_data_instance.load(parameters.mpr_cellpy_file_path)


def test_set_instrument(cellpy_data_instance, parameters):
    import os

    instrument = "maccor_txt"
    cellpy_data_instance.set_instrument(instrument=instrument)
    cellpy_data_instance.from_raw(parameters.mcc_file_path, sep="\t")
    cellpy_data_instance.make_step_table()
    cellpy_data_instance.make_summary()
    assert len(cellpy_data_instance.cell.raw) == 6704
    temp_dir = tempfile.mkdtemp()
    logging.debug(f"created a temporary directory and dumping csv there ({temp_dir})")
    cellpy_data_instance.to_csv(datadir=temp_dir)
    assert len(os.listdir(temp_dir)) > 0
    shutil.rmtree(temp_dir)


def test_cellpy_get(parameters):
    instrument = "maccor_txt"
    c = get(
        parameters.mcc_file_path,
        instrument=instrument,
        sep="\t",
        logging_mode="DEBUG",
        testing=True,
    )
    assert len(c.cell.raw) == 6704


# def test_cellpy_get_2(parameters):
#     from cellpy import prms
#
#     prms.Instruments.Maccor.format_params = "two"
#     instrument = "maccor_txt"
#     c = get(parameters.mcc_file_path2, instrument=instrument)
#     assert len(c.cell.raw) == 6704
