"""``cellpy.utils.live.poll`` (#781): the poll loop over ``CellpyCell.update()``."""

from __future__ import annotations

import shutil

import pytest

import cellpy
from cellpy.utils import live
from tests.incremental_support import (
    NEWARE_KWARGS,
    NEWARE_UIO,
    assert_cell_frames_equal,
    truncate_text_file,
)

pytestmark = pytest.mark.essential

HEAD_ROWS = 6000


class FakeClock:
    """Collects sleep calls; ``grow_at`` maps tick index → rows to write."""

    def __init__(self, path, grow_at):
        self.path = path
        self.grow_at = grow_at
        self.sleeps = []

    def __call__(self, seconds):
        self.sleeps.append(seconds)
        tick = len(self.sleeps)
        if tick in self.grow_at:
            rows = self.grow_at[tick]
            if rows is None:
                shutil.copyfile(NEWARE_UIO, self.path)
            else:
                truncate_text_file(NEWARE_UIO, self.path, rows)


@pytest.fixture
def live_file(tmp_path):
    return truncate_text_file(NEWARE_UIO, tmp_path / "live.csv", HEAD_ROWS)


def test_poll_updates_on_growth_and_stops_at_max_polls(live_file):
    full = cellpy.get(NEWARE_UIO, testing=True, **NEWARE_KWARGS)
    c = cellpy.get(live_file, testing=True, **NEWARE_KWARGS)
    seen = []
    clock = FakeClock(live_file, {2: 8800, 4: None})
    out = live.poll(c, interval=7, on_update=lambda cell: seen.append(len(cell.data.raw)), max_polls=5, sleep=clock)
    assert out is c
    assert clock.sleeps == [7] * 5
    assert seen == [8800, len(full.data.raw)]
    assert c.poll_status.polls == 5
    assert c.poll_status.updates == 2
    assert c.poll_status.stopped_by == "max_polls"
    assert_cell_frames_equal(c, full)


def test_poll_from_path_fires_on_update_for_the_initial_load(live_file):
    seen = []
    clock = FakeClock(live_file, {})
    c = live.poll(
        live_file,
        interval=1,
        on_update=lambda cell: seen.append(len(cell.data.raw)),
        max_polls=1,
        sleep=clock,
        testing=True,
        **NEWARE_KWARGS,
    )
    assert seen == [HEAD_ROWS]
    assert c.poll_status.updates == 1
    assert c.poll_status.polls == 1


def test_poll_stops_on_until(live_file):
    c = cellpy.get(live_file, testing=True, **NEWARE_KWARGS)
    clock = FakeClock(live_file, {1: None})
    live.poll(c, interval=1, until=lambda cell: len(cell.data.raw) > HEAD_ROWS, sleep=clock)
    assert c.poll_status.stopped_by == "until"
    assert c.poll_status.polls == 1


def test_poll_stops_when_source_complete(live_file):
    c = cellpy.get(live_file, testing=True, **NEWARE_KWARGS)
    c.source_complete = True
    clock = FakeClock(live_file, {})
    live.poll(c, interval=1, sleep=clock)
    assert c.poll_status.stopped_by == "complete"
    assert clock.sleeps == []


def test_poll_stops_on_timeout(live_file, monkeypatch):
    c = cellpy.get(live_file, testing=True, **NEWARE_KWARGS)
    now = [0.0]
    monkeypatch.setattr(live.time, "monotonic", lambda: now[0])

    def clock(seconds):
        now[0] += seconds

    live.poll(c, interval=10, timeout=25, sleep=clock)
    assert c.poll_status.stopped_by == "timeout"
    assert c.poll_status.polls == 3


def test_poll_records_update_errors_unless_raise_errors(live_file, monkeypatch):
    c = cellpy.get(live_file, testing=True, **NEWARE_KWARGS)

    def boom(**kwargs):
        raise RuntimeError("tester unplugged")

    monkeypatch.setattr(c, "update", boom)
    live.poll(c, interval=1, max_polls=3, sleep=lambda s: None)
    assert c.poll_status.stopped_by == "error"
    assert isinstance(c.poll_status.error, RuntimeError)
    assert c.poll_status.polls == 1
    with pytest.raises(RuntimeError):
        live.poll(c, interval=1, max_polls=3, sleep=lambda s: None, raise_errors=True)


def test_poll_keyboard_interrupt_returns_the_cell(live_file):
    c = cellpy.get(live_file, testing=True, **NEWARE_KWARGS)

    def interrupt(seconds):
        raise KeyboardInterrupt

    out = live.poll(c, interval=1, sleep=interrupt)
    assert out is c
    assert c.poll_status.stopped_by == "interrupted"


def test_processor_module_is_gone():
    with pytest.raises(ImportError):
        import cellpy.utils.processor  # noqa: F401
