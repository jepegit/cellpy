"""External metadata sources (#784, Epic M / M1): contract, registry, resolver hook.

The read path in one sentence: a source answers a `MetaQuery` with
`MetaRecord`s, `fetch_meta` degrades failures to an empty layer, the resolver
merges records into the journal/db layer below the journal row, and the cell
keeps an `ExternalLink` so the fetch is reproducible after save/load.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

import pytest
from cellpycore.metadata.models import CellMeta, TestMeta

from cellpy import log
from cellpy.readers import metadata_sources as ms
from cellpy.readers.cellpy_file import meta_archive
from cellpy.readers.meta_resolver import Layer, resolve_cell_meta, resolve_test_meta
from cellpy.readers.metadata_sources import (
    ExternalLink,
    MetadataSource,
    MetadataSourceAuthError,
    MetadataSourceError,
    MetaQuery,
    MetaRecord,
    SupportsMetadataPush,
    UnknownMetadataSource,
    fetch_meta,
    validate_record,
)
from cellpy.readers.metadata_sources import registry as registry_module
from cellpy.readers.metadata_sources.testing import (
    DictMetadataSource,
    check_metadata_source,
)

log.setup_logging(default_level=logging.DEBUG, testing=True)

RECORD = MetaRecord(
    "labdb",
    external_id="42",
    source_uri="https://labdb.test/api/cell/42/",
    cell={"mass": 1.23, "nom_cap": 3.5, "active_electrode_area": 1.767},
    test={"cell_name": "SAL_010", "test_family": "formation"},
)


@pytest.fixture
def clean_registry(monkeypatch):
    monkeypatch.setattr(registry_module, "_iter_entry_points", lambda: ())
    ms.clear_registry()
    yield
    ms.clear_registry()


@pytest.fixture
def labdb(clean_registry) -> DictMetadataSource:
    source = DictMetadataSource({("cell_name", "SAL_010"): RECORD, ("tag", "SAL_010"): RECORD}, name="labdb")
    ms.register(source)
    return source


# -- contract ------------------------------------------------------------------


@pytest.mark.essential
def test_protocol_is_structural():
    class Source:
        name = "x"

        def fetch(self, query):
            return ()

    class Pusher(Source):
        def register(self, record):
            return "id"

    assert isinstance(Source(), MetadataSource)
    assert not isinstance(Source(), SupportsMetadataPush)
    assert isinstance(Pusher(), SupportsMetadataPush)
    assert not isinstance(object(), MetadataSource)


def test_record_fields_and_link():
    assert RECORD.fields == ("active_electrode_area", "cell_name", "mass", "nom_cap", "test_family")
    link = RECORD.link()
    assert link.source_name == "labdb" and link.external_id == "42"
    assert ExternalLink.from_dict(link.to_dict()) == link
    assert MetaRecord("x").is_empty()


def test_query_describe_and_extra_copy():
    extra = {"b": 2, "a": 1}
    q = MetaQuery(key="k", kind="tag", project="P", extra=extra)
    extra["c"] = 3
    assert "c" not in q.extra
    assert q.describe() == "tag='k', project='P', a=1, b=2"


@pytest.mark.parametrize(
    ("record", "fragment"),
    [
        (MetaRecord("x", cell={"mas": 1.0}), "not metadata fields"),
        (MetaRecord("x", test={"uuid": "abc"}), "provenance"),
        (MetaRecord("x", cell={"mass": None}), "None"),
        (MetaRecord("", cell={"mass": 1.0}), "source_name"),
        ("not a record", "MetaRecord instances"),
    ],
)
def test_validate_record_rejects_broken_promises(record, fragment):
    with pytest.raises(MetadataSourceError, match=fragment):
        validate_record(record)


def test_validate_record_accepts_real_fields():
    assert validate_record(RECORD) is RECORD


# -- registry ------------------------------------------------------------------


def test_register_and_get_source(labdb):
    assert ms.names() == ("labdb",)
    assert ms.get_source("labdb") is labdb


def test_unknown_source_names_known_ones(labdb):
    with pytest.raises(UnknownMetadataSource, match="known: labdb"):
        ms.get_source("nope")


def test_register_rejects_class_without_name(clean_registry):
    class Nameless:
        def fetch(self, query):
            return ()

    with pytest.raises(MetadataSourceError, match="name"):
        ms.register(Nameless)


def test_register_rejects_class_without_fetch(clean_registry):
    class NoFetch:
        name = "nofetch"

    with pytest.raises(MetadataSourceError, match="fetch"):
        ms.register(NoFetch)


def test_class_registration_instantiates_once(clean_registry):
    made = []

    class Source:
        name = "counted"

        def __init__(self):
            made.append(self)

        def fetch(self, query):
            return ()

    ms.register(Source)
    assert ms.get_source("counted") is ms.get_source("counted")
    assert len(made) == 1


def test_entry_point_discovery_skips_broken_plugins(monkeypatch, caplog):
    class Good:
        name = "good"

        def fetch(self, query):
            return ()

    class EP:
        def __init__(self, name, value, load):
            self.name, self.value, self._load = name, value, load

        def load(self):
            return self._load()

    def boom():
        raise ImportError("no such module")

    class BadContract:
        name = "bad"

    eps = (
        EP("good", "pkg:Good", lambda: Good),
        EP("broken", "pkg:Broken", boom),
        EP("bad", "pkg:Bad", lambda: BadContract),
    )
    monkeypatch.setattr(registry_module, "_iter_entry_points", lambda: eps)
    ms.clear_registry()
    try:
        with caplog.at_level(logging.WARNING):
            assert ms.names() == ("good",)
        assert "could not load metadata source 'broken'" in caplog.text
        assert "does not satisfy the MetadataSource contract" in caplog.text
    finally:
        ms.clear_registry()


# -- fetch_meta null object ----------------------------------------------------


@pytest.mark.essential
def test_fetch_meta_returns_validated_records_with_timestamp(labdb):
    (record,) = fetch_meta("labdb", "SAL_010")
    assert record.cell["mass"] == 1.23
    assert record.fetched_at is not None
    assert labdb.queries[-1] == MetaQuery(key="SAL_010")


def test_fetch_meta_unknown_key_is_empty(labdb):
    assert fetch_meta("labdb", MetaQuery(key="nope", kind="tag")) == ()


@pytest.mark.essential
def test_fetch_meta_unknown_source_is_empty_layer_unless_strict(clean_registry, caplog):
    with caplog.at_level(logging.WARNING):
        assert fetch_meta("ghost", "SAL_010") == ()
    assert "unavailable" in caplog.text
    with pytest.raises(UnknownMetadataSource):
        fetch_meta("ghost", "SAL_010", strict=True)


def test_fetch_meta_unreachable_source_is_empty_layer(clean_registry, caplog):
    class Offline:
        name = "offline"

        def fetch(self, query):
            raise ConnectionError("network is down")

    ms.register(Offline)
    with caplog.at_level(logging.WARNING):
        assert fetch_meta("offline", "SAL_010") == ()
    assert "network is down" in caplog.text
    with pytest.raises(MetadataSourceError, match="network is down"):
        fetch_meta("offline", "SAL_010", strict=True)


@pytest.mark.essential
def test_fetch_meta_auth_error_is_never_swallowed(clean_registry):
    class Locked:
        name = "locked"

        def fetch(self, query):
            raise MetadataSourceAuthError("token rejected")

    ms.register(Locked)
    with pytest.raises(MetadataSourceAuthError, match="token rejected"):
        fetch_meta("locked", "SAL_010")


def test_fetch_meta_drops_invalid_records_unless_strict(clean_registry, caplog):
    bad = MetaRecord("sloppy", cell={"mas": 1.0})
    ms.register(DictMetadataSource({"k": (bad, MetaRecord("sloppy", cell={"mass": 2.0}))}, name="sloppy"))
    with caplog.at_level(logging.WARNING):
        records = fetch_meta("sloppy", "k")
    assert [r.cell for r in records] == [{"mass": 2.0}]
    assert "dropping the record" in caplog.text
    with pytest.raises(MetadataSourceError, match="not metadata fields"):
        fetch_meta("sloppy", "k", strict=True)


def test_fetch_meta_accepts_source_object(clean_registry):
    source = DictMetadataSource({"k": RECORD}, name="direct")
    assert fetch_meta(source, "k")[0].external_id == "42"


# -- resolver hook -------------------------------------------------------------


@pytest.mark.essential
def test_external_beats_raw_file_and_defaults_but_not_journal_or_kwargs():
    meta, res = resolve_cell_meta(
        CellMeta(),
        kwargs={"nom_cap": 9.0},
        journal={"mass": 2.0},
        external=RECORD,  # mass 1.23, nom_cap 3.5, area 1.767
        draft=CellMeta(mass=3.0, nom_cap=1.0, active_electrode_area=0.5),
        config_defaults={"mass": 4.0},
    )
    assert (meta.mass, meta.nom_cap, meta.active_electrode_area) == (2.0, 9.0, 1.767)
    assert res.source_of("mass") is Layer.JOURNAL and res.origin_of("mass") == "journal"
    assert res.source_of("nom_cap") is Layer.KWARGS and res.origin_of("nom_cap") is None
    assert res.source_of("active_electrode_area") is Layer.JOURNAL
    assert res.origin_of("active_electrode_area") == "labdb"
    assert res.fields_from_origin("labdb") == ("active_electrode_area",)
    assert "active_electrode_area: journal/db (labdb)" in res.explain()


def test_external_sources_are_applied_in_priority_order():
    first = MetaRecord("primary", cell={"mass": 1.0})
    second = MetaRecord("secondary", cell={"mass": 2.0, "nom_cap": 5.0})
    meta, res = resolve_cell_meta(CellMeta(), external=[first, second])
    assert meta.mass == 1.0 and meta.nom_cap == 5.0
    assert res.origin_of("mass") == "primary" and res.origin_of("nom_cap") == "secondary"


def test_external_test_fields_reach_test_meta_only():
    cell, _ = resolve_cell_meta(CellMeta(), external=RECORD)
    test, res = resolve_test_meta(TestMeta(), external=RECORD)
    assert test.cell_name == "SAL_010" and test.test_family == "formation"
    assert not hasattr(cell, "cell_name")
    assert res.origin_of("cell_name") == "labdb"


def test_external_accepts_name_mapping_pairs_and_rejects_junk():
    meta, res = resolve_cell_meta(CellMeta(), external=[("sheet", {"mass": 7.0})])
    assert meta.mass == 7.0 and res.origin_of("mass") == "sheet"
    with pytest.raises(TypeError):
        resolve_cell_meta(CellMeta(), external=[42])


def test_no_external_keeps_old_provenance_shape():
    _, res = resolve_cell_meta(CellMeta(), journal={"mass": 2.0})
    assert res.origins == {}
    assert res.explain() == "resolved metadata:\n  mass: journal/db"


# -- conformance kit -----------------------------------------------------------


def test_conformance_kit_passes_for_dict_source():
    source = DictMetadataSource({("tag", "SAL_010"): RECORD}, name="labdb")
    records = check_metadata_source(
        source,
        known=MetaQuery(key="SAL_010", kind="tag"),
        unknown=MetaQuery(key="nope", kind="tag"),
    )
    assert records == (RECORD,)


def test_conformance_kit_names_the_broken_promise():
    class RaisesOnUnknown:
        name = "raiser"

        def fetch(self, query):
            if query.key == "nope":
                raise KeyError(query.key)
            return (MetaRecord("raiser", cell={"mass": 1.0}),)

    with pytest.raises(AssertionError, match="unknown key"):
        check_metadata_source(RaisesOnUnknown(), known=MetaQuery(key="k"), unknown=MetaQuery(key="nope"))

    class WrongName:
        name = "right"

        def fetch(self, query):
            return () if query.key == "nope" else (MetaRecord("wrong", cell={"mass": 1.0}),)

    with pytest.raises(AssertionError, match="source_name"):
        check_metadata_source(WrongName(), known=MetaQuery(key="k"), unknown=MetaQuery(key="nope"))


# -- CellpyCell surface --------------------------------------------------------


@pytest.mark.essential
def test_cell_fetch_meta_applies_record_and_links(cell, labdb):
    cell.cell_name = "SAL_010"
    before = cell.data.meta_common.nom_cap
    records = cell.fetch_meta("labdb")
    assert len(records) == 1
    assert cell.data.meta_common.mass == pytest.approx(1.23)
    assert cell.data.meta_common.nom_cap == pytest.approx(3.5)
    assert cell.data.meta_common.nom_cap != before or before == 3.5
    assert cell.data.meta_common.active_electrode_area == pytest.approx(1.767)
    link = cell.external_links["labdb"]
    assert isinstance(link, ExternalLink)
    assert link.external_id == "42" and link.source_uri.endswith("/cell/42/")
    assert "mass" in link.fields and "cell_name" in link.fields
    assert labdb.queries[-1].key == "SAL_010"


def test_cell_fetch_meta_no_match_changes_nothing(cell, labdb):
    mass = cell.data.meta_common.mass
    assert cell.fetch_meta("labdb", "unknown-cell") == ()
    assert cell.data.meta_common.mass == mass
    assert cell.external_links == {}


def test_cell_fetch_meta_apply_false_only_returns(cell, labdb):
    mass = cell.data.meta_common.mass
    records = cell.fetch_meta("labdb", "SAL_010", apply=False)
    assert records and cell.data.meta_common.mass == mass
    assert cell.external_links == {}


def test_cell_fetch_meta_unknown_source_is_soft_unless_strict(cell, clean_registry):
    assert cell.fetch_meta("ghost", "SAL_010") == ()
    with pytest.raises(UnknownMetadataSource):
        cell.fetch_meta("ghost", "SAL_010", strict=True)


def test_cell_fetch_meta_passes_kind_project_and_extra(cell, labdb):
    cell.fetch_meta("labdb", "SAL_010", kind="tag", project="LongLife", include_batch=True)
    q = labdb.queries[-1]
    assert (q.kind, q.project, q.extra) == ("tag", "LongLife", {"include_batch": True})


def test_external_links_survive_v9_meta_document(cell, labdb):
    cell.fetch_meta("labdb", "SAL_010")
    doc = meta_archive.build_meta_document(cell.data)
    assert doc["external_links"]["labdb"]["external_id"] == "42"

    from cellpy.readers.data_structures import Data

    fresh = Data()
    meta_archive.apply_meta_document(fresh, doc)
    assert fresh.external_links["labdb"] == cell.external_links["labdb"]


def test_external_links_survive_save_and_load(cell, labdb, tmp_path):
    cell.fetch_meta("labdb", "SAL_010")
    path = tmp_path / "linked.cellpy"
    cell.save(path)

    import cellpy

    loaded = cellpy.get(path)
    assert loaded.external_links["labdb"].external_id == "42"
    assert loaded.data.meta_common.mass == pytest.approx(1.23)
