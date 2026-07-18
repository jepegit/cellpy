"""Round-trip / totality tests for the dormant ``cellpy_file.translate`` layer.

Native-headers plan Phase 1 (issue #458, Stage 1.15): the translation is
dormant on v1.x — these tests are what keep it correct until the Phase-3 flip
wires it into ``cellpy_file.load``:

1. v8 golden file → ``to_native`` → ``to_legacy`` reproduces every frame
   exactly (columns, order, values — lossless by construction).
2. Totality: every column in the golden v8 frames is classified (mapped or
   documented legacy-only) — an unclassified column fails until deliberately
   categorized in the core mapping.
3. The Stage-0 value-parity comparator (#434) is green between the legacy
   frames and their translated native twins.
"""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from cellpy import cellreader, log
from cellpy.readers.cellpy_file import translate
from tests import fdv
from tests.parity import assert_value_parity

log.setup_logging(default_level="DEBUG", testing=True)


@pytest.fixture(scope="module")
def golden_frames():
    # translate round-trips start from legacy-named frames; load on the legacy
    # path so the boundary to_native() does not run first.
    cell = cellreader.CellpyCell(native_schema=False)
    cell.load(fdv.cellpy_file_path)
    return {
        "raw": cell.data.raw.copy(),
        "steps": cell.data.steps.copy(),
        "summary": cell.data.summary.copy(),
    }


class _FrameCarrier:
    """Minimal Data stand-in: the translate layer only touches the frames."""

    def __init__(self, frames):
        self.raw = frames["raw"].copy()
        self.steps = frames["steps"].copy()
        self.summary = frames["summary"].copy()


def test_v8_round_trip_is_lossless(golden_frames):
    carrier = _FrameCarrier(golden_frames)
    translate.to_native(carrier)

    # native side really is native (and carries the injected test_id)
    assert "datapoint_num" in carrier.raw.columns
    assert "cycle_num" in carrier.steps.columns
    assert "cycle_num" in carrier.summary.columns
    assert (carrier.steps["test_id"] == 0).all()
    assert (carrier.summary["test_id"] == 0).all()

    translate.to_legacy(carrier)
    for family in ("raw", "steps", "summary"):
        assert_frame_equal(
            getattr(carrier, family), golden_frames[family], check_dtype=True
        )


def test_totality_every_golden_column_is_classified(golden_frames):
    unknown = {}
    for family in ("raw", "steps", "summary"):
        classified = translate.classify_legacy_columns(
            golden_frames[family].columns, family
        )
        bad = [col for col, kind in classified.items() if kind == "unknown"]
        if bad:
            unknown[family] = bad
    assert not unknown, f"unclassified legacy columns: {unknown}"


@pytest.mark.parametrize("family", ["raw", "steps", "summary"])
def test_value_parity_comparator_green_through_translation(golden_frames, family):
    carrier = _FrameCarrier(golden_frames)
    translate.to_native(carrier)
    assert_value_parity(golden_frames[family], getattr(carrier, family), family)


def test_summary_specific_columns_translate_both_ways(golden_frames):
    summary = golden_frames["summary"]
    native = translate.summary_to_native(summary)
    # a specific variant translated to its native name
    assert "test_cumulated_charge_capacity_gravimetric" in native.columns
    back = translate.summary_to_legacy(native)
    assert list(back.columns) == list(summary.columns)


def test_classify_rejects_unknown_family():
    with pytest.raises(ValueError, match="family"):
        translate.classify_legacy_columns(["a"], "bogus")
