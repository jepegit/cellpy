"""Batch progress bus + tqdm display (#916)."""

import polars as pl
import pytest

from cellpy.batch.journal import FILENAME, Journal
from cellpy.batch.policy import LoadPolicy, SourcePreference
from cellpy.batch.progress import (
    TqdmBatchProgress,
    in_notebook,
    progress_scope,
    should_show_default,
)
from cellpy.batch.runner import run
from cellpy.internals.progress import (
    ProgressEvent,
    emit,
    get_hook,
    set_cell_label,
    set_hook,
)


@pytest.fixture
def progress_events():
    events = []
    previous = set_hook(events.append)
    try:
        yield events
    finally:
        set_hook(previous)


def test_emit_is_silent_without_hook():
    set_hook(None)
    emit("copy", label="x")


def test_emit_records_phases(progress_events):
    emit("journal")
    emit("search")
    emit("parse", label="c1", n=1, total_n=1)
    phases = [e.phase for e in progress_events]
    assert phases == ["journal", "search", "parse"]
    assert progress_events[-1].label == "c1"


def test_emit_uses_cell_label_context(progress_events):
    token = set_cell_label("cell_a")
    try:
        emit("copy", n=1, total_n=1)
    finally:
        from cellpy.internals.progress import reset_cell_label

        reset_cell_label(token)
    assert progress_events[0].label == "cell_a"


def test_emit_swallows_hook_errors():
    def boom(_event):
        raise RuntimeError("nope")

    previous = set_hook(boom)
    try:
        emit("parse")
    finally:
        set_hook(previous)


@pytest.mark.essential
def test_run_emits_cell_start_parse_done(monkeypatch, progress_events):
    monkeypatch.setattr("cellpy.batch.runner._cellpy_get", lambda **kwargs: object())
    journal = Journal(
        name="t",
        project="p",
        pages=pl.DataFrame(
            {FILENAME: ["c_a"], "cellpy_file_name": ["x.cellpy"]}
        ),
    )
    seen = []
    br = run(
        journal,
        LoadPolicy(source=SourcePreference.CELLPY_ONLY),
        on_progress=lambda i, n, r: seen.append((i, n, r.label)),
    )
    assert br["c_a"].ok
    assert seen == [(1, 1, "c_a")]
    phases = [e.phase for e in progress_events]
    assert phases == ["cell_start", "parse", "parse", "cell_done"]
    assert all(e.label == "c_a" for e in progress_events)


@pytest.mark.essential
def test_on_progress_still_wins_with_event_hook(monkeypatch, progress_events):
    """3-arg on_progress stays the public completion callback."""
    monkeypatch.setattr("cellpy.batch.runner._cellpy_get", lambda **kwargs: object())
    journal = Journal(
        name="t",
        project="p",
        pages=pl.DataFrame(
            {
                FILENAME: ["a", "b"],
                "cellpy_file_name": ["x.cellpy", "y.cellpy"],
            }
        ),
    )
    seen = []
    run(
        journal,
        LoadPolicy(source=SourcePreference.CELLPY_ONLY),
        on_progress=lambda i, n, r: seen.append(i),
    )
    assert seen == [1, 2]
    assert [e.phase for e in progress_events].count("cell_done") == 2


@pytest.mark.essential
def test_tqdm_display_disable_tracks_cells():
    display = TqdmBatchProgress(2, disable=True)
    try:
        display(ProgressEvent("cell_start", label="a"))
        display(ProgressEvent("copy", label="a", n=1, total_n=1))
        display(ProgressEvent("parse", label="a", n=1, total_n=1))
        display(ProgressEvent("save", label="a", n=1, total_n=1))
        display(ProgressEvent("cell_done", label="a"))
        display(ProgressEvent("cell_start", label="b"))
        display(ProgressEvent("cell_done", label="b"))
        assert display.cells_done == 2
    finally:
        display.close()


def test_tqdm_processes_skips_child_bars():
    display = TqdmBatchProgress(1, show_children=False, disable=True)
    try:
        display(ProgressEvent("cell_start", label="a"))
        display(ProgressEvent("parse", label="a"))
        display(ProgressEvent("cell_done", label="a"))
        assert display.cells_done == 1
        assert display._children == {}
    finally:
        display.close()


def test_progress_scope_false_installs_noop_and_restores():
    previous = set_hook(None)
    try:
        with progress_scope(False, 1, "serial") as display:
            assert display is None
            assert get_hook() is not None
            emit("journal")
        assert get_hook() is None
    finally:
        set_hook(previous)


def test_progress_scope_callable_and_nested_inherit():
    events = []
    with progress_scope(events.append, 0, "serial"):
        with progress_scope(None, 1, "serial") as inner:
            assert inner is None
            emit("search")
    assert [e.phase for e in events] == ["search"]
    assert get_hook() is None


def test_progress_scope_true_attaches(monkeypatch):
    created = []
    real = TqdmBatchProgress

    def _wrapped(*args, **kwargs):
        kwargs["disable"] = True
        bar = real(*args, **kwargs)
        created.append(bar)
        return bar

    monkeypatch.setattr("cellpy.batch.progress.TqdmBatchProgress", _wrapped)
    with progress_scope(True, 1, "serial") as display:
        assert display is created[0]
    assert get_hook() is None


def test_should_show_default_false_when_not_tty(monkeypatch):
    monkeypatch.setattr("cellpy.batch.progress.in_notebook", lambda: False)

    class _Err:
        def isatty(self):
            return False

    monkeypatch.setattr("cellpy.batch.progress.sys.stderr", _Err())
    assert should_show_default() is False


def test_in_notebook_detects_zmq_shell(monkeypatch):
    class ZMQInteractiveShell:
        pass

    class _IPython:
        @staticmethod
        def get_ipython():
            return ZMQInteractiveShell()

    import sys

    monkeypatch.setitem(sys.modules, "IPython", _IPython)
    assert in_notebook() is True


def test_local_copy_emits_copy(tmp_path, progress_events):
    from cellpy.internals.otherpath import OtherPath

    src = tmp_path / "src.bin"
    src.write_bytes(b"abc")
    dest = tmp_path / "out"
    dest.mkdir()
    OtherPath(src).copy(dest)
    assert (dest / "src.bin").is_file()
    assert any(e.phase == "copy" for e in progress_events)
