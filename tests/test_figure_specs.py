"""The figure menu is a contract (#567).

The plotting redesign moves ~11 000 lines across three modules. These tests
compare the live figures against ``tests/data/figure_specs.json`` so that
moving the code cannot quietly change what is drawn.

If a change to a figure is *intended*, regenerate the snapshot in the same
commit — that makes it visible in review instead of invisible:

```shell
uv sync --extra batch
uv run python dev/snapshot_figure_specs.py
```
"""

from __future__ import annotations

import json
import logging

import pytest

from cellpy import log
from tests.figure_spec_support import (
    FIGURE_CASES,
    SNAPSHOT_PATH,
    FigureCase,
    describe_figure,
    render_case,
    plotly_available,
    seaborn_available,
)

log.setup_logging(default_level=logging.DEBUG, testing=True)

#: Data endpoints are compared with a tolerance rather than exactly. Figure
#: values come out of interpolation and unit conversion, and the ICA goldens
#: (#566) showed those differ between platforms at ~5e-7 relative.
VALUE_TOLERANCE = 1e-5


@pytest.fixture(scope="module")
def expected() -> dict:
    if not SNAPSHOT_PATH.is_file():
        pytest.skip(f"missing snapshot {SNAPSHOT_PATH}")
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))["figures"]


@pytest.fixture(scope="module")
def cell():
    from tests.figure_spec_support import load_figure_cell

    return load_figure_cell()


def _case_id(case: FigureCase) -> str:
    return case.name


def _compare_series(actual: dict, want: dict, where: str) -> list[str]:
    problems = []
    if actual["n"] != want["n"]:
        problems.append(f"{where}: {want['n']} points -> {actual['n']}")
    for edge in ("first", "last"):
        a, w = actual[edge], want[edge]
        if a is None or w is None:
            if a is not w:
                problems.append(f"{where}.{edge}: {w} -> {a}")
            continue
        if w == 0:
            if abs(a) > VALUE_TOLERANCE:
                problems.append(f"{where}.{edge}: {w} -> {a}")
        elif abs(a - w) / abs(w) > VALUE_TOLERANCE:
            problems.append(f"{where}.{edge}: {w} -> {a}")
    return problems


def _compare_plotly(actual: dict, want: dict) -> list[str]:
    problems = []
    if actual["n_traces"] != want["n_traces"]:
        problems.append(f"trace count: {want['n_traces']} -> {actual['n_traces']}")
        return problems

    for index, (a, w) in enumerate(zip(actual["traces"], want["traces"])):
        tag = f"trace[{index}] {w.get('name')!r}"
        for key in ("name", "type", "mode", "xaxis", "yaxis"):
            if a.get(key) != w.get(key):
                problems.append(f"{tag}.{key}: {w.get(key)!r} -> {a.get(key)!r}")
        problems += _compare_series(a["x"], w["x"], f"{tag}.x")
        problems += _compare_series(a["y"], w["y"], f"{tag}.y")

    if actual["axis_titles"] != want["axis_titles"]:
        problems.append(
            f"axis titles: {want['axis_titles']} -> {actual['axis_titles']}"
        )
    return problems


def _compare_matplotlib(actual: dict, want: dict) -> list[str]:
    problems = []
    if actual["n_panels"] != want["n_panels"]:
        problems.append(f"panel count: {want['n_panels']} -> {actual['n_panels']}")
        return problems

    for index, (a, w) in enumerate(zip(actual["panels"], want["panels"])):
        tag = f"panel[{index}]"
        for key in ("title", "xlabel", "ylabel", "n_lines", "n_collections"):
            if a.get(key) != w.get(key):
                problems.append(f"{tag}.{key}: {w.get(key)!r} -> {a.get(key)!r}")
        if a["n_lines"] != w["n_lines"]:
            continue
        for line_index, (al, wl) in enumerate(zip(a["lines"], w["lines"])):
            line_tag = f"{tag}.line[{line_index}] {wl.get('label')!r}"
            if al.get("label") != wl.get("label"):
                problems.append(
                    f"{line_tag}.label: {wl.get('label')!r} -> {al.get('label')!r}"
                )
            problems += _compare_series(al["x"], wl["x"], f"{line_tag}.x")
            problems += _compare_series(al["y"], wl["y"], f"{line_tag}.y")
    return problems


@pytest.mark.parametrize("case", FIGURE_CASES, ids=_case_id)
def test_figure_structure_matches_the_snapshot(case: FigureCase, expected, cell):
    reason = case.skip_reason()
    if reason:
        pytest.skip(reason)
    if case.name not in expected:
        pytest.skip(f"{case.name} is not in the snapshot; regenerate it")

    want = expected[case.name]
    actual = render_case(case, cell)

    assert actual["backend"] == want["backend"], (
        f"{case.name}: backend {want['backend']} -> {actual['backend']}"
    )

    # `cycle_info_plot` (both backends) and `cycles_plot` under plotly return
    # None rather than a figure, while `summary_plot`, `raw_plot` and
    # `cycles_plot` under matplotlib return one. That asymmetry is recorded
    # here as today's contract, not endorsed — unifying the return value is a
    # user-visible change and belongs with the redesign, not with its oracle.
    if want.get("empty"):
        assert actual.get("empty"), f"{case.name} now returns a figure"
        return

    if want["backend"] == "plotly":
        problems = _compare_plotly(actual, want)
    else:
        problems = _compare_matplotlib(actual, want)

    assert not problems, f"{case.name} changed:\n  " + "\n  ".join(problems)


@pytest.mark.essential
def test_the_snapshot_covers_the_whole_menu(expected):
    """A snapshot that quietly lost half its cases would pass everything."""
    if not (plotly_available and seaborn_available):
        pytest.skip("the full menu needs plotly and seaborn")
    missing = [c.name for c in FIGURE_CASES if c.name not in expected]
    assert not missing, f"cases with no snapshot: {missing}"
    assert len(expected) >= 50


@pytest.mark.essential
def test_plotting_does_not_mutate_the_cell(cell):
    """Drawing a figure must not change the data it drew from.

    `partition_summary_cv_steps` used to `set_index(..., inplace=True)` on
    `c.data.summary` itself, so one CV-split plot permanently removed the
    cycle column from the user's cell and broke every later plot (#567).
    """
    summary_before = list(cell.data.summary.columns)
    raw_before = list(cell.data.raw.columns)
    steps_before = list(cell.data.steps.columns)
    n_rows_before = len(cell.data.summary)

    from cellpy.utils.plotutils import summary_plot

    summary_plot(
        cell, y="capacities_gravimetric_split_constant_voltage", interactive=False
    )

    assert list(cell.data.summary.columns) == summary_before
    assert list(cell.data.raw.columns) == raw_before
    assert list(cell.data.steps.columns) == steps_before
    assert len(cell.data.summary) == n_rows_before


@pytest.mark.essential
def test_describe_figure_rejects_a_non_figure():
    with pytest.raises(TypeError, match="cannot describe"):
        describe_figure(object())
