"""Collected app chrome: summary labels/height (#801); cycles facets (#820)."""

from __future__ import annotations

import pandas as pd
import pytest
from cellpycore.config import CurveCols

from cellpy.plotting.collected import (
    _default_summary_y_label_mapper,
    _pretty_facet_annotation,
    _pretty_variable_label,
)

_CCOLS = CurveCols()


def _summary_frame() -> pd.DataFrame:
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
                    "value": 98.0,
                }
            )
    return pd.DataFrame(rows)


@pytest.mark.essential
def test_pretty_variable_label_strips_mode_suffix():
    assert _pretty_variable_label("charge_capacity_gravimetric") == "Charge Capacity (mAh/g)"
    assert _pretty_variable_label("coulombic_efficiency") == "Coulombic Efficiency (%)"
    assert (
        _pretty_variable_label("discharge_capacity_areal_cv")
        == "Discharge Capacity CV (mAh/cm**2)"
    )


@pytest.mark.essential
def test_pretty_variable_label_unknown_stays_unitless():
    assert _pretty_variable_label("some_custom_metric") == "Some Custom Metric"


@pytest.mark.essential
def test_default_summary_y_label_mapper():
    mapper = _default_summary_y_label_mapper(
        ["charge_capacity_gravimetric", "coulombic_efficiency"]
    )
    assert mapper["charge_capacity_gravimetric"] == "Charge Capacity (mAh/g)"
    assert mapper["coulombic_efficiency"] == "Coulombic Efficiency (%)"


@pytest.mark.essential
def test_summary_pretty_labels_clear_variable_facet_strip():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import summary_plotter

    theme.make_collector_templates()
    fig = summary_plotter(_summary_frame(), backend="plotly", group_cells=False)
    assert fig is not None
    texts = [getattr(a, "text", None) or "" for a in (fig.layout.annotations or ())]
    assert not any(t.startswith("variable=") for t in texts)
    from cellpy.plotting.collected import _plain_axis_title

    y_titles = [
        _plain_axis_title(fig.layout[k].title.text)
        for k in fig.layout
        if str(k).startswith("yaxis") and fig.layout[k].title.text
    ]
    assert "Charge Capacity (mAh/g)" in y_titles
    assert "Coulombic Efficiency (%)" in y_titles


@pytest.mark.essential
def test_summary_explicit_y_label_mapper_wins():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import summary_plotter

    theme.make_collector_templates()
    fig = summary_plotter(
        _summary_frame(),
        backend="plotly",
        group_cells=False,
        y_label_mapper={
            "charge_capacity_gravimetric": "Cap",
            "coulombic_efficiency": "CE",
        },
    )
    y_titles = [
        fig.layout[k].title.text
        for k in fig.layout
        if str(k).startswith("yaxis") and fig.layout[k].title.text
    ]
    assert "Cap" in y_titles
    assert "CE" in y_titles


@pytest.mark.essential
def test_summary_plotly_template_and_layout_updates():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import summary_plotter

    theme.make_collector_templates()
    fig_default = summary_plotter(
        _summary_frame(), backend="plotly", group_cells=False
    )
    fig = summary_plotter(
        _summary_frame(),
        backend="plotly",
        group_cells=False,
        plotly_template="plotly_white",
        layout_updates={"paper_bgcolor": "rgb(1,2,3)", "plot_bgcolor": "rgb(4,5,6)"},
    )
    assert fig is not None
    # Plotly expands the named template into a Template object (name not kept).
    assert str(fig.layout.template) != str(fig_default.layout.template)
    assert fig.layout.paper_bgcolor == "rgb(1,2,3)"
    assert fig.layout.plot_bgcolor == "rgb(4,5,6)"


@pytest.mark.essential
def test_summary_height_per_panel():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import summary_plotter

    theme.make_collector_templates()
    fig = summary_plotter(
        _summary_frame(),
        backend="plotly",
        group_cells=False,
        height_per_panel=180,
        figure_border_height=40,
        cols=1,
    )
    # 2 variables → 2 rows; height = border + rows * per_panel
    assert fig.layout.height == 40 + 2 * 180


@pytest.mark.essential
def test_collected_plot_forwards_app_hooks():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import collected_plot

    theme.make_collector_templates()
    fig = collected_plot(
        _summary_frame(),
        family_kind="summary",
        backend="plotly",
        group_cells=False,
        plotly_template="plotly_white",
        height_per_panel=150,
        figure_border_height=50,
        cols=1,
        layout_updates={"margin": dict(l=10, r=10, t=10, b=10)},
    )
    assert fig is not None
    assert fig.layout.height == 50 + 2 * 150
    assert fig.layout.margin.l == 10


def _cycles_frame() -> pd.DataFrame:
    rows = []
    for cell in ("demo", "other"):
        for cycle in (1, 2):
            for i, cap in enumerate((0.0, 0.5, 1.0)):
                rows.append(
                    {
                        "cell": cell,
                        "cycle_num": cycle,
                        _CCOLS.capacity: cap,
                        _CCOLS.potential: 3.5 - 0.1 * i,
                        "group": 1,
                        "sub_group": 1,
                    }
                )
    return pd.DataFrame(rows)


@pytest.mark.essential
def test_pretty_facet_annotation_cycles_and_cells():
    assert _pretty_facet_annotation("cycle_num=1") == "Cycle 1"
    assert _pretty_facet_annotation("cycle=10") == "Cycle 10"
    assert _pretty_facet_annotation("cell=demo") == "demo"
    assert _pretty_facet_annotation("variable=charge_capacity") == "variable=charge_capacity"
    assert _pretty_facet_annotation("nope") == "nope"


@pytest.mark.essential
def test_cycles_per_cell_facet_strips_are_pretty():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import collected_plot

    theme.make_collector_templates()
    fig = collected_plot(
        _cycles_frame(),
        family_kind="cycles",
        layout="per_cell",
        backend="plotly",
    )
    texts = [getattr(a, "text", None) or "" for a in (fig.layout.annotations or ())]
    assert texts
    assert not any("cell=" in t for t in texts)
    assert "demo" in texts
    assert "other" in texts


@pytest.mark.essential
def test_cycles_per_cycle_facet_strips_are_pretty():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import collected_plot

    theme.make_collector_templates()
    fig = collected_plot(
        _cycles_frame(),
        family_kind="cycles",
        layout="per_cycle",
        backend="plotly",
    )
    texts = [getattr(a, "text", None) or "" for a in (fig.layout.annotations or ())]
    assert texts
    assert not any(t.startswith("cycle_num=") or t.startswith("cycle=") for t in texts)
    assert "Cycle 1" in texts
    assert "Cycle 2" in texts
