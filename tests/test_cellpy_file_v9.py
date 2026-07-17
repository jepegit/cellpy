"""Essential tests for cellpy-file format v9 (zip-of-parquet + meta.json)."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from cellpycore.metadata import io as core_meta_io
from cellpycore.metadata.models import TestMeta

from cellpy.readers.cellpy_file import CELLPY_FILE_VERSION, v9 as cellpy_file_v9
from cellpy.readers.cellpy_file.format import (
    META_JSON_NAME,
    V9_RAW_PARQUET,
    V9_STEPS_PARQUET,
    V9_SUMMARY_PARQUET,
)
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


def _require_v8_with_fids() -> Path:
    if not V8_WITH_FIDS.is_file():
        pytest.skip(f"missing characterization fixture: {V8_WITH_FIDS}")
    return V8_WITH_FIDS


@pytest.mark.essential
def test_v8_to_v9_to_read_roundtrip(tmp_path):
    """Milestone A: v8 fixture → save v9 → load; tables/meta/fids preserved."""
    source = _require_v8_with_fids()
    original = load_cellpy_file(source)
    expected = snapshot_cell_state(original)
    meta_snapshot = {
        tid: core_meta_io.to_dict(original.data.tests.get(tid))
        for tid in original.data.tests.test_ids
    }

    outfile = tmp_path / "roundtrip.cellpy"
    original.save(outfile)

    assert outfile.is_file()
    assert cellpy_file_v9.is_zip_cellpy(outfile)

    with zipfile.ZipFile(outfile) as zf:
        names = set(zf.namelist())
        assert META_JSON_NAME in names
        assert V9_RAW_PARQUET in names
        assert V9_STEPS_PARQUET in names
        assert V9_SUMMARY_PARQUET in names
        meta_doc = json.loads(zf.read(META_JSON_NAME).decode("utf-8"))
    assert meta_doc["cellpy_file_version"] == CELLPY_FILE_VERSION
    assert "tests" in meta_doc
    assert "raw_units" in meta_doc
    assert "limits" in meta_doc

    reloaded = load_cellpy_file(outfile)

    assert_data_frames_equal(reloaded.data.raw, expected["raw"])
    assert_data_frames_equal(reloaded.data.steps, expected["steps"])
    assert_data_frames_equal(reloaded.data.summary, expected["summary"])
    # cellpy_file_version advances 8 → 9 on convert; compare the rest of meta.
    original.data.meta_common.cellpy_file_version = CELLPY_FILE_VERSION
    assert_meta_equal(original, reloaded)
    assert_raw_limits_and_units_equal(original, reloaded)
    assert_fid_lists_equal(original, reloaded)
    assert reloaded.data.meta_common.cellpy_file_version == CELLPY_FILE_VERSION

    result_meta = {
        tid: core_meta_io.to_dict(reloaded.data.tests.get(tid))
        for tid in reloaded.data.tests.test_ids
    }
    assert result_meta == meta_snapshot


@pytest.mark.essential
def test_v9_persists_extra_test_meta(tmp_path):
    """v9 round-trip keeps non-active TestMeta records (unlike v8)."""
    source = _require_v8_with_fids()
    cell = load_cellpy_file(source)
    cell.data.set_test_meta(TestMeta(test_id=1, cycle_mode="full"))

    outfile = tmp_path / "extras.cellpy"
    cell.save(outfile)
    reloaded = load_cellpy_file(outfile)

    assert sorted(reloaded.data.tests.test_ids) == [0, 1]
    assert reloaded.data.tests.get(1).cycle_mode == "full"


@pytest.mark.essential
def test_h5_suffix_still_writes_hdf5(tmp_path):
    """Path ending in .h5 still uses the v8 HDF5 writer."""
    import pandas as pd

    source = _require_v8_with_fids()
    cell = load_cellpy_file(source)
    outfile = tmp_path / "legacy.h5"
    cell.save(outfile)

    assert not cellpy_file_v9.is_zip_cellpy(outfile)
    with pd.HDFStore(outfile) as store:
        assert "/CellpyData/raw" in store.keys()
