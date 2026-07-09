"""Helpers for cellpy-file (HDF5) characterization tests."""

from __future__ import annotations

import math
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from cellpy import cellreader
from cellpy.readers.cellreader import CellpyCell
from tests.golden_support import DATE_TIME_GOLDEN_ABS_NS, date_time_as_epoch_ns

DATE_TIME_COLUMN = "date_time"


def load_cellpy_file(path: str | Path, **kwargs) -> CellpyCell:
    """Load a cellpy-file and return the populated ``CellpyCell`` instance."""
    cell = cellreader.CellpyCell()
    cell.load(path, **kwargs)
    return cell


def _normalize_meta_value(value: Any) -> Any:
    """Flatten single-element list wrappers from HDF meta tables."""
    import numpy as np

    if isinstance(value, np.ndarray):
        if value.size == 1:
            return _normalize_meta_value(
                value.item() if value.ndim == 0 else value.flat[0]
            )
        return value
    while isinstance(value, list) and len(value) == 1:
        value = value[0]
    return value


def _values_equal(left: Any, right: Any) -> bool:
    left = _normalize_meta_value(left)
    right = _normalize_meta_value(right)
    if left is right:
        return True
    if isinstance(left, float) and isinstance(right, float):
        if math.isnan(left) and math.isnan(right):
            return True
    try:
        if pd.isna(left) and pd.isna(right):
            return True
    except (TypeError, ValueError):
        pass
    return left == right


def assert_dataclass_fields_equal(actual: Any, expected: Any) -> None:
    """Compare two dataclass instances field-by-field (NaN-safe)."""
    if not is_dataclass(actual) or not is_dataclass(expected):
        raise TypeError("assert_dataclass_fields_equal expects dataclass instances")
    actual_dict = asdict(actual)
    expected_dict = asdict(expected)
    assert actual_dict.keys() == expected_dict.keys()
    for key in actual_dict:
        assert _values_equal(actual_dict[key], expected_dict[key]), (
            f"meta field {key!r}: {actual_dict[key]!r} != {expected_dict[key]!r}"
        )


def assert_data_frames_equal(actual: pd.DataFrame, expected: pd.DataFrame) -> None:
    """Compare DataFrames with sorted columns; ``date_time`` uses ns approx tolerance."""
    actual = actual[sorted(actual.columns)].copy()
    expected = expected[sorted(expected.columns)].copy()
    assert list(actual.columns) == list(expected.columns)

    other_cols = [c for c in actual.columns if c != DATE_TIME_COLUMN]
    if other_cols:
        assert_frame_equal(actual[other_cols], expected[other_cols])

    if DATE_TIME_COLUMN in actual.columns:
        act_ns = date_time_as_epoch_ns(actual[DATE_TIME_COLUMN]).tolist()
        exp_ns = date_time_as_epoch_ns(expected[DATE_TIME_COLUMN]).tolist()
        assert act_ns == pytest.approx(exp_ns, abs=DATE_TIME_GOLDEN_ABS_NS)


def assert_meta_equal(cell_a: CellpyCell, cell_b: CellpyCell) -> None:
    """Compare ``meta_common`` and ``meta_test_dependent`` on two loaded cells."""
    assert_dataclass_fields_equal(cell_a.data.meta_common, cell_b.data.meta_common)
    assert_dataclass_fields_equal(
        cell_a.data.meta_test_dependent, cell_b.data.meta_test_dependent
    )


def assert_raw_limits_and_units_equal(cell_a: CellpyCell, cell_b: CellpyCell) -> None:
    """Compare ``raw_limits`` and ``raw_units`` dicts."""
    assert cell_a.data.raw_limits == cell_b.data.raw_limits
    assert cell_a.data.raw_units == cell_b.data.raw_units


def fid_snapshot(cell: CellpyCell) -> list[tuple[Any, ...]]:
    """Stable tuple snapshot of raw-data file IDs for round-trip comparison."""
    return [
        (fid.name, fid.full_name, fid.size, fid.last_data_point)
        for fid in cell.data.raw_data_files
    ]


def assert_fid_lists_equal(cell_a: CellpyCell, cell_b: CellpyCell) -> None:
    """Compare fid lists; require at least one fid entry."""
    snap_a = fid_snapshot(cell_a)
    snap_b = fid_snapshot(cell_b)
    assert snap_a, "expected non-empty raw_data_files on reference cell"
    assert snap_b, "expected non-empty raw_data_files after round-trip"
    assert snap_a == snap_b


def snapshot_cell_state(cell: CellpyCell) -> dict[str, Any]:
    """Capture tables and metadata for round-trip comparison."""
    return {
        "raw": cell.data.raw.copy(),
        "steps": cell.data.steps.copy(),
        "summary": cell.data.summary.copy(),
        "fids": fid_snapshot(cell),
        "limits": dict(cell.data.raw_limits),
        "units": dict(cell.data.raw_units),
        "meta_common": asdict(cell.data.meta_common),
        "meta_test_dependent": asdict(cell.data.meta_test_dependent),
    }
