"""Real value-parity oracle: native pipeline vs legacy pipeline (issue #434).

Native-headers flip Stage 6. Runs the **full independent** native pipeline
(``CellpyCell(native_schema=True)``, the cellpy 2 default) and the legacy bridge
pipeline (``native_schema=False``) on the canonical Arbin ``.res``, then asserts
their frames carry equal values on every **mapped** column
(``tests.parity.assert_value_parity`` compares through
``cellpycore.legacy.mapping``). Columns the native pipeline does not produce
(e.g. shifted / RIC / cumulated-CE, tracked in #552) are skipped automatically;
columns that deliberately differ are listed in the exception sets below.
"""

from __future__ import annotations

import pytest

from cellpy import cellreader
from tests.parity import assert_value_parity
from tests.parity_support import (
    res_file_available,
    run_legacy_pipeline,
    run_native_pipeline,
)

# Documented intended divergences (native-headers plan §7 register): mapped
# columns present on both frames whose values deliberately differ between the
# corrected native pipeline and the legacy bridge. Keep this list tight — every
# entry is a known, reviewed semantic difference, not a bug to hide.
RAW_EXCEPTIONS: tuple[str, ...] = ()
STEP_EXCEPTIONS: tuple[str, ...] = ()
SUMMARY_EXCEPTIONS: tuple[str, ...] = ()


@pytest.fixture(scope="module")
def pipelines():
    if not res_file_available():
        pytest.skip("canonical Arbin .res testdata not available")
    legacy = cellreader.CellpyCell(native_schema=False)
    run_legacy_pipeline(legacy)
    native = cellreader.CellpyCell(native_schema=True)
    run_native_pipeline(native)
    return legacy, native


@pytest.mark.essential
def test_value_parity_raw(pipelines):
    legacy, native = pipelines
    assert_value_parity(
        legacy.data.raw.reset_index(drop=True),
        native.data.raw.reset_index(drop=True),
        "raw",
        exceptions=RAW_EXCEPTIONS,
    )


@pytest.mark.essential
def test_value_parity_steps(pipelines):
    legacy, native = pipelines
    assert_value_parity(
        legacy.data.steps.reset_index(drop=True),
        native.data.steps.reset_index(drop=True),
        "steps",
        exceptions=STEP_EXCEPTIONS,
    )


@pytest.mark.essential
def test_value_parity_summary(pipelines):
    legacy, native = pipelines
    assert_value_parity(
        legacy.data.summary.reset_index(drop=True),
        native.data.summary.reset_index(drop=True),
        "summary",
        exceptions=SUMMARY_EXCEPTIONS,
    )
