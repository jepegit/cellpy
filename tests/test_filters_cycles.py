"""Tests for cellpy.filters.cycles.filter_cycles."""

from __future__ import annotations

import logging

import pandas as pd
import pytest

from cellpy import log
from cellpy.filters import filter_cycles
from cellpy.parameters.internal_settings import get_headers_normal

log.setup_logging(default_level=logging.DEBUG, testing=True)


def _make_df(cycles: list[int], column: str | None = None) -> pd.DataFrame:
    if column is None:
        column = get_headers_normal().cycle_index_txt
    return pd.DataFrame(
        {
            column: cycles,
            "voltage": [3.0 + 0.01 * i for i in range(len(cycles))],
        }
    )


def test_returns_full_copy_when_no_filter() -> None:
    df = _make_df([1, 2, 3, 3, 4])
    out = filter_cycles(df)
    assert len(out) == len(df)
    assert out is not df  # copy, not the same object


def test_scalar_cycle() -> None:
    df = _make_df([1, 2, 2, 3, 4])
    out = filter_cycles(df, cycles=2)
    assert set(out["cycle_index"]) == {2}
    assert len(out) == 2


def test_iterable_cycles() -> None:
    df = _make_df([1, 2, 3, 4, 5])
    out = filter_cycles(df, cycles=[2, 4])
    assert list(out["cycle_index"]) == [2, 4]


def test_last_cycle_truncates() -> None:
    df = _make_df([1, 2, 3, 4, 5])
    out = filter_cycles(df, last_cycle=3)
    assert list(out["cycle_index"]) == [1, 2, 3]


def test_cycles_and_last_cycle_intersect() -> None:
    df = _make_df([1, 2, 3, 4, 5, 50])
    out = filter_cycles(df, cycles=[2, 5, 50], last_cycle=10)
    assert list(out["cycle_index"]) == [2, 5]


def test_default_column_resolves_from_headers_normal() -> None:
    df = _make_df([1, 2, 3])
    assert get_headers_normal().cycle_index_txt in df.columns
    out = filter_cycles(df, cycles=2)
    assert list(out["cycle_index"]) == [2]


def test_custom_column() -> None:
    df = pd.DataFrame({"my_cycle": [1, 2, 3], "x": [10, 20, 30]})
    out = filter_cycles(df, cycles=[1, 3], column="my_cycle")
    assert list(out["my_cycle"]) == [1, 3]


def test_missing_column_raises() -> None:
    df = pd.DataFrame({"not_cycle": [1, 2, 3]})
    with pytest.raises(KeyError, match="cycle_index"):
        filter_cycles(df, cycles=1)


def test_invalid_cycles_type_raises() -> None:
    df = _make_df([1, 2, 3])
    with pytest.raises(TypeError):
        filter_cycles(df, cycles=1.5)  # type: ignore[arg-type]


def test_empty_match_returns_empty_frame() -> None:
    df = _make_df([1, 2, 3])
    out = filter_cycles(df, cycles=99)
    assert len(out) == 0
    assert list(out.columns) == list(df.columns)
