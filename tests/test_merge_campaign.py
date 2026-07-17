"""Tests for the campaign merge (issue #507, V2-03/V2-07).

Campaign merge folds several *different tests* into one multi-test object:
distinct compact ``test_id`` per source in raw, per-test metadata records
(``Data.tests``), globally renumbered cycles, and per-test summary windowing
via the re-stamped step-table ``test_id``.
"""

from __future__ import annotations

import logging

import pandas as pd
import pytest

from cellpycore.metadata import io as core_meta_io
from cellpycore.metadata.models import TestMeta, TestMetaCollection

from cellpy import cellreader
from cellpy.exceptions import MixedCycleModesError
from cellpy.parameters.internal_settings import (
    get_headers_normal,
    get_headers_summary,
)
from cellpy.readers import merger, test_meta
from cellpy.readers.cellreader import merge_cells
from cellpy.readers.data_structures import Data

log_setup_done = False

HN = get_headers_normal()
HS = get_headers_summary()


def _mini_data(cycles=(1, 2), dp_start=1, mass=1.0, cycle_mode="anode", name="a"):
    """Small synthetic Data with a raw frame (2 rows per cycle)."""
    data = Data()
    rows = []
    dp = dp_start
    for cyc in cycles:
        for k in range(2):
            rows.append(
                {
                    HN.data_point_txt: dp,
                    HN.cycle_index_txt: cyc,
                    HN.test_time_txt: float(dp),
                    HN.current_txt: 1.0 if k == 0 else -1.0,
                    HN.voltage_txt: 3.5,
                }
            )
            dp += 1
    data.raw = pd.DataFrame(rows)
    data.meta_common.mass = mass
    data.meta_common.cell_name = name
    data.meta_test_dependent.cycle_mode = cycle_mode
    data.loaded_from = f"{name}.raw"
    return data


def _cell(data) -> cellreader.CellpyCell:
    c = cellreader.CellpyCell(initialize=True)
    c.data = data
    return c


# ------------------------------------------------------------- fold basics ----


def test_campaign_two_sources_ids_and_offsets():
    left = _cell(_mini_data(cycles=(1, 2, 3), mass=1.0, name="one"))
    right = _cell(_mini_data(cycles=(1, 2), mass=2.0, name="two"))
    n_left, n_right = len(left.data.raw), len(right.data.raw)

    left.merge(right)

    raw = left.data.raw
    assert len(raw) == n_left + n_right
    assert set(raw[HN.test_id_txt].unique()) == {0, 1}
    assert left.data.tests.test_ids == [0, 1]
    # cycles globally unique, contiguous blocks
    assert raw[HN.cycle_index_txt].max() == 5
    assert test_meta.cycle_ranges_per_test(left.data) == {0: (1, 3), 1: (4, 5)}
    # datapoints strictly increasing across the boundary
    dp = raw[HN.data_point_txt]
    assert dp.iloc[n_left] > dp.iloc[:n_left].max()


def test_campaign_metadata_fold_and_sources_unmutated():
    left = _cell(_mini_data(mass=1.0, cycle_mode="anode", name="one"))
    right_data = _mini_data(mass=2.0, cycle_mode="anode", name="two")
    right_raw_before = right_data.raw.copy()

    left.merge(right_data)

    rec0, rec1 = left.data.tests.get(0), left.data.tests.get(1)
    assert rec0.cell.mass == 1.0 and rec0.cell_name == "one"
    assert rec1.cell.mass == 2.0 and rec1.cell_name == "two"
    # active legacy boxes untouched by the fold
    assert left.data.meta_common.mass == 1.0
    # source not mutated
    pd.testing.assert_frame_equal(right_data.raw, right_raw_before)
    assert right_data._extra_tests == {}


def test_campaign_three_way_and_remerge_id_remap():
    a = _cell(_mini_data(name="a"))
    a.merge([_mini_data(name="b"), _mini_data(name="c")])
    assert a.data.tests.test_ids == [0, 1, 2]

    # merging an already-merged object remaps its colliding ids
    d = _cell(_mini_data(name="d"))
    d.merge(a)
    assert d.data.tests.test_ids == [0, 1, 2, 3]
    names = {tid: d.data.tests.get(tid).cell_name for tid in d.data.tests.test_ids}
    assert names[0] == "d" and set(names.values()) == {"a", "b", "c", "d"}


def test_campaign_metadata_renumbering_matches_core_merge_test_meta():
    """Our id assignment mirrors cellpycore's merge_test_meta priority rule."""
    left = _cell(_mini_data(name="one"))
    right = _mini_data(name="two")
    left.merge(right)
    ours = {tid: left.data.tests.get(tid).cell_name for tid in left.data.tests.test_ids}

    c_left = TestMetaCollection()
    c_left.add(TestMeta(test_id=0, cell_name="one"))
    c_right = TestMetaCollection()
    c_right.add(TestMeta(test_id=0, cell_name="two"))
    core_merged = core_meta_io.merge_test_meta(c_left, c_right, renumber=True)
    core_names = {tid: core_merged.get(tid).cell_name for tid in core_merged.test_ids}
    assert ours == core_names


def test_campaign_guards():
    left = _cell(_mini_data(name="one"))
    empty = Data()
    n = len(left.data.raw)
    left.merge(empty)  # empty source skipped with warning
    assert len(left.data.raw) == n
    assert left.data.tests.test_ids == [0]

    other = _mini_data(name="two")
    other.raw_units["current"] = "mA"
    with pytest.raises(ValueError, match="raw_units differ"):
        left.merge(other)

    with pytest.raises(NotImplementedError, match="original"):
        left.merge(_mini_data(name="three"), renumber_cycles=False)

    with pytest.raises(ValueError, match="unknown merge mode"):
        left.merge(_mini_data(name="four"), mode="bogus")

    with pytest.raises(TypeError, match="requires the cells"):
        left.merge(None)


def test_merge_cells_convenience_does_not_mutate():
    c1 = _cell(_mini_data(name="one"))
    c2 = _cell(_mini_data(name="two"))
    n1 = len(c1.data.raw)

    merged = merge_cells([c1, c2])

    assert merged is not c1
    assert merged.data.tests.test_ids == [0, 1]
    assert len(c1.data.raw) == n1
    assert c1.data._extra_tests == {}


# ---------------------------------------------------------------- mixed modes ----


def test_campaign_mixed_modes_stored_but_compute_raises(caplog):
    left = _cell(_mini_data(cycle_mode="anode", name="one"))
    with caplog.at_level(logging.WARNING):
        left.merge(_mini_data(cycle_mode="cathode", name="two"))
    assert any("different cycle_modes" in r.message for r in caplog.records)
    assert test_meta.cycle_modes_in_data(left.data) == {"anode", "cathode"}

    with pytest.raises(MixedCycleModesError):
        left.make_step_table()
    with pytest.raises(MixedCycleModesError):
        left.make_summary()


# ------------------------------------------------- real data: compute pins ----


@pytest.fixture
def campaign_cell(parameters):
    """Two real res files campaign-merged as distinct tests (same cycle_mode)."""
    left = cellreader.CellpyCell()
    left.from_raw(parameters.res_file_path)
    right = cellreader.CellpyCell()
    right.from_raw(parameters.res_file_path2)
    left.merge(right)
    return left


def test_campaign_real_data_structure(campaign_cell):
    raw = campaign_cell.data.raw
    assert set(raw[HN.test_id_txt].unique()) == {0, 1}
    ranges = test_meta.cycle_ranges_per_test(campaign_cell.data)
    assert set(ranges) == {0, 1}
    assert ranges[1][0] > ranges[0][1]  # no cycle overlap


def test_campaign_recompute_stamps_steps_and_windows_summary(campaign_cell):
    """The bridge tripwire: steps carry test_id; cumulatives reset per test."""
    campaign_cell.make_step_table()
    steps = campaign_cell.data.steps
    assert HN.test_id_txt in steps.columns
    assert set(steps[HN.test_id_txt].unique()) == {0, 1}

    campaign_cell.make_summary(find_ir=False, find_end_voltage=False)
    summary = campaign_cell.data.summary
    ranges = test_meta.cycle_ranges_per_test(campaign_cell.data)
    first_cycle_t1 = ranges[1][0]
    cum_col = "cumulated_charge_capacity"
    assert cum_col in summary.columns
    block1 = summary[summary[HS.cycle_index] >= first_cycle_t1]
    first_row = block1.iloc[0]
    # per-test windowing: the cumulation restarts at the test boundary, so the
    # first cumulated value of test 1 equals its own first charge capacity
    # (not the carried total of test 0).
    assert first_row[cum_col] == pytest.approx(
        first_row["charge_capacity"], rel=1e-6
    )


def test_single_test_steps_have_no_test_id_column(parameters):
    """Safety pin: the re-stamp gate stays off for non-campaign objects."""
    c = cellreader.CellpyCell()
    c.from_raw(parameters.res_file_path)
    c.make_step_table()
    assert HN.test_id_txt not in c.data.steps.columns


def test_campaign_save_warns_and_reloads_single(campaign_cell, tmp_path, caplog):
    """v8 HDF5 escape still drops non-active TestMeta (legacy limitation)."""
    campaign_cell.make_step_table()
    campaign_cell.make_summary(find_ir=False, find_end_voltage=False)
    outfile = tmp_path / "campaign.h5"
    with caplog.at_level(logging.WARNING):
        campaign_cell.save(outfile)
    assert any("not persist" in r.message or "persists" in r.message for r in caplog.records)

    reloaded = cellreader.CellpyCell()
    reloaded.load(outfile)
    assert reloaded.data.tests.test_ids == [0]


@pytest.mark.essential
def test_campaign_v9_roundtrip_preserves_tests_and_test_id(campaign_cell, tmp_path):
    """Milestone B: v9 save/load keeps both TestMeta rows and frame test_id."""
    campaign_cell.make_step_table()
    campaign_cell.make_summary(find_ir=False, find_end_voltage=False)
    before_meta = {
        tid: core_meta_io.to_dict(campaign_cell.data.tests.get(tid))
        for tid in campaign_cell.data.tests.test_ids
    }
    before_raw_ids = set(campaign_cell.data.raw[HN.test_id_txt].unique())
    before_step_ids = set(campaign_cell.data.steps[HN.test_id_txt].unique())

    outfile = tmp_path / "campaign.cellpy"
    campaign_cell.save(outfile)

    reloaded = cellreader.CellpyCell()
    reloaded.load(outfile)

    assert sorted(reloaded.data.tests.test_ids) == [0, 1]
    after_meta = {
        tid: core_meta_io.to_dict(reloaded.data.tests.get(tid))
        for tid in reloaded.data.tests.test_ids
    }
    assert after_meta == before_meta
    assert set(reloaded.data.raw[HN.test_id_txt].unique()) == before_raw_ids
    assert HN.test_id_txt in reloaded.data.steps.columns
    assert set(reloaded.data.steps[HN.test_id_txt].unique()) == before_step_ids


# ------------------------------------------------------- steps/summary concat ----


def test_campaign_merges_precomputed_steps_and_summary(parameters):
    left = cellreader.CellpyCell()
    left.from_raw(parameters.res_file_path)
    left.make_step_table()
    left.make_summary(find_ir=False, find_end_voltage=False)
    right = cellreader.CellpyCell()
    right.from_raw(parameters.res_file_path2)
    right.make_step_table()
    right.make_summary(find_ir=False, find_end_voltage=False)

    n_steps = len(left.data.steps) + len(right.data.steps)
    n_summary = len(left.data.summary) + len(right.data.summary)
    right_first_cum = right.data.summary["cumulated_charge_capacity"].iloc[0]

    left.merge(right)

    assert len(left.data.steps) == n_steps
    assert HN.test_id_txt in left.data.steps.columns
    assert set(left.data.steps[HN.test_id_txt].unique()) == {0, 1}
    assert len(left.data.summary) == n_summary
    # no cumulative carry-forward: test 1's first cumulated value unchanged
    ranges = test_meta.cycle_ranges_per_test(left.data)
    block1 = left.data.summary[
        left.data.summary[HS.cycle_index] >= ranges[1][0]
    ]
    assert block1["cumulated_charge_capacity"].iloc[0] == pytest.approx(
        right_first_cum, rel=1e-9
    )
