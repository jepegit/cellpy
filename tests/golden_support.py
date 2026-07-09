"""Helpers shared by golden regression tests and ``dev/regenerate_goldens.py``."""

from __future__ import annotations

import pandas as pd

# Summary ``date_time`` is stored as datetime64[ns] (or its int64 view). Sub-nanosecond
# rounding differs across platforms after parquet round-trip, so goldens floor to µs.
_DATETIME_GOLDEN_COLUMNS = ("date_time",)


def stabilize_summary_for_golden(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``df`` with platform-stable datetime columns for golden I/O."""
    out = df.copy()
    for col in _DATETIME_GOLDEN_COLUMNS:
        if col not in out.columns:
            continue
        series = out[col]
        if pd.api.types.is_datetime64_any_dtype(series):
            out[col] = pd.to_datetime(series).astype("datetime64[us]")
        elif pd.api.types.is_integer_dtype(series):
            # ns since epoch — floor to whole microseconds.
            out[col] = (series // 1_000) * 1_000
    return out
