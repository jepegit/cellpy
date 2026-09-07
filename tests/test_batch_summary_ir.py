"""Batch cycle-life IR panel: direction pick, fallback, warn (#949)."""

from __future__ import annotations

import importlib.util
import warnings

import pandas as pd
import pytest

from cellpy.parameters.internal_settings import get_headers_journal, get_headers_summary
from cellpy.plotting.batch_summary import (
    _pick_optional_summary,
    _select_ir_column,
    generate_summary_frame_for_plotting,
    plot_cycle_life_summary_plotly,
)

plotly_available = importlib.util.find_spec("plotly") is not None

hdr = get_headers_summary()
hdr_journal = get_headers_journal()


def _farms(*variables: str) -> list[pd.DataFrame]:
    idx = pd.Index([1, 2, 3], name=hdr.cycle_index)
    farms = []
    for var in variables:
        farm = pd.DataFrame({"cell_a": [1.0, 2.0, 3.0], "cell_b": [1.5, 2.5, 3.5]}, index=idx)
        farm.name = var
        farms.append(farm)
    return farms


def _pages() -> pd.DataFrame:
    cells = ["cell_a", "cell_b"]
    return pd.DataFrame(
        {
            hdr_journal.group: [1, 1],
            hdr_journal.sub_group: [1, 2],
            hdr_journal.mass: [1.0, 1.0],
            hdr_journal.total_mass: [1.0, 1.0],
            hdr_journal.loading: [1.0, 1.0],
            hdr_journal.nom_cap: [1.0, 1.0],
            hdr_journal.area: [1.0, 1.0],
            hdr_journal.label: cells,
            hdr_journal.cell_type: ["x", "x"],
            hdr_journal.instrument: ["a", "a"],
        },
        index=pd.Index(cells, name="cell"),
    )


class _Experiment:
    def __init__(self, farms: list[pd.DataFrame]) -> None:
        self.memory_dumped = {"summary_engine": farms}


_CORE = (
    hdr.coulombic_efficiency,
    hdr["charge_capacity_gravimetric"],
    hdr["discharge_capacity_gravimetric"],
)


def _frame(*extra: str) -> pd.DataFrame:
    return generate_summary_frame_for_plotting(_pages(), _Experiment(_farms(*_CORE, *extra)))


def _title(fig) -> str:
    return fig.layout.title.text or ""


@pytest.mark.essential
def test_pick_optional_summary_prefers_then_falls_back():
    available = [hdr.ir_charge]
    assert _pick_optional_summary(available, hdr.ir_discharge, hdr.ir_charge) == hdr.ir_charge
    assert _pick_optional_summary(available, hdr.ir_charge, hdr.ir_discharge) == hdr.ir_charge
    assert _pick_optional_summary(available, hdr.ir_discharge, None) is None


@pytest.mark.essential
def test_select_ir_falls_back_and_warns():
    with pytest.warns(UserWarning, match="has no ir_discharge"):
        picked = _select_ir_column([hdr.ir_charge], "discharge", ir=True)
    assert picked == hdr.ir_charge


@pytest.mark.essential
def test_select_ir_warns_when_neither_column_exists():
    with pytest.warns(UserWarning, match="skipping the IR panel"):
        assert _select_ir_column(["coulombic_efficiency"], "discharge", ir=True) is None


@pytest.mark.essential
def test_select_ir_false_is_silent():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", UserWarning)
        assert _select_ir_column([hdr.ir_charge], "discharge", ir=False) is None
    assert not [w for w in caught if issubclass(w.category, UserWarning)]


@pytest.mark.essential
@pytest.mark.skipif(not plotly_available, reason="plotly extra not installed")
def test_discharge_direction_uses_ir_discharge_when_present():
    frame = _frame(hdr.ir_charge, hdr.ir_discharge)
    fig = plot_cycle_life_summary_plotly(frame, ir=True, direction="discharge")
    assert "IR (discharge)" in _title(fig)
    assert "IR (charge)" not in _title(fig)


@pytest.mark.essential
@pytest.mark.skipif(not plotly_available, reason="plotly extra not installed")
def test_discharge_direction_falls_back_to_ir_charge():
    frame = _frame(hdr.ir_charge)
    with pytest.warns(UserWarning, match="has no ir_discharge"):
        fig = plot_cycle_life_summary_plotly(frame, ir=True, direction="discharge")
    assert "IR (charge)" in _title(fig)


@pytest.mark.essential
@pytest.mark.skipif(not plotly_available, reason="plotly extra not installed")
def test_ir_false_omits_the_panel_even_when_columns_exist():
    frame = _frame(hdr.ir_charge, hdr.ir_discharge)
    fig = plot_cycle_life_summary_plotly(frame, ir=False, direction="discharge")
    assert "IR (" not in _title(fig)


@pytest.mark.essential
@pytest.mark.skipif(not plotly_available, reason="plotly extra not installed")
def test_missing_ir_columns_warn_and_skip_the_panel():
    frame = _frame()
    with pytest.warns(UserWarning, match="skipping the IR panel"):
        fig = plot_cycle_life_summary_plotly(frame, ir=True, direction="discharge")
    assert "IR (" not in _title(fig)
