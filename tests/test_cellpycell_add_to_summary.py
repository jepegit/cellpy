"""Tests for CellpyCell.add_to_summary."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


def _summary_cycles(cell) -> pd.Series:
    """Cycle-index values for each summary row, regardless of whether
    cycle_index is stored as a column or as the summary's index."""
    summary = cell.data.summary
    hdrs_cycle = cell.headers_summary.cycle_index
    if hdrs_cycle in summary.columns:
        return summary[hdrs_cycle]
    return pd.Series(summary.index, index=summary.index, name=hdrs_cycle)


def test_add_to_summary_last_default(cell):
    """Default method='last' maps a per-cycle constant onto summary."""
    raw = cell.data.raw
    hdr_cycle_raw = cell.headers_normal.cycle_index_txt

    raw["fake_temp"] = raw[hdr_cycle_raw] * 10.0

    cell.add_to_summary("fake_temp")

    summary = cell.data.summary
    assert "fake_temp" in summary.columns
    expected = _summary_cycles(cell) * 10.0
    np.testing.assert_allclose(
        summary["fake_temp"].to_numpy(dtype=float),
        expected.to_numpy(dtype=float),
    )


def test_add_to_summary_first_vs_last(cell):
    """For cycles with more than one raw row, first < last for a monotonic
    counter."""
    raw = cell.data.raw
    hdr_cycle_raw = cell.headers_normal.cycle_index_txt

    raw["counter"] = np.arange(len(raw), dtype=float)

    cell.add_to_summary("counter", method="first", new_name="counter_first")
    cell.add_to_summary("counter", method="last", new_name="counter_last")

    summary = cell.data.summary
    rows_per_cycle = raw.groupby(hdr_cycle_raw).size()
    multi_row_cycles = set(rows_per_cycle.index[rows_per_cycle > 1])
    assert multi_row_cycles, (
        "test fixture has no cycle with >1 raw rows; cannot exercise reducer"
    )

    cycles = _summary_cycles(cell)
    multi = summary[cycles.isin(multi_row_cycles).to_numpy()]
    assert (multi["counter_first"] < multi["counter_last"]).all()


def test_add_to_summary_mean_matches_pandas(cell):
    """method='mean' matches a manual groupby+mean+map."""
    raw = cell.data.raw
    hdr_cycle_raw = cell.headers_normal.cycle_index_txt

    raw["fake_temp"] = raw[hdr_cycle_raw].astype(float) + np.arange(
        len(raw), dtype=float
    ) * 0.01

    cell.add_to_summary("fake_temp", method="mean")

    summary = cell.data.summary
    per_cycle = raw.groupby(hdr_cycle_raw)["fake_temp"].mean()
    expected = _summary_cycles(cell).map(per_cycle).to_numpy(dtype=float)
    np.testing.assert_allclose(
        summary["fake_temp"].to_numpy(dtype=float), expected
    )


def test_add_to_summary_new_name(cell):
    """new_name renames the resulting summary column."""
    raw = cell.data.raw
    hdr_cycle_raw = cell.headers_normal.cycle_index_txt
    raw["fake_temp"] = raw[hdr_cycle_raw] * 1.0

    cell.add_to_summary("fake_temp", new_name="cell_temperature")

    summary = cell.data.summary
    assert "cell_temperature" in summary.columns
    assert "fake_temp" not in summary.columns


def test_add_to_summary_chainable(cell):
    """The method returns the same CellpyCell instance."""
    raw = cell.data.raw
    hdr_cycle_raw = cell.headers_normal.cycle_index_txt
    raw["fake_temp"] = raw[hdr_cycle_raw] * 1.0

    result = cell.add_to_summary("fake_temp")
    assert result is cell


def test_add_to_summary_unknown_column_raises(cell):
    with pytest.raises(ValueError, match="not found in raw"):
        cell.add_to_summary("definitely_not_a_real_column")


def test_add_to_summary_unknown_method_raises(cell):
    raw = cell.data.raw
    hdr_cycle_raw = cell.headers_normal.cycle_index_txt
    raw["fake_temp"] = raw[hdr_cycle_raw] * 1.0

    with pytest.raises(ValueError, match="method must be one of"):
        cell.add_to_summary("fake_temp", method="median")
