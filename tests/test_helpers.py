import logging

import pytest

from cellpy import log
from cellpy.exceptions import NullData
from cellpy.utils import helpers

log.setup_logging(default_level=logging.DEBUG, testing=True)


# TODO: manually renaming cellpy fixture to cell; remove this when all instances of dataset is renamed to cell
@pytest.fixture
def cell(dataset):
    return dataset


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
    cell.make_step_table()
    filtered_summary = helpers.select_summary_based_on_rate(cell, 0.04)
    assert len(filtered_summary) == 3


def test_remove_outliers_on_index(cell):
    last = cell.get_cycle_numbers()[-1]
    s1 = helpers.remove_outliers_from_summary_on_index(cell.data.summary, indexes=[15])
    s2 = helpers.remove_outliers_from_summary_on_index(
        cell.data.summary, indexes=[15], remove_last=True
    )
    assert 14 in s1.index
    assert 15 not in s1.index
    assert last in s1.index
    assert last not in s2.index
    assert 15 not in s2.index


def test_concatenate_summaries(cell):
    # the function should be moved to batch utils and the tests are in test_batch
    pass
