"""Essential tests for lightweight ``read_meta`` (issue #799)."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

import cellpy
from cellpy.readers.cellpy_file import CELLPY_FILE_VERSION, read_meta, v9 as cellpy_file_v9
from cellpy.readers.cellpy_file.format import META_JSON_NAME
from tests.cellpy_file_support import load_cellpy_file

HDF5_DIR = Path(__file__).resolve().parents[1] / "testdata" / "hdf5"
V8_WITH_FIDS = HDF5_DIR / "20160805_test001_45_cc_v8_with_fids.h5"


def _require_v8_with_fids() -> Path:
    if not V8_WITH_FIDS.is_file():
        pytest.skip(f"missing characterization fixture: {V8_WITH_FIDS}")
    return V8_WITH_FIDS


@pytest.mark.essential
def test_read_meta_v9_matches_zip_member(tmp_path):
    source = _require_v8_with_fids()
    cell = load_cellpy_file(source)
    outfile = tmp_path / "peek.cellpy"
    cell.save(outfile)

    with zipfile.ZipFile(outfile) as zf:
        expected = json.loads(zf.read(META_JSON_NAME).decode("utf-8"))

    meta = read_meta(outfile)
    assert meta == expected
    assert meta["cellpy_file_version"] == CELLPY_FILE_VERSION
    assert "mass" in meta["cell"]
    assert cellpy.read_meta(outfile) == meta


@pytest.mark.essential
def test_read_meta_v9_does_not_touch_parquet(tmp_path, monkeypatch):
    source = _require_v8_with_fids()
    cell = load_cellpy_file(source)
    outfile = tmp_path / "no_parquet.cellpy"
    cell.save(outfile)

    def _boom(*_args, **_kwargs):
        raise AssertionError("parquet member must not be read by read_meta")

    monkeypatch.setattr(cellpy_file_v9, "_read_parquet_member", _boom)
    meta = read_meta(outfile)
    assert meta["cellpy_file_version"] == CELLPY_FILE_VERSION


@pytest.mark.essential
def test_read_meta_hdf5_common_fields():
    source = _require_v8_with_fids()
    meta = read_meta(source)
    assert meta["cellpy_file_version"] == 8
    assert "mass" in meta["cell"]
    assert "active_electrode_area" in meta["cell"]


@pytest.mark.essential
def test_read_meta_missing_file(tmp_path):
    missing = tmp_path / "nope.cellpy"
    with pytest.raises(IOError, match="does not exist"):
        read_meta(missing)
