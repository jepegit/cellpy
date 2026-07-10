"""Unit tests for benchmarks/check_baseline.py (issue #476)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmarks.check_baseline import compare


def _write_bench_json(path: Path, means: dict[str, float]) -> None:
    payload = {
        "benchmarks": [
            {"name": name, "stats": {"mean": mean}} for name, mean in means.items()
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


@pytest.fixture
def baseline_file(tmp_path: Path) -> Path:
    path = tmp_path / "baseline.json"
    _write_bench_json(
        path,
        {
            "test_benchmark_batch_summary_collection": 0.050,
            "test_benchmark_peak_rss_kib": 100.0,
        },
    )
    return path


def test_compare_passes_within_warn_band(tmp_path: Path, baseline_file: Path) -> None:
    current = tmp_path / "current.json"
    _write_bench_json(current, {"test_benchmark_batch_summary_collection": 0.055})
    result = compare(current, baseline_file)
    assert result.warnings == ()
    assert result.failures == ()


def test_compare_warns_above_warn_threshold(tmp_path: Path, baseline_file: Path) -> None:
    current = tmp_path / "current.json"
    _write_bench_json(current, {"test_benchmark_batch_summary_collection": 0.065})
    result = compare(current, baseline_file, warn_tolerance=0.20, fail_tolerance=1.0)
    assert len(result.warnings) == 1
    assert "test_benchmark_batch_summary_collection" in result.warnings[0]
    assert result.failures == ()


def test_compare_fails_above_fail_threshold(tmp_path: Path, baseline_file: Path) -> None:
    current = tmp_path / "current.json"
    _write_bench_json(current, {"test_benchmark_batch_summary_collection": 0.130})
    result = compare(current, baseline_file, warn_tolerance=0.20, fail_tolerance=1.0)
    assert result.failures
    assert "exceeds max slowdown +100%" in result.failures[0]


def test_compare_skips_peak_rss(tmp_path: Path) -> None:
    baseline = tmp_path / "baseline.json"
    _write_bench_json(baseline, {"test_benchmark_peak_rss_kib": 100.0})
    current = tmp_path / "current.json"
    _write_bench_json(current, {})
    result = compare(current, baseline)
    assert result.warnings == ()
    assert result.failures == ()
