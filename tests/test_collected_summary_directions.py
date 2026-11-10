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

    series = list(fig.data)
    assert {t.name for t in series} == {"a", "b"}
    assert sum(1 for t in series if t.showlegend) == 2  # one entry per cell
    dashes = {t.line.dash for t in series}
    assert dashes == {"solid", "dash"}
    # One legend group per series, charge and discharge together (#1193).
    assert {t.legendgroup for t in series} == {"a", "b"}
    for name in ("a", "b"):
        grouped = {t.line.dash for t in series if t.legendgroup == name}
        assert grouped == {"solid", "dash"}

    buttons = _direction_buttons(fig)
    assert buttons["Charge"].args[0]["visible"] is False
    assert buttons["Charge"].args2[0]["visible"] is True


@pytest.mark.essential
def test_direction_buttons_hide_one_direction():
    """Charge hides charge traces only. CE stays out of both buttons (#1193)."""
    fig = _plot(_frame())
    buttons = _direction_buttons(fig)
    for label, token in (("Charge", "charge"), ("Discharge", "discharge")):
        indices = _button_indices(buttons[label])
        assert indices
        assert {_trace_direction(fig.data[i]) for i in indices} == {token}
        assert buttons[label].args[0]["visible"] is False
        assert buttons[label].args2[0]["visible"] is True
    chosen = set(_button_indices(buttons["Charge"])) | set(_button_indices(buttons["Discharge"]))
    plain = [i for i, trace in enumerate(fig.data) if _trace_direction(trace) == ""]
    assert plain
    assert not chosen.intersection(plain)


@pytest.mark.essential
def test_spread_direction_buttons_include_bands():
    """``spread=True`` toggles the mean line and both ±std bands (#1193)."""
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import summary_plotter

    theme.make_collector_templates()
    fig = summary_plotter(_frame().assign(mean=1.0, std=0.1), backend="plotly", spread=True)
    buttons = _direction_buttons(fig)
    for label, token in (("Charge", "charge"), ("Discharge", "discharge")):
        indices = _button_indices(buttons[label])
        names = [str(fig.data[i].name) for i in indices]
        assert {_trace_direction(fig.data[i]) for i in indices} == {token}
        assert any(not name.startswith(("Upper Bound", "Lower Bound")) for name in names)
        assert any(name.startswith("Upper Bound") for name in names)
        assert any(name.startswith("Lower Bound") for name in names)
    groups = {}
    for trace in fig.data:
        if str(trace.name).startswith(("Upper Bound", "Lower Bound")):
            continue
        groups.setdefault(trace.legendgroup, set()).add(trace.line.dash)
    assert groups
    for dashes in groups.values():
        assert "dash" in dashes
        assert "solid" in dashes


@pytest.mark.essential
def test_combine_directions_false_keeps_one_facet_per_variable():
    fig = _plot(_frame(), combine_directions=False)
    assert len(_yaxes(fig)) == 3
    _assert_no_direction_control(fig)


def _series_traces(fig):
    return [t for t in fig.data if getattr(t, "legend", None) != "legend2"]


def _trace_direction(trace) -> str:
    meta = getattr(trace, "meta", None)
    if isinstance(meta, dict):
        value = meta.get("direction") or ""
    else:
        value = ""
    return value if value in {"charge", "discharge"} else ""


def _direction_buttons(fig):
    menus = list(fig.layout.updatemenus or ())
    assert len(menus) == 1
    buttons = {button.label: button for button in menus[0].buttons}
    assert list(buttons) == ["Charge", "Discharge"]
    texts = [getattr(ann, "text", None) for ann in (fig.layout.annotations or ())]
    assert "Direction" in texts
    return buttons


def _button_indices(button) -> list[int]:
    return [int(i) for i in button.args[1]]


def _assert_no_direction_control(fig):
    assert not [t for t in fig.data if getattr(t, "legend", None) == "legend2"]
    assert "legend2" not in fig.layout.to_plotly_json()
    assert not list(fig.layout.updatemenus or ())
    texts = [getattr(ann, "text", None) for ann in (fig.layout.annotations or ())]
    assert "Direction" not in texts


@pytest.mark.essential
@pytest.mark.parametrize(
    "variable,word",
    [
        ("charge_capacity_gravimetric", "Charge"),
        ("discharge_capacity_gravimetric", "Discharge"),
    ],
)
def test_lone_direction_stays_solid_without_direction_legend(variable, word):
    """One direction in the frame: keep its y-title, solid line, no Direction legend."""
    fig = _plot(_frame(variables=(variable, "coulombic_efficiency")))
    titles = [fig.layout[k].title.text for k in _yaxes(fig)]
    assert any(t.startswith(f"{word} Capacity") for t in titles)
    assert {t.line.dash for t in _series_traces(fig)} <= {None, "solid"}
    _assert_no_direction_control(fig)


@pytest.mark.essential
def test_unpaired_direction_stays_solid_beside_a_combined_panel():
    """``ir_discharge`` alone stays solid even when capacity overlays both directions."""
    fig = _plot(
        _frame(
            variables=(
                "charge_capacity_gravimetric",
                "discharge_capacity_gravimetric",
                "ir_discharge",
            )
        )
    )
    buttons = _direction_buttons(fig)
    discharge_idx = set(_button_indices(buttons["Discharge"]))
    ir_keys = [k for k in _yaxes(fig) if "Ir" in (fig.layout[k].title.text or "")]
    assert len(ir_keys) == 1
    suffix = ir_keys[0].removeprefix("yaxis")
    trace_axis = "y" if suffix == "" else f"y{suffix}"
    ir_traces = [t for t in _series_traces(fig) if t.yaxis == trace_axis]
    assert ir_traces
    assert {t.line.dash for t in ir_traces} <= {None, "solid"}
    ir_positions = [i for i, t in enumerate(fig.data) if t.yaxis == trace_axis]
    assert not discharge_idx.intersection(ir_positions)


@pytest.mark.essential
def test_lone_discharge_spread_stays_solid():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import summary_plotter

    theme.make_collector_templates()
    frame = _frame(variables=("discharge_capacity_gravimetric",)).assign(mean=1.0, std=0.1)
    # ``mean`` marks a grouped frame, which sets ``group_cells`` itself.
    fig = summary_plotter(frame, backend="plotly", spread=True)
    dashes = {t.line.dash for t in fig.data if getattr(t.line, "dash", None)}
    assert "dash" not in dashes
    _assert_no_direction_control(fig)


@pytest.mark.essential
def test_no_direction_tokens_means_no_direction_legend():
    fig = _plot(_frame(variables=("coulombic_efficiency", "cumulated_step_time")))
    assert len(_yaxes(fig)) == 2
    _assert_no_direction_control(fig)


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
