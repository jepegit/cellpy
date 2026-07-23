"""Tests for the matplotlib summary backend and backend= API (#639)."""

from __future__ import annotations

import warnings

import pytest

from cellpy.plotting.backends import get_backend
from cellpy.plotting.backends.base import Backend
from cellpy.plotting.backends.mpl import MatplotlibBackend
from cellpy.plotting.backends.plotly import PlotlyBackend
from cellpy.utils import plotutils
from cellpy.utils.plotutils import summary_plot


@pytest.mark.essential
def test_get_backend_known_names():
    assert isinstance(get_backend("plotly"), PlotlyBackend)
    assert isinstance(get_backend("matplotlib"), MatplotlibBackend)
    assert isinstance(get_backend("plotly"), Backend)
    assert isinstance(get_backend("matplotlib"), Backend)


@pytest.mark.essential
def test_get_backend_unknown_raises():
    with pytest.raises(ValueError, match="unknown plotting backend"):
        get_backend("seaborn")


@pytest.mark.essential
def test_seaborn_plot_builder_is_gone():
    assert not hasattr(plotutils, "SeabornPlotBuilder")


@pytest.mark.essential
def test_interactive_alias_warns_and_maps(cell):
    from cellpy import _deprecation

    # warn_once is once-per-call-site across the whole process; reset so this
    # test is order-independent in the essential suite.
    _deprecation._WARNED_SITES.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            interactive=False,
            show_formation=False,
        )
    assert fig is not None
    messages = [
        str(w.message)
        for w in caught
        if issubclass(w.category, DeprecationWarning)
        and "interactive" in str(w.message)
    ]
    assert messages, "expected DeprecationWarning for interactive="
    assert "backend=" in messages[0] or "matplotlib" in messages[0]


@pytest.mark.essential
def test_backend_matplotlib_no_interactive_warning(cell):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        fig = summary_plot(
            cell,
            y="capacities_gravimetric",
            backend="matplotlib",
            show_formation=False,
        )
    assert fig is not None
    interactive_warns = [
        w
        for w in caught
        if issubclass(w.category, DeprecationWarning)
        and "interactive" in str(w.message)
    ]
    assert not interactive_warns
