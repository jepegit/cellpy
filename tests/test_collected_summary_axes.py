"""Collected summary facet axes: share_y / match_axes / y_ranges (#804)."""

from __future__ import annotations

import pandas as pd
import pytest

from cellpy.plotting.collected import _resolve_share_y


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


@pytest.mark.essential
def test_resolve_share_y_prefers_share_y_over_match_axes():
    assert _resolve_share_y(share_y=False, match_axes=True, default=True) is False
    assert _resolve_share_y(share_y=True, match_axes=False, default=False) is True
    assert _resolve_share_y(share_y=None, match_axes=None, default=False) is False
    assert _resolve_share_y(share_y=None, match_axes=True, default=False) is True


@pytest.mark.essential
def test_summary_default_independent_y_axes():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import summary_plotter

    theme.make_collector_templates()
    fig = summary_plotter(_summary_frame(), backend="plotly", group_cells=False)
    assert fig is not None
    assert fig.layout.yaxis.matches in (None, False)
    assert fig.layout.yaxis2.matches in (None, False)


@pytest.mark.essential
def test_summary_share_y_true_matches_axes():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import summary_plotter

    theme.make_collector_templates()
    fig = summary_plotter(
        _summary_frame(), backend="plotly", group_cells=False, share_y=True
    )
    assert fig is not None
    # Plotly links secondary facet rows to the primary y-axis.
    assert fig.layout.yaxis2.matches == "y"


@pytest.mark.essential
def test_summary_match_axes_alias_and_share_y_wins():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import summary_plotter

    theme.make_collector_templates()
    fig = summary_plotter(
        _summary_frame(),
        backend="plotly",
        group_cells=False,
        match_axes=True,
        share_y=False,
    )
    assert fig is not None
    assert fig.layout.yaxis2.matches in (None, False)


@pytest.mark.essential
def test_summary_y_ranges_per_panel():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import (
        _yaxis_key_for_variable,
        summary_plotter,
    )

    theme.make_collector_templates()
    fig = summary_plotter(
        _summary_frame(),
        backend="plotly",
        group_cells=False,
        y_ranges={"coulombic_efficiency": [0, 110]},
    )
    assert fig is not None
    ce_key = _yaxis_key_for_variable(fig, "coulombic_efficiency")
    cap_key = _yaxis_key_for_variable(fig, "charge_capacity_gravimetric")
    assert ce_key is not None
    assert cap_key is not None
    assert list(fig.layout[ce_key].range) == [0.0, 110.0]
    assert fig.layout[ce_key].autorange is False
    # Capacity panel left to autorange (no fixed range from y_ranges).
    assert fig.layout[cap_key].range is None


@pytest.mark.essential
def test_summary_y_ranges_forces_independent_when_share_y_true():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import (
        _yaxis_key_for_variable,
        summary_plotter,
    )

    theme.make_collector_templates()
    fig = summary_plotter(
        _summary_frame(),
        backend="plotly",
        group_cells=False,
        share_y=True,
        y_ranges={"coulombic_efficiency": [0, 110]},
    )
    assert fig is not None
    assert fig.layout.yaxis2.matches in (None, False)
    ce_key = _yaxis_key_for_variable(fig, "coulombic_efficiency")
    assert list(fig.layout[ce_key].range) == [0.0, 110.0]


@pytest.mark.essential
def test_collected_plot_forwards_y_ranges():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import (
        _yaxis_key_for_variable,
        collected_plot,
    )

    theme.make_collector_templates()
    fig = collected_plot(
        _summary_frame(),
        family_kind="summary",
        backend="plotly",
        group_cells=False,
        y_ranges={"coulombic_efficiency": [0.0, 110.0]},
    )
    assert fig is not None
    ce_key = _yaxis_key_for_variable(fig, "coulombic_efficiency")
    assert list(fig.layout[ce_key].range) == [0.0, 110.0]


def _group_avg_summary_frame() -> pd.DataFrame:
    """Long group-averaged summary frame (mean/std, no cell) for spread path."""
    rows = []
    for group in (1, 2):
        for cycle in (1, 2, 3):
            rows.append(
                {
                    "cycle": cycle,
                    "group": group,
                    "sub_group": 1,
                    "variable": "charge_capacity_gravimetric",
                    "mean": 100.0 + cycle + group,
                    "std": 2.0,
                }
            )
            rows.append(
                {
                    "cycle": cycle,
                    "group": group,
                    "sub_group": 1,
                    "variable": "coulombic_efficiency",
                    "mean": 1.0e6 if cycle == 2 else 98.0,
                    "std": 0.5,
                }
            )
    return pd.DataFrame(rows)


@pytest.mark.essential
def test_spread_share_y_true_matches_axes():
    """Group avg + Spread + share_y links secondary facet y-axes (#817)."""
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import summary_plotter

    theme.make_collector_templates()
    fig = summary_plotter(
        _group_avg_summary_frame(),
        backend="plotly",
        spread=True,
        share_y=True,
    )
    assert fig is not None
    assert fig.layout.yaxis2.matches == "y"


@pytest.mark.essential
def test_spread_default_independent_y_axes():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import summary_plotter

    theme.make_collector_templates()
    fig = summary_plotter(
        _group_avg_summary_frame(),
        backend="plotly",
        spread=True,
    )
    assert fig is not None
    assert fig.layout.yaxis.matches in (None, False)
    assert fig.layout.yaxis2.matches in (None, False)


@pytest.mark.essential
def test_spread_y_ranges_forces_independent_when_share_y_true():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import (
        _yaxis_key_for_variable,
        summary_plotter,
    )

    theme.make_collector_templates()
    fig = summary_plotter(
        _group_avg_summary_frame(),
        backend="plotly",
        spread=True,
        share_y=True,
        y_ranges={"coulombic_efficiency": [0, 110]},
    )
    assert fig is not None
    assert fig.layout.yaxis2.matches in (None, False)
    ce_key = _yaxis_key_for_variable(fig, "coulombic_efficiency")
    assert ce_key is not None
    assert list(fig.layout[ce_key].range) == [0.0, 110.0]


@pytest.mark.essential
def test_collected_plot_spread_share_y():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import collected_plot

    theme.make_collector_templates()
    fig = collected_plot(
        _group_avg_summary_frame(),
        family_kind="summary",
        backend="plotly",
        spread=True,
        share_y=True,
    )
    assert fig is not None
    assert fig.layout.yaxis2.matches == "y"


@pytest.mark.essential
def test_spread_mean_traces_have_hovertemplate():
    """Mean hover matches group_it fields + std; bounds skip hover (#875)."""
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import summary_plotter

    theme.make_collector_templates()
    fig = summary_plotter(
        _group_avg_summary_frame(),
        backend="plotly",
        spread=True,
    )
    mean_templates = []
    for trace in fig.data:
        name = trace.name or ""
        if name.startswith("Upper Bound") or name.startswith("Lower Bound"):
            assert trace.hoverinfo == "skip"
            continue
        tmpl = trace.hovertemplate or ""
        mean_templates.append(tmpl)
        assert "mean=%{y}" in tmpl
        assert "variable=" in tmpl
        assert "Cycle (n.)=%{x}" in tmpl
        assert "std=%{customdata}" in tmpl
        assert "group=" in tmpl
    assert mean_templates, "expected at least one mean trace with hovertemplate"
