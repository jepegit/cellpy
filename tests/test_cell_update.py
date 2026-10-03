"""``CellpyCell.update()`` (#164): refresh a cell from a raw source that grew.

The oracle is a full ``cellpy.get`` of the complete file: a cell loaded from a
truncated copy, then ``update()``-ed after the copy grew, must carry the same
raw / steps / summary frames.
"""

from __future__ import annotations

import shutil

import pytest

import cellpy
from cellpy.exceptions import NoDataFound
from cellpy.readers.cellreader import CellpyCell
from tests.incremental_support import (
    NEWARE_KWARGS,
    NEWARE_UIO,
    assert_cell_frames_equal,
    truncate_text_file,
)

pytestmark = pytest.mark.essential

MID_CYCLE_3 = 6000  # rows; well inside the third of four cycles
MID_CYCLE_4 = 8800
SINGLE_CYCLE = 1000  # rows; still inside the first cycle


@pytest.fixture(scope="module")
def full_cell():
    return cellpy.get(NEWARE_UIO, testing=True, **NEWARE_KWARGS)


@pytest.fixture
def live_file(tmp_path):
    return truncate_text_file(NEWARE_UIO, tmp_path / "live.csv", MID_CYCLE_3)


def _grow(path, n_rows=None):
    if n_rows is None:
        shutil.copyfile(NEWARE_UIO, path)
    else:
        truncate_text_file(NEWARE_UIO, path, n_rows)


def test_update_on_unchanged_source_is_a_noop(live_file):
    c = cellpy.get(live_file, testing=True, **NEWARE_KWARGS)
    n_raw = len(c.data.raw)
    assert c.update() is False
    assert len(c.data.raw) == n_raw


def test_update_after_growth_equals_full_load(live_file, full_cell):
    c = cellpy.get(live_file, testing=True, **NEWARE_KWARGS)
    _grow(live_file)
    assert c.update() is True
    assert_cell_frames_equal(c, full_cell)


def test_update_twice_tracks_the_marker(live_file, full_cell):
    c = cellpy.get(live_file, testing=True, **NEWARE_KWARGS)
    _grow(live_file, MID_CYCLE_4)
    assert c.update() is True
    assert len(c.data.raw) == MID_CYCLE_4
    marker = c._load_marker
    assert marker is not None and marker.row_count is not None
    assert marker.row_count < MID_CYCLE_4  # rewound to the last cycle start
    _grow(live_file)
    assert c.update() is True
    assert_cell_frames_equal(c, full_cell)


def test_update_refreshes_file_id(live_file):
    c = cellpy.get(live_file, testing=True, **NEWARE_KWARGS)
    fid = c.data.raw_data_files[0]
    old_size, old_last = fid.size, fid.last_data_point
    _grow(live_file)
    c.update()
    assert fid.size > old_size
    assert fid.last_data_point > old_last
    assert fid.last_data_point == int(c.data.raw[c.schema.raw.datapoint_num].max())
    assert c.data.raw_data_files_length[-1] == len(c.data.raw)
    assert c.update() is False  # stats now match the file again


def test_update_after_cellpy_file_round_trip(live_file, tmp_path):
    c = cellpy.get(live_file, testing=True, mass=1.3, **NEWARE_KWARGS)
    cellpy_file = tmp_path / "live.cellpy"
    c.save(cellpy_file)
    reloaded = cellpy.get(cellpy_file, testing=True)
    assert reloaded.tester != "neware_txt"  # the file does not carry the loader
    _grow(live_file)
    assert reloaded.update() is True
    assert reloaded.tester == "neware_txt"
    assert reloaded.mass == pytest.approx(1.3)
    expected = cellpy.get(NEWARE_UIO, testing=True, mass=1.3, **NEWARE_KWARGS)
    assert_cell_frames_equal(reloaded, expected)


def test_update_falls_back_to_full_reload_and_keeps_meta(tmp_path):
    live = truncate_text_file(NEWARE_UIO, tmp_path / "live.csv", SINGLE_CYCLE)
    c = cellpy.get(live, testing=True, mass=2.5, **NEWARE_KWARGS)
    c.cell_name = "keep-me"
    _grow(live)
    # A single-cycle head leaves nothing before the rewind point, so core
    # rejects the chunk and update() reloads the whole file instead.
    assert c.update() is True
    assert c.mass == pytest.approx(2.5)
    assert c.cell_name == "keep-me"
    expected = cellpy.get(NEWARE_UIO, testing=True, mass=2.5, **NEWARE_KWARGS)
    assert_cell_frames_equal(c, expected)


def test_update_force_reloads_an_unchanged_source(live_file):
    c = cellpy.get(live_file, testing=True, **NEWARE_KWARGS)
    before = c.data.raw.copy()
    assert c.update(force=True) is True
    assert len(c.data.raw) == len(before)


def test_update_without_raw_source_raises():
    c = CellpyCell(initialize=True)
    with pytest.raises(NoDataFound):
        c.update()


def test_update_uses_full_reload_for_non_incremental_loader(live_file, full_cell, monkeypatch):
    c = cellpy.get(live_file, testing=True, **NEWARE_KWARGS)
    calls = []

    def _no_incremental(*args, **kwargs):
        calls.append(1)
        raise AssertionError("incremental path must not run")

    monkeypatch.setattr(c, "_update_incremental", _no_incremental)
    # Pretend the loader lacks load_since (a fresh subclass sidesteps the ABC
    # isinstance cache): the protocol check must route to full reload.
    not_incremental = type("NotIncremental", (type(c.loader_class),), {"load_since": None})
    c.loader_class.__class__ = not_incremental
    _grow(live_file)
    assert c.update() is True
    assert calls == []
    assert_cell_frames_equal(c, full_cell)
