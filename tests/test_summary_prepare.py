"""Tests for summary prepare → FigureSpec (#638)."""

from __future__ import annotations

import pytest

from cellpy.plotting.context import from_source
from cellpy.plotting.prepare.summary import prepare
from cellpy.plotting import registry
from cellpy.utils.plotutils import SummaryPlotConfig, SummaryPlotInfo, summary_plot


@pytest.mark.essential
def test_prepare_returns_frame_and_figure_spec(cell):
    config = SummaryPlotConfig(y="capacities_gravimetric")
    family = registry.get(config.y)
    frame, spec = prepare(
        from_source(cell), family, config, plot_info=SummaryPlotInfo(cell)
    )
    assert frame is not None
    assert len(frame) > 0
    assert "value" in frame.columns
    assert "variable" in frame.columns
    assert spec.extras.get("x") is not None
    assert spec.extras.get("number_of_rows") == 1
    assert "prepared_data_info" in spec.extras
    assert "render" in spec.extras


@pytest.mark.essential
def test_prepare_ce_family_has_two_rows(cell):
    config = SummaryPlotConfig(y="capacities_gravimetric_coulombic_efficiency")
    family = registry.get(config.y)
    frame, spec = prepare(
        from_source(cell), family, config, plot_info=SummaryPlotInfo(cell)
    )
    assert spec.extras.get("number_of_rows") == 2
    assert "row" in frame.columns
    assert frame["row"].nunique() == 2
    render = spec.extras["render"]
    assert render.get("show_formation") is True
    assert render.get("formation_layout") is not None


@pytest.mark.essential
def test_return_data_frame_shape(cell):
    fig, data = summary_plot(
        cell,
        y="capacities_gravimetric",
        return_data=True,
        interactive=False,
        show_formation=False,
    )
    assert fig is not None
    assert "value" in data.columns
    assert "variable" in data.columns
    # cycle column is schema-bound (legacy cycle_index or native cycle_num)
    cycle_cols = {"cycle_index", "cycle_num"}
    assert cycle_cols.intersection(data.columns)


@pytest.mark.essential
def test_plotly_path_uses_backend(cell):
    pytest.importorskip("plotly")
    fig = summary_plot(
        cell,
        y="capacities_gravimetric",
        interactive=True,
        show_formation=True,
    )
    assert fig is not None
    assert hasattr(fig, "to_plotly_json")
