import logging
import pathlib
import os
import tempfile
from dataclasses import dataclass

import pytest

from cellpy import log


log.setup_logging(default_level="DEBUG", testing=True)


@dataclass
class Params:
    current_file_path: str = os.path.dirname(os.path.realpath(__file__))
    data_dir: str = os.path.abspath(os.path.join(current_file_path, "../testdata"))
    res_file_name: str = "20160805_test001_45_cc_01.res"
    raw_data_dir: str = os.path.join(data_dir, "data")
    output_dir: str = os.path.join(data_dir, "out")
    res_file_path: str = os.path.join(raw_data_dir, res_file_name)
    cellpy_file_name: str = "20160805_test001_45_cc_01.h5"
    cellpy_file_path: str = os.path.join(output_dir, cellpy_file_name)


@pytest.fixture
def clp_params():
    """Files, Directories, and Variables to be used in the tests."""
    return Params()


@pytest.fixture(scope="module")
def clean_dir():
    new_path = tempfile.mkdtemp()
    return new_path


@pytest.fixture(scope="function")
def cpi():
    logging.debug("******* Created a cellpydata-instance *******")
    from cellpy import cellreader, log

    log.setup_logging(default_level="DEBUG", testing=True)

    return cellreader.CellpyCell()


def test_create_cellpyfile(cpi, tmp_path, clp_params, capsys):
    # create a cellpy file from the res-file (used for testing)
    cpi.set_instrument("arbin_res")
    cpi.from_raw(clp_params.res_file_path)
    with capsys.disabled():
        print(f"\nFilename: {clp_params.res_file_path}")
        print("\nHERE IS THE DATA:")
        print(cpi.data)
    cpi.mass = 1.0
    cpi.make_summary(find_ir=True, find_end_voltage=True)
    name = pathlib.Path(tmp_path) / pathlib.Path(clp_params.cellpy_file_path).name
    logging.info(f"trying to save the cellpy file to {name}")
    cpi.save(name)


def test_generate_absolute_summary_columns(capsys, clp_params):
    from cellpy.slim import summarizers, selectors
    from cellpy import cellreader, log

    log.setup_logging(default_level="DEBUG", testing=True)

    cpi = cellreader.CellpyCell()

    nom_cap = 1.0
    mass = 1.0
    cpi.set_instrument("arbin_res")
    cpi.from_raw(clp_params.res_file_path)

    nom_cap_abs = cpi.nominal_capacity_as_absolute(nom_cap, mass, "gravimetric")

    with capsys.disabled():
        print(cpi)
        print(nom_cap_abs)
    cpi.make_step_table()
    data = cpi.core.data
    selector = selectors.create_selector(data)
    cpi.core.make_core_summary(data, selector, find_ir=True, find_end_voltage=True)

    data = summarizers.generate_absolute_summary_columns(data)
