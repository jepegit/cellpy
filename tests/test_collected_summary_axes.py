"""Collected summary facet axes: share_y / match_axes / y_ranges (#804)."""

from __future__ import annotations

import pandas as pd
import pytest

from cellpy.plotting import theme
from cellpy.plotting.collected import (
    _yaxis_key_for_facet_label,
    collected_plot,
    summary_plotter,
)


def _summary_frame() -> pd.DataFrame:
    """Long summary frame with capacity-like and CE-like scales."""
    rows = []
    for cell in ("a", "b"):
        for cycle in (1, 2, 3):
            rows.append(
                {
                    "cycle": cycle,
                    "cell": cell,
                    "group": 1,
                    "sub_group": 1,
                    "variable": "charge_capacity_gravimetric",
                    "value": 100.0 + cycle,
                }
            )
            rows.append(
                {
                    "cycle": cycle,
                    "cell": cell,
                    "group": 1,
                    "sub_group": 1,
                    "variable": "coulombic_efficiency",
                    "value": 1.0e6 if cycle == 2 else 98.0,
                }
            )
    return pd.DataFrame(rows)


@pytest.fixture(autouse=True)
def _collector_templates():
    theme.make_collector_templates()


@pytest.mark.essential
def test_summary_default_independent_y_axes():
    fig = summary_plotter(_summary_frame(), backend="plotly", group_cells=False)
    assert fig.layout.yaxis.matches in (None, False)
    assert fig.layout.yaxis2.matches in (None, False)


@pytest.mark.essential
def test_summary_share_y_true_matches_axes():
    fig = summary_plotter(
        _summary_frame(), backend="plotly", group_cells=False, share_y=True
    )
    # Plotly links secondary facet rows to the primary y-axis.
    assert fig.layout.yaxis2.matches == "y"


@pytest.mark.essential
def test_summary_match_axes_alias_and_share_y_wins():
    fig = summary_plotter(
        _summary_frame(),
        backend="plotly",
        group_cells=False,
        match_axes=True,
        share_y=False,
    )
    assert fig.layout.yaxis2.matches in (None, False)


@pytest.mark.essential
def test_summary_y_ranges_per_panel():
    fig = summary_plotter(
        _summary_frame(),
        backend="plotly",
        group_cells=False,
        y_ranges={"coulombic_efficiency": [0, 110]},
    )
    ce_key = _yaxis_key_for_facet_label(fig, "variable=coulombic_efficiency")
    cap_key = _yaxis_key_for_facet_label(fig, "variable=charge_capacity_gravimetric")
    assert ce_key is not None
    assert cap_key is not None
    assert list(fig.layout[ce_key].range) == [0.0, 110.0]
    assert fig.layout[ce_key].autorange is False
    # Capacity panel left to autorange (no fixed range from y_ranges).
    assert fig.layout[cap_key].range is None


@pytest.mark.essential
def test_summary_y_ranges_forces_independent_when_share_y_true():
    fig = summary_plotter(
        _summary_frame(),
        backend="plotly",
        group_cells=False,
        share_y=True,
        y_ranges={"coulombic_efficiency": [0, 110]},
    )
    assert fig.layout.yaxis2.matches in (None, False)
    ce_key = _yaxis_key_for_facet_label(fig, "variable=coulombic_efficiency")
    assert list(fig.layout[ce_key].range) == [0.0, 110.0]


@pytest.mark.essential
def test_collected_plot_forwards_y_ranges():
    fig = collected_plot(
        _summary_frame(),
        family_kind="summary",
        backend="plotly",
        group_cells=False,
        y_ranges={"coulombic_efficiency": [0.0, 110.0]},
    )
    ce_key = _yaxis_key_for_facet_label(fig, "variable=coulombic_efficiency")
    assert list(fig.layout[ce_key].range) == [0.0, 110.0]
