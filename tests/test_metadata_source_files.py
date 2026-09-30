"""File pointers from external metadata sources (#1107, Epic M / M4).

A source that knows where a test's files live hands cellpy `FileRef`s on the
`MetaRecord`; ``cellpy.get(source=...)`` opens them directly and only falls
back to ``filefinder`` when the record has none. Everything without ``files``
behaves as before.
"""

from __future__ import annotations

import logging
import pathlib

import pytest

import cellpy
from cellpy import log
from cellpy.exceptions import NoDataFound
from cellpy.readers import metadata_sources as ms
from cellpy.readers.cellreader import CellpyCell
from cellpy.readers.metadata_sources import (
    ExternalLink,
    FileRef,
    MetadataSourceError,
    MetaRecord,
    validate_record,
)
from cellpy.readers.metadata_sources import registry as registry_module
from cellpy.readers.metadata_sources.testing import DictMetadataSource

log.setup_logging(default_level=logging.DEBUG, testing=True)


@pytest.fixture
def clean_registry(monkeypatch):
    monkeypatch.setattr(registry_module, "_iter_entry_points", lambda: ())
    ms.clear_registry()
    yield
    ms.clear_registry()


@pytest.fixture
def no_filefinder(monkeypatch):
    """Fail loudly if anything reaches for ``filefinder.search_for_files``."""
    from cellpy.readers import filefinder

    def _boom(*args, **kwargs):
        raise AssertionError("filefinder must not run when the source gave file pointers")

    monkeypatch.setattr(filefinder, "search_for_files", _boom)


def _record(parameters, *, files=(), mass=1.23, **test) -> MetaRecord:
    return MetaRecord(
        "labdb",
        external_id="42",
        source_uri="https://labdb.test/api/test/42/",
        cell={"mass": mass, "nom_cap": 3.5},
        test={"cell_name": parameters.run_name, **test},
        files=files,
    )


@pytest.fixture
def labdb(clean_registry, parameters) -> DictMetadataSource:
    raw = FileRef("raw", pathlib.Path(parameters.res_file_path).as_posix(), loader="arbin_res", size=1613824)
    with_files = _record(parameters, files=(raw,))
    without_files = _record(parameters, mass=4.56)
    source = DictMetadataSource(
        {
            ("tag", "WITH_FILES"): with_files,
            ("tag", "NO_FILES"): without_files,
            ("cell_name", parameters.run_name): with_files,
            ("cell_name", pathlib.Path(parameters.res_file_path).stem): with_files,
        },
        name="labdb",
    )
    ms.register(source)
    return source


# -- contract ------------------------------------------------------------------


@pytest.mark.essential
def test_file_refs_are_coerced_and_ordered():
    record = MetaRecord(
        "labdb",
        files=[
            {"kind": "raw", "uri": "b.res", "order": 2},
            FileRef("cellpy", "a.cellpy"),
            {"kind": "raw", "uri": "a.res", "order": 1, "loader": "arbin_res"},
        ],
    )
    assert [f.uri for f in record.raw_files()] == ["a.res", "b.res"]
    assert record.cellpy_file().uri == "a.cellpy"
    assert all(isinstance(f, FileRef) for f in record.files)
    validate_record(record)


@pytest.mark.essential
@pytest.mark.parametrize(
    "files, message",
    [
        ((FileRef("tape", "x"),), "kind"),
        ((FileRef("raw", ""),), "uri is empty"),
        ((FileRef("raw", "x"), FileRef("cellpy", "x")), "listed twice"),
        (("x.res",), "FileRef instances"),
    ],
)
def test_validate_record_rejects_bad_file_refs(files, message):
    with pytest.raises(MetadataSourceError, match=message):
        validate_record(MetaRecord("labdb", files=files))


def test_file_ref_dict_round_trip():
    ref = FileRef("raw", "scp://host/data/a.res", order=3, size=10, mtime="2026-01-01T00:00:00Z", loader="arbin_res")
    again = FileRef.from_dict(ref.to_dict())
    assert again == ref
    assert "checksum" not in ref.to_dict()


def test_external_link_files_round_trip_and_omitted_when_empty():
    link = ExternalLink("labdb", files=("a.res", "a.cellpy"))
    assert ExternalLink.from_dict(link.to_dict()) == link
    assert "files" not in ExternalLink("labdb").to_dict()
    assert ExternalLink.from_dict({"source_name": "labdb"}).files == ()


# -- cell path -----------------------------------------------------------------


@pytest.mark.essential
def test_get_from_source_opens_pointed_files_without_filefinder(labdb, no_filefinder, parameters):
    c = cellpy.get(source="labdb", key="WITH_FILES", kind="tag", testing=True)

    assert c is not None
    assert c.data.meta_common.mass == pytest.approx(1.23)
    link = c.external_links["labdb"]
    assert link.external_id == "42"
    assert link.files == (pathlib.Path(parameters.res_file_path).as_posix(),)
    assert "mass" in link.fields
    assert labdb.queries[-1].kind == "tag"


def test_from_source_classmethod_is_an_alias(labdb, no_filefinder):
    c = CellpyCell.from_source("labdb", "WITH_FILES", kind="tag", testing=True)
    assert c.data.meta_common.mass == pytest.approx(1.23)


@pytest.mark.essential
def test_explicit_keywords_beat_the_source(labdb, no_filefinder):
    c = cellpy.get(source="labdb", key="WITH_FILES", kind="tag", mass=9.9, testing=True)
    assert c.data.meta_common.mass == pytest.approx(9.9)
    # the source still counts as a contributor for what it supplied
    assert c.external_links["labdb"].external_id == "42"


@pytest.mark.essential
def test_record_without_files_falls_back_to_filefinder(labdb, monkeypatch, parameters):
    from cellpy.readers import filefinder

    calls = []

    def _search(run_name, *args, **kwargs):
        calls.append(run_name)
        return [parameters.res_file_path], ""

    monkeypatch.setattr(filefinder, "search_for_files", _search)
    c = cellpy.get(source="labdb", key="NO_FILES", kind="tag", instrument="arbin_res", testing=True)

    assert calls == [parameters.run_name]
    assert c.data.meta_common.mass == pytest.approx(4.56)
    assert c.external_links["labdb"].files == ()


def test_filename_plus_source_only_enriches(labdb, no_filefinder, parameters):
    c = cellpy.get(parameters.res_file_path, instrument="arbin_res", source="labdb", testing=True)
    # key defaulted to the filename stem, kind cell_name
    assert labdb.queries[-1].key == pathlib.Path(parameters.res_file_path).stem
    assert c.data.meta_common.mass == pytest.approx(1.23)
    assert c.external_links["labdb"].files == ()


def test_no_record_without_filename_raises(labdb):
    with pytest.raises(NoDataFound, match="no record"):
        cellpy.get(source="labdb", key="UNKNOWN", kind="tag", testing=True)


def test_no_record_with_filename_loads_anyway(labdb, parameters):
    c = cellpy.get(
        parameters.res_file_path,
        instrument="arbin_res",
        source="labdb",
        key="UNKNOWN",
        kind="tag",
        testing=True,
    )
    assert c is not None
    assert "labdb" not in (c.external_links or {})
    assert c.data.meta_common.mass == pytest.approx(1.0)  # the default, untouched


def test_unknown_source_is_strict_when_it_is_the_only_way(clean_registry):
    with pytest.raises(MetadataSourceError):
        cellpy.get(source="nope", key="x", kind="tag", testing=True)


def test_unknown_source_is_soft_when_a_filename_is_given(clean_registry, parameters):
    c = cellpy.get(parameters.res_file_path, instrument="arbin_res", source="nope", testing=True)
    assert c is not None


def test_file_pointers_survive_save_and_load(labdb, no_filefinder, tmp_path, parameters):
    c = cellpy.get(source="labdb", key="WITH_FILES", kind="tag", testing=True)
    path = tmp_path / "pointed.cellpy"
    c.save(path)

    loaded = cellpy.get(path, testing=True)
    link = loaded.external_links["labdb"]
    assert link.files == (pathlib.Path(parameters.res_file_path).as_posix(),)
    assert loaded.data.meta_common.mass == pytest.approx(1.23)


def test_cellpy_pointer_is_opened_directly(clean_registry, no_filefinder, tmp_path, parameters):
    saved = tmp_path / "from_pointer.cellpy"
    cellpy.get(parameters.res_file_path, instrument="arbin_res", testing=True).save(saved)
    record = _record(parameters, files=(FileRef("cellpy", saved.as_posix()),), mass=7.7)
    ms.register(DictMetadataSource({("tag", "T"): record}, name="labdb"))

    c = cellpy.get(source="labdb", key="T", kind="tag", testing=True)

    assert c.data.meta_common.mass == pytest.approx(7.7)
    assert c.external_links["labdb"].files == (saved.as_posix(),)
    # the summary was refreshed with the new mass, not left stale
    assert c.data.summary is not None and not c.data.summary.empty
