"""Collected ICA line plots honour direction / both (#821)."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import pytest

from cellpy.plotting.collected import _select_direction


def _ica_frame() -> pd.DataFrame:
    """Tidy ICA frame with distinct charge vs discharge lobes."""
    rows = []
    for cell in ("a",):
        for cycle in (1, 2):
            for i, v in enumerate((0.1, 0.2, 0.3)):
                rows.append(
                    {
                        "cell": cell,
                        "group": 1,
                        "sub_group": 1,
                        "cycle": cycle,
                        "direction": "charge",
                        "voltage": v,
                        "capacity": float(i),
                        "dqdv": 10.0 + cycle + i,
                    }
                )
            for i, v in enumerate((0.3, 0.2, 0.1)):
                rows.append(
                    {
                        "cell": cell,
                        "group": 1,
                        "sub_group": 1,
                        "cycle": cycle,
                        "direction": "discharge",
                        "voltage": v,
                        "capacity": float(i),
                        # Distinct scale so charge vs discharge figures differ.
                        "dqdv": 1000.0 + cycle + i,
                    }
                )
    return pd.DataFrame(rows)


def _trace_ys(fig) -> list[float]:
    ys: list[float] = []
    for tr in fig.data:
        if tr.y is None:
            continue
        ys.extend(float(v) for v in np.asarray(tr.y).ravel() if v is not None)
    return ys


@pytest.mark.essential
def test_select_direction_both_leaves_frame_unchanged():
    frame = _ica_frame()
    out = _select_direction(frame, "both")
    assert len(out) == len(frame)
    assert set(out["direction"]) == {"charge", "discharge"}


@pytest.mark.essential
def test_ica_line_direction_charge_filters_half_cycles():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import ica_plotter

    theme.make_collector_templates()
    fig = ica_plotter(
        _ica_frame(),
        cycles_to_plot=[1, 2],
        backend="plotly",
        method="fig_pr_cell",
        direction="charge",
    )
    assert fig is not None
    ys = _trace_ys(fig)
    assert ys
    assert max(ys) < 100.0  # charge lobe only (dqdv ~10s)


@pytest.mark.essential
def test_ica_line_direction_discharge_differs_from_charge():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import ica_plotter

    theme.make_collector_templates()
    frame = _ica_frame()
    fig_c = ica_plotter(
        frame, cycles_to_plot=[1], backend="plotly", method="fig_pr_cell", direction="charge"
    )
    fig_d = ica_plotter(
        frame,
        cycles_to_plot=[1],
        backend="plotly",
        method="fig_pr_cell",
        direction="discharge",
    )
    ys_c = _trace_ys(fig_c)
    ys_d = _trace_ys(fig_d)
    assert max(ys_c) < 100.0
    assert min(ys_d) > 100.0


@pytest.mark.essential
def test_ica_line_direction_both_overlays_without_coerce():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import ica_plotter

    theme.make_collector_templates()
    fig = ica_plotter(
        _ica_frame(),
        cycles_to_plot=[1],
        backend="plotly",
        method="fig_pr_cell",
        direction="both",
    )
    assert fig is not None
    # line_dash splits charge/discharge into separate traces (no join).
    dashes = {getattr(tr.line, "dash", None) for tr in fig.data}
    assert len(dashes) >= 2
    ys = _trace_ys(fig)
    assert max(ys) > 100.0
    assert min(ys) < 100.0


@pytest.mark.essential
def test_ica_invalid_direction_warns_and_coerces(caplog):
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import ica_plotter

    theme.make_collector_templates()
    with caplog.at_level(logging.WARNING, logger="cellpy.plotting.collected"):
        fig = ica_plotter(
            _ica_frame(),
            cycles_to_plot=[1],
            backend="plotly",
            method="fig_pr_cell",
            direction="sideways",
        )
    assert fig is not None
    assert any("sideways" in r.message for r in caplog.records)
    ys = _trace_ys(fig)
    assert max(ys) < 100.0  # coerced to charge


@pytest.mark.essential
def test_collected_plot_ica_per_cell_honours_direction():
    pytest.importorskip("plotly", reason="plotting extras (batch) not installed")
    from cellpy.plotting import theme
    from cellpy.plotting.collected import collected_plot

    theme.make_collector_templates()
    fig = collected_plot(
        _ica_frame(),
        family_kind="ica",
        layout="per_cell",
        backend="plotly",
        direction="discharge",
        cycles=[1, 2],
    )
    assert fig is not None
    ys = _trace_ys(fig)
    assert min(ys) > 100.0
