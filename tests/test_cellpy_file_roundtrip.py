"""Characterization tests for cellpy-file (HDF5) load/save behavior (Stage 0.2).

Locks current behavior before the cellpy-file module extraction refactor.
See ``architecture-plan/cellpy-file-loading-refactor-plan.md`` Step 0.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd
import pytest

from cellpy import cellreader, prms
from cellpy.exceptions import WrongFileVersion
from cellpy.internals.connections import OtherPath
from cellpy.parameters.internal_settings import get_headers_normal, get_headers_summary
from tests.cellpy_file_support import (
    assert_data_frames_equal,
    assert_fid_lists_equal,
    assert_meta_equal,
    assert_raw_limits_and_units_equal,
    load_cellpy_file,
    snapshot_cell_state,
)

HDF5_DIR = Path(__file__).resolve().parents[1] / "testdata" / "hdf5"

V8_WITH_FIDS = HDF5_DIR / "20160805_test001_45_cc_v8_with_fids.h5"
RAW_RES = (
    Path(__file__).resolve().parents[1]
    / "testdata"
    / "data"
    / "20160805_test001_45_cc_01.res"
)

LEGACY_SUCCESS = [
    ("v6", "20160805_test001_45_cc_v6.h5", 6),
    ("v7", "20160805_test001_45_cc_v7.h5", 7),
]

LEGACY_TYPE_ERROR = [
    ("v4", "20160805_test001_45_cc_v4.h5"),
    ("v5", "20160805_test001_45_cc_v5.h5"),
]


def _require_v8_with_fids() -> Path:
    if not V8_WITH_FIDS.is_file():
        pytest.skip(f"missing characterization fixture: {V8_WITH_FIDS}")
    return V8_WITH_FIDS


@pytest.mark.essential
def test_v8_roundtrip_preserves_tables_meta_limits_fids(tmp_path):
    """Load v8 oracle → save → reload; full equality on frames, meta, limits, fids."""
    source = _require_v8_with_fids()
    original = load_cellpy_file(source)
    expected = snapshot_cell_state(original)

    outfile = tmp_path / source.name
    original.save(outfile)

    reloaded = load_cellpy_file(outfile)

    assert_data_frames_equal(reloaded.data.raw, expected["raw"])
    assert_data_frames_equal(reloaded.data.steps, expected["steps"])
    assert_data_frames_equal(reloaded.data.summary, expected["summary"])
    assert_meta_equal(original, reloaded)
    assert_raw_limits_and_units_equal(original, reloaded)
    assert_fid_lists_equal(original, reloaded)

    with pd.HDFStore(outfile) as store:
        keys = sorted(store.keys())
    assert "/CellpyData/raw" in keys
    assert "/CellpyData/steps" in keys
    assert "/CellpyData/summary" in keys
    assert "/CellpyData/fid" in keys
    assert "/CellpyData/info" in keys


@pytest.mark.essential
def test_v8_limits_stored_unprefixed_in_info_table(tmp_path):
    """Limits-prefix trap: raw limits must be unprefixed keys in /CellpyData/info."""
    source = _require_v8_with_fids()
    cell = load_cellpy_file(source)
    outfile = tmp_path / "limits_check.h5"
    cell.save(outfile)

    assert prms._cellpyfile_raw_limit_pre_id == ""

    with pd.HDFStore(outfile) as store:
        info = store.select("/CellpyData/info")

    for limit_key in cell.data.raw_limits:
        assert limit_key in info.columns, (
            f"limit {limit_key!r} must be stored unprefixed in info table"
        )
        prefixed = f"{prms._cellpyfile_raw_limit_pre_id}{limit_key}"
        if prefixed != limit_key:
            assert prefixed not in info.columns

    unit_cols = [c for c in info.columns if c.startswith("raw_unit_")]
    assert unit_cols, "expected raw_unit_* columns in info table"


@pytest.mark.essential
def test_v8_load_selector_max_cycle_truncates_consistently():
    """``selector={'max_cycle': N}`` truncates summary/raw/steps and sets limits."""
    source = _require_v8_with_fids()
    max_cycle = 3

    full = load_cellpy_file(source)
    selected = load_cellpy_file(source, selector={"max_cycle": max_cycle})

    assert selected.limit_loaded_cycles == max_cycle
    assert selected.limit_data_points == 3119
    assert len(selected.data.summary) == max_cycle
    assert selected.data.summary.index.max() == max_cycle

    hn = get_headers_normal()
    cycle_col = hn.cycle_index_txt
    assert selected.data.raw[cycle_col].max() <= max_cycle
    assert len(selected.data.raw) < len(full.data.raw)
    assert len(selected.data.steps) < len(full.data.steps)


@pytest.mark.parametrize("label,filename", LEGACY_TYPE_ERROR)
def test_legacy_v4_v5_currently_raise_typeerror_on_meta_extract(label, filename):
    """Pin current v4/v5 load failure (missing ``upgrade_from_to`` on meta extract)."""
    path = HDF5_DIR / filename
    if not path.is_file():
        pytest.skip(f"missing legacy fixture: {path}")

    cell = cellreader.CellpyCell()
    with pytest.raises(TypeError):
        cell.load(path, accept_old=True)


@pytest.mark.parametrize("label,filename,version", LEGACY_SUCCESS)
def test_legacy_v6_v7_load_shapes_and_columns(label, filename, version):
    """Legacy v6/v7: load succeeds with expected shapes and renamed columns."""
    path = HDF5_DIR / filename
    if not path.is_file():
        pytest.skip(f"missing legacy fixture: {path}")

    cell = load_cellpy_file(path, accept_old=True)
    hn = get_headers_normal()
    hs = get_headers_summary()

    assert cell.data.raw.shape[0] > 0
    assert cell.data.summary.shape[0] > 0
    assert hn.data_point_txt in cell.data.raw.columns
    assert hn.cycle_index_txt in cell.data.raw.columns
    assert cell.data.summary.index.name == hs.cycle_index
    assert hs.data_point in cell.data.summary.columns
    assert hs.discharge_capacity in cell.data.summary.columns
    assert cell.data.meta_common.cellpy_file_version == version


def test_legacy_v0_raises_wrong_file_version():
    """Too-old v0 layout cannot read file version."""
    path = HDF5_DIR / "20160805_test001_45_cc_v0.h5"
    if not path.is_file():
        pytest.skip(f"missing legacy fixture: {path}")

    cell = cellreader.CellpyCell()
    with pytest.raises(WrongFileVersion, match="VERY old"):
        cell.load(path, accept_old=True)


def test_missing_required_store_key_raises_current_exception(tmp_path):
    """Missing summary key → bare Exception with OH MY GOD message (current contract)."""
    source = HDF5_DIR / "20160805_test001_45_cc_v8.h5"
    if not source.is_file():
        pytest.skip(f"missing fixture: {source}")

    corrupt = tmp_path / "corrupt.h5"
    shutil.copy(source, corrupt)
    with pd.HDFStore(corrupt, "a") as store:
        store.remove("/CellpyData/summary")

    cell = cellreader.CellpyCell()
    with pytest.raises(Exception, match="OH MY GOD") as exc_info:
        cell.load(corrupt)

    assert "/CellpyData/summary" in str(exc_info.value)


def test_check_file_ids_matches_res_provenance():
    """``check_file_ids`` returns True when cellpy-file fids match the source .res."""
    if not V8_WITH_FIDS.is_file() or not RAW_RES.is_file():
        pytest.skip("v8_with_fids or canonical .res fixture missing")

    cell = cellreader.CellpyCell()
    assert cell.check_file_ids(
        rawfiles=OtherPath(RAW_RES),
        cellpyfile=OtherPath(V8_WITH_FIDS),
    )
