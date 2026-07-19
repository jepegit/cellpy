"""Golden regression tests for the ICA (dQ/dV) pipeline (#566).

These are the numeric net under the ICA redesign: the recipe is a chain of
order-sensitive operations (interpolate V(q) → optional pre-smooth → invert to
q(V) → optional smooth → differentiate → optional gaussian → normalize), and
reordering any two of them still yields a plausibly-shaped curve. Only values
catch that.
"""

from __future__ import annotations

import json

import pandas as pd
import pytest

from tests.ica_golden_support import (
    ICA_GOLDEN_CASES,
    IcaGoldenCase,
    assert_ica_matches_golden,
    capture_ica_case,
)


def _ica_case_id(case: IcaGoldenCase) -> str:
    return case.suite


@pytest.mark.essential
@pytest.mark.parametrize("case", ICA_GOLDEN_CASES, ids=_ica_case_id)
def test_ica_output_matches_golden(case: IcaGoldenCase):
    reason = case.skip_reason()
    if reason:
        pytest.skip(reason)

    expected = pd.read_parquet(case.golden_dir / "ica.parquet")
    actual, _ = capture_ica_case(case)
    assert_ica_matches_golden(actual, expected)


@pytest.mark.essential
@pytest.mark.parametrize("case", ICA_GOLDEN_CASES, ids=_ica_case_id)
def test_ica_metrics_match_golden(case: IcaGoldenCase):
    reason = case.skip_reason()
    if reason:
        pytest.skip(reason)

    expected = json.loads((case.golden_dir / "metrics.json").read_text(encoding="utf-8"))
    _, actual = capture_ica_case(case)

    assert actual["n_rows"] == expected["n_rows"]
    assert actual["n_columns"] == expected["n_columns"]
    assert actual["columns"] == expected["columns"]

    # Compared with a tolerance, not exactly: this first failed on Linux with
    # 122.614595 against a golden of 122.614594 recorded on Windows. Rounding
    # the stored value does not help - a total that lands near the rounding
    # boundary still flips. See the note in ica_golden_support for the measured
    # cross-platform spread.
    assert set(actual["sums"]) == set(expected["sums"])
    for column, value in expected["sums"].items():
        assert actual["sums"][column] == pytest.approx(value, rel=1e-5), column
