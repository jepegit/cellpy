"""Batch live refresh (#782): ``Batch.refresh`` / ``update(live=True)`` / ``poll``."""

from __future__ import annotations

import shutil

import pytest

import cellpy
from cellpy.batch.facade import from_cells
from tests.incremental_support import (
    NEWARE_KWARGS,
    NEWARE_UIO,
    assert_cell_frames_equal,
    truncate_text_file,
)

pytestmark = pytest.mark.essential

HEAD_ROWS = 6000


@pytest.fixture(scope="module")
def full_cell():
    return cellpy.get(NEWARE_UIO, testing=True, **NEWARE_KWARGS)


@pytest.fixture
def live_batch(tmp_path):
    paths = {}
    cells = {}
    for label in ("cell_a", "cell_b"):
        path = truncate_text_file(NEWARE_UIO, tmp_path / f"{label}.csv", HEAD_ROWS)
        paths[label] = path
        cells[label] = cellpy.get(path, testing=True, **NEWARE_KWARGS)
    return from_cells(cells), paths


def _grow(path):
    shutil.copyfile(NEWARE_UIO, path)


def test_refresh_reports_per_cell_and_updates_summaries(live_batch, full_cell):
    b, paths = live_batch
    n_before = len(b.summaries)
    assert b.refresh() == {"cell_a": False, "cell_b": False}
    _grow(paths["cell_b"])
    assert b.refresh() == {"cell_a": False, "cell_b": True}
    assert len(b.summaries) > n_before  # cache was cleared and rebuilt
    assert_cell_frames_equal(b.cells["cell_b"], full_cell)
    assert len(b.cells["cell_a"].data.raw) == HEAD_ROWS


def test_refresh_subset_and_error_capture(live_batch, monkeypatch):
    b, paths = live_batch

    def boom(**kwargs):
        raise RuntimeError("tester unplugged")

    monkeypatch.setattr(b.cells["cell_a"], "update", boom)
    outcome = b.refresh()
    assert isinstance(outcome["cell_a"], RuntimeError)
    assert outcome["cell_b"] is False
    with pytest.raises(RuntimeError):
        b.refresh(labels=["cell_a"], raise_errors=True)
    assert b.refresh(labels=["cell_b"]) == {"cell_b": False}


def test_update_live_does_not_reload(live_batch, full_cell):
    b, paths = live_batch
    result_before = b.result
    _grow(paths["cell_a"])
    assert b.update(live=True) is result_before
    assert_cell_frames_equal(b.cells["cell_a"], full_cell)


def test_poll_refreshes_and_reruns_report(live_batch, full_cell):
    b, paths = live_batch
    ticks = []
    seen = []

    def clock(seconds):
        ticks.append(seconds)
        if len(ticks) == 1:
            _grow(paths["cell_a"])
        elif len(ticks) == 3:
            _grow(paths["cell_b"])

    status = b.poll(interval=5, max_polls=4, on_update=lambda batch, outcome: seen.append(outcome), sleep=clock)
    assert ticks == [5] * 4
    assert status.polls == 4
    assert status.updates == 2
    assert status.stopped_by == "max_polls"
    assert seen == [{"cell_a": True, "cell_b": False}, {"cell_a": False, "cell_b": True}]
    assert b.poll_status is status
    assert set(b.last_report["cell"].to_list()) == {"cell_a", "cell_b"}
    assert_cell_frames_equal(b.cells["cell_a"], full_cell)
    assert_cell_frames_equal(b.cells["cell_b"], full_cell)


def test_poll_stops_on_until_and_complete(live_batch):
    b, paths = live_batch
    status = b.poll(interval=1, until=lambda batch: True, sleep=lambda s: None)
    assert status.stopped_by == "until" and status.polls == 0
    for cell in b.cells.values():
        cell.source_complete = True
    status = b.poll(interval=1, sleep=lambda s: None)
    assert status.stopped_by == "complete" and status.polls == 0


def test_poll_stops_on_cell_error(live_batch, monkeypatch):
    b, paths = live_batch

    def boom(**kwargs):
        raise RuntimeError("tester unplugged")

    monkeypatch.setattr(b.cells["cell_b"], "update", boom)
    status = b.poll(interval=1, max_polls=3, sleep=lambda s: None)
    assert status.stopped_by == "error"
    assert isinstance(status.error, RuntimeError)
    assert status.polls == 1
