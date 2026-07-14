"""Tests for cellpy deprecation conventions (issue #437)."""

import warnings

import pytest

from cellpy import _deprecation
from cellpy._deprecation import warn_once
from cellpy.exceptions import (
    CellpyError,
    ConfigurationError,
    CorruptCellpyFile,
    LoaderError,
    UnitsError,
)
from cellpy.utils.helpers import make_new_cell


@pytest.mark.essential
def test_warn_once_emits_once_per_call_site():
    _deprecation._WARNED_SITES.clear()
    _deprecation._REGISTRY.clear()

    def _call():
        warn_once("demo_fn", "replacement.fn")

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        _call()
        _call()

    assert len(caught) == 1
    assert "demo_fn is deprecated" in str(caught[0].message)
    assert "replacement.fn" in str(caught[0].message)


@pytest.mark.essential
def test_warn_once_registers_for_deprecations_md():
    _deprecation._WARNED_SITES.clear()
    _deprecation._REGISTRY.clear()

    warn_once("other_fn", "new_api", removal="2.2")

    registry = _deprecation.get_registry()
    assert "other_fn" in registry
    assert registry["other_fn"].replacement == "new_api"
    assert registry["other_fn"].removal == "2.2"

    rendered = _deprecation.render_deprecations_md()
    assert "`other_fn`" in rendered
    assert "`new_api`" in rendered


@pytest.mark.essential
def test_make_new_cell_uses_warn_once():
    _deprecation._WARNED_SITES.clear()

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        make_new_cell()
        make_new_cell()

    make_new_cell_warnings = [w for w in caught if "make_new_cell" in str(w.message)]
    assert len(make_new_cell_warnings) == 1
    assert "CellpyCell.vacant" in str(make_new_cell_warnings[0].message)


@pytest.mark.essential
def test_easyplot_import_warns_once():
    import importlib
    import sys

    _deprecation._WARNED_SITES.clear()

    # Drop cached module so import runs warn_once again in this test process.
    sys.modules.pop("cellpy.utils.easyplot", None)

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        importlib.import_module("cellpy.utils.easyplot")
        importlib.import_module("cellpy.utils.easyplot")

    assert len(caught) == 1
    message = str(caught[0].message)
    assert "cellpy.utils.easyplot is deprecated" in message
    assert "cellpy.utils.plotutils and cellpy.utils.collectors" in message
    assert "removed in 2.0" in message


@pytest.mark.essential
def test_exception_tree_stubs():
    assert issubclass(CorruptCellpyFile, CellpyError)
    assert issubclass(ConfigurationError, CellpyError)
    assert issubclass(UnitsError, CellpyError)
    assert issubclass(LoaderError, CellpyError)


@pytest.mark.essential
def test_deprecations_md_matches_renderer():
    _deprecation._REGISTRY.clear()
    _deprecation._seed_known_deprecations()

    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    on_disk = (repo_root / "DEPRECATIONS.md").read_text(encoding="utf-8")
    rendered = _deprecation.render_deprecations_md()
    assert on_disk == rendered
