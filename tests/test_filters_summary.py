"""Tests for cellpy.filters.summary.filter_summary."""

from __future__ import annotations

import logging

import pandas as pd
import pytest

from cellpy import log
from cellpy.filters import filter_summary, register_range_filter

log.setup_logging(default_level=logging.DEBUG, testing=True)


def _summary(rows: list[tuple[int, float, float]]) -> pd.DataFrame:
    """Build a minimal summary frame: (cycle_index, charge_c_rate,
    discharge_c_rate)."""
    return pd.DataFrame(
        rows,
        columns=["cycle_index", "charge_c_rate", "discharge_c_rate"],
    )


def test_returns_full_copy_when_no_filter() -> None:
    df = _summary([(1, 0.1, 0.1), (2, 0.5, 0.5)])
    out = filter_summary(df)
    assert len(out) == len(df)
    assert out is not df


def test_rate_range_low_high_exclusive_inclusive() -> None:
    df = _summary(
        [
            (1, 0.0, 0.0),
            (2, 0.1, 0.1),
            (3, 0.5, 0.5),
            (4, 1.0, 1.0),
        ]
    )
    out = filter_summary(df, rate=(0.1, 1.0))
    assert list(out["cycle_index"]) == [3, 4]


def test_rate_delta_range_exclusive_lower_inclusive_upper() -> None:
    df = _summary(
        [
            (1, 0.4, 0.4),
            (2, 0.5, 0.5),
            (3, 0.6, 0.6),
            (4, 0.7, 0.7),
        ]
    )
    out = filter_summary(df, rate={"value": 0.5, "delta": 0.1})
    assert list(out["cycle_index"]) == [2, 3]


def test_default_rate_columns_ands_across_both() -> None:
    df = _summary(
        [
            (1, 0.05, 0.5),
            (2, 0.5, 0.5),
            (3, 0.5, 2.0),
            (4, 1.5, 1.5),
        ]
    )
    out = filter_summary(df, rate=(0.1, 1.0))
    assert list(out["cycle_index"]) == [2]


def test_rate_columns_single_string_filters_only_that_column() -> None:
    df = _summary(
        [
            (1, 0.05, 0.5),
            (2, 0.5, 0.05),
            (3, 0.5, 2.0),
            (4, 0.5, 0.5),
        ]
    )
    out = filter_summary(df, rate=(0.1, 1.0), rate_columns="discharge_c_rate")
    assert list(out["cycle_index"]) == [1, 4]


def test_rate_columns_single_tuple_equivalent_to_string() -> None:
    df = _summary(
        [
            (1, 0.05, 0.5),
            (2, 0.5, 0.05),
            (3, 0.5, 0.5),
        ]
    )
    out_str = filter_summary(df, rate=(0.1, 1.0), rate_columns="charge_c_rate")
    out_tup = filter_summary(df, rate=(0.1, 1.0), rate_columns=("charge_c_rate",))
    pd.testing.assert_frame_equal(out_str, out_tup)


def test_missing_rate_column_raises_keyerror() -> None:
    df = pd.DataFrame({"cycle_index": [1, 2], "charge_c_rate": [0.5, 0.5]})
    with pytest.raises(KeyError, match="discharge_c_rate"):
        filter_summary(df, rate=(0.1, 1.0))


def test_unknown_filter_name_raises_valueerror() -> None:
    df = _summary([(1, 0.5, 0.5)])
    with pytest.raises(ValueError, match="unknown filter name"):
        filter_summary(df, capacity=(0, 100))


def test_bad_range_lower_ge_upper_raises_valueerror() -> None:
    df = _summary([(1, 0.5, 0.5)])
    with pytest.raises(ValueError, match="lower bound"):
        filter_summary(df, rate=(1.0, 1.0))


def test_bad_delta_negative_raises_valueerror() -> None:
    df = _summary([(1, 0.5, 0.5)])
    with pytest.raises(ValueError, match="delta"):
        filter_summary(df, rate={"value": 0.5, "delta": -0.1})


def test_bad_range_type_raises_typeerror() -> None:
    df = _summary([(1, 0.5, 0.5)])
    with pytest.raises(TypeError):
        filter_summary(df, rate="not-a-range")


def test_register_range_filter_extension_point() -> None:
    """Custom filters can be registered and used through extra kwargs."""
    from cellpy.filters.summary import _RANGE_FILTERS, _rate_filter

    register_range_filter("cycle_window", _rate_filter)
    try:
        df = _summary(
            [
                (1, 0.5, 0.5),
                (2, 0.5, 0.5),
                (3, 0.5, 0.5),
                (4, 0.5, 0.5),
            ]
        )
        out = filter_summary(
            df, cycle_window=(1, 3), cycle_window_columns="cycle_index"
        )
        assert list(out["cycle_index"]) == [2, 3]
    finally:
        del _RANGE_FILTERS["cycle_window"]


def test_orphan_columns_kwarg_raises_valueerror() -> None:
    df = _summary([(1, 0.5, 0.5)])
    with pytest.raises(ValueError, match="no matching registered filter"):
        filter_summary(df, capacity_columns="something")


def test_index_preserved_after_filter() -> None:
    df = _summary([(1, 0.05, 0.05), (2, 0.5, 0.5), (3, 2.0, 2.0)])
    df.index = [10, 20, 30]
    out = filter_summary(df, rate=(0.1, 1.0))
    assert list(out.index) == [20]
