"""Cellpy-owned metadata archive helpers (issue #510 Milestone B / V2-14)."""

from __future__ import annotations

from pathlib import Path

import pytest
from cellpycore.metadata import io as core_meta_io
from cellpycore.metadata.models import TestMeta, TestMetaCollection

from cellpy.readers.cellpy_file import meta_archive
from tests.cellpy_file_support import load_cellpy_file

HDF5_DIR = Path(__file__).resolve().parents[1] / "testdata" / "hdf5"
V8_WITH_FIDS = HDF5_DIR / "20160805_test001_45_cc_v8_with_fids.h5"


def _require_v8() -> Path:
    if not V8_WITH_FIDS.is_file():
        pytest.skip(f"missing fixture: {V8_WITH_FIDS}")
    return V8_WITH_FIDS


@pytest.mark.essential
def test_save_load_meta_archive_roundtrip_data(tmp_path):
    cell = load_cellpy_file(_require_v8())
    cell.data.set_test_meta(TestMeta(test_id=1, cycle_mode="full", cell_name="extra"))
    before = {
        tid: core_meta_io.to_dict(cell.data.tests.get(tid))
        for tid in cell.data.tests.test_ids
    }

    path = tmp_path / "campaign.meta.json"
    meta_archive.save_meta_archive(cell.data, path)
    doc = meta_archive.load_meta_archive(path)
    collection = meta_archive.collection_from_meta_document(doc)

    assert sorted(collection.test_ids) == [0, 1]
    assert collection.get(1).cycle_mode == "full"
    assert {
        tid: core_meta_io.to_dict(collection.get(tid)) for tid in collection.test_ids
    } == before


@pytest.mark.essential
def test_save_load_meta_archive_from_collection(tmp_path):
    collection = TestMetaCollection()
    collection.add(TestMeta(test_id=0, cycle_mode="anode", cell_name="a"))
    collection.add(TestMeta(test_id=1, cycle_mode="cathode", cell_name="b"))

    path = tmp_path / "tests.meta.json"
    meta_archive.save_meta_archive(collection, path, active_test_id=0)
    loaded = meta_archive.collection_from_meta_document(
        meta_archive.load_meta_archive(path)
    )
    assert loaded.test_ids == [0, 1]
    assert loaded.get(1).cycle_mode == "cathode"


@pytest.mark.essential
def test_core_archive_stubs_still_raise():
    """Boundary: persistence stays in cellpy; core stubs remain stubs."""
    with pytest.raises(NotImplementedError):
        core_meta_io.save_archive(TestMeta(test_id=0), "unused.h5")
    with pytest.raises(NotImplementedError):
        core_meta_io.load_archive("unused.h5")
