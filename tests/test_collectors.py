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

Collector figure structure is snapshotted in
``tests/data/collector_figure_specs.json`` (#657) — regenerate with::

    MPLBACKEND=Agg uv run python -c "from tests.test_collectors import write_collector_figure_specs; write_collector_figure_specs()"
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# Reuse the batch fixtures (clean_dir → batch_instance → populated_batch).
from tests.test_batch import (  # noqa: F401  (imported for fixture resolution)
    batch_instance,
    clean_dir,
    populated_batch,
)
from tests.figure_spec_support import describe_figure

plotly = pytest.importorskip("plotly", reason="plotting extras (batch) not installed")

from cellpy.utils import collectors as collectors_mod  # noqa: E402
from cellpy.utils.collectors import (  # noqa: E402
    BatchCyclesCollector,
    BatchICACollector,
    BatchSummaryCollector,
)

COLLECTOR_SNAPSHOT_PATH = (
    Path(__file__).resolve().parent / "data" / "collector_figure_specs.json"
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


def test_batch_ica_collector_uses_the_specced_frame(populated_batch):
    """ica_collector migrated off the 1.x frame (#591 resolved #566's leftover).

    The collected frame is now the specced ICA frame: direction spelled out
    "charge"/"discharge" (cell-centric, decision #591) plus the dqdv column.
    """
    collector = BatchICACollector(populated_batch)
    cols = set(collector.data.columns)
    assert {"cycle", "direction", "voltage", "capacity", "dqdv"} <= cols, cols
    directions = set(collector.data["direction"].unique())
    assert directions <= {"charge", "discharge"}, directions


def test_batch_ica_collector_film_mode(populated_batch):
    """Film mode filters by direction, which now means matching the string."""
    collector = BatchICACollector(populated_batch, plot_type="film")
    _assert_ran(collector)


def test_select_direction_handles_both_encodings():
    """The plotters see specced string frames and raw ±1 get_cap frames."""
    import pandas as pd

    from cellpy.utils.collectors import _select_direction

    specced = pd.DataFrame(
        {"direction": ["charge", "discharge", "charge"], "v": [1, 2, 3]}
    )
    picked = _select_direction(specced, "charge")
    assert list(picked["v"]) == [1, 3]

    legacy = pd.DataFrame({"direction": [-1, 1, -1], "v": [1, 2, 3]})
    picked = _select_direction(legacy, "charge")
    assert list(picked["v"]) == [1, 3]  # historical -1 -> "charge" mapping kept
    picked = _select_direction(legacy, "discharge")
    assert list(picked["v"]) == [2]

    without = pd.DataFrame({"v": [1, 2]})
    assert len(_select_direction(without, "charge")) == 2


def test_drawing_bodies_live_in_plotting_not_collectors():
    """Collectors no longer define sequence/summary/cycles/ica/spread plotters (#657)."""
    for name in (
        "sequence_plotter",
        "summary_plotter",
        "cycles_plotter",
        "ica_plotter",
        "spread_plot",
        "_cycles_plotter",
    ):
        assert not hasattr(collectors_mod, name), name


def test_batch_collector_plot_aliases_render(populated_batch):
    """``BatchCollector.plot`` is a thin alias of ``render`` (#657)."""
    collector = BatchSummaryCollector(populated_batch, autorun=False)
    collector.collect()
    collector.plot()
    assert collector.figure is not None


def _collector_figure_menu(populated_batch) -> dict:
    """Minimum collector column for the #657 oracle."""
    from cellpy.plotting import collected_plot

    summary = BatchSummaryCollector(populated_batch, autorun=False)
    summary.collect()
    cycles = BatchCyclesCollector(populated_batch, autorun=False)
    cycles.collect()
    ica_film = BatchICACollector(populated_batch, plot_type="film", autorun=False)
    ica_film.collect()
    # spread_plot needs group_it so the frame carries mean/std columns
    summary_spread = BatchSummaryCollector(
        populated_batch, group_it=True, spread=True, autorun=False
    )
    summary_spread.collect()

    figures = {
        "collected_summary[plotly]": describe_figure(
            collected_plot(summary.data, family_kind="summary", backend="plotly")
        ),
        "collected_cycles_per_cell[plotly]": describe_figure(
            collected_plot(
                cycles.data,
                family_kind="cycles",
                layout="per_cell",
                backend="plotly",
            )
        ),
        "collected_ica_film[plotly]": describe_figure(
            collected_plot(
                ica_film.data,
                family_kind="ica",
                kind="film",
                backend="plotly",
            )
        ),
        "collected_summary_spread[plotly]": describe_figure(
            collected_plot(
                summary_spread.data,
                family_kind="summary",
                kind="spread",
                backend="plotly",
            )
        ),
    }
    return {"figures": figures}


def write_collector_figure_specs(populated_batch=None) -> Path:
    """Regenerate ``collector_figure_specs.json`` (dev helper / snapshot regen)."""
    if populated_batch is None:
        raise RuntimeError("pass a populated_batch when calling from tests")
    specs = _collector_figure_menu(populated_batch)
    COLLECTOR_SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    COLLECTOR_SNAPSHOT_PATH.write_text(
        json.dumps(specs, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return COLLECTOR_SNAPSHOT_PATH


@pytest.mark.essential
def test_collector_figure_structure_matches_snapshot(populated_batch):
    """Collector layouts are part of the plotting contract (#657)."""
    if not COLLECTOR_SNAPSHOT_PATH.is_file():
        pytest.skip(f"missing snapshot {COLLECTOR_SNAPSHOT_PATH}")
    expected = json.loads(COLLECTOR_SNAPSHOT_PATH.read_text(encoding="utf-8"))["figures"]
    actual = _collector_figure_menu(populated_batch)["figures"]
    assert set(actual) == set(expected)
    for name, want in expected.items():
        got = actual[name]
        assert got["backend"] == want["backend"], name
        assert got.get("n_traces") == want.get("n_traces"), name
        assert got.get("n_axes") == want.get("n_axes"), name
