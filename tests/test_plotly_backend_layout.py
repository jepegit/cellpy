"""Unit tests for the generic plotly formation layout engine (#637)."""

from __future__ import annotations

import pytest

plotly = pytest.importorskip("plotly")
import plotly.graph_objects as go

from cellpy.plotting.backends.base import Backend
from cellpy.plotting.backends.plotly import (
    MAX_FORMATIONATION_ROWS,
    PlotlyBackend,
    configure_formation_layout,
)
from cellpy.utils import plotutils


def _blank_fig() -> go.Figure:
    return go.Figure(data=[go.Scatter(x=[1, 2], y=[1, 2])])


@pytest.mark.essential
@pytest.mark.parametrize("n_rows", [1, 2, 3, 4])
def test_configure_formation_layout_annotation_count(n_rows):
    fig = _blank_fig()
    configure_formation_layout(
        fig,
        n_rows=n_rows,
        x_axis_domain_formation=[0.0, 0.2],
        x_axis_domain_rest=[0.21, 0.95],
        x_axis_range_formation=[0, 3],
        x_axis_range_rest=[3, 10],
    )
    assert len(fig.layout.annotations) == 2 * n_rows


@pytest.mark.essential
def test_configure_formation_layout_rejects_too_many_rows():
    fig = _blank_fig()
    with pytest.raises(NotImplementedError, match="more than four"):
        configure_formation_layout(
            fig,
            n_rows=MAX_FORMATIONATION_ROWS + 1,
            x_axis_domain_formation=[0.0, 0.2],
            x_axis_domain_rest=[0.21, 0.95],
            x_axis_range_formation=[0, 3],
            x_axis_range_rest=[3, 10],
        )


@pytest.mark.essential
def test_per_row_count_methods_are_gone():
    builder = plotutils.PlotlyPlotBuilder()
    assert not hasattr(builder, "_configure_formation_1_row")
    assert not hasattr(builder, "_configure_formation_2_rows")
    assert not hasattr(builder, "_configure_formation_3_rows")
    assert not hasattr(builder, "_configure_formation_4_rows")


@pytest.mark.essential
def test_plotly_backend_satisfies_protocol():
    assert isinstance(PlotlyBackend(), Backend)
