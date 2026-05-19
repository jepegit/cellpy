import pandas as pd
import pytest
from cellpy import get
from . import fdv


def test_load_batmo_bdf():
    c = get(
        filename=fdv.batmo_file_path,
        instrument="batmo_bdf",
        testing=True,
        cycle_mode="anode",
    )
    
    # Assert that data is loaded
    assert not c.data.raw.empty
    
    # Check that test time is in seconds (max time should be > 1000s)
    max_time = c.data.raw["test_time"].max()
    assert max_time > 1000.0, "Time was not correctly converted to seconds"
    
    # Check that step_index is strictly increasing
    step_indices = c.data.raw["step_index"].unique()
    assert len(step_indices) > 100, "Step indices were not cumulated properly"
    
    # Check step index monotonic property
    assert c.data.raw["step_index"].is_monotonic_increasing, "Step index is not strictly increasing"

    # Test for missing columns
    assert "current" in c.data.raw.columns
    assert "voltage" in c.data.raw.columns
    assert "cycle_index" in c.data.raw.columns

    assert c._validate_step_table()


def test_batmo_bdf_step_index_is_preprocessed_to_continuous_segments():
    raw_bdf = pd.read_csv(fdv.batmo_file_path)
    raw_local_step = raw_bdf["Step Index / 1"]
    raw_cycle = raw_bdf["Cycle Count / 1"]
    raw_step_group = raw_cycle.astype(str) + "_" + raw_local_step.astype(str)
    expected_cellpy_step = (raw_step_group != raw_step_group.shift()).cumsum()

    assert not raw_local_step.is_monotonic_increasing
    assert (raw_local_step.diff() < 0).sum() == (raw_cycle.diff() > 0).sum()

    c = get(
        filename=fdv.batmo_file_path,
        instrument="batmo_bdf",
        testing=True,
        cycle_mode="anode",
    )

    loaded = c.data.raw.reset_index(drop=True)
    pd.testing.assert_series_equal(
        loaded["step_index"],
        expected_cellpy_step.astype(loaded["step_index"].dtype).rename("step_index"),
        check_index=False,
    )

    assert loaded["step_index"].is_monotonic_increasing
    assert loaded["step_index"].nunique() == len(c.data.steps)
    assert (loaded.groupby("step_index")["step_time"].min() == 0.0).all()
    assert {"charge", "discharge"}.issubset(set(c.data.steps["type"]))
    assert not c.get_cap(cycle=1, method="forth-and-forth", mode="absolute").empty
