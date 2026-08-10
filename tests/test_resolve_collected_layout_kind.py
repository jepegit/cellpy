"""resolve_collected_layout_kind validation and film alias (#874)."""

from __future__ import annotations

import pytest

from cellpy.plotting.collected import resolve_collected_layout_kind as r


@pytest.mark.essential
def test_defaults_are_per_cell_line():
    assert r() == ("per_cell", "line", "fig_pr_cell")


@pytest.mark.essential
def test_kind_film():
    assert r(kind="film") == ("per_cell", "film", "film")


@pytest.mark.essential
def test_layout_film_aliases_kind_film():
    assert r(layout="film") == ("per_cell", "film", "film")


@pytest.mark.essential
def test_layout_film_conflicts_with_other_kind():
    with pytest.raises(ValueError, match="conflicts"):
        r(layout="film", kind="line")


@pytest.mark.essential
@pytest.mark.parametrize(
    "kwargs,expected",
    [
        ({"layout": "per_cell"}, ("per_cell", "line", "fig_pr_cell")),
        ({"layout": "per_cycle"}, ("per_cycle", "line", "fig_pr_cycle")),
        ({"layout": "summary"}, ("summary", "line", "summary")),
        ({"method": "fig_pr_cycle"}, ("per_cycle", "line", "fig_pr_cycle")),
        ({"spread": True}, ("per_cell", "spread", "fig_pr_cell")),
        ({"kind": "spread", "layout": "summary"}, ("summary", "spread", "summary")),
    ],
)
def test_valid_resolutions(kwargs, expected):
    assert r(**kwargs) == expected


@pytest.mark.essential
def test_unknown_layout_raises():
    with pytest.raises(ValueError, match="Unknown layout"):
        r(layout="totally_bogus")


@pytest.mark.essential
def test_unknown_kind_raises():
    with pytest.raises(ValueError, match="Unknown kind"):
        r(kind="nope")


@pytest.mark.essential
def test_unknown_method_raises():
    with pytest.raises(ValueError, match="Unknown method"):
        r(method="totally_bogus")
