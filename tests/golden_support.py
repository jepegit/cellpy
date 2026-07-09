"""Helpers shared by golden regression tests and ``dev/regenerate_goldens.py``."""

from __future__ import annotations

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

# ``date_time`` can differ by 1 ns across platforms after parquet round-trip.
# Compare as epoch-ns with a 1 µs absolute tolerance.
DATE_TIME_GOLDEN_ABS_NS = 1_000
DATE_TIME_GOLDEN_COLUMN = "date_time"


def sort_summary_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with lexicographically sorted columns (golden convention)."""
    return df[sorted(df.columns)].copy()


def date_time_as_epoch_ns(series: pd.Series) -> pd.Series:
    """Normalize ``date_time`` to int64 nanoseconds since epoch for comparison."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series).astype("datetime64[ns]").astype("int64")
    return series.astype("int64")


def assert_summary_matches_golden(actual: pd.DataFrame, expected: pd.DataFrame) -> None:
    """Compare summary frames: exact on all columns except ``date_time`` (approx ns)."""
    actual = sort_summary_columns(actual)
    expected = sort_summary_columns(expected)
    assert list(actual.columns) == list(expected.columns)

    other_cols = [c for c in actual.columns if c != DATE_TIME_GOLDEN_COLUMN]
    assert_frame_equal(actual[other_cols], expected[other_cols])

    if DATE_TIME_GOLDEN_COLUMN in actual.columns:
        act_ns = date_time_as_epoch_ns(actual[DATE_TIME_GOLDEN_COLUMN]).tolist()
        exp_ns = date_time_as_epoch_ns(expected[DATE_TIME_GOLDEN_COLUMN]).tolist()
        assert act_ns == pytest.approx(exp_ns, abs=DATE_TIME_GOLDEN_ABS_NS)
