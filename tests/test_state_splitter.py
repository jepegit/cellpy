"""Regression tests for state-splitting loaders (#580).

`_state_splitter` silently produced all-zero capacities on pandas 3 for every
loader that splits a single signed column by state (maccor_txt, neware_txt,
batmo_bdf). No test asserted that a loaded capacity was non-zero, so a whole
release shipped with it.

These tests exist to make that specific silence impossible.
"""

from __future__ import annotations

import logging

import pandas as pd
import pytest

from cellpy import log
from cellpy.readers.instruments.processors.post_processors import _state_splitter

log.setup_logging(default_level=logging.DEBUG, testing=True)


STATES = {
    "column_name": "State",
    "charge_keys": ["C"],
    "discharge_keys": ["D"],
    "rest_keys": ["R"],
}


def _raw() -> pd.DataFrame:
    """Two cycles: rest, charge to 3, discharge to 2."""
    return pd.DataFrame(
        {
            "data_point": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "cycle_index": [1, 1, 1, 1, 1, 2, 2, 2, 2, 2],
            "State": ["R", "C", "C", "D", "D", "R", "C", "C", "D", "D"],
            "charge_capacity": [0.0, 1.0, 3.0, 1.0, 2.0, 0.0, 1.5, 3.5, 1.0, 2.5],
        }
    )


def _split(raw: pd.DataFrame) -> pd.DataFrame:
    return _state_splitter(
        raw,
        base_col_name="charge_capacity",
        n_charge=1,
        n_discharge=1,
        new_col_name_charge="charge_capacity",
        new_col_name_discharge="discharge_capacity",
        temp_col_name_charge="tmp_charge",
        temp_col_name_discharge="tmp_discharge",
        propagate=True,
        states=STATES,
    )


@pytest.mark.essential
def test_split_produces_non_zero_capacities():
    """The assertion whose absence let #580 ship."""
    out = _split(_raw())
    assert out["charge_capacity"].max() > 0, "charge capacity is all zeros (#580)"
    assert out["discharge_capacity"].max() > 0, "discharge capacity is all zeros (#580)"


@pytest.mark.essential
def test_charge_column_takes_the_charge_rows():
    out = _split(_raw())
    # Cycle 1 charges to 3.0 on rows 2-3.
    assert out.loc[2, "charge_capacity"] == 3.0


@pytest.mark.essential
def test_charge_value_propagates_to_the_end_of_its_cycle():
    out = _split(_raw())
    # After the last charge row of cycle 1, the charge column holds its final
    # value rather than dropping back to zero (the legacy "propagate").
    assert out.loc[3, "charge_capacity"] == 3.0
    assert out.loc[4, "charge_capacity"] == 3.0


@pytest.mark.essential
def test_each_cycle_starts_from_zero():
    out = _split(_raw())
    # Row 5 is the rest step at the start of cycle 2.
    assert out.loc[5, "charge_capacity"] == 0.0
    assert out.loc[5, "discharge_capacity"] == 0.0


@pytest.mark.essential
def test_discharge_column_takes_the_discharge_rows():
    out = _split(_raw())
    assert out.loc[4, "discharge_capacity"] == 2.0


@pytest.mark.essential
def test_total_failure_raises_instead_of_returning_zeros():
    """A failure on *every* cycle is a bug, not bad data.

    Silently returning a zero column is what made #580 invisible; a column of
    zeros is indistinguishable from a real measurement of nothing.
    """
    raw = _raw().drop(columns=["State"])  # makes every cycle fail
    with pytest.raises(ValueError, match="every cycle"):
        _split(raw)


@pytest.mark.essential
def test_maccor_file_loads_with_real_capacities():
    """End to end on a real file — the user-visible symptom of #580."""
    import cellpy
    import cellpy.utils.example_data as ed

    cell = cellpy.get(
        ed.maccor_file_path(),
        instrument="maccor_txt",
        model="THREE",
        mass=1.0,
        testing=True,
    )
    raw = cell.data.raw
    assert raw["cumulative_charge_capacity"].max() > 0
    assert raw["cumulative_discharge_capacity"].max() > 0

    summary = cell.data.summary
    assert summary["charge_capacity"].max() > 0
    assert summary["discharge_capacity"].max() > 0
