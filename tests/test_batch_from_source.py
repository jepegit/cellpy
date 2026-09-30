"""``batch.from_source`` — a journal built from metadata-source records (#1107).

Offline against `DictMetadataSource`: pages carry the record's metadata and
file pointers, rows without pointers go through the journal-style file
search (or are left ``None`` with ``file_search=False``), and loaded cells
get their `ExternalLink` after ``update()``.
"""

from __future__ import annotations

import logging
import pathlib

import pytest

from cellpy import batch as batch_api
from cellpy import log
from cellpy.batch import Batch, journal_from_records
from cellpy.batch.journal import FILENAME, read_journal, write_journal
from cellpy.batch.policy import LoadPolicy, SourcePreference
from cellpy.batch.source import SESSION_KEY, default_batch_name, pages_from_records
from cellpy.exceptions import NoDataFound
from cellpy.readers import metadata_sources as ms
from cellpy.readers.metadata_sources import FileRef, MetaRecord
from cellpy.readers.metadata_sources import registry as registry_module
from cellpy.readers.metadata_sources.testing import DictMetadataSource
from tests import fdv

log.setup_logging(default_level=logging.DEBUG, testing=True)

RES = pathlib.Path(fdv.res_file_path).as_posix()
H5 = pathlib.Path(fdv.cellpy_file_path).as_posix()


def _rec(name, *, external_id, files=(), mass=1.0, cycle_mode=None):
    cell = {"mass": mass, "nom_cap": 3.5, "active_electrode_area": 1.767}
    test = {"cell_name": name}
    if cycle_mode:
        test["cycle_mode"] = cycle_mode
    return MetaRecord(
        "labdb",
        external_id=external_id,
        source_uri=f"https://labdb.test/api/test/{external_id}/",
        cell=cell,
        test=test,
        files=files,
    )


WITH_RAW = _rec(
    "cell_a",
    external_id="1",
    mass=1.1,
    cycle_mode="anode",
    files=(FileRef("raw", RES, loader="arbin_res", size=10, mtime="2026-01-01T00:00:00Z"),),
)
WITH_CELLPY = _rec("cell_b", external_id="2", mass=2.2, files=(FileRef("cellpy", H5),))
NO_FILES = _rec("cell_c", external_id="3", mass=3.3)


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
            ("tag", "SAL"): (WITH_RAW, WITH_CELLPY, NO_FILES),
            ("tag", "POINTED"): (WITH_RAW, WITH_CELLPY),
        },
        name="labdb",
    )
    ms.register(source)
    return source


@pytest.fixture
def no_filefinder(monkeypatch):
    from cellpy.readers import filefinder

    def _boom(*args, **kwargs):
        raise AssertionError("filefinder must not run when every record has file pointers")

    monkeypatch.setattr(filefinder, "search_for_files", _boom)


# -- pages ---------------------------------------------------------------------


@pytest.mark.essential
def test_pages_carry_metadata_and_pointers(no_filefinder):
    pages, links = pages_from_records((WITH_RAW, WITH_CELLPY), source_name="labdb")

    rows = {row[FILENAME]: row for row in pages.iter_rows(named=True)}
    a, b = rows["cell_a"], rows["cell_b"]
    assert a["mass"] == pytest.approx(1.1) and a["cycle_mode"] == "anode"
    assert a["raw_file_names"] == [RES] and a["cellpy_file_name"] is None
    assert a["instrument"] == "arbin_res"
    assert a["raw_file_size"] == 10 and a["raw_file_mtime"] == "2026-01-01T00:00:00Z"
    assert b["cellpy_file_name"] == H5 and b["raw_file_names"] is None
    assert a["external_id"] == "1" and b["source_uri"].endswith("/2/")

    assert links["cell_a"]["files"] == [RES]
    assert "mass" in links["cell_a"]["fields"] and "cycle_mode" in links["cell_a"]["fields"]
    assert links["cell_b"]["source_name"] == "labdb"


@pytest.mark.essential
def test_rows_without_pointers_use_the_journal_file_search(monkeypatch):
    from cellpy.batch import _dbengine

    seen = {}

    def _find(info, **kwargs):
        seen["names"] = list(info["filename"])
        seen["kwargs"] = kwargs
        info["raw_file_names"] = [[RES]] * len(info["filename"])
        info["cellpy_file_name"] = [None] * len(info["filename"])
        return info

    monkeypatch.setattr(_dbengine, "find_files", _find)
    pages, links = pages_from_records((WITH_RAW, NO_FILES), source_name="labdb", file_search_kwargs={"pre_path": "x"})

    assert seen["names"] == ["cell_c"]  # only the row without pointers
    assert seen["kwargs"] == {"pre_path": "x"}
    row = pages.filter(pages[FILENAME] == "cell_c").row(0, named=True)
    assert row["raw_file_names"] == [RES]
    assert links["cell_c"].get("files", []) == []


def test_file_search_false_leaves_paths_none(no_filefinder):
    pages, _ = pages_from_records((NO_FILES,), source_name="labdb", file_search=False)
    row = pages.row(0, named=True)
    assert row["raw_file_names"] is None and row["cellpy_file_name"] is None


def test_duplicate_labels_are_suffixed_and_fallbacks_used():
    twin = _rec("cell_a", external_id="9")
    anon = MetaRecord("labdb", external_id="77", cell={"mass": 1.0})
    nameless = MetaRecord("labdb", cell={"mass": 1.0})
    pages, _ = pages_from_records((WITH_RAW, twin, anon, nameless), source_name="labdb", file_search=False)
    assert pages[FILENAME].to_list() == ["cell_a", "cell_a_2", "77", "cell_004"]


def test_default_batch_name_is_filesystem_safe():
    assert default_batch_name("batbase", "tag", "SAL 010/x") == "batbase_tag_SAL-010-x"
    assert default_batch_name("batbase", "project", None) == "batbase_project_all"


def test_journal_from_records_keeps_links_in_session_and_round_trips(tmp_path):
    journal = journal_from_records(
        (WITH_RAW, WITH_CELLPY), source_name="labdb", name="j", project="p", file_search=False
    )
    assert journal.project == "p"
    assert set(journal.session[SESSION_KEY]) == {"cell_a", "cell_b"}

    path = write_journal(journal, tmp_path / "j.json")
    again = read_journal(path)
    assert again.session[SESSION_KEY]["cell_a"]["files"] == [RES]


# -- Batch.from_source ---------------------------------------------------------


@pytest.mark.essential
def test_from_source_builds_pages_like_a_journal(labdb, no_filefinder):
    b = batch_api.from_source("labdb", "POINTED")

    assert isinstance(b, Batch)
    assert b.journal.name == "labdb_tag_POINTED"
    assert b.journal.project == "labdb"  # defaults to the source name
    assert b.cell_names == ["cell_a", "cell_b"]
    assert labdb.queries[-1].kind == "tag" and labdb.queries[-1].key == "POINTED"


def test_from_source_kind_defaults_to_tag_and_extra_passes_through(labdb, no_filefinder):
    Batch.from_source("labdb", "POINTED", name="mine", project="p2", channel=3)
    q = labdb.queries[-1]
    assert q.kind == "tag" and q.project == "p2" and q.extra == {"channel": 3}


def test_from_source_no_records_raises(labdb):
    with pytest.raises(NoDataFound, match="no records"):
        batch_api.from_source("labdb", "NOTHING")


def test_from_source_unknown_source_is_strict(clean_registry):
    from cellpy.readers.metadata_sources import MetadataSourceError

    with pytest.raises(MetadataSourceError):
        batch_api.from_source("nope", "x")


@pytest.mark.essential
def test_update_loads_pointed_files_and_stamps_links(labdb, no_filefinder):
    b = batch_api.from_source("labdb", "POINTED", policy=LoadPolicy(source=SourcePreference.NEWEST))
    result = b.update(progress=False, testing=True)

    assert result is not None
    assert set(b.cells) == {"cell_a", "cell_b"}
    a = b.cells["cell_a"]
    assert a.data.meta_common.mass == pytest.approx(1.1)
    assert a.external_links["labdb"].external_id == "1"
    assert a.external_links["labdb"].files == (RES,)
    assert b.cells["cell_b"].external_links["labdb"].files == (H5,)
