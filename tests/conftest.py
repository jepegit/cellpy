"""pytest fixtures for cellpy"""
import logging
import pathlib

import pytest

from cellpy.readers.core import Data
from . import fdv

# NOTE: all tests can now use the parameters fixture instead of importing fdv directly.
# NOTE: if you decide to implement scoped fixtures in a module, you will have to either
#   add a new fixture here (e.g. dataset_module_scope with corresponding parameters_module_scope)
#   and use those, or duplicate the fixtures inside the module

# TODO: change name of 'dataset' to 'cell' (this will require changes all usage of 'dataset' to 'cell' in all modules)


@pytest.fixture
def hello_world():
    return "hello cellpy!"


@pytest.fixture
def parameters():
    """Files, Directories, and Variables to be used in the tests."""
    return fdv


@pytest.fixture(scope="function")
def cellpy_data_instance():
    logging.debug("******* Created a cellpydata-instance *******")
    from cellpy import cellreader, log

    log.setup_logging(default_level="DEBUG", testing=True)

    return cellreader.CellpyData()


@pytest.fixture
def dataset(cellpy_data_instance) -> Data:
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
