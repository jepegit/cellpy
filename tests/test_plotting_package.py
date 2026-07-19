"""The consolidated plotting plumbing (#567 Phase 1).

Phase 1 moved the verifiably duplicated helpers into `cellpy.plotting`. These
tests pin the two things that matter about a move like that: there is now
exactly *one* implementation, and the old import paths still resolve to it.
"""

from __future__ import annotations

import importlib.util
import logging
import pickle

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import pytest

from cellpy import log, plotting
from cellpy.plotting import figures, labels, theme

log.setup_logging(default_level=logging.DEBUG, testing=True)

plotly_available = importlib.util.find_spec("plotly") is not None


# --- one implementation, reachable from the old names ------------------------


@pytest.mark.essential
def test_figure_io_is_one_implementation():
    """These five existed as full copies in plotutils *and* collectors."""
    from cellpy.utils import collectors, plotutils

    for name in (
        "load_figure",
        "load_plotly_figure",
        "load_matplotlib_figure",
        "save_matplotlib_figure",
        "make_matplotlib_manager",
    ):
        canonical = getattr(figures, name)
        assert getattr(plotutils, name) is canonical, name
        assert getattr(collectors, name) is canonical, name


@pytest.mark.essential
def test_legend_and_marker_helpers_are_one_implementation():
    """These existed in three places under two naming conventions."""
    from cellpy.utils import collectors, plotutils
    from cellpy.utils.batch_tools import batch_plotters

    assert plotutils._plotly_legend_replacer is labels.legend_replacer
    assert collectors.legend_replacer is labels.legend_replacer
    assert batch_plotters._plotly_legend_replacer is labels.legend_replacer

    assert plotutils._plotly_remove_markers is labels.remove_markers
    assert collectors.remove_markers is labels.remove_markers
    assert batch_plotters._plotly_remove_markers is labels.remove_markers


@pytest.mark.essential
def test_template_builder_is_one_implementation():
    from cellpy.utils import plotutils
    from cellpy.utils.batch_tools import batch_plotters

    assert plotutils._make_plotly_template is theme.make_plotly_template
    assert batch_plotters._make_plotly_template is theme.make_plotly_template


@pytest.mark.essential
def test_the_package_exports_what_it_owns():
    for name in plotting.__all__:
        assert hasattr(plotting, name), name


# --- collectors imports without the plotting extras ---------------------------


@pytest.mark.essential
def test_collectors_has_no_import_time_plotly_calls():
    """`import cellpy.utils.collectors` used to raise NameError: 'go'.

    Four `go.layout.Template(...)` calls ran at module level, so the module was
    simply unimportable on an install without the `batch` extra. They are built
    lazily in theme.py now.
    """
    import ast
    import pathlib

    source = (
        pathlib.Path(__file__).resolve().parents[1] / "cellpy" / "utils" / "collectors.py"
    ).read_text(encoding="utf-8")

    plotly_aliases = {"go", "pio", "px", "plotly"}
    offenders = []

    class ImportTimeVisitor(ast.NodeVisitor):
        """Visit only what actually executes when the module is imported.

        Function bodies do not run at import, so they are skipped. Class
        bodies *do* run, so they are visited — but the methods inside them are
        function definitions and are skipped in turn.
        """

        def visit_FunctionDef(self, node):
            return

        visit_AsyncFunctionDef = visit_FunctionDef

        def visit_Attribute(self, node):
            root = node
            while isinstance(root, ast.Attribute):
                root = root.value
            if isinstance(root, ast.Name) and root.id in plotly_aliases:
                offenders.append(f"line {node.lineno}: {root.id}.…")
            self.generic_visit(node)

    ImportTimeVisitor().visit(ast.parse(source))

    assert not offenders, (
        "plotly is touched at import time again, which makes collectors "
        f"unimportable without the batch extra: {offenders}"
    )


# --- behaviour ----------------------------------------------------------------


@pytest.mark.essential
def test_load_figure_picks_the_backend_from_the_suffix(tmp_path):
    fig = plt.figure()
    target = tmp_path / "a_figure.pkl"
    figures.save_matplotlib_figure(fig, target)
    plt.close(fig)

    loaded = figures.load_figure(target)
    assert loaded is not None
    assert hasattr(loaded, "get_axes")


@pytest.mark.essential
def test_load_figure_reports_an_unknown_backend(tmp_path, caplog):
    target = tmp_path / "a_figure.pkl"
    target.write_bytes(b"")
    with caplog.at_level(logging.WARNING):
        assert figures.load_figure(target, backend="bokeh") is None
    assert "not supported" in caplog.text


@pytest.mark.essential
def test_load_plotly_figure_degrades_instead_of_raising(tmp_path):
    """The unguarded collectors copy raised here; the kept copy returns None."""
    target = tmp_path / "not_really_json.json"
    target.write_text("definitely not a figure", encoding="utf-8")
    assert figures.load_plotly_figure(target) is None


@pytest.mark.essential
def test_matplotlib_round_trip_with_a_new_manager(tmp_path):
    fig = plt.figure()
    fig.add_subplot(111).plot([0, 1], [1, 0])
    target = tmp_path / "round_trip.pkl"
    figures.save_matplotlib_figure(fig, target)
    plt.close(fig)

    loaded = figures.load_matplotlib_figure(target, create_new_manager=True)
    assert loaded.canvas.manager is not None
    assert len(loaded.get_axes()) == 1
    plt.close(loaded)


# --- the legend replacer -------------------------------------------------------


class _FakeTrace:
    """Enough of a plotly trace to exercise the label logic without plotly."""

    def __init__(self, name):
        self.name = name
        self.hovertemplate = "y=%{y}"
        self.legendgroup = None
        self.marker = object()
        self.mode = "markers"

    def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@pytest.fixture
def journal():
    from cellpy.parameters.internal_settings import get_headers_journal

    hdr = get_headers_journal()
    return pd.DataFrame(
        {
            hdr.group: [1, 1, 2],
            hdr.sub_group: [1, 2, 1],
            "cell": ["cell_a", "cell_b", "cell_c"],
        }
    )


@pytest.mark.essential
def test_legend_replacer_substitutes_the_cell_name(journal):
    trace = labels.legend_replacer(_FakeTrace("1,2"), journal)
    assert trace.name == "cell_b"
    assert trace.hovertemplate.startswith("cell_b<br>")


@pytest.mark.essential
def test_legend_replacer_groups_by_group_or_by_cell(journal):
    grouped = labels.legend_replacer(_FakeTrace("1,2"), journal, group_legends=True)
    assert grouped.legendgroup == 1

    ungrouped = labels.legend_replacer(_FakeTrace("1,2"), journal, group_legends=False)
    assert ungrouped.legendgroup == "cell_b"


@pytest.mark.essential
def test_legend_replacer_inverted_mode(journal):
    """The batch_plotters-only option that made its copy the superset."""
    plain = labels.legend_replacer(_FakeTrace("2,1"), journal)
    inverted = labels.legend_replacer(
        _FakeTrace("2,1"), journal, inverted_mode=True
    )
    assert plain.name == "cell_c"
    assert inverted.name == "cell_b"


@pytest.mark.essential
def test_legend_replacer_leaves_an_unrecognised_label_alone(journal):
    trace = labels.legend_replacer(_FakeTrace("just a name"), journal)
    assert trace.name == "just a name"


@pytest.mark.essential
def test_remove_markers():
    trace = labels.remove_markers(_FakeTrace("1,1"))
    assert trace.marker is None
    assert trace.mode == "lines"


# --- templates ------------------------------------------------------------------


@pytest.mark.essential
@pytest.mark.skipif(not plotly_available, reason="plotly not installed")
def test_templates_register_under_their_names():
    import plotly.io as pio

    assert theme.make_plotly_template("a_test_template") is not None
    assert "a_test_template" in pio.templates

    built = theme.make_collector_templates()
    assert set(built) == set(theme.COLLECTOR_TEMPLATE_NAMES)
    for name in theme.COLLECTOR_TEMPLATE_NAMES:
        assert name in pio.templates


@pytest.mark.essential
@pytest.mark.skipif(plotly_available, reason="needs an install without plotly")
def test_templates_return_none_without_plotly():
    assert theme.make_plotly_template() is None
    assert theme.make_collector_templates() is None
