"""Tests for shared cycle legend vs colorbar policy (#648)."""

from __future__ import annotations

import pytest

from cellpy.plotting.cycle_legend import (
    DEFAULT_LEGEND_CYCLE_LIMIT,
    pop_cycle_legend_options,
    resolve_cycle_legend_mode,
)


@pytest.mark.essential
@pytest.mark.parametrize(
    ("n", "kwargs", "expected"),
    [
        (1, {}, "legend"),
        (DEFAULT_LEGEND_CYCLE_LIMIT, {}, "legend"),
        (DEFAULT_LEGEND_CYCLE_LIMIT + 1, {}, "colorbar"),
        (3, {"force_colorbar": True}, "colorbar"),
        (20, {"force_legend": True}, "legend"),
        (20, {"force_colorbar": True, "force_legend": True}, "legend"),
    ],
)
def test_resolve_cycle_legend_mode(n, kwargs, expected):
    assert resolve_cycle_legend_mode(n, **kwargs) == expected


@pytest.mark.essential
def test_pop_cycle_legend_options_kwargs_win_and_consume():
    extras = {"legend_cycle_limit": 5, "force_colorbar": True}
    kwargs = {"legend_cycle_limit": 12, "force_nonbar": True}
    opts = pop_cycle_legend_options(extras, kwargs)
    assert opts == {
        "legend_cycle_limit": 12,
        "force_colorbar": True,
        "force_legend": True,
    }
    assert "legend_cycle_limit" not in kwargs
    assert "force_nonbar" not in kwargs
