"""Tests for the per-test metadata API (``Data.tests``, issue #506).

Covers: the legacy->core translation helpers, the derived-collection semantics
(legacy boxes stay authoritative for the active test), v1-file backward compat
(single record, ``test_id=0``), the mixed-cycle-mode compute guard, and the v8
save/load round-trip of the collection.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from cellpycore.metadata import io as core_meta_io
from cellpycore.metadata.models import TestMeta

from cellpy import cellreader
from cellpy.exceptions import MixedCycleModesError
from cellpy.parameters.internal_settings import (
    CellpyMetaCommon,
    CellpyMetaIndividualTest,
    get_headers_normal,
)
from cellpy.readers import test_meta
from cellpy.readers.data_structures import Data
from tests.cellpy_file_support import load_cellpy_file

HDF5_DIR = Path(__file__).resolve().parents[1] / "testdata" / "hdf5"
V8_WITH_FIDS = HDF5_DIR / "20160805_test001_45_cc_v8_with_fids.h5"

LEGACY_FILES = [
    ("v4", "20160805_test001_45_cc_v4.h5"),
    ("v5", "20160805_test001_45_cc_v5.h5"),
    ("v6", "20160805_test001_45_cc_v6.h5"),
    ("v7", "20160805_test001_45_cc_v7.h5"),
    ("v8", "20160805_test001_45_cc_v8_with_fids.h5"),
]


def _require(path: Path) -> Path:
    if not path.is_file():
        pytest.skip(f"missing fixture: {path}")
    return path


# ---------------------------------------------------------------- helpers ----


def test_unwrap_variants():
    assert test_meta._unwrap(["anode"]) == "anode"
    assert test_meta._unwrap(("anode",)) == "anode"
    assert test_meta._unwrap("anode") == "anode"
    assert test_meta._unwrap(np.float64(1.5)) == 1.5
    assert test_meta._unwrap([np.int64(3)]) == 3
    assert test_meta._unwrap(None) is None
    # multi-element sequences are left alone (nothing sensible to unwrap)
    assert test_meta._unwrap([1, 2]) == [1, 2]


def test_schedule_file_name_survives_mapping():
    individual = CellpyMetaIndividualTest()
    individual.schedule_file_name = "myschedule.sdu"
    _, mapped = test_meta.legacy_boxes_to_mappings(CellpyMetaCommon(), individual)
    assert mapped["schedule_file_name"] == "myschedule.sdu"


def test_build_apply_build_fixed_point():
    """build -> apply -> build is a fixed point on the mapped fields."""
    data = Data()
    data.meta_common.mass = 1.234
    data.meta_common.cell_name = "cell_x"
    data.meta_test_dependent.cycle_mode = "cathode"
    data.meta_test_dependent.channel_index = 7

    first = test_meta.build_active_test_meta(data)

    other = Data()
    test_meta.apply_test_meta_to_legacy(
        first, other.meta_common, other.meta_test_dependent
    )
    second = test_meta.build_active_test_meta(other)

    assert core_meta_io.to_dict(second) == core_meta_io.to_dict(first)
    assert other.meta_common.mass == 1.234
    assert other.meta_test_dependent.cycle_mode == "cathode"


# ------------------------------------------------------- collection on Data ----


def test_fresh_data_has_single_test_zero():
    data = Data()
    assert data.active_test_id == 0
    assert data.tests.test_ids == [0]
    record = data.tests.get(0)
    assert record.cycle_mode == data.meta_test_dependent.cycle_mode
    assert record.cell is not None
    assert record.cell.mass == data.meta_common.mass


def test_set_cycle_mode_active_writes_through():
    """Active-test writes land on the attribute the core engine reads."""
    data = Data()
    data.set_cycle_mode("cathode")
    assert data.meta_test_dependent.cycle_mode == "cathode"
    assert data.get_cycle_mode() == "cathode"
    assert data.tests.get(0).cycle_mode == "cathode"


def test_set_test_meta_active_writes_through():
    data = Data()
    record = data.tests.get(0)
    record.cycle_mode = "cathode"
    record.cell.mass = 9.9
    data.set_test_meta(record)
    assert data.meta_test_dependent.cycle_mode == "cathode"
    assert data.meta_common.mass == 9.9


def test_extra_test_record_is_isolated():
    data = Data()
    data.set_test_meta(TestMeta(test_id=1, cycle_mode="full"))
    assert data.tests.test_ids == [0, 1]
    assert data.get_cycle_mode(1) == "full"
    # active untouched
    assert data.get_cycle_mode() == data.meta_test_dependent.cycle_mode
    data.set_cycle_mode("cathode", test_id=1)
    assert data.get_cycle_mode(1) == "cathode"
    with pytest.raises(KeyError, match="no TestMeta record"):
        data.get_cycle_mode(42)


def test_mutating_derived_record_does_not_persist():
    """The active record is a snapshot: edits do not write back (documented)."""
    data = Data()
    before = data.meta_test_dependent.cycle_mode
    data.tests.get(0).cycle_mode = "something_else"
    assert data.meta_test_dependent.cycle_mode == before
    assert data.tests.get(0).cycle_mode == before


def test_vacant_copies_extra_tests():
    cell = cellreader.CellpyCell(initialize=True)
    cell.data.set_test_meta(TestMeta(test_id=1, cycle_mode="full"))
    other = cellreader.CellpyCell.vacant(cell=cell)
    assert other.data.tests.test_ids == [0, 1]
    assert other.data.get_cycle_mode(1) == "full"


# ------------------------------------------------------------ mixed modes ----


def _mixed_mode_cell():
    cell = cellreader.CellpyCell(initialize=True)
    cell.data.set_cycle_mode("anode")
    cell.data.set_test_meta(TestMeta(test_id=1, cycle_mode="cathode"))
    return cell


def test_mixed_modes_raise_when_both_tests_in_raw():
    import pandas as pd

    cell = _mixed_mode_cell()
    hdr = get_headers_normal().test_id_txt
    cell.data.raw = pd.DataFrame({hdr: [0, 0, 1, 1], "current": [1.0, -1, 1, -1]})
    assert test_meta.cycle_modes_in_data(cell.data) == {"anode", "cathode"}
    with pytest.raises(MixedCycleModesError, match="different cycle_modes"):
        cell.make_step_table()
    with pytest.raises(MixedCycleModesError, match="different cycle_modes"):
        cell.make_summary()


def test_mixed_modes_dormant_without_test_id_column():
    """Extras without raw rows are dormant: no test_id column -> active only."""
    import pandas as pd

    cell = _mixed_mode_cell()
    cell.data.raw = pd.DataFrame({"current": [1.0, -1.0]})
    assert test_meta.cycle_modes_in_data(cell.data) == {"anode"}


# ------------------------------------------------- file compat / round-trip ----


@pytest.mark.parametrize("label,filename", LEGACY_FILES)
def test_files_load_as_single_test_zero(label, filename):
    """V2-04: v4-v8 files surface as a single-test collection (test_id=0)."""
    path = _require(HDF5_DIR / filename)
    cell = load_cellpy_file(path, accept_old=True)

    tests = cell.data.tests
    assert tests.test_ids == [0]
    assert len(tests) == 1
    record = tests.get(0)
    # scalar (not a 1-element list), matching the public property
    assert not isinstance(record.cycle_mode, (list, tuple))
    assert record.cycle_mode == cell.cycle_mode
    assert record.cell.mass == cell.data.meta_common.mass


@pytest.mark.essential
def test_v8_roundtrip_preserves_collection(tmp_path):
    """V2-01: save -> reload keeps the (single-record) collection identical."""
    source = _require(V8_WITH_FIDS)
    original = load_cellpy_file(source)
    snapshot = {
        tid: core_meta_io.to_dict(original.data.tests.get(tid))
        for tid in original.data.tests.test_ids
    }

    outfile = tmp_path / source.name
    original.save(outfile)
    reloaded = load_cellpy_file(outfile)

    result = {
        tid: core_meta_io.to_dict(reloaded.data.tests.get(tid))
        for tid in reloaded.data.tests.test_ids
    }
    assert result == snapshot


def test_save_warns_about_unpersisted_extras(tmp_path, caplog):
    source = _require(V8_WITH_FIDS)
    cell = load_cellpy_file(source)
    cell.data.set_test_meta(TestMeta(test_id=1, cycle_mode="full"))

    outfile = tmp_path / "extras.h5"
    with caplog.at_level("WARNING"):
        cell.save(outfile)
    assert any("not persist" in r.message or "persists" in r.message for r in caplog.records)

    reloaded = load_cellpy_file(outfile)
    assert reloaded.data.tests.test_ids == [0]
