"""pytest fixtures for cellpy"""

import logging
import pathlib

import pytest

from cellpy.readers.core import Data
from cellpy.readers.cellreader import CellpyCell
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

    return cellreader.CellpyCell()


@pytest.fixture
def dataset(cellpy_data_instance) -> CellpyCell:
    from cellpy import cellreader

    p = pathlib.Path(fdv.cellpy_file_path)

    if not p.is_file():
        logging.info(f"pytest fixture could not find {fdv.cellpy_file_path} - making it from raw and saving")
        a = cellreader.CellpyCell()
        a.from_raw(fdv.res_file_path)
        a.set_mass(1.0)
        a.make_summary(find_ir=True, find_end_voltage=True)
        a.save(fdv.cellpy_file_path)

    return cellpy_data_instance.load(fdv.cellpy_file_path)


@pytest.fixture
def rate_dataset(cellpy_data_instance) -> CellpyCell:
    """Fixture for CellpyCell instance with rate data loaded from cellpy-file"""

    return cellpy_data_instance.load(fdv.rate_cell_path)

@pytest.fixture
def gitt_datasett(cellpy_data_instance) -> CellpyCell:
    """Fixture for CellpyCell instance with GITT data loaded from cellpy-file"""

    return cellpy_data_instance.load(fdv.gitt_file_path)


@pytest.fixture
def cell(cellpy_data_instance) -> CellpyCell:
    """Fixture for CellpyCell instance loaded from cellpy-file"""
    # changed name from dataset to cell
    from cellpy import cellreader

    p = pathlib.Path(fdv.cellpy_file_path)

    if not p.is_file():
        logging.info(f"pytest fixture could not find {fdv.cellpy_file_path} - making it from raw and saving")
        a = cellreader.CellpyCell()
        a.from_raw(fdv.res_file_path)
        a.make_summary(find_ir=True, find_end_voltage=True)
        a.save(fdv.cellpy_file_path)

    return cellpy_data_instance.load(fdv.cellpy_file_path)


@pytest.fixture
def raw_cell(cellpy_data_instance) -> CellpyCell:
    """Fixture for CellpyCell instance loaded from a raw-file"""
    from cellpy import cellreader

    a = cellreader.CellpyCell()
    a.from_raw(fdv.res_file_path)
    a.make_summary(find_ir=True, find_end_voltage=True)

    return a


@pytest.fixture
def mock_env_cellpy_user(monkeypatch, parameters):
    """Mock the environment variables for cellpy"""
    monkeypatch.setenv("CELLPY_USER", parameters.env_cellpy_user)


@pytest.fixture
def mock_env_cellpy_host(monkeypatch, parameters):
    """Mock the environment variables for cellpy"""
    monkeypatch.setenv("CELLPY_HOST", parameters.env_cellpy_host)


@pytest.fixture
def mock_env_cellpy_key_filename(monkeypatch, parameters):
    """Mock the environment variables for cellpy"""
    monkeypatch.setenv("CELLPY_KEY_FILENAME", parameters.env_cellpy_key_filename)


@pytest.fixture
def mock_env_cellpy_password(monkeypatch, parameters):
    """Mock the environment variables for cellpy"""
    monkeypatch.setenv("CELLPY_PASSWORD", parameters.env_cellpy_password)


@pytest.fixture
def cell_with_summary(cell):
    """Fixture for CellpyCell with pre-computed summary (alias for cell)."""
    # Ensure summary exists
    if cell.data.summary is None or len(cell.data.summary) == 0:
        cell.make_summary(find_ir=True, find_end_voltage=True)
    return cell


@pytest.fixture
def cell_with_cv_data(cell):
    """Fixture for CellpyCell with CV step data.
    
    Note: This uses the same cell fixture but ensures step table is made
    which is needed for CV-related plots.
    """
    # Ensure step table exists for CV detection
    if cell.data.steps is None or len(cell.data.steps) == 0:
        cell.make_step_table()
    # Ensure summary exists
    if cell.data.summary is None or len(cell.data.summary) == 0:
        cell.make_summary(find_ir=True, find_end_voltage=True)
    return cell