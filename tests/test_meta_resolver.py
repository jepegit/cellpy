"""MetaResolver and provenance stamping (#562, metadata plan Steps 3-4).

The resolver exists to make one question answerable: *where did this value come
from?* So most of these tests assert the recorded source, not just the value —
a resolver that picks correctly but cannot say why leaves "my batch used a
default mass for one cell in forty" just as invisible as before.
"""

from __future__ import annotations

import datetime
import logging

import pytest
from cellpycore.metadata.models import CellMeta, TestMeta

from cellpy import log
from cellpy.readers.meta_resolver import (
    Layer,
    MetaResolver,
    resolve_cell_meta,
    science_defaults_for_cell,
)
from cellpy.readers.provenance import (
    file_identity_hash,
    new_cell_uuid,
    preserve_cell_uuid,
    stamp_provenance,
)

log.setup_logging(default_level=logging.DEBUG, testing=True)


# -- precedence ----------------------------------------------------------------


@pytest.mark.essential
def test_kwargs_beat_every_other_layer():
    meta, resolution = resolve_cell_meta(
        CellMeta(),
        kwargs={"mass": 1.0},
        journal={"mass": 2.0},
        draft=CellMeta(mass=3.0),
        config_defaults={"mass": 4.0},
    )
    assert meta.mass == 1.0
    assert resolution.source_of("mass") is Layer.KWARGS


@pytest.mark.essential
def test_journal_beats_file_and_defaults():
    meta, resolution = resolve_cell_meta(
        CellMeta(),
        journal={"mass": 2.0},
        draft=CellMeta(mass=3.0),
        config_defaults={"mass": 4.0},
    )
    assert meta.mass == 2.0
    assert resolution.source_of("mass") is Layer.JOURNAL


@pytest.mark.essential
def test_file_beats_defaults():
    meta, resolution = resolve_cell_meta(
        CellMeta(), draft=CellMeta(mass=3.0), config_defaults={"mass": 4.0}
    )
    assert meta.mass == 3.0
    assert resolution.source_of("mass") is Layer.RAW_FILE


@pytest.mark.essential
def test_defaults_are_the_last_resort():
    meta, resolution = resolve_cell_meta(CellMeta(), config_defaults={"mass": 4.0})
    assert meta.mass == 4.0
    assert resolution.source_of("mass") is Layer.CONFIG_DEFAULT


@pytest.mark.essential
def test_the_acceptance_case_all_four_layers_at_once():
    """Issue #562's stated acceptance: kwarg wins, and every field reports."""
    meta, resolution = resolve_cell_meta(
        CellMeta(),
        kwargs={"mass": 1.0},
        journal={"nom_cap": 22.0},
        draft=CellMeta(material="graphite"),
        config_defaults={"cell_type": "standard"},
    )
    assert meta.mass == 1.0
    assert meta.nom_cap == 22.0
    assert meta.material == "graphite"
    assert meta.cell_type == "standard"

    assert resolution.source_of("mass") is Layer.KWARGS
    assert resolution.source_of("nom_cap") is Layer.JOURNAL
    assert resolution.source_of("material") is Layer.RAW_FILE
    assert resolution.source_of("cell_type") is Layer.CONFIG_DEFAULT


# -- "I don't know" is not "set it to None" ------------------------------------


@pytest.mark.essential
def test_a_none_in_a_higher_layer_does_not_erase_a_lower_one():
    """A journal with blank columns must not wipe what the instrument knew."""
    meta, resolution = resolve_cell_meta(
        CellMeta(),
        journal={"mass": None},
        draft=CellMeta(mass=3.0),
    )
    assert meta.mass == 3.0
    assert resolution.source_of("mass") is Layer.RAW_FILE


@pytest.mark.essential
def test_unresolved_fields_report_no_source():
    _, resolution = resolve_cell_meta(CellMeta(), kwargs={"mass": 1.0})
    assert resolution.source_of("nom_cap") is None


# -- the provenance record itself ----------------------------------------------


@pytest.mark.essential
def test_fields_from_lists_what_a_layer_contributed():
    _, resolution = resolve_cell_meta(
        CellMeta(),
        kwargs={"mass": 1.0, "nom_cap": 2.0},
        config_defaults={"cell_type": "standard"},
    )
    assert resolution.fields_from(Layer.KWARGS) == ("mass", "nom_cap")
    assert resolution.fields_from(Layer.CONFIG_DEFAULT) == ("cell_type",)


@pytest.mark.essential
def test_explain_names_the_layer_in_words():
    _, resolution = resolve_cell_meta(CellMeta(), config_defaults={"mass": 4.0})
    explanation = resolution.explain()
    assert "mass" in explanation
    assert "config default" in explanation


@pytest.mark.essential
def test_unknown_fields_are_ignored():
    """A journal column that matches nothing must not invent a field."""
    meta, resolution = resolve_cell_meta(
        CellMeta(), journal={"not_a_metadata_field": 1.0}
    )
    assert not hasattr(meta, "not_a_metadata_field")
    assert resolution.source_of("not_a_metadata_field") is None


@pytest.mark.essential
def test_resolver_accepts_dataclass_mapping_and_model_layers():
    """Layers arrive in three shapes; the resolver normalises them."""

    class ModelLike:
        def model_dump(self):
            return {"mass": 9.0}

    resolver = MetaResolver(("mass",))
    meta, resolution = resolver.resolve(config_defaults=ModelLike(), into=CellMeta())
    assert meta.mass == 9.0
    assert resolution.source_of("mass") is Layer.CONFIG_DEFAULT


# -- config defaults translation -----------------------------------------------


@pytest.mark.essential
def test_science_defaults_are_translated_to_metadata_names():
    """Config says default_mass; the model says mass."""
    import cellpy.config as config

    mapped = science_defaults_for_cell(config.defaults)
    assert "mass" in mapped
    assert "default_mass" not in mapped
    assert "nom_cap" in mapped


@pytest.mark.essential
def test_science_defaults_flow_through_the_resolver():
    import cellpy.config as config

    meta, resolution = resolve_cell_meta(
        CellMeta(), config_defaults=science_defaults_for_cell(config.defaults)
    )
    assert meta.mass is not None
    assert resolution.source_of("mass") is Layer.CONFIG_DEFAULT


# -- provenance stamping --------------------------------------------------------


@pytest.mark.essential
def test_stamp_provenance_fills_the_framework_fields(tmp_path):
    source = tmp_path / "cell.res"
    source.write_bytes(b"some raw data")

    meta = stamp_provenance(
        TestMeta(),
        source=source,
        source_type="arbin_res",
        loaded_datetime=datetime.datetime(2026, 7, 19, tzinfo=datetime.timezone.utc),
    )

    assert meta.source_kind == "file"
    assert meta.source_type == "arbin_res"
    assert meta.source_uri == str(source)
    assert meta.raw_file_names == ["cell.res"]
    assert meta.loaded_datetime.year == 2026
    assert meta.source_uuid


@pytest.mark.essential
def test_file_identity_hash_is_stable_for_the_same_file(tmp_path):
    source = tmp_path / "cell.res"
    source.write_bytes(b"identical bytes")
    assert file_identity_hash(source) == file_identity_hash(source)


@pytest.mark.essential
def test_file_identity_hash_differs_for_different_content(tmp_path):
    a = tmp_path / "a.res"
    b = tmp_path / "b.res"
    a.write_bytes(b"content one")
    b.write_bytes(b"content two")
    assert file_identity_hash(a) != file_identity_hash(b)


@pytest.mark.essential
def test_file_identity_hash_ignores_the_path(tmp_path):
    """Identity is the file's content, not where it happens to sit."""
    first = tmp_path / "one" / "cell.res"
    second = tmp_path / "two" / "renamed.res"
    for path in (first, second):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"same bytes")
    assert file_identity_hash(first) == file_identity_hash(second)


@pytest.mark.essential
def test_missing_source_does_not_break_the_load(tmp_path):
    """Loading a cellpy file whose raw has moved must still work."""
    assert file_identity_hash(tmp_path / "gone.res") is None


# -- cell uuid ------------------------------------------------------------------


@pytest.mark.essential
def test_new_cell_uuids_are_unique():
    assert new_cell_uuid() != new_cell_uuid()


@pytest.mark.essential
def test_merge_keeps_the_first_uuid_rather_than_minting_one():
    """The merged object continues that cell; a new identity would break the
    link back to files already saved from it."""

    class Holder:
        uuid = None

    original = Holder()
    original.uuid = "the-original"
    other = Holder()
    other.uuid = "the-other"

    target = Holder()
    kept = preserve_cell_uuid(target, original, other)
    assert kept == "the-original"
    assert target.uuid == "the-original"


@pytest.mark.essential
def test_uuid_is_minted_when_no_source_has_one():
    class Holder:
        uuid = None

    target = Holder()
    minted = preserve_cell_uuid(target, Holder())
    assert minted
    assert target.uuid == minted


# -- the null-object guarantee ---------------------------------------------------


@pytest.mark.essential
def test_resolving_nothing_leaves_a_usable_empty_object():
    """Engines must run on empty metadata (architecture plan §4)."""
    meta, resolution = resolve_cell_meta(CellMeta())
    assert isinstance(meta, CellMeta)
    assert resolution.sources == {}


# -- end to end through a real loader -------------------------------------------


@pytest.mark.essential
def test_resolution_end_to_end_through_the_pilot_loader():
    """The ingestion entry point, on a real file and a real loader draft.

    Unit tests above use hand-built layers; this one proves the pieces fit
    together on the path the port will actually take.
    """
    import cellpy.config as config
    import cellpy.utils.example_data as ed
    from cellpy.readers.instruments.maccor_txt_native import MaccorTxtLoader
    from cellpy.readers.meta_resolver import resolve_from_loader_result

    source = ed.maccor_file_path()
    result = MaccorTxtLoader().load(source)[0]

    cell_meta, test_meta, cell_resolution, _ = resolve_from_loader_result(
        result,
        source=source,
        source_type="maccor_txt",
        kwargs={"mass": 2.5},
        config_defaults=science_defaults_for_cell(config.defaults),
    )

    # the user's kwarg wins over the config default
    assert cell_meta.mass == 2.5
    assert cell_resolution.source_of("mass") is Layer.KWARGS
    # ... and a field only the defaults know still gets filled
    assert cell_resolution.source_of("cell_type") is Layer.CONFIG_DEFAULT

    # provenance is stamped by the framework, not by the loader
    assert test_meta.source_type == "maccor_txt"
    assert test_meta.source_uri == str(source)
    assert test_meta.source_uuid
    assert test_meta.loaded_datetime is not None


@pytest.mark.essential
def test_the_loader_draft_carried_no_provenance():
    """Restates the contract from the other side: the draft must be clean."""
    import cellpy.utils.example_data as ed
    from cellpy.readers.instruments.maccor_txt_native import MaccorTxtLoader

    draft = MaccorTxtLoader().load(ed.maccor_file_path())[0].test_meta
    assert draft.source_uri is None
    assert draft.source_uuid is None
    assert draft.loaded_datetime is None
