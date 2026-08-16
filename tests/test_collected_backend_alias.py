"""``collected_plot(backend="matplotlib")`` on a collected frame (#925).

The collected layouts have no matplotlib engine of their own, so the flag
aliases to the historical seaborn path. It used to raise ``TypeError`` from
``warn_once`` before drawing anything, and the summary path raised again on the
y-label mapper once that was fixed, so this call had never returned a figure.
"""

from __future__ import annotations

import warnings

import pandas as pd
import pytest


def _grouped_summary_frame() -> pd.DataFrame:
    """A group-averaged summary frame (the ``group_it=True`` long shape)."""
    rows = []
    for group in (1, 2):
        for cycle in (1, 2, 3):
            for variable in ("cap_charge", "cap_discharge", "ce"):
                rows.append(
                    {
                        "group": group,
                        "cycle": cycle,
                        "variable": variable,
                        "mean": 100.0 + cycle + group,
                        "std": 1.0,
                    }
                )
    return pd.DataFrame(rows)


@pytest.mark.essential
def test_collected_summary_matplotlib_backend_returns_a_figure():
    pytest.importorskip("seaborn", reason="plotting extras (batch) not installed")
    import matplotlib

    matplotlib.use("Agg")

    from cellpy.plotting.collected import collected_plot

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        figure = collected_plot(
            _grouped_summary_frame(),
            family_kind="summary",
            backend="matplotlib",
            height=600,
        )

    assert figure is not None
    messages = [str(w.message) for w in caught]
    assert any('backend="matplotlib"' in message for message in messages)


@pytest.mark.essential
def test_the_notice_names_a_replacement():
    """``warn_once`` takes ``(name, replacement)``, not a ready message."""
    pytest.importorskip("seaborn", reason="plotting extras (batch) not installed")
    import matplotlib

    matplotlib.use("Agg")

    from cellpy import _deprecation
    from cellpy.plotting.collected import collected_plot

    _deprecation._WARNED_SITES.clear()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        collected_plot(
            _grouped_summary_frame(), family_kind="summary", backend="matplotlib"
        )

    messages = [str(w.message) for w in caught]
    assert any('use backend="plotly" instead' in message for message in messages)
