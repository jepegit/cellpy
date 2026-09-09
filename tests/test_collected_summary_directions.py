"""Collected summary panels: charge / discharge share a panel, dash = direction (#1009)."""

from __future__ import annotations

import pandas as pd
import pytest

from cellpy.plotting.collected import (
    _pretty_variable_label,
    _pretty_variable_name,
    split_direction,
)

_VARIABLES = (
    "charge_capacity_gravimetric",
    "discharge_capacity_gravimetric",
    "coulombic_efficiency",
)


def _frame(variables=_VARIABLES, cells=("a", "b")) -> pd.DataFrame:
    rows = []
    for cell in cells:
        for cycle in (1, 2, 3):
            for i, variable in enumerate(variables):
                rows.append(
                    {
                        "cycle": cycle,
                        "cell": cell,
                        "group": 1,
                        "sub_group": 1,
                        "variable": variable,
                        "value": 100.0 - cycle - 10 * i,
                    }
                )
    return pd.DataFrame(rows)


def _yaxes(fig) -> list:
    return [k for k in fig.layout if str(k).startswith("yaxis")]


def _plot(frame, **kwargs):
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import summary_plotter

    theme.make_collector_templates()
    return summary_plotter(frame, backend="plotly", group_cells=False, **kwargs)


@pytest.mark.essential
def test_split_direction_prefix_suffix_midname_and_none():
    assert split_direction("charge_capacity_gravimetric_cv") == ("capacity_gravimetric_cv", "charge")
    assert split_direction("discharge_capacity_areal") == ("capacity_areal", "discharge")
    assert split_direction("potential_end_charge") == ("potential_end", "charge")
    assert split_direction("test_cumulated_discharge_capacity_loss_gravimetric") == (
        "test_cumulated_capacity_loss_gravimetric",
        "discharge",
    )
    assert split_direction("mod_01_discharge_capacity_gravimetric") == (
        "mod_01_capacity_gravimetric",
        "discharge",
    )
    assert split_direction("coulombic_efficiency") == ("coulombic_efficiency", None)
    assert split_direction("ir_charge") == ("ir", "charge")


@pytest.mark.essential
def test_pretty_labels_for_panel_keys():
    assert _pretty_variable_label("capacity_gravimetric") == "Capacity (mAh/g)"
    assert _pretty_variable_label("capacity_gravimetric_non_cv") == "Capacity non-CV (mAh/g)"
    assert _pretty_variable_name("charge_capacity_areal_cv") == "Charge Capacity CV"
    assert _pretty_variable_label("mod_01_capacity_gravimetric") == "Normalized Capacity (%)"


@pytest.mark.essential
def test_charge_and_discharge_share_a_panel_with_dash_styles():
    fig = _plot(_frame())
    assert len(_yaxes(fig)) == 2  # capacity + CE, not 3

    series = [t for t in fig.data if t.legend != "legend2"]
    assert {t.name for t in series} == {"a", "b"}
    assert sum(1 for t in series if t.showlegend) == 2  # one entry per cell
    dashes = {t.line.dash for t in series}
    assert dashes == {"solid", "dash"}

    direction_legend = [t for t in fig.data if t.legend == "legend2"]
    assert [t.name for t in direction_legend] == ["Charge", "Discharge"]
    assert [t.line.dash for t in direction_legend] == ["solid", "dash"]
    assert fig.layout.legend2.title.text == "Direction"


@pytest.mark.essential
def test_combine_directions_false_keeps_one_facet_per_variable():
    fig = _plot(_frame(), combine_directions=False)
    assert len(_yaxes(fig)) == 3
    assert not [t for t in fig.data if t.legend == "legend2"]
    assert "legend2" not in fig.layout.to_plotly_json()


@pytest.mark.essential
def test_lone_direction_keeps_its_own_label_but_gets_the_dash():
    """Only ``charge_x`` present: no merge partner, so the panel stays "Charge …"."""
    fig = _plot(_frame(variables=("charge_capacity_gravimetric", "coulombic_efficiency")))
    titles = [fig.layout[k].title.text for k in _yaxes(fig)]
    assert any(t.startswith("Charge Capacity") for t in titles)
    assert [t.name for t in fig.data if t.legend == "legend2"] == ["Charge"]


@pytest.mark.essential
def test_no_direction_tokens_means_no_direction_legend():
    fig = _plot(_frame(variables=("coulombic_efficiency", "cumulated_step_time")))
    assert len(_yaxes(fig)) == 2
    assert not [t for t in fig.data if t.legend == "legend2"]
    assert "legend2" not in fig.layout.to_plotly_json()


@pytest.mark.essential
def test_y_ranges_accept_original_variable_names():
    fig = _plot(_frame(), y_ranges={"discharge_capacity_gravimetric": [0, 5]})
    ranged = [k for k in _yaxes(fig) if fig.layout[k].range is not None]
    assert len(ranged) == 1
    assert tuple(fig.layout[ranged[0]].range) == (0.0, 5.0)
    assert "Capacity" in fig.layout[ranged[0]].title.text


@pytest.mark.essential
def test_order_variables_accept_original_variable_names():
    fig = _plot(
        _frame(),
        order_variables=["coulombic_efficiency", "charge_capacity_gravimetric"],
    )
    # top facet is the one with the highest domain
    top = max(_yaxes(fig), key=lambda k: fig.layout[k].domain[1])
    assert "Coulombic" in fig.layout[top].title.text
