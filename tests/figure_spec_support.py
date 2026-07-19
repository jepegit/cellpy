"""Structural figure snapshots for the plotting redesign (#567, Phase 0).

The plotting stack is ~11 000 lines across three modules with four overlapping
generations, and the redesign moves all of it. Pixel diffing is the wrong
instrument — brittle, huge, and it tells you *that* something moved, not what.
These snapshots record the **structure** of each figure instead: how many
traces, on which axes, with which names, how many points, and what the axis
titles say.

That is enough to catch the failures that matter in a refactor of this kind —
a lost trace, a panel that stopped being drawn, a mislabelled axis, a series
plotted against the wrong column — while staying stable across plotly and
matplotlib version bumps.

Both backends are described into the *same* shape, so the plan's "one spec,
two renderers" claim becomes checkable: a family that renders differently
under plotly and matplotlib shows up as a diff between two entries here.
"""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = REPO_ROOT / "tests" / "data" / "figure_specs.json"

plotly_available = importlib.util.find_spec("plotly") is not None
seaborn_available = importlib.util.find_spec("seaborn") is not None

#: Values are rounded before they are recorded. Figure data is derived through
#: interpolation and unit conversion, so the last bits differ between
#: platforms — the ICA goldens (#566) were bitten by exactly that.
VALUE_DIGITS = 6


def _round(value: Any) -> Any:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number:  # NaN
        return None
    return round(number, VALUE_DIGITS)


def _series_fingerprint(values) -> dict[str, Any]:
    """Length plus endpoints — enough to spot a series plotted from the wrong column."""
    try:
        sequence = list(values)
    except TypeError:
        return {"n": 0, "first": None, "last": None}
    if not sequence:
        return {"n": 0, "first": None, "last": None}
    return {
        "n": len(sequence),
        "first": _round(sequence[0]),
        "last": _round(sequence[-1]),
    }


def _describe_plotly(figure) -> dict[str, Any]:
    document = figure.to_dict()
    layout = document.get("layout", {})

    traces = []
    for trace in document.get("data", []):
        traces.append(
            {
                "name": trace.get("name"),
                "type": trace.get("type"),
                "mode": trace.get("mode"),
                "xaxis": trace.get("xaxis", "x"),
                "yaxis": trace.get("yaxis", "y"),
                "x": _series_fingerprint(trace.get("x")),
                "y": _series_fingerprint(trace.get("y")),
            }
        )

    axis_titles = {}
    for key, value in layout.items():
        if not key.startswith(("xaxis", "yaxis")):
            continue
        if isinstance(value, dict):
            title = value.get("title")
            if isinstance(title, dict):
                title = title.get("text")
            axis_titles[key] = title

    return {
        "backend": "plotly",
        "n_traces": len(traces),
        "traces": traces,
        "axis_titles": dict(sorted(axis_titles.items())),
        "n_axes": len(axis_titles),
    }


def _describe_matplotlib(figure) -> dict[str, Any]:
    panels = []
    for axes in figure.get_axes():
        lines = []
        for line in axes.get_lines():
            lines.append(
                {
                    "label": line.get_label(),
                    "x": _series_fingerprint(line.get_xdata()),
                    "y": _series_fingerprint(line.get_ydata()),
                }
            )
        panels.append(
            {
                "title": axes.get_title(),
                "xlabel": axes.get_xlabel(),
                "ylabel": axes.get_ylabel(),
                "n_lines": len(lines),
                "n_collections": len(axes.collections),
                "lines": lines,
            }
        )

    return {
        "backend": "matplotlib",
        "n_panels": len(panels),
        "panels": panels,
    }


def describe_figure(figure) -> dict[str, Any]:
    """Describe *figure* structurally, whichever backend produced it."""
    if figure is None:
        return {"backend": None, "empty": True}
    if hasattr(figure, "to_dict") and hasattr(figure, "data"):
        return _describe_plotly(figure)
    if hasattr(figure, "get_axes"):
        return _describe_matplotlib(figure)
    raise TypeError(f"cannot describe a figure of type {type(figure)!r}")


# --- the figure menu ---------------------------------------------------------

#: Every predefined y-set `summary_plot` accepts, read off `_create_col_info`.
#: A family missing from this list is a family with no regression net.
SUMMARY_FAMILIES = (
    "voltages",
    "capacities",
    "capacities_gravimetric",
    "capacities_areal",
    "capacities_absolute",
    "capacities_gravimetric_split_constant_voltage",
    "capacities_areal_split_constant_voltage",
    "capacities_gravimetric_coulombic_efficiency",
    "capacities_areal_coulombic_efficiency",
    "capacities_absolute_coulombic_efficiency",
    "capacities_gravimetric_with_rate",
    "capacities_areal_with_rate",
    "capacities_absolute_with_rate",
    "fullcell_standard_gravimetric",
    "fullcell_standard_areal",
    "fullcell_standard_absolute",
    "fullcell_standard_cumloss_gravimetric",
    "fullcell_standard_cumloss_areal",
    "fullcell_standard_cumloss_absolute",
    "fullcell_standard_dev",
)


@dataclass(frozen=True)
class FigureCase:
    """One figure in the menu."""

    name: str
    function: str
    kwargs: dict[str, Any] = field(default_factory=dict)
    needs_plotly: bool = False
    needs_seaborn: bool = False

    def skip_reason(self) -> str | None:
        if self.needs_plotly and not plotly_available:
            return "plotly not installed"
        if self.needs_seaborn and not seaborn_available:
            return "seaborn not installed"
        return None


def _summary_cases() -> list[FigureCase]:
    cases: list[FigureCase] = []
    for family in SUMMARY_FAMILIES:
        cases.append(
            FigureCase(
                name=f"summary_plot[{family}][plotly]",
                function="summary_plot",
                kwargs={"y": family, "interactive": True},
                needs_plotly=True,
            )
        )
        cases.append(
            FigureCase(
                name=f"summary_plot[{family}][matplotlib]",
                function="summary_plot",
                kwargs={"y": family, "interactive": False},
                needs_seaborn=True,
            )
        )
    return cases


#: Options that change layout rather than data — the ones a layout engine
#: rewrite is most likely to break.
def _summary_option_cases() -> list[FigureCase]:
    family = "capacities_gravimetric_coulombic_efficiency"
    variants = {
        "no_formation": {"show_formation": False},
        "formation_10": {"formation_cycles": 10},
        "no_legend": {"show_legend": False},
        "no_markers": {"markers": False},
        "shared_y": {"share_y": True},
        "titled": {"title": "a title"},
        "x_cycle_index_legacy_spelling": {"x": "cycle_index"},
    }
    cases = []
    for label, kwargs in variants.items():
        cases.append(
            FigureCase(
                name=f"summary_plot[{label}][plotly]",
                function="summary_plot",
                kwargs={"y": family, "interactive": True, **kwargs},
                needs_plotly=True,
            )
        )
    return cases


def _other_family_cases() -> list[FigureCase]:
    return [
        FigureCase(
            name="raw_plot[plotly]",
            function="raw_plot",
            kwargs={"interactive": True},
            needs_plotly=True,
        ),
        FigureCase(
            name="raw_plot[matplotlib]",
            function="raw_plot",
            kwargs={"interactive": False},
        ),
        FigureCase(
            name="cycle_info_plot[plotly]",
            function="cycle_info_plot",
            kwargs={"cycle": 3, "interactive": True},
            needs_plotly=True,
        ),
        FigureCase(
            name="cycle_info_plot[matplotlib]",
            function="cycle_info_plot",
            kwargs={"cycle": 3, "interactive": False},
        ),
        FigureCase(
            name="cycles_plot[plotly]",
            function="cycles_plot",
            kwargs={"interactive": True},
            needs_plotly=True,
        ),
        FigureCase(
            name="cycles_plot[matplotlib]",
            function="cycles_plot",
            kwargs={"interactive": False},
        ),
    ]


FIGURE_CASES: tuple[FigureCase, ...] = tuple(
    _summary_cases() + _summary_option_cases() + _other_family_cases()
)


def load_figure_cell():
    """The canonical Arbin cell, with the summary the plots need."""
    from tests.ica_golden_support import load_golden_cell

    return load_golden_cell()


def render_case(case: FigureCase, cell) -> dict[str, Any]:
    """Render one case and return its structural description."""
    import matplotlib

    matplotlib.use("Agg")

    from cellpy.utils import plotutils

    function: Callable = getattr(plotutils, case.function)
    figure = function(cell, **case.kwargs)
    description = describe_figure(figure)

    # Free the matplotlib figure; the menu renders ~50 of them in one process.
    if hasattr(figure, "get_axes"):
        import matplotlib.pyplot as plt

        plt.close(figure)

    return description


def build_figure_specs(cell=None) -> dict[str, Any]:
    """Render the whole menu and describe each figure."""
    if cell is None:
        cell = load_figure_cell()

    specs: dict[str, Any] = {}
    for case in FIGURE_CASES:
        if case.skip_reason():
            continue
        specs[case.name] = render_case(case, cell)
    return {"figures": specs}
