"""Collect -> plot end-to-end tests for the collectors redesign (Epic B, #705-708).

The collector subsystem now lives in :mod:`cellpy.collect` (redesign, #708);
``cellpy.utils.collectors`` is a thin shim whose legacy ``Batch*Collector``
family is removed in 2.1. These tests drive each public collector end to end on
the new ``cellpy.batch`` facade (construction autoruns collection; ``.plot()``
hands the tidy frame to :func:`cellpy.plotting.collected_plot`), so a broken
column migration or a plotter regression fails loudly. They require the
plotting extras; the ``full`` CI job installs them (``uv sync --extra batch``)
and they skip cleanly when the extras or the batch testdata are absent.
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

from cellpy.collect import (  # noqa: E402
    cycles_collector,
    ica_collector,
    standard_gravimetric,
    summary_collector,
)
from cellpy.utils import collectors as collectors_mod  # noqa: E402


def _assert_rendered(collector):
    """A collector that autoran must have a non-empty frame and build a figure."""
    assert collector.data is not None, "collector produced no data"
    assert collector.data.height > 0, "collector data is empty"
    figure = collector.plot()
    assert figure is not None, "collector did not build a figure"
    assert len(figure.data) > 0, "figure has no traces"


# ---- new collectors run end to end --------------------------------------


def test_summary_collector_runs(populated_batch):
    _assert_rendered(summary_collector(populated_batch))


def test_cycles_collector_runs_native_curve_cols(populated_batch):
    """Capacity-curve frame carries native CurveCols names (#540):
    capacity/potential/cycle_num (voltage/cycle were the legacy names)."""
    collector = cycles_collector(populated_batch, cycles=(1, 2))
    _assert_rendered(collector)
    cols = set(collector.data.columns)
    assert {"capacity", "potential", "cycle_num"} <= cols, f"missing curve cols in {cols}"
    assert "voltage" not in cols, f"legacy curve name in {cols}"


def test_collect_cycles_forwards_mode_and_method(populated_batch, monkeypatch):
    """CurveOptions.mode/method reach the per-cell get_cap call (#788)."""
    from cellpy.collect import collect_cycles

    captured: dict = {}
    cell0 = next(iter(populated_batch.cells.values()))
    original = cell0.get_cap

    def spy(*args, **kwargs):
        captured.update(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(cell0, "get_cap", spy)
    col = collect_cycles(populated_batch, cycles=(1,), mode="areal", method="forth")

    assert captured.get("mode") == "areal"
    assert captured.get("method") == "forth"
    assert col.meta.options["mode"] == "areal"
    assert col.meta.options["method"] == "forth"


def test_collect_cycles_mode_method_default_to_none(populated_batch, monkeypatch):
    """Unset mode/method are NOT forwarded, so get_cap keeps its own defaults (#788)."""
    from cellpy.collect import collect_cycles

    captured: dict = {}
    cell0 = next(iter(populated_batch.cells.values()))
    original = cell0.get_cap

    def spy(*args, **kwargs):
        captured.update(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(cell0, "get_cap", spy)
    collect_cycles(populated_batch, cycles=(1,))

    assert "mode" not in captured
    assert "method" not in captured


def test_ica_collector_uses_the_specced_frame(populated_batch):
    """The ICA frame is the specced frame (#566/#591): cycle/direction/voltage/
    capacity/dqdv, direction spelled out (cell-centric charge/discharge)."""
    collector = ica_collector(populated_batch, cycles=(1, 2))
    _assert_rendered(collector)
    cols = set(collector.data.columns)
    assert {"cycle", "direction", "voltage", "capacity", "dqdv"} <= cols, cols
    directions = set(collector.data["direction"].unique().to_list())
    assert directions <= {"charge", "discharge"}, directions


def test_ica_collector_film_mode(populated_batch):
    """Film layout filters by direction (matching the spelled-out string)."""
    collector = ica_collector(populated_batch, cycles=(1, 2))
    figure = collector.plot(kind="film", direction="charge")
    assert figure is not None
    assert len(figure.data) > 0


def test_ica_collector_fig_pr_cycle(populated_batch):
    """Per-cycle ICA layout uses the ICA ``cycle`` column (#679)."""
    collector = ica_collector(populated_batch, cycles=(1, 2))
    figure = collector.plot(method="fig_pr_cycle")
    assert figure is not None


def test_standard_gravimetric_recipe_runs(populated_batch):
    """The standard recipe collects the grouped summary product."""
    collector = standard_gravimetric(populated_batch, columns=("charge_capacity",))
    assert collector.data is not None
    assert "variable" in collector.data.columns  # grouped long format


# ---- shim contract ------------------------------------------------------


@pytest.mark.parametrize(
    "name, replacement",
    [
        ("BatchCollector", "cellpy.collect.BatchCollector"),
        ("BatchSummaryCollector", "cellpy.collect.summary_collector"),
        ("BatchCyclesCollector", "cellpy.collect.cycles_collector"),
        ("BatchICACollector", "cellpy.collect.ica_collector"),
    ],
)
def test_legacy_collector_classes_are_removed(name, replacement):
    """Clean break (#708): the legacy classes raise, pointing at cellpy.collect."""
    cls = getattr(collectors_mod, name)
    with pytest.raises(NotImplementedError, match="cellpy.collect"):
        cls("anything")


@pytest.mark.parametrize(
    "name",
    ["summary_collector", "cycles_collector", "ica_collector",
     "standard_gravimetric_collector", "pick_named_cell"],
)
def test_legacy_collector_functions_are_removed(name):
    fn = getattr(collectors_mod, name)
    with pytest.raises(NotImplementedError, match="cellpy.collect"):
        fn("anything")


def test_select_direction_handles_both_encodings():
    """`_select_direction` is still re-exported here (owned by plotting)."""
    import pandas as pd

    from cellpy.utils.collectors import _select_direction

    specced = pd.DataFrame(
        {"direction": ["charge", "discharge", "charge"], "v": [1, 2, 3]}
    )
    assert list(_select_direction(specced, "charge")["v"]) == [1, 3]

    legacy = pd.DataFrame({"direction": [-1, 1, -1], "v": [1, 2, 3]})
    assert list(_select_direction(legacy, "charge")["v"]) == [1, 3]
    assert list(_select_direction(legacy, "discharge")["v"]) == [2]

    without = pd.DataFrame({"v": [1, 2]})
    assert len(_select_direction(without, "charge")) == 2


def test_drawing_bodies_live_in_plotting_not_collectors():
    """Collectors never define sequence/summary/cycles/ica/spread plotters (#657)."""
    for name in (
        "sequence_plotter",
        "summary_plotter",
        "cycles_plotter",
        "ica_plotter",
        "spread_plot",
        "_cycles_plotter",
    ):
        assert not hasattr(collectors_mod, name), name


def test_shim_still_reexports_the_shared_plotting_helpers():
    """The figure/label/drawing helpers stay importable from collectors (#567)."""
    for name in (
        "load_figure",
        "load_plotly_figure",
        "load_matplotlib_figure",
        "save_matplotlib_figure",
        "make_matplotlib_manager",
        "legend_replacer",
        "remove_markers",
        "collected_plot",
    ):
        assert hasattr(collectors_mod, name), name
