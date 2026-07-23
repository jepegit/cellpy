"""CV-split summary partitioning (#654).

``selector_type`` on ``make_summary`` is a deprecated no-op; partition helpers
must use ``exclude_step_types=["cv_"]`` for without-CV and ``full - non_cv``
for with-CV.
"""

from __future__ import annotations

import pytest

from cellpy.utils import helpers, plotutils
from cellpy.utils.helpers import _cv_partition_summary_frames, _summary_cycle_column


@pytest.mark.essential
def test_cv_partition_frames_identity_on_rate_cell(rate_dataset):
    """With-CV charge capacity is the full − non_cv delta (rate cell has cv_charge)."""
    c = rate_dataset
    c.make_step_table()
    c.make_summary()

    full, non_cv, only_cv = _cv_partition_summary_frames(c)
    cycle = _summary_cycle_column(full)
    assert cycle is not None

    col = "charge_capacity"
    assert col in full.columns
    f = full.set_index(cycle)[col]
    n = non_cv.set_index(cycle)[col]
    v = only_cv.set_index(cycle)[col]

    assert (v > 0).any(), "fixture must yield a non-zero CV charge delta"
    assert (f - n - v).abs().max() == pytest.approx(0.0, abs=1e-12)


@pytest.mark.essential
def test_partition_summary_cv_steps_melt_splits_capacity(rate_dataset):
    """Melted CV-split rows: all ≈ without CV + with CV on charge capacity."""
    c = rate_dataset
    c.make_step_table()
    c.make_summary()
    cycle = _summary_cycle_column(c.data.summary)
    col = "charge_capacity"

    s = plotutils.partition_summary_cv_steps(
        c, cycle, [col], split=True, var_name="variable", value_name="value"
    )
    assert set(s["row"].unique()) == {"all", "without CV", "with CV"}

    pivot = s.pivot_table(index=cycle, columns="row", values="value", aggfunc="first")
    assert (pivot["with CV"] > 0).any()
    assert (pivot["all"] - pivot["without CV"] - pivot["with CV"]).abs().max() == (
        pytest.approx(0.0, abs=1e-12)
    )


@pytest.mark.essential
def test_partition_summary_cv_steps_cc_only_has_zero_cv(figure_cell):
    """Golden CC-only figure cell: with-CV ≈ 0, without-CV ≈ all."""
    cycle = _summary_cycle_column(figure_cell.data.summary)
    # Prefer gravimetric if present (summary_plot family), else raw.
    hs = figure_cell.headers_summary
    col = hs.charge_capacity + "_gravimetric"
    if col not in figure_cell.data.summary.columns:
        col = "charge_capacity"
        if col not in figure_cell.data.summary.columns:
            col = hs.charge_capacity

    s = plotutils.partition_summary_cv_steps(
        figure_cell, cycle, [col], split=True, var_name="variable", value_name="value"
    )

    pivot = s.pivot_table(index=cycle, columns="row", values="value", aggfunc="first")
    assert pivot["with CV"].fillna(0).abs().max() == pytest.approx(0.0, abs=1e-12)
    assert (pivot["all"] - pivot["without CV"]).abs().max() == pytest.approx(
        0.0, abs=1e-9
    )


@pytest.mark.essential
def test_wide_partition_adds_cv_suffix_columns(rate_dataset):
    """helpers wide path exposes ``*_cv`` / ``*_non_cv`` capacity columns."""
    c = rate_dataset
    c.make_step_table()
    c.make_summary()
    cycle = _summary_cycle_column(c.data.summary)
    col = "charge_capacity"

    wide = helpers._partition_summary_based_on_cv_steps(
        c, column_set=[col], x=cycle
    )
    assert f"{col}_cv" in wide.columns
    assert f"{col}_non_cv" in wide.columns
    assert (wide[f"{col}_cv"] > 0).any()
    assert (
        wide[col] - wide[f"{col}_non_cv"] - wide[f"{col}_cv"]
    ).abs().max() == pytest.approx(0.0, abs=1e-12)


@pytest.fixture
def figure_cell():
    from tests.figure_spec_support import load_figure_cell

    return load_figure_cell()
