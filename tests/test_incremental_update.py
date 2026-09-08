"""L6 golden equality: incremental update == full load (issue #778).

Head + tail through ``update_core_data`` must match a single ``cellpy.get`` of the
whole file on ``raw`` / ``steps`` / ``summary``. Fixture: ``neware_uio.csv``
(9065 rows, 4 cycles, 32 steps).
"""

import pytest

import cellpy
from tests.incremental_support import (
    NEWARE_KWARGS,
    NEWARE_UIO,
    assert_cell_frames_equal,
    assert_frames_equal,
    incremental_update,
    tail_rows,
    truncate_text_file,
)

pytestmark = pytest.mark.skipif(not NEWARE_UIO.is_file(), reason="neware_uio.csv fixture missing")


@pytest.fixture(scope="module")
def full():
    return cellpy.get(NEWARE_UIO, testing=True, **NEWARE_KWARGS)


@pytest.fixture(scope="module")
def cut_points(full):
    """Datapoint numbers derived from the full step table: mid-step, step end, cycle end."""
    st = full.schema.steps
    steps = full.data.steps
    first_cycle = steps[steps[st.cycle_num] == steps[st.cycle_num].min()]
    step_end = int(first_cycle[st.datapoint_num_last].iloc[-3])
    cycle_end = int(first_cycle[st.datapoint_num_last].iloc[-1])
    later = steps[steps[st.cycle_num] == steps[st.cycle_num].min() + 1].iloc[0]
    mid_step = (int(later[st.datapoint_num_first]) + int(later[st.datapoint_num_last])) // 2
    return {"mid_step": mid_step, "step_end": step_end, "cycle_end": cycle_end}


def _head(tmp_path, n_rows):
    path = truncate_text_file(NEWARE_UIO, tmp_path / "head.csv", n_rows)
    return cellpy.get(path, testing=True, **NEWARE_KWARGS)


def _run(tmp_path, full, cut, overlap):
    head = _head(tmp_path, cut)
    dp = full.schema.raw.datapoint_num
    assert int(head.data.raw[dp].max()) == cut
    tail = tail_rows(full.data.raw, dp, since=cut, overlap=overlap)
    return incremental_update(head, tail)


@pytest.mark.essential
@pytest.mark.parametrize("cut", ["mid_step", "step_end", "cycle_end"])
def test_overlap_reread_equals_full_load(tmp_path, full, cut_points, cut):
    """Tail re-reads at least one already-seen row: the spanning step is rebuilt."""
    updated = _run(tmp_path, full, cut_points[cut], overlap=1)
    assert_cell_frames_equal(updated, full)


@pytest.mark.essential
@pytest.mark.parametrize("cut", ["step_end", "cycle_end"])
def test_gap_append_on_boundary_equals_full_load(tmp_path, full, cut_points, cut):
    """No overlap is fine when the head ends exactly on a step / cycle boundary."""
    updated = _run(tmp_path, full, cut_points[cut], overlap=0)
    assert_cell_frames_equal(updated, full)


@pytest.mark.essential
def test_gap_append_mid_step_equals_full_load(tmp_path, full, cut_points):
    """Gap-append mid-step equals a full load (cellpycore 0.2.6 / core#148)."""
    updated = _run(tmp_path, full, cut_points["mid_step"], overlap=0)
    assert_cell_frames_equal(updated, full)


@pytest.mark.essential
def test_empty_tail_is_noop(tmp_path, full, cut_points):
    """Empty new_raw leaves frames unchanged (cellpycore 0.2.6 / core#147)."""
    head = _head(tmp_path, cut_points["mid_step"])
    before = {k: getattr(head.data, k).copy() for k in ("raw", "steps", "summary")}
    updated = incremental_update(head, full.data.raw.iloc[0:0])
    dp = full.schema.raw.datapoint_num
    st = full.schema.steps
    assert_frames_equal(updated.data.raw, before["raw"], dp, "raw")
    assert_frames_equal(updated.data.steps, before["steps"], [st.cycle_num, st.step_num], "steps")
    assert_frames_equal(updated.data.summary, before["summary"], full.schema.summary.cycle_num, "summary")
