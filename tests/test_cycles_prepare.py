"""Tests for cycles_plot prepare → spec → render (#646)."""

from __future__ import annotations

import warnings

import pytest

from cellpy.plotting.context import from_source
from cellpy.plotting.prepare.curves import CyclesPrepareConfig, prepare
from cellpy.plotting import registry as plot_registry
from cellpy.utils import plotutils
from cellpy.utils.plotutils import cycles_plot


@pytest.mark.essential
def test_private_cycles_plotters_are_gone():
    assert not hasattr(plotutils, "_cycles_plotter_plotly")
    assert not hasattr(plotutils, "_cycles_plotter_matplotlib")
    assert not hasattr(plotutils, "CyclesPlotterConfig")


@pytest.mark.essential
def test_prepare_returns_cycles_spec(cell):
    family = plot_registry.get("cycles")
    ctx = from_source(cell)
    config = CyclesPrepareConfig(backend="matplotlib", show_formation=True)
    frame, spec = prepare(ctx, family, config)
    assert not frame.empty
    assert spec.extras.get("kind") == "cycles"
    assert "form_cycles" in spec.extras
    assert "rest_cycles" in spec.extras
    assert spec.supports_formation is True


@pytest.mark.essential
def test_cycles_plot_backend_matplotlib(cell):
    fig = cycles_plot(cell, backend="matplotlib", return_figure=True)
    assert fig is not None
    assert hasattr(fig, "get_axes")


@pytest.mark.essential
def test_cycles_plot_interactive_and_range_shims_removed(cell):
    # interactive=/xlim/ylim were removed in 2.1 (E1, #713); canonical spellings only.
    import inspect

    params = inspect.signature(cycles_plot).parameters
    assert "interactive" not in params
    assert "xlim" not in params and "ylim" not in params
    fig = cycles_plot(
        cell, backend="matplotlib", x_range=[0, 1], y_range=[0, 2], return_figure=True
    )
    assert fig is not None


@pytest.mark.essential
def test_cycles_plot_return_data(cell):
    fig, frame = cycles_plot(
        cell, backend="matplotlib", return_figure=True, return_data=True
    )
    assert fig is not None
    assert not frame.empty
    assert "capacity" in frame.columns
