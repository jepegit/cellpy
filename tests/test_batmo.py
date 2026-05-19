import pytest
from cellpy import get
from . import fdv


def test_load_batmo_bdf():
    c = get(
        filename=fdv.batmo_file_path, 
        instrument="batmo_bdf", 
        testing=True
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
