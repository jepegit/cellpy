"""pytest fixtures for cellpy"""
import logging
import pathlib

import pytest

from . import fdv


@pytest.fixture
def hello_world():
    return "hello cellpy!"


@pytest.fixture
def parameters():
    """Files, Directories, and Variables to be used in the tests."""
    return fdv


@pytest.fixture
def cellpy_data_instance():
    from cellpy import cellreader
    from cellpy import log

    log.setup_logging(default_level="DEBUG")

    return cellreader.CellpyData()


@pytest.fixture
def dataset(cellpy_data_instance):
    from cellpy import cellreader

    p = pathlib.Path(fdv.cellpy_file_path)

    if not p.is_file():
        logging.info(
            f"pytest fixture could not find {fdv.cellpy_file_path} - making it from raw and saving"
        )
        a = cellreader.CellpyData()
        a.from_raw(fdv.res_file_path)
        a.set_mass(1.0)
        a.make_summary(find_ocv=False, find_ir=True, find_end_voltage=True)
        a.save(fdv.cellpy_file_path)

    return cellpy_data_instance.load(fdv.cellpy_file_path)
