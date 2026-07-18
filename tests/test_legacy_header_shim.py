"""Tests for the D6 legacy-header attribute shim (native-headers flip, Stage 2).

The shim is not wired into ``CellpyCell`` yet (Stage 5), so these test it
directly against a native ``config.default_schema()``.
"""

from __future__ import annotations

import warnings

import pytest
from cellpycore.config import default_schema

from cellpy import _deprecation
from cellpy.parameters.legacy_header_shim import (
    LegacyHeaderShim,
    build_legacy_shims,
)


@pytest.fixture
def shims():
    return build_legacy_shims(default_schema())


def _count_dep_warnings(fn):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        value = fn()
    n = sum(1 for w in caught if issubclass(w.category, DeprecationWarning))
    return value, n


def test_build_legacy_shims_frames(shims):
    assert set(shims) == {"headers_normal", "headers_step_table", "headers_summary"}
    assert all(isinstance(s, LegacyHeaderShim) for s in shims.values())


def test_raw_renamed_attributes_resolve_and_warn(shims):
    hn = shims["headers_normal"]
    assert _count_dep_warnings(lambda: hn.voltage_txt) == ("potential", 1)
    assert _count_dep_warnings(lambda: hn.cycle_index_txt) == ("cycle_num", 1)
    assert _count_dep_warnings(lambda: hn.data_point_txt) == ("datapoint_num", 1)


def test_step_and_summary_renamed_attributes_resolve(shims):
    hst = shims["headers_step_table"]
    hs = shims["headers_summary"]
    assert _count_dep_warnings(lambda: hst.cycle) == ("cycle_num", 1)
    assert _count_dep_warnings(lambda: hst.voltage) == ("potential", 1)
    assert _count_dep_warnings(lambda: hs.cycle_index) == ("cycle_num", 1)


def test_unchanged_names_pass_through_without_warning(shims):
    # native names (and legacy names that equal the native name) do not warn.
    hn = shims["headers_normal"]
    hs = shims["headers_summary"]
    assert _count_dep_warnings(lambda: hn.potential) == ("potential", 0)
    assert _count_dep_warnings(lambda: hn.current) == ("current", 0)
    assert _count_dep_warnings(lambda: hs.charge_capacity) == ("charge_capacity", 0)


def test_summary_specific_column_by_key_composes(shims):
    hs = shims["headers_summary"]
    value, _ = _count_dep_warnings(lambda: hs["charge_capacity_gravimetric"])
    assert value == "charge_capacity_gravimetric"
    value2, _ = _count_dep_warnings(lambda: hs["discharge_capacity_areal"])
    assert value2 == "discharge_capacity_areal"


def test_duplicate_value_pair_resolves_and_warns(shims):
    hs = shims["headers_summary"]
    # charge_capacity_raw shares the "charge_capacity" column value.
    assert _count_dep_warnings(lambda: hs.discharge_capacity_raw) == (
        "discharge_capacity",
        1,
    )
    assert _count_dep_warnings(lambda: hs.charge_capacity_raw) == (
        "charge_capacity",
        1,
    )


def test_getitem_matches_getattr(shims):
    hn = shims["headers_normal"]
    assert hn["voltage_txt"] == "potential"
    assert hn["voltage_txt"] == hn.voltage_txt


def test_legacy_only_attribute_resolves_to_unchanged_name(shims):
    # Legacy-only columns are not renamed by the flip (to_native passes them
    # through), so the shim returns their unchanged legacy name (no warning).
    hn = shims["headers_normal"]
    hst = shims["headers_step_table"]
    hs = shims["headers_summary"]
    assert _count_dep_warnings(lambda: hn.power_txt) == ("power", 0)
    assert _count_dep_warnings(lambda: hn.datetime_txt) == ("date_time", 0)
    assert _count_dep_warnings(lambda: hn.test_id_txt) == ("test_id", 0)
    assert _count_dep_warnings(lambda: hst.info) == ("info", 0)
    assert _count_dep_warnings(lambda: hst.ustep) == ("ustep", 0)
    assert _count_dep_warnings(lambda: hs.shifted_charge_capacity) == (
        "shifted_charge_capacity",
        0,
    )


def test_unknown_attribute_raises(shims):
    with pytest.raises(AttributeError):
        _ = shims["headers_normal"].not_a_real_attr


def test_warns_once_per_attribute(shims):
    _deprecation._WARNED_SITES.clear()
    hn = shims["headers_normal"]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        hn.voltage_txt
        hn.voltage_txt
        hn.voltage_txt
    voltage_warnings = [
        w for w in caught if "headers_normal.voltage_txt" in str(w.message)
    ]
    assert len(voltage_warnings) == 1


def test_bad_frame_rejected():
    with pytest.raises(ValueError, match="unknown frame"):
        LegacyHeaderShim("nonsense", default_schema().raw)
