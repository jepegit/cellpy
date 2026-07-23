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
    assert ICA_COLS.legacy_dqdv not in frame.columns
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
def test_ica_plot_interactive_alias_warns(cell):
    from cellpy import _deprecation

    _deprecation._WARNED_SITES.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        fig = ica_plot(cell, cycles=1, interactive=False)
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
def test_dva_plot_interactive_alias_warns(cell):
    from cellpy import _deprecation

    _deprecation._WARNED_SITES.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        fig = dva_plot(cell, cycles=1, interactive=False)
    assert fig is not None
    messages = [
        str(w.message)
        for w in caught
        if issubclass(w.category, DeprecationWarning)
        and "interactive" in str(w.message)
    ]
    assert messages
