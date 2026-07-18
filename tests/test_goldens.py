"""Golden-fixture regression tests for cellpy-side characterization oracles.

Fixtures live under ``tests/data/goldens/`` and are regenerated only via
``dev/regenerate_goldens.py``. See ``tests/README.md``.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from cellpy import cellreader
from tests.golden_support import assert_summary_matches_golden

REPO_ROOT = Path(__file__).resolve().parents[1]
GOLDENS_ROOT = REPO_ROOT / "tests" / "data" / "goldens"
RES_FILE = REPO_ROOT / "testdata" / "data" / "20160805_test001_45_cc_01.res"

PIPELINE_SMOKE_DIR = GOLDENS_ROOT / "pipeline_smoke"
PIPELINE_SMOKE_SUMMARY = PIPELINE_SMOKE_DIR / "summary.parquet"
PIPELINE_SMOKE_METRICS = PIPELINE_SMOKE_DIR / "metrics.json"


def _pipeline_smoke_inputs_available() -> bool:
    return (
        RES_FILE.is_file()
        and PIPELINE_SMOKE_SUMMARY.is_file()
        and PIPELINE_SMOKE_METRICS.is_file()
    )


def _run_pipeline_smoke() -> tuple[pd.DataFrame, pd.DataFrame, str]:
    cell = cellreader.CellpyCell()
    cell.from_raw(str(RES_FILE))
    cell.mass = 1.0
    cell.make_step_table()
    cell.make_summary()
    summary = cell.data.summary.reset_index(drop=True)
    steps = cell.data.steps.reset_index(drop=True)
    # summary per-cycle datapoint column (native name via the header shim)
    return summary, steps, cell.headers_summary.data_point


@pytest.mark.essential
def test_pipeline_smoke_metrics_match_golden():
    if not _pipeline_smoke_inputs_available():
        pytest.skip("pipeline_smoke goldens or Arbin .res testdata not available")

    expected = json.loads(PIPELINE_SMOKE_METRICS.read_text(encoding="utf-8"))
    summary, steps, datapoint_col = _run_pipeline_smoke()

    actual = {
        "n_steps": len(steps),
        "n_cycles": len(summary),
        "cycle1_data_point": int(summary.loc[summary.index[0], datapoint_col]),
    }
    assert actual["n_steps"] == expected["n_steps"]
    assert actual["n_cycles"] == expected["n_cycles"]
    assert actual["cycle1_data_point"] == expected["cycle1_data_point"]


@pytest.mark.essential
def test_pipeline_smoke_summary_matches_golden_parquet():
    if not _pipeline_smoke_inputs_available():
        pytest.skip("pipeline_smoke goldens or Arbin .res testdata not available")

    expected = pd.read_parquet(PIPELINE_SMOKE_SUMMARY)
    summary, _ = _run_pipeline_smoke()
    assert_summary_matches_golden(summary, expected)
