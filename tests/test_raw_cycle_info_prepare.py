"""Tests for raw_plot / cycle_info_plot prepare → spec → render (#647)."""

from __future__ import annotations

import warnings

import pytest

from cellpy.plotting.context import from_source
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
def test_raw_plot_interactive_alias_warns(cell):
    from cellpy import _deprecation

    _deprecation._WARNED_SITES.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        fig = raw_plot(cell, interactive=False)
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
def test_cycle_info_plot_interactive_alias_warns(cell):
    from cellpy import _deprecation

    _deprecation._WARNED_SITES.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        cycle_info_plot(cell, cycle=3, interactive=False)
    messages = [
        str(w.message)
        for w in caught
        if issubclass(w.category, DeprecationWarning)
        and "interactive" in str(w.message)
    ]
    assert messages
