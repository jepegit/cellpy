"""Golden regression tests for tier-1 loader raw-output snapshots."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from tests.loader_golden_support import (
    LOADER_GOLDEN_SPECS,
    LoaderGoldenSpec,
    assert_raw_matches_golden,
    load_loader_snapshot,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def _loader_golden_ids(spec: LoaderGoldenSpec) -> str:
    return spec.suite


@pytest.mark.essential
@pytest.mark.parametrize("spec", LOADER_GOLDEN_SPECS, ids=_loader_golden_ids)
def test_loader_raw_matches_golden_parquet(spec: LoaderGoldenSpec):
    reason = spec.skip_reason()
    if reason:
        pytest.skip(reason)

    expected = pd.read_parquet(spec.golden_dir / "raw.parquet")
    raw, _, _ = load_loader_snapshot(spec)
    assert_raw_matches_golden(raw, expected)


@pytest.mark.essential
@pytest.mark.parametrize("spec", LOADER_GOLDEN_SPECS, ids=_loader_golden_ids)
def test_loader_raw_units_match_golden(spec: LoaderGoldenSpec):
    reason = spec.skip_reason()
    if reason:
        pytest.skip(reason)

    expected = json.loads(
        (spec.golden_dir / "raw_units.json").read_text(encoding="utf-8")
    )
    _, meta, _ = load_loader_snapshot(spec)
    assert meta["raw_units"] == expected


@pytest.mark.essential
@pytest.mark.parametrize("spec", LOADER_GOLDEN_SPECS, ids=_loader_golden_ids)
def test_loader_meta_matches_golden(spec: LoaderGoldenSpec):
    reason = spec.skip_reason()
    if reason:
        pytest.skip(reason)

    expected = json.loads((spec.golden_dir / "meta.json").read_text(encoding="utf-8"))
    _, meta, _ = load_loader_snapshot(spec)
    actual = {
        "meta_common": meta["meta_common"],
        "meta_test_dependent": meta["meta_test_dependent"],
        "raw_limits": meta["raw_limits"],
    }
    if "custom_info" in meta:
        actual["custom_info"] = meta["custom_info"]
    assert actual == expected


@pytest.mark.essential
@pytest.mark.parametrize("spec", LOADER_GOLDEN_SPECS, ids=_loader_golden_ids)
def test_loader_metrics_match_golden(spec: LoaderGoldenSpec):
    reason = spec.skip_reason()
    if reason:
        pytest.skip(reason)

    expected = json.loads(
        (spec.golden_dir / "metrics.json").read_text(encoding="utf-8")
    )
    _, _, metrics = load_loader_snapshot(spec)
    assert metrics == expected
