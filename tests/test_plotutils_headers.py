"""Regressions found by the figure oracle (#567).

Every test here corresponds to something that was broken on cellpy 2 and that
no test caught, because the only plotting test file in the repo was excluded
from CI and the other plot families had no tests at all.

The common cause is a binding that could not see the runtime: module-level
header singletons built at import time, which answered with *legacy* column
names no matter which cell you handed them. The native-headers flip then made
every lookup through them miss.
"""

from __future__ import annotations

import importlib.util
import logging

import matplotlib

matplotlib.use("Agg")

import pytest

from cellpy import log
from cellpy.utils import plotutils

log.setup_logging(default_level=logging.DEBUG, testing=True)

plotly_available = importlib.util.find_spec("plotly") is not None
seaborn_available = importlib.util.find_spec("seaborn") is not None


@pytest.fixture(scope="module")
def cell():
    from tests.figure_spec_support import load_figure_cell

    return load_figure_cell()


# --- the module-level singletons are gone ------------------------------------


@pytest.mark.essential
def test_no_module_level_header_singletons():
    """The trap itself: a header table fixed at import time.

    `_hdr_raw = get_headers_normal()` could not know whether the cell it was
    used with carried native or legacy columns, so it was wrong for every
    cellpy 2 cell. Guarding the name keeps it from creeping back.
    """
    for name in ("_hdr_raw", "_hdr_steps", "_hdr_summary"):
        assert not hasattr(plotutils, name), (
            f"plotutils.{name} is back — use _LiveHeaders(cell, frame) instead"
        )


@pytest.mark.essential
def test_live_headers_track_the_cell(cell):
    hdr = plotutils._LiveHeaders(cell, "raw")
    columns = set(cell.data.raw.columns)
    for legacy_attr in (
        "voltage_txt",
        "current_txt",
        "cycle_index_txt",
        "step_index_txt",
        "test_time_txt",
    ):
        assert hdr[legacy_attr] in columns, legacy_attr
        assert getattr(hdr, legacy_attr) == hdr[legacy_attr]


@pytest.mark.essential
def test_live_headers_compose_step_statistics(cell):
    hdr = plotutils._LiveHeaders(cell, "steps")
    columns = set(cell.data.steps.columns)
    assert hdr.stat("voltage", "delta") in columns
    assert hdr.stat("current", "min") in columns
    assert hdr.stat("point", "max") in columns
    assert hdr.stat("charge", "delta") in columns


@pytest.mark.essential
def test_live_headers_name_the_column_they_cannot_find(cell):
    hdr = plotutils._LiveHeaders(cell, "raw")
    with pytest.raises(KeyError, match="no raw column named"):
        hdr["not_a_column_txt"]


@pytest.mark.essential
def test_normalized_cycle_index_is_dialect_invariant():
    """plotutils compares against this name literally, so it must not move."""
    from cellpycore.legacy import mapping

    from cellpy.parameters.internal_settings import get_headers_summary

    legacy = get_headers_summary().normalized_cycle_index
    native = mapping.LEGACY_ATTR_TO_SCHEMA["cycle"]["normalized_cycle_index"]
    assert legacy == native == plotutils._NORMALIZED_CYCLE_INDEX


# --- the plot families that were simply broken --------------------------------


@pytest.mark.essential
@pytest.mark.parametrize("interactive", [False, True])
def test_raw_plot_runs_on_a_native_cell(cell, interactive):
    """`raw_plot` raised KeyError: 'voltage' on every cellpy 2 cell."""
    if interactive and not plotly_available:
        pytest.skip("plotly not installed")
    figure = plotutils.raw_plot(cell, interactive=interactive)
    assert figure is not None


@pytest.mark.essential
@pytest.mark.parametrize("plot_type", ["voltage-current", "capacity", "raw"])
def test_raw_plot_predefined_types_run(cell, plot_type):
    """Each plot_type reaches a different set of raw columns."""
    figure = plotutils.raw_plot(cell, interactive=False, plot_type=plot_type)
    assert figure is not None


@pytest.mark.essential
@pytest.mark.parametrize("interactive", [False, True])
def test_cycle_info_plot_runs_on_a_native_cell(cell, interactive):
    """`cycle_info_plot` raised on both the raw and the step frame."""
    if interactive and not plotly_available:
        pytest.skip("plotly not installed")
    plotutils.cycle_info_plot(cell, cycle=3, interactive=interactive)


# --- user-supplied column names ----------------------------------------------


@pytest.mark.essential
@pytest.mark.skipif(not seaborn_available, reason="seaborn not installed")
def test_summary_plot_accepts_the_legacy_x_spelling(cell):
    """`x="cycle_index"` is what this module's own docstring tells you to pass."""
    figure = plotutils.summary_plot(
        cell, y="capacities_gravimetric", x="cycle_index", interactive=False
    )
    assert figure is not None


@pytest.mark.essential
@pytest.mark.skipif(not seaborn_available, reason="seaborn not installed")
def test_summary_plot_accepts_the_native_x_spelling(cell):
    figure = plotutils.summary_plot(
        cell, y="capacities_gravimetric", x="cycle_num", interactive=False
    )
    assert figure is not None


@pytest.mark.essential
def test_resolving_an_unknown_column_leaves_it_alone(cell):
    """So the eventual error names what the user actually asked for."""
    assert plotutils._resolve_summary_column(cell, "wibble") == "wibble"
    assert plotutils._resolve_summary_column(cell, None) is None


@pytest.mark.essential
def test_resolving_a_native_name_is_a_no_op(cell):
    assert plotutils._resolve_summary_column(cell, "cycle_num") == "cycle_num"


# --- plotting must not touch the data ----------------------------------------


@pytest.mark.essential
@pytest.mark.skipif(not seaborn_available, reason="seaborn not installed")
def test_cv_split_plot_leaves_the_summary_frame_alone(cell):
    """`partition_summary_cv_steps` used to set_index in place on c.data.summary.

    One CV-split plot and the cell permanently lost its cycle column — which
    broke every later plot, and any user code reading that column.
    """
    before = list(cell.data.summary.columns)
    plotutils.summary_plot(
        cell, y="capacities_gravimetric_split_constant_voltage", interactive=False
    )
    assert list(cell.data.summary.columns) == before
    assert cell.data.summary.index.name != "cycle_num"


# --- summary_plot_legacy is a delegate now ------------------------------------


@pytest.mark.essential
@pytest.mark.skipif(not seaborn_available, reason="seaborn not installed")
def test_summary_plot_legacy_delegates_and_warns(cell):
    """The old implementation could not draw anything at all.

    Its first statement unpacked the return value of
    `SummaryPlotInfo._create_col_info`, which stores its results as attributes
    and returns None — so every call raised TypeError, on any cell, since the
    refactor that introduced the class (#567). The name now delegates to
    summary_plot, which is strictly better than the TypeError callers got.
    """
    import warnings as _warnings

    from tests.figure_spec_support import describe_figure

    with _warnings.catch_warnings(record=True) as caught:
        _warnings.simplefilter("always")
        via_legacy = plotutils.summary_plot_legacy(
            cell, y="capacities_gravimetric", interactive=False
        )
    assert any(
        issubclass(w.category, DeprecationWarning)
        and "summary_plot_legacy" in str(w.message)
        for w in caught
    )

    direct = plotutils.summary_plot(
        cell, y="capacities_gravimetric", interactive=False
    )
    assert describe_figure(via_legacy) == describe_figure(direct)

    import matplotlib.pyplot as plt

    plt.close(via_legacy)
    plt.close(direct)


@pytest.mark.essential
def test_the_dead_helper_went_with_it():
    assert not hasattr(plotutils, "_report_summary_plot_info")
