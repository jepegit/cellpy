"""Tests for the native-schema opt-in (issue #511, V2-11).

The flag is off by default (the whole existing suite is the legacy-path
oracle); these tests exercise the opt-in pipeline: from_raw -> make_step_table
-> make_summary -> save/load (v9), plus the guards.
"""

from __future__ import annotations

import logging

import pandas as pd
import pytest
from cellpycore.cell_core import OldCellpyCellCore
from cellpycore.config import default_schema

from cellpy import cellreader
from cellpy.readers.cellpy_file import translate as cellpy_file_translate
from cellpy.readers.native_core import NativeCellpyCellCore

log = logging.getLogger(__name__)

SCHEMA = default_schema()


@pytest.fixture
def native_cell(parameters):
    c = cellreader.CellpyCell(native_schema=True)
    c.from_raw(parameters.res_file_path)
    return c


def test_flag_defaults_to_legacy_bridge():
    c = cellreader.CellpyCell()
    assert c.native_schema is False
    assert isinstance(c.core, OldCellpyCellCore)


def test_flag_selects_native_core():
    c = cellreader.CellpyCell(native_schema=True)
    assert c.native_schema is True
    assert isinstance(c.core, NativeCellpyCellCore)
    assert not isinstance(c.core, OldCellpyCellCore)


@pytest.mark.essential
def test_native_from_raw_emits_native_raw_columns(native_cell):
    raw = native_cell.data.raw
    for col in (
        SCHEMA.raw.datapoint_num,
        SCHEMA.raw.cycle_num,
        SCHEMA.raw.step_num,
        SCHEMA.raw.potential,
        SCHEMA.raw.test_id,
    ):
        assert col in raw.columns
    # the legacy names are gone (renamed, not duplicated)
    for legacy in ("data_point", "cycle_index", "step_index", "voltage"):
        assert legacy not in raw.columns


@pytest.mark.essential
def test_native_step_and_summary_pipeline(native_cell):
    native_cell.make_step_table()
    steps = native_cell.data.steps
    assert SCHEMA.step.cycle_num in steps.columns
    assert SCHEMA.step.step_num in steps.columns
    assert "cycle" not in steps.columns  # legacy step name absent

    native_cell.make_summary(find_ir=False)
    summary = native_cell.data.summary
    assert SCHEMA.cycle.cycle_num in summary.columns
    assert SCHEMA.cycle.charge_capacity in summary.columns
    assert "cycle_index" not in summary.columns  # legacy summary name absent


def test_native_summary_value_parity_with_legacy_path(parameters, native_cell):
    """The Phase-3 oracle in miniature: native values == legacy values through
    the mapping on shared summary columns."""
    native_cell.make_summary(find_ir=False)
    native_as_legacy = cellpy_file_translate.summary_to_legacy(
        native_cell.data.summary.copy()
    )

    legacy = cellreader.CellpyCell()
    legacy.from_raw(parameters.res_file_path)
    legacy.make_summary(find_ir=False)
    legacy_summary = legacy.data.summary

    key = "cycle_index"
    shared = [
        c
        for c in native_as_legacy.columns
        if c in legacy_summary.columns
        and c != key
        and pd.api.types.is_numeric_dtype(legacy_summary[c])
        # IR semantics differ deliberately between the paths (F4); the
        # native path uses the corrected extractor.
        and not c.startswith("ir_")
    ]
    assert len(shared) > 5

    left = native_as_legacy.sort_values(key).reset_index(drop=True)
    right = legacy_summary.sort_values(key).reset_index(drop=True)
    assert len(left) == len(right)
    for col in shared:
        pd.testing.assert_series_equal(
            left[col].astype(float),
            right[col].astype(float),
            check_names=False,
            rtol=1e-6,
            atol=1e-12,
            obj=f"summary column {col!r}",
        )


@pytest.mark.essential
def test_native_v9_roundtrip(native_cell, tmp_path):
    native_cell.make_step_table()
    native_cell.make_summary(find_ir=False)
    outfile = tmp_path / "native.cellpy"
    native_cell.save(outfile)

    reloaded = cellreader.CellpyCell(native_schema=True)
    reloaded.load(outfile)

    for attr in ("raw", "steps", "summary"):
        original = getattr(native_cell.data, attr)
        loaded = getattr(reloaded.data, attr)
        assert set(loaded.columns) == set(original.columns), attr
        pd.testing.assert_frame_equal(
            loaded[original.columns].reset_index(drop=True),
            original.reset_index(drop=True),
            check_dtype=False,
            check_exact=False,
            rtol=1e-9,
            obj=f"frame {attr!r}",
        )


def test_native_hdf5_save_raises(native_cell, tmp_path):
    native_cell.make_step_table()
    native_cell.make_summary(find_ir=False)
    with pytest.raises(ValueError, match="native-schema"):
        native_cell.save(tmp_path / "nope.h5")


def test_native_merge_raises(native_cell, parameters):
    other = cellreader.CellpyCell()
    other.from_raw(parameters.res_file_path2)
    with pytest.raises(NotImplementedError, match="native-schema"):
        native_cell.merge(other)
