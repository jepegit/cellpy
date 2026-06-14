"""Fixture-free unit tests for pure helper/utility functions.

Added under issue #372 (test improvements). These target small, pure
functions that need no data files, network, or CellpyCell fixtures, so they
run fast and stay deterministic. Use this module as the pattern for further
low-cost coverage additions.
"""

import pathlib

import numpy as np
import pandas as pd
import pytest

from cellpy.internals import connections as internals_core
from cellpy.readers import data_structures as core
from cellpy.utils import helpers


class TestInterpolateYonX:
    """cellpy.readers.data_structures.interpolate_y_on_x (the base interpolator)."""

    @staticmethod
    def _linear_df():
        # y = 2 * x
        return pd.DataFrame({"x": [0.0, 1.0, 2.0, 3.0, 4.0], "y": [0.0, 2.0, 4.0, 6.0, 8.0]})

    def test_number_of_points_linear(self):
        out = core.interpolate_y_on_x(self._linear_df(), x="x", y="y", number_of_points=5)
        assert list(out.columns) == ["x", "y"]
        assert len(out) == 5
        # linear relationship must be preserved by interpolation
        assert np.allclose(out["y"].values, 2.0 * out["x"].values)

    def test_direction_negative_inverts_range(self):
        out = core.interpolate_y_on_x(
            self._linear_df(), x="x", y="y", number_of_points=5, direction=-1
        )
        assert len(out) == 5
        # with direction=-1 the x-range is generated high -> low
        assert out["x"].iloc[0] > out["x"].iloc[-1]
        assert np.allclose(out["y"].values, 2.0 * out["x"].values)

    def test_new_x_tuple_branch(self):
        # the (start, end, n) tuple form is an explicit branch in the function
        out = core.interpolate_y_on_x(self._linear_df(), x="x", y="y", new_x=(0.0, 4.0, 9))
        assert len(out) == 9
        assert np.allclose(out["y"].values, 2.0 * out["x"].values)

    def test_default_columns_used_when_not_given(self):
        # x/y default to the first two columns
        out = core.interpolate_y_on_x(self._linear_df(), number_of_points=3)
        assert np.allclose(out["y"].values, 2.0 * out["x"].values)


class TestCheckConnection:
    """cellpy.internals.connections.check_connection short-circuits on local paths."""

    def test_local_path_returns_empty_dict(self):
        # a plain local path is not "external", so no network access happens
        result = internals_core.check_connection(pathlib.Path(".").resolve())
        assert result == {}


class TestAddCvStepColumns:
    """cellpy.utils.helpers.add_cv_step_columns."""

    def test_expands_only_capacity_columns(self):
        result = helpers.add_cv_step_columns(["cycle_index", "charge_capacity", "voltage"])
        assert result == [
            "cycle_index",
            "charge_capacity",
            "charge_capacity_cv",
            "charge_capacity_non_cv",
            "voltage",
        ]

    def test_no_capacity_columns_unchanged(self):
        cols = ["cycle_index", "voltage", "current"]
        assert helpers.add_cv_step_columns(cols) == cols

    def test_empty_input(self):
        assert helpers.add_cv_step_columns([]) == []


class TestFixGroupNames:
    """cellpy.utils.helpers.fix_group_names de-duplicates by appending 'x'."""

    def test_duplicates_are_made_unique(self):
        assert helpers.fix_group_names(["a", "a", "b", "a"]) == ["a", "ax", "b", "axx"]

    def test_already_unique_unchanged(self):
        assert helpers.fix_group_names(["a", "b", "c"]) == ["a", "b", "c"]
