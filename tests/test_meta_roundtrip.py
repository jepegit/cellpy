"""Metadata round-trip and merge contracts (#563, metadata plan Steps 4-5).

cellpy 2.0 freezes the v9 on-disk metadata layout — changing it afterwards
means a v10 — so these are contract tests, not smoke tests: they assert
field-by-field equality rather than "it loaded without raising".
"""

from __future__ import annotations

import logging
import warnings
from dataclasses import fields, is_dataclass

import pytest

from cellpy import log

log.setup_logging(default_level=logging.DEBUG, testing=True)


def _field_values(model) -> dict:
    if model is None:
        return {}
    if is_dataclass(model):
        return {f.name: getattr(model, f.name) for f in fields(model)}
    return {}


def _comparable(value):
    """Normalise values that legitimately change representation on disk."""
    from pathlib import Path

    if isinstance(value, Path) or hasattr(value, "as_posix"):
        try:
            return Path(str(value)).as_posix()
        except Exception:
            return str(value)
    if isinstance(value, (list, tuple)):
        return [_comparable(item) for item in value]
    return value


def _assert_meta_equal(before, after, *, label: str, ignore: set[str] = frozenset()):
    values_before = _field_values(before)
    values_after = _field_values(after)

    assert set(values_before) == set(values_after), (
        f"{label}: the set of metadata fields changed across save/load"
    )

    differences = []
    for name, original in values_before.items():
        if name in ignore:
            continue
        restored = values_after[name]
        if _comparable(original) != _comparable(restored):
            differences.append(f"{name}: {original!r} -> {restored!r}")

    assert not differences, f"{label} changed across save/load:\n  " + "\n  ".join(
        differences
    )


@pytest.fixture
def loaded_cell():
    import cellpy.utils.example_data as ed

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ed.raw_file(testing=True)


# -- round trip -----------------------------------------------------------------


def _cell_meta(cell):
    """The CellMeta for a loaded cell.

    It hangs off the per-test records as ``.cell``; the ``c.data.meta`` facade
    the plan describes is a 2.1 target and does not exist yet, so go through
    the records rather than assume it.
    """
    records = list(cell.data.tests)
    return records[0].cell if records else None


@pytest.mark.essential
def test_cell_meta_survives_a_v9_round_trip(loaded_cell, tmp_path):
    """Field-by-field, not "it loaded"."""
    import cellpy

    target = tmp_path / "roundtrip.cellpy"
    before = _cell_meta(loaded_cell)
    assert before is not None, "fixture produced no test records"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        loaded_cell.save(target)
        reloaded = cellpy.get(target, testing=True)

    _assert_meta_equal(before, _cell_meta(reloaded), label="CellMeta")


@pytest.mark.essential
def test_test_meta_survives_a_v9_round_trip(loaded_cell, tmp_path):
    import cellpy

    target = tmp_path / "roundtrip.cellpy"
    before = list(loaded_cell.data.tests)

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        loaded_cell.save(target)
        reloaded = cellpy.get(target, testing=True)

    after = list(reloaded.data.tests)
    assert len(after) == len(before), "a test record was lost across save/load"

    for index, (original, restored) in enumerate(zip(before, after)):
        _assert_meta_equal(
            original,
            restored,
            label=f"TestMeta[{index}]",
            # loaded_datetime is re-stamped by the load itself, by design.
            ignore={"loaded_datetime", "cell"},
        )


@pytest.mark.essential
def test_raw_units_survive_a_v9_round_trip(loaded_cell, tmp_path):
    """Unit plan Phase 5: units must travel with the data."""
    import cellpy

    target = tmp_path / "roundtrip.cellpy"
    before = loaded_cell.data.raw_units

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        loaded_cell.save(target)
        reloaded = cellpy.get(target, testing=True)

    _assert_meta_equal(before, reloaded.data.raw_units, label="raw_units")


@pytest.mark.essential
def test_the_meta_document_is_versioned(loaded_cell):
    """A frozen format needs a version in it, or migration has nothing to read."""
    from cellpy.readers.cellpy_file import meta_archive

    document = meta_archive.build_meta_document(loaded_cell.data)
    assert document["schema_version"]
    assert document["cellpy_file_version"]
    # the frame schemas are versioned independently of the document
    assert document["raw_schema_version"]
    assert document["step_schema_version"]
    assert document["cycle_schema_version"]


@pytest.mark.essential
def test_the_meta_document_keeps_units_and_limits_separate(loaded_cell):
    """G3/G4: unit and limit blocks are their own keys, not prefixed rows."""
    from cellpy.readers.cellpy_file import meta_archive

    document = meta_archive.build_meta_document(loaded_cell.data)
    assert "raw_units" in document
    assert "cellpy_units" in document
    assert "limits" in document
    assert isinstance(document["tests"], dict)


# -- merge ----------------------------------------------------------------------


@pytest.mark.essential
def test_merging_preserves_both_tests_metadata():
    """Metadata plan Step 5: per-test meta survives a campaign merge."""
    import cellpy.utils.example_data as ed

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        first = ed.raw_file(testing=True)
        second = ed.raw_file(testing=True)

    before = len(list(first.data.tests)) + len(list(second.data.tests))

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        merged = first.merge(second)

    after = list(merged.data.tests)
    assert len(after) == before, (
        "merging lost a test record; per-test metadata must survive the merge"
    )


@pytest.mark.essential
def test_merging_keeps_a_single_cell_identity():
    """The merged object continues one cell — it does not become a third.

    A fresh uuid here would break the link back to files already saved from
    that cell (see cellpy.readers.provenance.preserve_cell_uuid).
    """
    import cellpy.utils.example_data as ed

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        first = ed.raw_file(testing=True)
        second = ed.raw_file(testing=True)

    original_uuid = (first.data._provenance or {}).get("uuid")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        merged = first.merge(second)

    merged_uuid = (merged.data._provenance or {}).get("uuid")
    assert merged_uuid, "merged cell has no identity"
    assert merged_uuid == original_uuid, (
        "merge minted a new cell identity instead of continuing the first"
    )
