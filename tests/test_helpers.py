import pytest
import logging
import pandas as pd
from cellpy import log
from cellpy.utils import helpers
from . import fdv
from cellpy.exceptions import NullData


log.setup_logging(default_level=logging.DEBUG)


@pytest.fixture
def cell():
    from cellpy import cellreader

    d = cellreader.CellpyData()
    d.load(fdv.cellpy_file_path)
    return d


def test_split_experiment(cell):
    list_of_all_cycles = cell.get_cycle_numbers()
    c1, c2 = helpers.split_experiment(cell, 10)
    list_of_first_cycles = c1.get_cycle_numbers()
    list_of_last_cycles = c2.get_cycle_numbers()
    assert all(list_of_first_cycles == range(1, 10))
    assert list_of_all_cycles[-1] == list_of_last_cycles[-1]


def test_split_experiment_new(cell):
    list_of_all_cycles = cell.get_cycle_numbers()
    c1, c2 = cell.split(10)
    list_of_first_cycles = c1.get_cycle_numbers()
    list_of_last_cycles = c2.get_cycle_numbers()
    assert all(list_of_first_cycles == range(1, 10))
    assert list_of_all_cycles[-1] == list_of_last_cycles[-1]


def test_select_summary_based_on_rate(cell):
    cell.make_step_table(add_c_rate=True)
    filtered_summary = helpers.select_summary_based_on_rate(cell, 0.04)
    assert len(filtered_summary) == 3
