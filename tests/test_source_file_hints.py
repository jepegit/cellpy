"""Source-recorded file stats as ``update()`` hints (#1124, Epic M).

A metadata-source record whose raw `FileRef` carries ``size`` / ``mtime``
lets `CellpyCell.update()` skip the (possibly remote) ``stat`` when those
values equal what cellpy loaded. Anything without such values, or with a
differing value, goes through today's stat-based path.
"""

from __future__ import annotations

import datetime
import logging
import pathlib

import pytest

import cellpy
from cellpy import batch as batch_api
from cellpy import log
from cellpy.batch.policy import LoadPolicy, SourcePreference
from cellpy.batch.source import SESSION_KEY
from cellpy.internals.otherpath import OtherPath
from cellpy.readers import metadata_sources as ms
from cellpy.readers.cellreader import _mtime_epoch, _source_hint_matches_loaded
from cellpy.readers.metadata_sources import ExternalLink, FileRef, MetaRecord
from cellpy.readers.metadata_sources import registry as registry_module
from cellpy.readers.metadata_sources.testing import DictMetadataSource
from tests import fdv

log.setup_logging(default_level=logging.DEBUG, testing=True)

RES = pathlib.Path(fdv.res_file_path)
RES_URI = RES.as_posix()
RES_STAT = RES.stat()
RES_MTIME_ISO = datetime.datetime.fromtimestamp(RES_STAT.st_mtime, tz=datetime.timezone.utc).isoformat()


def _record(**ref_kwargs) -> MetaRecord:
    files = (FileRef("raw", RES_URI, loader="arbin_res", **ref_kwargs),) if ref_kwargs else ()
    return MetaRecord(
        "labdb",
        external_id="42",
        cell={"mass": 1.23},
        test={"cell_name": fdv.run_name},
        files=files or (FileRef("raw", RES_URI, loader="arbin_res"),),
    )


@pytest.fixture
def clean_registry(monkeypatch):
    monkeypatch.setattr(registry_module, "_iter_entry_points", lambda: ())
    ms.clear_registry()
    yield
    ms.clear_registry()


@pytest.fixture
def labdb(clean_registry) -> DictMetadataSource:
    source = DictMetadataSource(
        {
            ("tag", "MATCH"): _record(size=RES_STAT.st_size, mtime=RES_MTIME_ISO),
            ("tag", "SIZE_OFF"): _record(size=RES_STAT.st_size + 1, mtime=RES_MTIME_ISO),
            ("tag", "MTIME_ONLY"): _record(mtime=RES_STAT.st_mtime),
            ("tag", "BAD_MTIME"): _record(size=RES_STAT.st_size, mtime="yesterday-ish"),
            ("tag", "NO_STATS"): _record(),
        },
        name="labdb",
    )
    ms.register(source)
    return source


@pytest.fixture
def no_stat(monkeypatch):
    """Count ``OtherPath.stat`` calls; the hint path must not reach it."""
    calls: list[str] = []
    original = OtherPath.stat

    def _stat(self, *args, **kwargs):
        calls.append(str(self))
        return original(self, *args, **kwargs)

    monkeypatch.setattr(OtherPath, "stat", _stat)
    return calls


def _load(tag):
    return cellpy.get(source="labdb", key=tag, kind="tag", testing=True)


# -- comparison rule -----------------------------------------------------------


@pytest.mark.essential
@pytest.mark.parametrize(
    "value, expected",
    [
        (None, None),
        (1_700_000_000, 1_700_000_000.0),
        ("2023-11-14T22:13:20+00:00", 1_700_000_000.0),
        ("2023-11-14T22:13:20Z", 1_700_000_000.0),
        ("2023-11-14T22:13:20", 1_700_000_000.0),  # naive → UTC
        ("not a date", None),
    ],
)
def test_mtime_epoch(value, expected):
    assert _mtime_epoch(value) == expected


class _Fid:
    def __init__(self, size, last_modified):
        self.size = size
        self.last_modified = last_modified


@pytest.mark.essential
def test_hint_matches_only_when_every_recorded_stat_agrees():
    fid = _Fid(100, 1_700_000_000.0)
    assert _source_hint_matches_loaded(FileRef("raw", "x", size=100, mtime=1_700_000_000.4), fid)
    assert _source_hint_matches_loaded(FileRef("raw", "x", size=100), fid)
    assert _source_hint_matches_loaded(FileRef("raw", "x", mtime="2023-11-14T22:13:20Z"), fid)
    assert not _source_hint_matches_loaded(FileRef("raw", "x"), fid)
    assert not _source_hint_matches_loaded(FileRef("raw", "x", size=101), fid)
    assert not _source_hint_matches_loaded(FileRef("raw", "x", size=100, mtime=1_700_000_002.0), fid)
    assert not _source_hint_matches_loaded(FileRef("raw", "x", size=100, mtime="???"), fid)
    assert not _source_hint_matches_loaded(FileRef("raw", "x", size=100), _Fid(None, None))


# -- back-link -----------------------------------------------------------------


@pytest.mark.essential
def test_link_keeps_stat_carrying_raw_refs_and_round_trips():
    record = MetaRecord(
        "labdb",
        files=(
            FileRef("raw", "a.res", size=1, mtime="2026-01-01T00:00:00Z"),
            FileRef("raw", "b.res"),
            FileRef("cellpy", "a.cellpy", size=5),
        ),
    )
    link = record.link(files=("a.res", "b.res"))
    assert [r.uri for r in link.file_refs] == ["a.res"]
    assert link.file_ref_for("a.res").size == 1
    assert link.file_ref_for("b.res") is None
    again = ExternalLink.from_dict(link.to_dict())
    assert again == link
    assert again.file_refs[0].mtime == "2026-01-01T00:00:00Z"
    # pre-#1124 documents stay byte-identical
    assert "file_refs" not in ExternalLink("labdb", files=("b.res",)).to_dict()
    assert record.link(files=("b.res",)).file_refs == ()


# -- cell path -----------------------------------------------------------------


@pytest.mark.essential
def test_matching_hint_skips_stat(labdb, no_stat):
    c = _load("MATCH")
    assert c.external_links["labdb"].file_refs[0].size == RES_STAT.st_size
    no_stat.clear()

    assert c.update() is False
    assert no_stat == []


@pytest.mark.essential
def test_differing_size_falls_back_to_stat(labdb, no_stat):
    c = _load("SIZE_OFF")
    no_stat.clear()

    assert c.update() is False  # the file itself did not change
    assert no_stat, "stat must run when the source's size differs"


def test_mtime_only_hint_is_enough(labdb, no_stat):
    c = _load("MTIME_ONLY")
    no_stat.clear()
    assert c.update() is False
    assert no_stat == []


def test_unparsable_mtime_falls_back_to_stat(labdb, no_stat):
    c = _load("BAD_MTIME")
    no_stat.clear()
    assert c.update() is False
    assert no_stat


@pytest.mark.essential
def test_record_without_stats_behaves_as_today(labdb, no_stat):
    c = _load("NO_STATS")
    assert c.external_links["labdb"].file_refs == ()
    no_stat.clear()
    assert c.update() is False
    assert no_stat


def test_force_ignores_the_hint(labdb, no_stat):
    c = _load("MATCH")
    n_raw = len(c.data.raw)
    assert c.update(force=True) is True
    assert len(c.data.raw) == n_raw


def test_hints_survive_save_and_load(labdb, no_stat, tmp_path):
    c = _load("MATCH")
    path = tmp_path / "hinted.cellpy"
    c.save(path)

    loaded = cellpy.get(path, testing=True)
    link = loaded.external_links["labdb"]
    assert link.file_refs[0].uri == RES_URI
    assert link.file_refs[0].size == RES_STAT.st_size
    no_stat.clear()
    assert loaded.update() is False
    assert no_stat == []


def test_refetch_on_a_loaded_cell_replaces_the_hints(labdb, no_stat):
    c = _load("SIZE_OFF")
    assert c.external_links["labdb"].file_refs[0].size == RES_STAT.st_size + 1

    c.fetch_meta("labdb", "MATCH", kind="tag")

    assert c.external_links["labdb"].file_refs[0].size == RES_STAT.st_size
    no_stat.clear()
    assert c.update() is False
    assert no_stat == []


# -- batch path ----------------------------------------------------------------


def test_batch_links_carry_hints_and_refresh_skips_stat(labdb, no_stat):
    b = batch_api.from_source("labdb", "MATCH", policy=LoadPolicy(source=SourcePreference.NEWEST))
    assert b.journal.session[SESSION_KEY][fdv.run_name]["file_refs"][0]["size"] == RES_STAT.st_size

    b.update(progress=False, testing=True)
    cell = b.cells[fdv.run_name]
    assert cell.external_links["labdb"].file_refs[0].size == RES_STAT.st_size
    no_stat.clear()

    assert b.refresh() == {fdv.run_name: False}
    assert no_stat == []
