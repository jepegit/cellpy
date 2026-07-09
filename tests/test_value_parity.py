"""Trivial-pass value-parity tests for the legacy bridge (issue #434)."""

from __future__ import annotations

import pytest

from tests.parity import assert_value_parity
from tests.parity_support import (
    build_native_raw,
    build_native_steps,
    build_native_summary,
    res_file_available,
    run_legacy_pipeline,
)


@pytest.fixture
def parity_cell(cellpy_data_instance):
    if not res_file_available():
        pytest.skip("canonical Arbin .res testdata not available")
    run_legacy_pipeline(cellpy_data_instance)
    return cellpy_data_instance


@pytest.mark.essential
def test_value_parity_raw_bridge_trivial_pass(parity_cell):
    legacy_raw = parity_cell.data.raw.reset_index(drop=True)
    native_raw = build_native_raw(parity_cell)
    assert_value_parity(legacy_raw, native_raw, "raw")


@pytest.mark.essential
def test_value_parity_steps_bridge_trivial_pass(parity_cell):
    legacy_steps = parity_cell.data.steps.reset_index(drop=True)
    native_steps = build_native_steps(parity_cell)
    assert_value_parity(legacy_steps, native_steps, "steps")


@pytest.mark.essential
def test_value_parity_summary_bridge_trivial_pass(parity_cell):
    legacy_summary = parity_cell.data.summary.reset_index(drop=True)
    native_summary = build_native_summary(parity_cell)
    assert_value_parity(legacy_summary, native_summary, "summary")
