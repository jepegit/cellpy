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
def test_cycles_plot_interactive_alias_warns(cell):
    from cellpy import _deprecation

    _deprecation._WARNED_SITES.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        fig = cycles_plot(cell, interactive=False, return_figure=True)
    assert fig is not None
    messages = [
        str(w.message)
        for w in caught
        if issubclass(w.category, DeprecationWarning)
        and "interactive" in str(w.message)
    ]
    assert messages
    assert "backend=" in messages[0] or "matplotlib" in messages[0]


@pytest.mark.essential
def test_cycles_plot_xlim_ylim_alias_warns(cell):
    from cellpy import _deprecation

    _deprecation._WARNED_SITES.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        fig = cycles_plot(
            cell,
            backend="matplotlib",
            xlim=[0, 1],
            ylim=[0, 2],
            return_figure=True,
        )
    assert fig is not None
    texts = [str(w.message) for w in caught if issubclass(w.category, DeprecationWarning)]
    assert any("xlim" in t for t in texts)
    assert any("ylim" in t for t in texts)


@pytest.mark.essential
def test_cycles_plot_return_data(cell):
    fig, frame = cycles_plot(
        cell, backend="matplotlib", return_figure=True, return_data=True
    )
    assert fig is not None
    assert not frame.empty
    assert "capacity" in frame.columns
