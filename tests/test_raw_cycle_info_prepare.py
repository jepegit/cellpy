"""Tests for raw_plot / cycle_info_plot prepare → spec → render (#647)."""

from __future__ import annotations

import warnings

import pytest

from cellpy.plotting.context import from_source
from cellpy.plotting.headers import LiveHeaders
from cellpy.plotting.prepare.raw import RawPrepareConfig, prepare as prepare_raw
from cellpy.plotting.prepare.steps import (
    CycleInfoPrepareConfig,
    prepare as prepare_cycle_info,
)
from cellpy.plotting import registry as plot_registry
from cellpy.utils import plotutils
from cellpy.utils.plotutils import cycle_info_plot, raw_plot


@pytest.mark.essential
def test_private_raw_and_cycle_info_helpers_are_gone():
    assert not hasattr(plotutils, "_cycle_info_plot_plotly")
    assert not hasattr(plotutils, "_cycle_info_plot_matplotlib")
    assert not hasattr(plotutils, "_get_info")
    assert not hasattr(plotutils, "_plot_step")


@pytest.mark.essential
def test_prepare_raw_returns_raw_spec(cell):
    family = plot_registry.get("raw")
    ctx = from_source(cell)
    config = RawPrepareConfig(backend="matplotlib")
    frame, spec = prepare_raw(ctx, family, config)
    assert not frame.empty
    assert spec.extras.get("kind") == "raw"
    assert spec.extras.get("y")
    assert "Time" in (spec.x_axis.label or "")


@pytest.mark.essential
def test_prepare_cycle_info_returns_cycle_info_spec(cell):
    family = plot_registry.get("cycle_info")
    ctx = from_source(cell)
    config = CycleInfoPrepareConfig(cycle=3, backend="matplotlib")
    frame, spec = prepare_cycle_info(ctx, family, config)
    assert not frame.empty
    assert spec.extras.get("kind") == "cycle_info"
    assert spec.extras.get("cycle") == 3
    assert "steps" in spec.extras


@pytest.mark.essential
def test_raw_plot_backend_matplotlib(cell):
    fig = raw_plot(cell, backend="matplotlib")
    assert fig is not None
    assert hasattr(fig, "get_axes")


@pytest.mark.essential
def test_cycle_info_plot_backend_matplotlib(cell):
    assert cycle_info_plot(cell, cycle=3, backend="matplotlib") is None
    axes = cycle_info_plot(cell, cycle=3, backend="matplotlib", get_axes=True)
    assert axes is not None


@pytest.mark.essential
def test_prepare_raw_cycles_selects_only_the_requested_cycles(cell):
    family = plot_registry.get("raw")
    ctx = from_source(cell)
    cycle_col = LiveHeaders(cell, "raw")["cycle_index_txt"]

    full, _ = prepare_raw(ctx, family, RawPrepareConfig(backend="matplotlib"))
    wanted = sorted(full[cycle_col].unique())[:2]

    frame, _ = prepare_raw(
        ctx, family, RawPrepareConfig(backend="matplotlib", cycles=wanted)
    )
    assert sorted(frame[cycle_col].unique()) == wanted
    assert len(frame) < len(full)

    single, _ = prepare_raw(
        ctx, family, RawPrepareConfig(backend="matplotlib", cycles=wanted[0])
    )
    assert sorted(single[cycle_col].unique()) == [wanted[0]]


@pytest.mark.essential
def test_prepare_raw_max_points_thins_but_keeps_the_extremes(cell):
    family = plot_registry.get("raw")
    ctx = from_source(cell)

    full, spec = prepare_raw(
        ctx, family, RawPrepareConfig(backend="matplotlib", plot_type="full")
    )
    thinned, _ = prepare_raw(
        ctx,
        family,
        RawPrepareConfig(backend="matplotlib", plot_type="full", max_points=500),
    )

    assert len(thinned) < len(full)
    assert len(thinned) <= 500
    # Endpoints survive, so the x range does not shrink.
    x = spec.extras["x"]
    assert thinned[x].iloc[0] == full[x].iloc[0]
    assert thinned[x].iloc[-1] == full[x].iloc[-1]
    # Per-bucket min/max keeps every trace's extremes — striding would not.
    for column in spec.extras["y"]:
        assert thinned[column].min() == full[column].min()
        assert thinned[column].max() == full[column].max()


@pytest.mark.essential
def test_prepare_raw_max_points_is_a_no_op_when_already_small(cell):
    family = plot_registry.get("raw")
    ctx = from_source(cell)
    full, _ = prepare_raw(ctx, family, RawPrepareConfig(backend="matplotlib"))
    frame, _ = prepare_raw(
        ctx,
        family,
        RawPrepareConfig(backend="matplotlib", max_points=len(full) + 1),
    )
    assert len(frame) == len(full)


@pytest.mark.essential
def test_raw_plot_exposes_cycles_and_max_points(cell):
    import inspect

    parameters = inspect.signature(raw_plot).parameters
    assert "cycles" in parameters
    assert "max_points" in parameters
    assert raw_plot(cell, backend="matplotlib", cycles=1, max_points=200) is not None


@pytest.mark.essential
def test_raw_and_cycle_info_interactive_removed(cell):
    import inspect

    assert "interactive" not in inspect.signature(raw_plot).parameters
    assert "interactive" not in inspect.signature(cycle_info_plot).parameters
    assert raw_plot(cell, backend="matplotlib") is not None
    cycle_info_plot(cell, cycle=3, backend="matplotlib")
