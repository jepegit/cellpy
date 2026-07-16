"""Contract tests for the legacy <-> core metadata field mapping.

``cellpycore.legacy.meta_mapping`` pins cellpy's legacy metadata field
inventories as frozensets (core cannot import cellpy). Its docstring assigns
cellpy the job of guarding that those pinned lists match the real legacy
dataclasses — these are those guards (issue #506; same arrangement as the
header-mapping contract tests).
"""

import dataclasses

import pytest

from cellpycore.legacy import meta_mapping
from cellpycore.metadata.models import CellMeta, TestMeta

from cellpy.parameters.internal_settings import (
    CellpyMetaCommon,
    CellpyMetaIndividualTest,
)


def _field_names(cls) -> set:
    return {f.name for f in dataclasses.fields(cls)}


@pytest.mark.essential
def test_pinned_common_fields_match_dataclass():
    assert meta_mapping.LEGACY_COMMON_FIELDS == _field_names(CellpyMetaCommon)


@pytest.mark.essential
def test_pinned_individual_fields_match_dataclass():
    # ``schedule_file_name`` is deliberately an un-annotated class attribute in
    # the legacy dataclass (so ``asdict`` drops it) but still carries data and
    # participates in the mapping — compare fields plus that documented attr.
    assert (
        _field_names(CellpyMetaIndividualTest)
        == meta_mapping.LEGACY_INDIVIDUAL_FIELDS - {"schedule_file_name"}
    )
    assert hasattr(CellpyMetaIndividualTest, "schedule_file_name")
    assert "schedule_file_name" not in _field_names(CellpyMetaIndividualTest)


@pytest.mark.essential
def test_mapping_totality_legacy_side():
    """Every legacy field appears exactly once across pair tables + LEGACY_ONLY."""
    mapped_common = [lf for lf, _ in meta_mapping.COMMON_TO_CELL_PAIRS] + [
        lf for lf, _ in meta_mapping.COMMON_TO_TEST_PAIRS
    ]
    mapped_individual = [lf for lf, _ in meta_mapping.INDIVIDUAL_TO_TEST_PAIRS]
    legacy_only = set(meta_mapping.LEGACY_ONLY)

    assert len(mapped_common) == len(set(mapped_common)), "duplicate common mapping"
    assert len(mapped_individual) == len(set(mapped_individual)), (
        "duplicate individual mapping"
    )
    assert set(mapped_common) & legacy_only == set()
    assert (
        set(mapped_common) | legacy_only == meta_mapping.LEGACY_COMMON_FIELDS
    ), "common fields not fully covered"
    assert set(mapped_individual) == meta_mapping.LEGACY_INDIVIDUAL_FIELDS, (
        "individual fields not fully covered"
    )


@pytest.mark.essential
def test_mapping_totality_core_side():
    """Every CellMeta / TestMeta field is a pair target or documented core-only."""
    cell_targets = {cf for _, cf in meta_mapping.COMMON_TO_CELL_PAIRS}
    test_targets = {cf for _, cf in meta_mapping.COMMON_TO_TEST_PAIRS} | {
        cf for _, cf in meta_mapping.INDIVIDUAL_TO_TEST_PAIRS
    }
    assert cell_targets | meta_mapping.CORE_ONLY_CELL == _field_names(CellMeta)
    assert test_targets | meta_mapping.CORE_ONLY_TEST == _field_names(TestMeta)


@pytest.mark.essential
def test_translation_smoke_defaults():
    """Default legacy boxes translate to a single-test (test_id=0) TestMeta."""
    cell, test = meta_mapping.legacy_meta_to_core(
        CellpyMetaCommon(), CellpyMetaIndividualTest()
    )
    assert isinstance(cell, CellMeta)
    assert isinstance(test, TestMeta)
    assert test.test_id == 0
    # cycle_mode default flows from cellpy config through the mapping
    assert test.cycle_mode == CellpyMetaIndividualTest().cycle_mode
