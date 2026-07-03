import logging

import numpy as np
import pandas as pd
import pytest

from cellpy import log
from cellpy.exceptions import NullData
from cellpy.utils import helpers

log.setup_logging(default_level=logging.DEBUG, testing=True)


# ----------------------------------------------------------------------
# Fixture-free unit tests on synthetic summary frames (issue #372).
# Cycle 5 is a high outlier, cycle 9 a low outlier.
# ----------------------------------------------------------------------


@pytest.fixture
def synthetic_summary():
    idx = pd.Index(range(1, 11), name="cycle_index")
    charge = [1.00, 1.01, 0.99, 1.02, 5.00, 1.00, 0.98, 1.01, 0.10, 1.00]
    discharge = [0.98, 1.00, 0.98, 1.00, 4.90, 0.99, 0.97, 1.00, 0.09, 0.99]
    return pd.DataFrame(
        {"charge_capacity": charge, "discharge_capacity": discharge}, index=idx
    )


def test_remove_outliers_on_value(synthetic_summary):
    filtered = helpers.remove_outliers_from_summary_on_value(
        synthetic_summary, low=0.5, high=2.0
    )
    assert list(filtered.index) == [1, 2, 3, 4, 6, 7, 8, 10]


def test_remove_outliers_on_value_freeze_indexes(synthetic_summary):
    filtered = helpers.remove_outliers_from_summary_on_value(
        synthetic_summary, low=0.5, high=2.0, freeze_indexes=[5]
    )
    assert 5 in filtered.index
    assert 9 not in filtered.index


def test_remove_outliers_on_zscore(synthetic_summary):
    filtered = helpers.remove_outliers_from_summary_on_zscore(
        synthetic_summary, zscore_limit=1.5
    )
    assert 5 not in filtered.index
    assert 1 in filtered.index


def test_remove_outliers_on_window(synthetic_summary):
    filtered = helpers.remove_outliers_from_summary_on_window(
        synthetic_summary, window_size=3, cut=0.3
    )
    assert 5 not in filtered.index
    assert 1 in filtered.index


def test_remove_outliers_on_nn_distance(synthetic_summary):
    filtered = helpers.remove_outliers_from_summary_on_nn_distance(
        synthetic_summary, distance=0.7
    )
    assert 5 not in filtered.index
    assert 9 not in filtered.index
    assert 1 in filtered.index


def test_remove_first_cycles(synthetic_summary):
    filtered = helpers.remove_first_cycles_from_summary(synthetic_summary, first=3)
    assert list(filtered.index) == list(range(3, 11))


def test_remove_first_cycles_noop(synthetic_summary):
    assert helpers.remove_first_cycles_from_summary(synthetic_summary).equals(
        synthetic_summary
    )


def test_remove_last_cycles(synthetic_summary):
    filtered = helpers.remove_last_cycles_from_summary(synthetic_summary, last=8)
    assert list(filtered.index) == list(range(1, 9))


def test_add_normalized_cycle_index(synthetic_summary):
    s = synthetic_summary.copy()
    s["cumulated_charge_capacity_gravimetric"] = np.cumsum(s["charge_capacity"])
    out = helpers.add_normalized_cycle_index(s, nom_cap=2.0)
    assert out["normalized_cycle_index"].iloc[0] == pytest.approx(0.5)
    assert out["normalized_cycle_index"].iloc[-1] == pytest.approx(6.555)


def test_create_rate_column():
    df = pd.DataFrame({"current_avr": [-0.002, 0.001, 0.0005]})
    rates = helpers.create_rate_column(df, nom_cap=1.0, spec_conv_factor=1000)
    assert list(rates) == [2.0, 1.0, 0.5]


class TestCreateGroupNames:
    def test_custom_dict_hit(self):
        assert helpers.create_group_names({2: "my-group"}, 2, None, None, None) == "my-group"

    def test_custom_dict_miss_falls_back_to_generic(self):
        assert helpers.create_group_names({2: "my-group"}, 3, None, None, None) == "group-03"

    def test_custom_str_prefix(self):
        assert helpers.create_group_names("pre", 4, None, None, None) == "pre-group-04"

    def test_group_label_from_pages(self):
        pages = pd.DataFrame({"group": [1, 2], "group_label": ["alpha", "beta"]})
        assert helpers.create_group_names(None, 2, None, None, pages) == "beta"

    def test_fallback_on_key_index_bounds(self):
        keys = ["cellA_01_x", "cellA_01_y"]
        assert helpers.create_group_names(None, 1, [0, 2], keys, None) == "cellA_01"


# TODO: manually renaming cellpy fixture to cell; remove this when all instances of dataset is renamed to cell
@pytest.fixture
def cell(dataset):
    return dataset


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
