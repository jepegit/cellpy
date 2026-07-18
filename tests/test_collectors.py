"""Smoke/characterization tests for the batch collectors + plotters.

Before this file nothing in the suite exercised `cellpy.utils.collectors`'
collect→plot paths, and CI did not even install the plotting extras
(`plotly`/`seaborn` live in the `batch` optional-dependency group). That left
the collector/plotter code — including the curve-frame consumers that the
native-headers flip must migrate (#540) — with **no** test net.

These tests drive each public collector end to end (construction autoruns the
data collection and the plot) so a broken column-name migration or a plotter
regression fails loudly. They require the plotting extras; the `full` CI job
installs them (`uv sync --extra batch`), and they skip cleanly when the extras
or the batch testdata are absent.
"""

from __future__ import annotations

import pytest

# Reuse the batch fixtures (clean_dir → batch_instance → populated_batch).
from tests.test_batch import (  # noqa: F401  (imported for fixture resolution)
    batch_instance,
    clean_dir,
    populated_batch,
)

plotly = pytest.importorskip("plotly", reason="plotting extras (batch) not installed")

from cellpy.utils.collectors import (  # noqa: E402
    BatchCyclesCollector,
    BatchICACollector,
    BatchSummaryCollector,
)


def _assert_ran(collector):
    """A collector that autoran must have collected data and built a figure."""
    assert collector.data is not None, "collector produced no data"
    assert not collector.data.empty, "collector data is empty"
    assert collector.figure is not None, "collector did not build a figure"


def test_batch_summary_collector_runs(populated_batch):
    """Summary collector collects + plots (guards the summary-frame path that
    #540 must NOT touch)."""
    _assert_ran(BatchSummaryCollector(populated_batch))


def test_batch_cycles_collector_runs(populated_batch):
    """Capacity-curve collector collects `get_cap` frames + plots (the curve
    consumer path the flip migrates — #540)."""
    collector = BatchCyclesCollector(populated_batch)
    _assert_ran(collector)
    # the collected curve frame carries native CurveCols names (#540):
    # capacity/potential/cycle_num (voltage/cycle were the legacy names).
    cols = set(collector.data.columns)
    assert {"capacity", "potential", "cycle_num"} <= cols, f"missing curve cols in {cols}"
    assert "voltage" not in cols and "cycle" not in cols, f"legacy curve name in {cols}"


def test_batch_ica_collector_runs(populated_batch):
    """ICA (dQ/dV) collector collects + plots."""
    collector = BatchICACollector(populated_batch)
    _assert_ran(collector)
