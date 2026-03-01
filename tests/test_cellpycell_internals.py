"""tests for internal methods of CellpyCell (cellreader.py)"""

import os
import pathlib
import logging

import pytest

import cellpy
from cellpy.readers import core
from cellpy import log, prms
from cellpy.exceptions import DeprecatedFeature, WrongFileVersion
from cellpy.parameters.internal_settings import get_headers_summary

log.setup_logging(default_level="DEBUG", testing=True)


def test_cellpyfile_has_data_point_as_index(cell):
    """Check if the raw data has data_point as index."""
    assert cell.has_data_point_as_index()


def test_raw_has_data_point_as_index(raw_cell):
    """Check if the raw data has data_point as index."""
    assert raw_cell.has_data_point_as_index()


def test_cellpyfile_has_data_point_as_column(cell):
    """Check if the raw data has data_point as column."""
    assert cell.has_data_point_as_column()


def test_raw_has_data_point_as_column(raw_cell):
    """Check if the raw data has data_point as column."""
    assert raw_cell.has_data_point_as_column()


def test_has_no_full_duplicates(cell):
    """Check if the raw data has no full duplicates."""
    assert cell.has_no_full_duplicates()


def test_has_no_partial_duplicates(cell):
    """Check if the raw data has no partial duplicates."""
    assert cell.has_no_partial_duplicates()
    assert cell.has_no_partial_duplicates(subset="data_point")


def test_create_cellpy_file(cellpy_data_instance, tmp_path, parameters):
    # create a cellpy file from the res-file (used for testing)
    cellpy_data_instance.from_raw(parameters.res_file_path)
    name = pathlib.Path(tmp_path) / pathlib.Path(parameters.cellpy_file_path).name
    cellpy_data_instance.save(name, ensure_step_table=True)
    assert name.is_file()

    new_cellpy_data = cellpy.get(name, testing=True)
    print(new_cellpy_data.data.summary.head())


def test_check_file_ids(cellpy_data_instance, tmp_path, parameters):
    # create a cellpy file from the res-file (used for testing)
    cellpy_data_instance.from_raw(parameters.res_file_path)
    print()
    print(cellpy_data_instance)
    cellpy_data_instance.mass = 1.0
    cellpy_data_instance.make_summary(find_ir=True, find_end_voltage=True)
    name = pathlib.Path(tmp_path) / pathlib.Path(parameters.cellpy_file_path).name
    logging.info(f"trying to save the cellpy file to {name}")
    cellpy_data_instance.save(name)
