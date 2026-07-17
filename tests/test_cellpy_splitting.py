import logging

import pandas as pd
import pytest

from cellpy import log
from cellpy.exceptions import NullData
from cellpy.utils import helpers

log.setup_logging(default_level=logging.DEBUG, testing=True)


# TODO: manually renaming cellpy fixture to cell; remove this when all instances of dataset is renamed to cell
@pytest.fixture
def cell(dataset):
    return dataset


def test_split(cell):
    list_of_all_cycles = cell.get_cycle_numbers()
    c1, c2 = cell.split(10)
    list_of_first_cycles = c1.get_cycle_numbers()
    list_of_last_cycles = c2.get_cycle_numbers()
    assert list_of_first_cycles[0] == 1
    assert list_of_first_cycles[-1] == 9
    assert list_of_all_cycles[-1] == list_of_last_cycles[-1]


def test_drop_to(cell):
    c1 = cell.drop_to(10)
    list_of_new_cycles = c1.get_cycle_numbers()
    print(list_of_new_cycles)
    assert list_of_new_cycles[0] == 10
    assert list_of_new_cycles[-1] == cell.get_cycle_numbers()[-1]


def test_drop_from(cell):
    c1 = cell.drop_from(10)
    list_of_new_cycles = c1.get_cycle_numbers()
    assert list_of_new_cycles[0] == 1
    assert list_of_new_cycles[-1] == 9


# pins added with the #519 extraction (behaviour unchanged, coverage was thin)
def test_from_cycle(cell):
    c1 = cell.from_cycle(10)
    list_of_new_cycles = c1.get_cycle_numbers()
    assert list_of_new_cycles[0] == 10
    assert list_of_new_cycles[-1] == cell.get_cycle_numbers()[-1]


def test_to_cycle(cell):
    c1 = cell.to_cycle(9)
    list_of_new_cycles = c1.get_cycle_numbers()
    assert list_of_new_cycles[0] == 1
    assert list_of_new_cycles[-1] == 9


def test_drop_edges(cell):
    c1 = cell.drop_edges(5, 10)
    list_of_new_cycles = c1.get_cycle_numbers()
    assert list_of_new_cycles[0] == 5
    assert list_of_new_cycles[-1] == 9


def test_drop_edges_bad_args_raise(cell):
    with pytest.raises(ValueError):
        cell.drop_edges(10, 5)
    with pytest.raises(ValueError):
        cell.drop_edges(5, 5)


def test_split_many_list(cell):
    c1, c2, c3 = cell.split_many([5, 10])
    assert c1.get_cycle_numbers()[-1] == 4
    assert c2.get_cycle_numbers()[0] == 5
    assert c2.get_cycle_numbers()[-1] == 9
    assert c3.get_cycle_numbers()[0] == 10


def test_with_cycles(cell):
    picked = [2, 4, 6]
    c1 = cell.with_cycles(picked)
    assert list(c1.get_cycle_numbers()) == picked
    assert set(c1.data.steps[cell.headers_step_table.cycle].unique()) == set(picked)
