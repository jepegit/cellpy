"""Tests for the public ``CellpyCell.schema`` header API (#558, native-headers Phase 4).

``c.schema`` is the sanctioned replacement for the legacy ``headers_*``
attributes. Its contract: whatever ``c.schema.<frame>.<column>`` returns is a
valid column key for the matching ``c.data.<frame>`` — on the native runtime
that is the native cellpy-core name, on the legacy runtime the legacy one.
"""

from __future__ import annotations

import logging
import warnings

import pytest

from cellpy import _deprecation, log
from cellpy.parameters.cell_schema import CellSchema
from cellpy.readers.cellreader import CellpyCell

log.setup_logging(default_level=logging.DEBUG, testing=True)


@pytest.fixture
def native_cell() -> CellpyCell:
    return CellpyCell()


@pytest.fixture
def legacy_cell() -> CellpyCell:
    return CellpyCell(native_schema=False)


@pytest.mark.essential
def test_schema_is_available_on_a_vacant_cell(native_cell):
    # The null-object guarantee: no data required to ask for column names.
    assert isinstance(native_cell.schema, CellSchema)
    assert native_cell.schema.raw.potential == "potential"


@pytest.mark.essential
def test_schema_frames_are_named_after_the_data_frames(native_cell):
    schema = native_cell.schema
    # raw/steps/summary — matching c.data.raw / .steps / .summary, *not*
    # cellpy-core's raw/step/cycle spelling. On the native runtime the frames
    # pass through to the core schema untouched.
    assert schema.raw is native_cell.core.schema.raw
    assert schema.steps is native_cell.core.schema.step
    assert schema.summary is native_cell.core.schema.cycle


@pytest.mark.essential
def test_schema_resolves_native_names(native_cell):
    schema = native_cell.schema
    assert schema.raw.potential == "potential"
    assert schema.steps.cycle_num == "cycle_num"
    assert schema.summary.charge_capacity == "charge_capacity"


@pytest.mark.essential
def test_schema_is_cached(native_cell):
    assert native_cell.schema is native_cell.schema


@pytest.mark.essential
def test_native_spelling_resolves_on_the_legacy_runtime(legacy_cell):
    # Native spelling everywhere; the *value* tracks the runtime. This is what
    # lets cellpy internals — which run on both runtimes — be written once.
    assert legacy_cell.schema.raw.potential == "voltage"
    assert legacy_cell.schema.raw.cycle_num == "cycle_index"
    assert legacy_cell.schema.steps.step_type == "type"
    assert legacy_cell.schema.summary.charge_capacity == "charge_capacity"


@pytest.mark.essential
def test_legacy_runtime_still_accepts_legacy_spelling(legacy_cell):
    # Unmigrated code keeps resolving on the legacy path.
    assert legacy_cell.schema.raw.voltage_txt == "voltage"


@pytest.mark.essential
def test_legacy_runtime_specific_summary_columns(legacy_cell):
    assert (
        legacy_cell.schema.summary.charge_capacity_gravimetric
        == "charge_capacity_gravimetric"
    )


@pytest.mark.essential
def test_unknown_column_raises_on_both_runtimes(native_cell, legacy_cell):
    for cell in (native_cell, legacy_cell):
        with pytest.raises(AttributeError):
            cell.schema.raw.not_a_column


@pytest.mark.essential
def test_schema_does_not_warn(native_cell):
    _deprecation._WARNED_SITES.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        native_cell.schema.raw.potential
        native_cell.schema.summary.charge_capacity
    assert not [w for w in caught if issubclass(w.category, DeprecationWarning)]


@pytest.mark.essential
@pytest.mark.parametrize(
    "legacy_attr, schema_frame, native_attr",
    [
        ("headers_normal", "raw", "potential"),
        ("headers_step_table", "steps", "cycle_num"),
        ("headers_summary", "summary", "charge_capacity"),
    ],
)
def test_legacy_shim_and_schema_agree(
    native_cell, legacy_attr, schema_frame, native_attr
):
    via_schema = getattr(getattr(native_cell.schema, schema_frame), native_attr)
    via_shim = getattr(getattr(native_cell, legacy_attr), native_attr)
    assert via_schema == via_shim


@pytest.mark.essential
def test_legacy_attribute_warns_and_names_the_schema_replacement(native_cell):
    _deprecation._WARNED_SITES.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        value = native_cell.headers_normal.voltage_txt

    assert value == native_cell.schema.raw.potential
    messages = [
        str(w.message) for w in caught if issubclass(w.category, DeprecationWarning)
    ]
    assert len(messages) == 1
    # The warning must name the exact attribute to type, not the concept.
    assert "c.schema.raw.potential" in messages[0]


@pytest.mark.essential
def test_core_pipeline_does_not_trip_its_own_deprecation(dataset):
    """cellpy's own code must be migrated off ``headers_*`` (#558).

    Guards the failure mode found while migrating: dropping a local
    ``hdr = self.headers_step_table`` binding silently re-resolved a later use
    to the module-level *legacy* singleton, which indexes a native frame with
    legacy names. A warning from inside cellpy means a site is still on the
    shim — or has fallen through to the legacy singleton.
    """
    _deprecation._WARNED_SITES.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        dataset.make_step_table()
        dataset.make_summary()
        dataset._validate_step_table()

    offenders = [
        str(w.message)
        for w in caught
        if issubclass(w.category, DeprecationWarning)
        and "headers_" in str(w.message)
    ]
    assert not offenders, f"cellpy internals still on the header shim: {offenders}"


@pytest.mark.essential
def test_schema_columns_are_keys_into_the_frames(dataset):
    """The contract, end to end: schema names index the real frames."""
    schema = dataset.schema
    assert schema.raw.potential in dataset.data.raw.columns
    assert schema.summary.charge_capacity in dataset.data.summary.columns
    assert schema.steps.cycle_num in dataset.data.steps.columns
