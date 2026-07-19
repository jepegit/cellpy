"""Tests for the 2.0 ICA/DVA API (#566).

The golden suites in ``test_ica_goldens.py`` pin the *numbers*. This file pins
the *contract*: the option object, the specced output frame, direction
labelling, failure reporting, and the analytic correctness of ``dvdq``.
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import pytest

from cellpy import ica
from cellpy.exceptions import NullData

# --- synthetic curves --------------------------------------------------------
# A straight V(q) is the one case where both derivatives are known in closed
# form, which makes it an oracle that shares no code with the implementation.

LINEAR_SLOPE = 0.004  # V per capacity unit
LINEAR_INTERCEPT = 0.05


def linear_half_cycle(n: int = 400):
    capacity = np.linspace(0.0, 250.0, n)
    voltage = LINEAR_INTERCEPT + LINEAR_SLOPE * capacity
    return voltage, capacity


RAW = ica.IcaOptions(pre_smoothing=False, post_smoothing=False, normalize=False)


# --- IcaOptions --------------------------------------------------------------


def test_options_are_frozen():
    options = ica.IcaOptions()
    with pytest.raises(Exception):
        options.voltage_fwhm = 0.5


def test_options_accept_the_1x_boolean_normalize():
    assert ica.IcaOptions(normalize=True).normalize == "area"
    assert ica.IcaOptions(normalize=False).normalize is False


def test_options_reject_nonsense_normalize():
    with pytest.raises(ValueError, match="normalize must be"):
        ica.IcaOptions(normalize="nom_cap")


def test_options_reject_the_unfinished_hist_method():
    with pytest.raises(ValueError, match="hist"):
        ica.IcaOptions(increment_method="hist")


@pytest.mark.parametrize(
    "kwargs, match",
    [
        ({"savgol_order": 0}, "savgol_order"),
        ({"savgol_window_divisor": 0}, "savgol_window_divisor"),
        ({"normalizing_roof": 0}, "normalizing_roof"),
        ({"max_points": 1}, "max_points"),
    ],
)
def test_options_validate_at_construction(kwargs, match):
    with pytest.raises(ValueError, match=match):
        ica.IcaOptions(**kwargs)


def test_options_replace_rejects_typos():
    with pytest.raises(TypeError, match="voltage_fwmh"):
        ica.IcaOptions().replace(voltage_fwmh=0.02)


def test_options_replace_returns_a_new_object():
    base = ica.IcaOptions()
    changed = base.replace(voltage_fwhm=0.05)
    assert base.voltage_fwhm == 0.01
    assert changed.voltage_fwhm == 0.05


# --- the pure core -----------------------------------------------------------


def test_dvdq_of_a_straight_line_is_its_slope():
    """dV/dq of V = a + s·q is s everywhere. No implementation shared."""
    voltage, capacity = linear_half_cycle()
    result = ica.transform_half_cycle(voltage, capacity, RAW, derivative="dvdq")
    assert result.y == pytest.approx(LINEAR_SLOPE, rel=1e-9)


def test_dqdv_of_a_straight_line_is_the_reciprocal_slope():
    voltage, capacity = linear_half_cycle()
    result = ica.transform_half_cycle(voltage, capacity, RAW, derivative="dqdv")
    assert result.y == pytest.approx(1.0 / LINEAR_SLOPE, rel=1e-6)


def test_dvdq_of_a_parabola_matches_the_analytic_derivative():
    """V(q) = a + b·q + c·q² has dV/dq = b + 2c·q."""
    a, b, c = 0.05, 0.004, -5e-6
    capacity = np.linspace(0.0, 250.0, 2001)
    voltage = a + b * capacity + c * capacity**2

    result = ica.transform_half_cycle(voltage, capacity, RAW, derivative="dvdq")
    expected = b + 2 * c * result.x
    assert result.y == pytest.approx(expected, rel=1e-6)


def test_derivative_mode_is_validated():
    voltage, capacity = linear_half_cycle()
    with pytest.raises(ValueError, match="derivative must be"):
        ica.transform_half_cycle(voltage, capacity, RAW, derivative="dqdt")


def test_core_raises_null_data_on_missing_input():
    with pytest.raises(NullData):
        ica.transform_half_cycle(None, None)


def test_core_raises_null_data_on_a_single_point():
    with pytest.raises(NullData):
        ica.transform_half_cycle(np.array([1.0]), np.array([0.0]))


def test_core_rejects_mismatched_lengths():
    with pytest.raises(ValueError, match="same length"):
        ica.transform_half_cycle(np.zeros(10), np.zeros(11))


def test_core_returns_the_partner_coordinate():
    voltage, capacity = linear_half_cycle()
    result = ica.transform_half_cycle(voltage, capacity, RAW)
    assert len(result.partner) == len(result.x)
    # On a straight line the capacity at voltage v is exactly (v - a)/s.
    assert result.partner == pytest.approx(
        (result.x - LINEAR_INTERCEPT) / LINEAR_SLOPE, rel=1e-6
    )


# --- no hidden state ---------------------------------------------------------


def test_core_does_not_mutate_its_options():
    """The 1.x Converter wrote the derived normalizing factor back onto itself."""
    options = ica.IcaOptions()
    before = repr(options)
    voltage, capacity = linear_half_cycle()
    ica.transform_half_cycle(voltage, capacity, options)
    assert repr(options) == before
    assert options.normalizing_factor is None


def test_core_is_deterministic_across_interleaved_calls():
    """A reused 1.x Converter carried one half-cycle's normalization into the next.

    Running A, then a differently-scaled B, then A again must give A twice.
    """
    options = ica.IcaOptions()
    voltage_a, capacity_a = linear_half_cycle()
    voltage_b, capacity_b = linear_half_cycle()
    capacity_b = capacity_b * 3.0  # a very different normalizing factor

    first = ica.transform_half_cycle(voltage_a, capacity_a, options)
    ica.transform_half_cycle(voltage_b, capacity_b, options)
    again = ica.transform_half_cycle(voltage_a, capacity_a, options)

    assert np.array_equal(first.y, again.y)
    assert first.normalizing_factor == again.normalizing_factor


def test_normalizing_factor_is_reported_not_stored():
    voltage, capacity = linear_half_cycle()
    result = ica.transform_half_cycle(voltage, capacity, ica.IcaOptions())
    assert result.normalizing_factor == pytest.approx(capacity[-1])


# --- the specced frame -------------------------------------------------------


def test_dqdv_frame_has_the_specced_columns(dataset):
    frame = ica.dqdv(dataset, cycles=[1, 2])
    assert list(frame.columns) == [
        "cycle",
        "direction",
        "voltage",
        "capacity",
        "dqdv",
        "dq",
    ]


def test_dvdq_frame_has_the_specced_columns(dataset):
    frame = ica.dvdq(dataset, cycles=[1, 2])
    assert list(frame.columns) == ["cycle", "direction", "capacity", "voltage", "dvdq"]


def test_the_deprecated_dq_column_duplicates_dqdv(dataset):
    frame = ica.dqdv(dataset, cycles=1)
    pd.testing.assert_series_equal(
        frame["dq"], frame["dqdv"], check_names=False
    )


def test_frame_attrs_record_the_recipe(dataset):
    frame = ica.dqdv(dataset, cycles=1, voltage_fwhm=0.02)
    assert frame.attrs["derivative"] == "dqdv"
    assert frame.attrs["options"].voltage_fwhm == 0.02
    assert frame.attrs["normalized"] == "area"
    assert frame.attrs["failures"] == []


def test_dvdq_defaults_to_no_normalization(dataset):
    frame = ica.dvdq(dataset, cycles=1)
    assert frame.attrs["normalized"] is False


def test_direction_is_spelled_out(dataset):
    frame = ica.dqdv(dataset, cycles=1)
    assert set(frame["direction"]) <= {"charge", "discharge"}


def test_direction_labels_follow_cycle_mode(dataset):
    """The ±1 code in the curve frame means opposite things for the two modes.

    This is exactly the ambiguity the specced frame removes: 1.x handed back
    the raw code and left the reader to reconstruct it from cycle_mode.
    """
    as_anode = ica.dqdv(dataset, cycles=1, cycle_mode="anode")
    as_cathode = ica.dqdv(dataset, cycles=1, cycle_mode="cathode")

    anode_first = as_anode.iloc[0]["direction"]
    cathode_first = as_cathode.iloc[0]["direction"]
    assert anode_first == "discharge"
    assert cathode_first == "charge"


def test_direction_filter_selects_one_branch(dataset):
    charge = ica.dqdv(dataset, cycles=[1, 2], direction="charge")
    assert set(charge["direction"]) == {"charge"}

    both = ica.dqdv(dataset, cycles=[1, 2])
    assert len(charge) == (both["direction"] == "charge").sum()


def test_direction_is_validated(dataset):
    with pytest.raises(ValueError, match="direction must be"):
        ica.dqdv(dataset, cycles=1, direction="up")


# --- sources -----------------------------------------------------------------


def test_source_can_be_a_curve_frame(dataset):
    curves = dataset.get_cap(
        cycle=[1, 2],
        method="forth-and-forth",
        categorical_column=True,
        label_cycle_number=True,
        insert_nan=False,
    )
    from_frame = ica.dqdv(curves, cycle_mode=dataset.cycle_mode)
    from_cell = ica.dqdv(dataset, cycles=[1, 2])
    pd.testing.assert_frame_equal(from_frame, from_cell)


def test_source_can_be_two_arrays():
    voltage, capacity = linear_half_cycle()
    frame = ica.dqdv((voltage, capacity), options=RAW)
    assert list(frame["direction"].unique()) == ["charge"]
    assert frame["dqdv"].to_numpy() == pytest.approx(1.0 / LINEAR_SLOPE, rel=1e-6)


def test_a_frame_without_the_curve_columns_says_so():
    with pytest.raises(ValueError, match="missing column"):
        ica.dqdv(pd.DataFrame({"nope": [1.0, 2.0]}))


def test_an_unusable_source_says_so():
    with pytest.raises(TypeError, match="cannot read curves"):
        ica.dqdv("not a cell")


def test_taper_trimming_is_not_silently_dropped(dataset):
    """It only exists on the legacy split path; saying so beats ignoring it."""
    with pytest.raises(TypeError, match="trim_taper_steps"):
        ica.dqdv(dataset, cycles=1, trim_taper_steps=1)


# --- failures are visible ----------------------------------------------------


def _one_point_curve_frame():
    """A cycle whose charge branch has too few points to differentiate."""
    from cellpycore.config import CurveCols

    cols = CurveCols()
    return pd.DataFrame(
        {
            cols.cycle_num: [1, 1, 1, 1],
            cols.direction: [-1, -1, -1, 1],
            cols.potential: [0.1, 0.2, 0.3, 0.9],
            cols.capacity: [0.0, 1.0, 2.0, 3.0],
        }
    )


def test_a_failing_half_cycle_warns_instead_of_vanishing():
    frame = _one_point_curve_frame()
    with pytest.warns(RuntimeWarning, match="failed for 1 half-cycle"):
        result = ica.dqdv(frame)
    assert result.attrs["failures"][0]["cycle"] == 1
    assert "NullData" in result.attrs["failures"][0]["error"]


def test_strict_turns_a_failing_half_cycle_into_an_error():
    frame = _one_point_curve_frame()
    with pytest.raises(ValueError, match="failed for 1 half-cycle"):
        ica.dqdv(frame, strict=True)


def test_a_surviving_branch_is_still_returned():
    frame = _one_point_curve_frame()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        result = ica.dqdv(frame)
    assert not result.empty
    assert set(result["direction"]) == {"discharge"}


# --- wide conversion ---------------------------------------------------------


def test_to_wide_gives_a_cycle_multiindex(dataset):
    frame = ica.dqdv(dataset, cycles=[1, 2], direction="charge")
    wide = ica.to_wide(frame)
    assert wide.columns.names == ["cycle", "value"]
    assert set(wide.columns.get_level_values(0)) == {1, 2}
    assert set(wide.columns.get_level_values(1)) == {"voltage", "dqdv"}


def test_to_wide_keeps_directions_apart(dataset):
    frame = ica.dqdv(dataset, cycles=1)
    wide = ica.to_wide(frame)
    assert set(wide.columns.get_level_values(0)) == {"1 charge", "1 discharge"}


def test_to_wide_of_dvdq_uses_the_capacity_axis(dataset):
    frame = ica.dvdq(dataset, cycles=1, direction="charge")
    wide = ica.to_wide(frame)
    assert set(wide.columns.get_level_values(1)) == {"capacity", "dvdq"}


# --- dqdv and dvdq agree -----------------------------------------------------


def test_the_two_derivatives_are_reciprocal_on_a_real_half_cycle(dataset):
    """dQ/dV and dV/dQ describe the same curve, so they must invert each other.

    Compared at matched capacities rather than pointwise, because the two run
    on different grids (voltage-uniform vs capacity-uniform).
    """
    capacity, voltage = dataset.get_ccap(5, as_frame=False)

    ica_result = ica.transform_half_cycle(voltage, capacity, RAW, derivative="dqdv")
    dva_result = ica.transform_half_cycle(voltage, capacity, RAW, derivative="dvdq")

    # interpolate dQ/dV onto the capacity grid dV/dQ lives on
    order = np.argsort(ica_result.partner)
    dqdv_at_capacity = np.interp(
        dva_result.x, ica_result.partner[order], ica_result.y[order]
    )

    interior = slice(len(dva_result.x) // 10, -len(dva_result.x) // 10)
    product = dqdv_at_capacity[interior] * dva_result.y[interior]
    # Tight enough to catch a wrong grid spacing: a 5% error in the dV/dQ step
    # lands at 0.95 and fails here, but passes at abs=0.05.
    assert np.median(product) == pytest.approx(1.0, abs=0.02)
