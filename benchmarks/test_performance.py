"""Stage 0.9 performance benchmarks for cellpy v1.x baselines (issue #436).

Run explicitly (excluded from default ``pytest`` collection under ``tests/``)::

    uv run pytest benchmarks/ --benchmark-only

Capture or refresh the committed baseline on **ubuntu-latest** (match CI)::

    uv run pytest benchmarks/ --benchmark-only --benchmark-save=v1x \\
        --benchmark-json=benchmarks/baselines/v1x_ubuntu_py313.json

Compare against the baseline (fail on slowdown >20%%)::

    uv run pytest benchmarks/ --benchmark-only --benchmark-json=/tmp/bench.json
    uv run python benchmarks/check_baseline.py /tmp/bench.json benchmarks/baselines/v1x_ubuntu_py313.json
"""

from __future__ import annotations

import cellpy
from cellpy.readers import cellreader

from benchmarks.conftest import peak_rss_kib
from benchmarks.paths import RES_FILE, V8_FILE

import pytest

pytestmark = pytest.mark.benchmark


def _run_single_cell_pipeline() -> None:
    cell = cellreader.CellpyCell()
    cell.from_raw(str(RES_FILE))
    cell.mass = 1.0
    cell.make_step_table()
    cell.make_summary()
    assert not cell.data.summary.empty


def test_benchmark_single_cell_pipeline(benchmark):
    """load → make_step_table → make_summary on the canonical Arbin ``.res``."""

    def run():
        _run_single_cell_pipeline()
        rss = peak_rss_kib()
        if rss is not None:
            benchmark.extra_info["peak_rss_kib"] = rss

    benchmark.pedantic(run, iterations=1, warmup_rounds=1)


def test_benchmark_batch_summary_collection(benchmark, batch_twenty_cells):
    """Batch summary collection on 20 cells (``concat_summaries``, same path as collector)."""
    from cellpy.utils.helpers import concat_summaries

    def run():
        frame = concat_summaries(
            batch_twenty_cells,
            columns=["charge_capacity_gravimetric"],
        )
        assert frame is not None
        assert not frame.empty

    benchmark.pedantic(run, iterations=1, warmup_rounds=0)


def test_benchmark_v8_cellpy_file_load(benchmark):
    """Load the committed v8 cellpy-file oracle."""

    def run():
        cell = cellpy.get(str(V8_FILE), testing=True)
        assert not cell.data.raw.empty

    benchmark.pedantic(run, iterations=1, warmup_rounds=1)


def test_benchmark_get_cap_all_cycles(benchmark, pipeline_cell):
    """``get_cap`` over all cycles on a pre-built cell."""

    def run():
        curves = pipeline_cell.get_cap(cycle=None, mode="gravimetric")
        assert not curves.empty

    benchmark.pedantic(run, iterations=1, warmup_rounds=0)


def test_benchmark_peak_rss_kib(benchmark):
    """Record peak RSS (Linux only); informational — not gated by the slowdown compare."""
    if peak_rss_kib() is None:
        pytest.skip("peak RSS sampling is only recorded on Linux")

    def run():
        _run_single_cell_pipeline()
        return peak_rss_kib()

    rss = benchmark.pedantic(run, iterations=1, warmup_rounds=0)
    benchmark.extra_info["peak_rss_kib"] = rss
    assert rss is not None and rss > 0
