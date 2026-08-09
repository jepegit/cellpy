"""Tests for ica_plot / dva_plot prepare → spec → render (#648)."""

from __future__ import annotations

import ast
import warnings
from pathlib import Path

import pytest

from cellpy.ica import CHARGE, DISCHARGE, ICA_COLS
from cellpy.plotting.context import from_source
from cellpy.plotting.prepare.ica import IcaPrepareConfig, prepare as prepare_ica
from cellpy.plotting import registry as plot_registry
from cellpy.utils.plotutils import dva_plot, ica_plot


@pytest.mark.essential
def test_prepare_ica_module_does_not_import_converter():
    source = Path("cellpy/plotting/prepare/ica.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported_names.add(alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.name.split(".")[-1])
    assert "Converter" not in imported_names
    assert "to_wide" not in imported_names


@pytest.mark.essential
def test_prepare_ica_returns_ica_spec(cell):
    family = plot_registry.get("ica")
    ctx = from_source(cell)
    config = IcaPrepareConfig(derivative="dqdv", cycles=1, backend="matplotlib")
    frame, spec = prepare_ica(ctx, family, config)
    assert not frame.empty
    assert spec.extras.get("kind") == "ica"
    assert ICA_COLS.dqdv in frame.columns
    assert "dq" not in frame.columns  # legacy dq column removed in 2.1 (#714)
    assert {CHARGE, DISCHARGE} <= set(frame[ICA_COLS.direction].unique())


@pytest.mark.essential
def test_prepare_dva_returns_dva_spec(cell):
    family = plot_registry.get("dva")
    ctx = from_source(cell)
    config = IcaPrepareConfig(derivative="dvdq", cycles=1, backend="matplotlib")
    frame, spec = prepare_ica(ctx, family, config)
    assert not frame.empty
    assert spec.extras.get("kind") == "dva"
    assert ICA_COLS.dvdq in frame.columns
    assert {CHARGE, DISCHARGE} <= set(frame[ICA_COLS.direction].unique())


@pytest.mark.essential
def test_ica_plot_backend_matplotlib(cell):
    fig = ica_plot(cell, cycles=1, backend="matplotlib")
    assert fig is not None
    assert hasattr(fig, "get_axes")


@pytest.mark.essential
def test_dva_plot_backend_matplotlib(cell):
    fig = dva_plot(cell, cycles=1, backend="matplotlib")
    assert fig is not None
    assert hasattr(fig, "get_axes")


@pytest.mark.essential
def test_ica_dva_interactive_removed(cell):
    import inspect

    assert "interactive" not in inspect.signature(ica_plot).parameters
    assert "interactive" not in inspect.signature(dva_plot).parameters
    assert ica_plot(cell, cycles=1, backend="matplotlib") is not None
    assert dva_plot(cell, cycles=1, backend="matplotlib") is not None


@pytest.mark.essential
@pytest.mark.parametrize("plot_fn", [ica_plot, dva_plot])
def test_ica_dva_plotly_both_direction_dash_differs(cell, plot_fn):
    """direction='both' must be visually distinguishable, not just via hover (#862)."""
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    fig = plot_fn(cell, cycles=[1], direction="both", backend="plotly")
    dashes = {trace.line.dash for trace in fig.data}
    assert dashes == {"solid", "dot"}


@pytest.mark.essential
@pytest.mark.parametrize("plot_fn", [ica_plot, dva_plot])
@pytest.mark.parametrize("direction", [CHARGE, DISCHARGE])
def test_ica_dva_plotly_single_direction_stays_solid(cell, plot_fn, direction):
    """A single direction has nothing to disambiguate, so it stays solid."""
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    fig = plot_fn(cell, cycles=[1], direction=direction, backend="plotly")
    dashes = {trace.line.dash for trace in fig.data}
    assert dashes == {"solid"}


@pytest.mark.essential
@pytest.mark.parametrize("plot_fn", [ica_plot, dva_plot])
def test_ica_dva_matplotlib_both_direction_linestyle_differs(cell, plot_fn):
    """Matplotlib backend gets the same charge/discharge distinction (#862)."""
    fig = plot_fn(cell, cycles=[1], direction="both", backend="matplotlib")
    lines = fig.get_axes()[0].get_lines()
    linestyles = {line.get_linestyle() for line in lines}
    assert linestyles == {"-", ":"}
