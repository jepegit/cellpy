"""Collected per-cell layouts follow the cycle legend/colorbar policy (#928).

``cycles_collector(b).plot(layout="per_cell")`` used to always colour by cycle
with a discrete legend, so a full batch produced a legend hundreds of entries
long. The single-cell ``cycles_plot`` has had the
:mod:`cellpy.plotting.cycle_legend` rule since #648; these tests pin the
collected path to the same rule and the same default limit.
"""

from __future__ import annotations

import pandas as pd
import pytest

from cellpy.plotting.cycle_legend import DEFAULT_LEGEND_CYCLE_LIMIT

pytest.importorskip("plotly", reason="plotting extras (batch) not installed")

from cellpy.plotting.collected import collected_plot  # noqa: E402


def _curves(n_cycles: int, cells: tuple[str, ...] = ("a", "b")) -> pd.DataFrame:
    rows = []
    for cell in cells:
        for cycle in range(1, n_cycles + 1):
            for capacity, potential in ((0.0, 0.1), (float(cycle), 0.2)):
                rows.append(
                    {
                        "cell": cell,
                        "cycle_num": cycle,
                        "capacity": capacity,
                        "potential": potential,
                        "group": 1,
                        "sub_group": 1,
                    }
                )
    return pd.DataFrame(rows)


def _legend_entries(fig) -> int:
    return sum(1 for trace in fig.data if trace.showlegend is not False)


def _colorbars(fig) -> int:
    return sum(1 for trace in fig.data if getattr(trace.marker, "showscale", None))


@pytest.mark.essential
def test_many_cycles_get_a_colorbar_not_a_long_legend():
    fig = collected_plot(
        _curves(DEFAULT_LEGEND_CYCLE_LIMIT + 5), family_kind="cycles", layout="per_cell"
    )
    assert _colorbars(fig) == 1
    assert _legend_entries(fig) == 0


@pytest.mark.essential
def test_few_cycles_keep_the_discrete_legend():
    fig = collected_plot(
        _curves(DEFAULT_LEGEND_CYCLE_LIMIT), family_kind="cycles", layout="per_cell"
    )
    assert _colorbars(fig) == 0
    assert _legend_entries(fig) == DEFAULT_LEGEND_CYCLE_LIMIT


@pytest.mark.essential
def test_force_colorbar_overrides_a_short_cycle_list():
    fig = collected_plot(
        _curves(3), family_kind="cycles", layout="per_cell", force_colorbar=True
    )
    assert _colorbars(fig) == 1
    assert _legend_entries(fig) == 0


@pytest.mark.essential
def test_force_legend_overrides_a_long_cycle_list():
    fig = collected_plot(
        _curves(DEFAULT_LEGEND_CYCLE_LIMIT + 5),
        family_kind="cycles",
        layout="per_cell",
        force_legend=True,
    )
    assert _colorbars(fig) == 0
    assert _legend_entries(fig) == DEFAULT_LEGEND_CYCLE_LIMIT + 5


@pytest.mark.essential
def test_legend_cycle_limit_raises_the_threshold():
    n = DEFAULT_LEGEND_CYCLE_LIMIT + 5
    fig = collected_plot(
        _curves(n), family_kind="cycles", layout="per_cell", legend_cycle_limit=n
    )
    assert _colorbars(fig) == 0
    assert _legend_entries(fig) == n


@pytest.mark.essential
def test_per_cycle_layout_is_untouched_by_the_cycle_policy():
    """``per_cycle`` colours by cell, so the cycle rule must not fire (#928)."""
    fig = collected_plot(
        _curves(DEFAULT_LEGEND_CYCLE_LIMIT + 5),
        family_kind="cycles",
        layout="per_cycle",
    )
    assert _colorbars(fig) == 0
    assert _legend_entries(fig) > 0
