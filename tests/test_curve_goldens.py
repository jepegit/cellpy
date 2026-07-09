"""Golden regression tests for get_cap-family curve extraction snapshots."""

from __future__ import annotations

import json

import pandas as pd
import pytest
from cellpy.exceptions import NullData

from tests.curve_golden_support import (
    CURVE_GOLDEN_CASES,
    CurveGoldenCase,
    _call_curve_func,
    assert_curve_matches_golden,
    capture_curve_case,
    load_golden_cell,
    read_null_data_descriptor,
    run_curve_case,
)


def _curve_case_id(case: CurveGoldenCase) -> str:
    return case.suite


@pytest.mark.essential
@pytest.mark.parametrize("case", CURVE_GOLDEN_CASES, ids=_curve_case_id)
def test_curve_extraction_matches_golden(case: CurveGoldenCase):
    reason = case.skip_reason()
    if reason:
        pytest.skip(reason)

    if case.expect_null_data:
        with pytest.raises(NullData):
            cell = load_golden_cell()
            _call_curve_func(cell, case)
        expected = read_null_data_descriptor(case.golden_dir / "null_data.json")
        _, _, actual_null = capture_curve_case(case)
        assert actual_null is not None
        assert actual_null["exception"] == expected["exception"]
        assert expected["message"] in actual_null["message"]
        return

    expected = pd.read_parquet(case.golden_dir / "curve.parquet")
    actual = run_curve_case(case)
    assert_curve_matches_golden(actual, expected)


@pytest.mark.essential
@pytest.mark.parametrize("case", CURVE_GOLDEN_CASES, ids=_curve_case_id)
def test_curve_metrics_match_golden(case: CurveGoldenCase):
    reason = case.skip_reason()
    if reason:
        pytest.skip(reason)

    expected = json.loads(
        (case.golden_dir / "metrics.json").read_text(encoding="utf-8")
    )
    frame, metrics, null_data = capture_curve_case(case)
    assert metrics == expected
    if case.expect_null_data:
        assert frame is None
        assert null_data is not None
    else:
        assert frame is not None
        assert null_data is None
