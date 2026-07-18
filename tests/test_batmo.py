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
    
    hn = c.headers_normal
    # Assert that data is loaded
    assert not c.data.raw.empty

    # Check that test time is in seconds (max time should be > 1000s)
    max_time = c.data.raw[hn.test_time_txt].max()
    assert max_time > 1000.0, "Time was not correctly converted to seconds"

    # Check that step_index is strictly increasing
    step_indices = c.data.raw[hn.step_index_txt].unique()
    assert len(step_indices) > 100, "Step indices were not cumulated properly"

    # Check step index monotonic property
    assert c.data.raw[
        hn.step_index_txt
    ].is_monotonic_increasing, "Step index is not strictly increasing"

    # Test for missing columns
    assert hn.current_txt in c.data.raw.columns
    assert hn.voltage_txt in c.data.raw.columns
    assert hn.cycle_index_txt in c.data.raw.columns

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

    hn = c.headers_normal
    hst = c.headers_step_table
    si = hn.step_index_txt
    loaded = c.data.raw.reset_index(drop=True)
    pd.testing.assert_series_equal(
        loaded[si],
        expected_cellpy_step.astype(loaded[si].dtype).rename(si),
        check_index=False,
    )

    assert loaded[si].is_monotonic_increasing
    assert loaded[si].nunique() == len(c.data.steps)
    assert (loaded.groupby(si)[hn.step_time_txt].min() == 0.0).all()
    assert {"charge", "discharge"}.issubset(set(c.data.steps[hst.type]))
    assert not c.get_cap(cycle=1, method="forth-and-forth", mode="absolute").empty
