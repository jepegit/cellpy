"""Tests for SUMMARY_META_DEPENDENCIES and CellpyCell.refresh_after (#846)."""

import pytest

from cellpy.readers.cellreader import (
    SUMMARY_META_DEPENDENCIES,
    normalize_summary_meta_fields,
)


def test_summary_meta_dependencies_keys():
    assert set(SUMMARY_META_DEPENDENCIES) == {
        "mass",
        "active_electrode_area",
        "nominal_capacity",
        "cycle_mode",
    }
    for entry in SUMMARY_META_DEPENDENCIES.values():
        assert entry["affects"]
        assert entry["notes"]


def test_normalize_summary_meta_fields_aliases():
    assert normalize_summary_meta_fields("active_mass") == ("mass",)
    assert normalize_summary_meta_fields(("area", "nom_cap")) == (
        "active_electrode_area",
        "nominal_capacity",
    )
    assert normalize_summary_meta_fields(None) == tuple(SUMMARY_META_DEPENDENCIES)


def test_normalize_summary_meta_fields_unknown():
    with pytest.raises(ValueError, match="Unknown summary meta field"):
        normalize_summary_meta_fields("temperature")


@pytest.mark.essential
def test_refresh_after_mass_updates_gravimetric(dataset):
    h = dataset.schema.summary
    grav_col = f"{h.charge_capacity}_gravimetric"
    assert grav_col in dataset.data.summary.columns

    before = dataset.data.summary[grav_col].copy()
    old_mass = float(dataset.mass)
    dataset.mass = old_mass * 2.0
    dataset.refresh_after(("mass",))

    after = dataset.data.summary[grav_col]
    # Doubling mass halves gravimetric capacity (factor ∝ 1/mass).
    ratio = (before / after).dropna()
    assert ratio.notna().any()
    assert (ratio - 2.0).abs().max() < 1e-6


def test_refresh_after_unknown_field_raises(dataset):
    with pytest.raises(ValueError, match="Unknown summary meta field"):
        dataset.refresh_after(("temperature",))


@pytest.mark.essential
def test_refresh_after_nominal_capacity_updates_c_rate(dataset):
    """Doubling nominal capacity halves C-rate (rate = current / capacity)."""
    h = dataset.schema.summary
    col = h.charge_c_rate
    assert col in dataset.data.summary.columns
    before = dataset.data.summary[col].astype(float)
    assert before.abs().max() > 0

    dataset.nominal_capacity = float(dataset.nominal_capacity) * 2.0
    dataset.refresh_after(("nominal_capacity",))

    after = dataset.data.summary[col].astype(float)
    mask = before.abs() > 1e-6
    ratio = (before[mask] / after[mask]).dropna()
    assert not ratio.empty
    # Step C-rate is rounded to 5 decimals before the current-unit factor,
    # so the ratio is 2 within that rounding, not bit-exact.
    assert (ratio - 2.0).abs().max() < 1e-2
