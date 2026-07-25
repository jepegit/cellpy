"""Regression tests for issue #668 (v1.x batch plot + nested cycle_mode)."""

from types import SimpleNamespace

import pandas as pd
import pytest

from cellpy.exceptions import NullData
from cellpy.parameters.internal_settings import get_headers_summary
from cellpy.readers.cellpy_file.meta import unwrap_meta_value
from cellpy.utils.batch_tools.batch_plotters import generate_summary_frame_for_plotting
from cellpy.utils.batch_tools.engines import summary_engine


def _minimal_summary_frame():
    hdr = get_headers_summary()
    df = pd.DataFrame(
        {
            hdr["discharge_capacity_gravimetric"]: [1.0, 0.9],
            hdr["charge_capacity_gravimetric"]: [1.05, 0.95],
            hdr["coulombic_efficiency"]: [95.0, 94.0],
        },
        index=[1, 2],
    )
    df.index.name = hdr.cycle_index
    return df


def _stub_experiment(*, cached_summary, cell_names=("cell_a",)):
    """Mimic post-update / ``all_in_memory=False``: cache good, cells empty."""

    class _StubCell:
        def __init__(self):
            self.data = SimpleNamespace(summary=pd.DataFrame())

    class _StubData:
        def __getitem__(self, key):
            return _StubCell()

    selected = [
        "discharge_capacity_gravimetric",
        "charge_capacity_gravimetric",
        "coulombic_efficiency",
    ]
    frames = {name: cached_summary.copy() for name in cell_names} if cached_summary is not None else None
    return SimpleNamespace(
        selected_summaries=selected,
        summary_frames=frames,
        cell_names=list(cell_names),
        cell_data_frames={name: _StubCell() for name in cell_names},
        data=_StubData(),
    )


@pytest.mark.essential
@pytest.mark.parametrize(
    "value,expected",
    [
        ("anode", "anode"),
        (["anode"], "anode"),
        ([["anode"]], "anode"),
        (("anode",), "anode"),
        (None, None),
        ([1, 2], [1, 2]),
    ],
)
def test_unwrap_meta_value_variants(value, expected):
    assert unwrap_meta_value(value) == expected


@pytest.mark.essential
def test_summary_frame_unnamed_cycle_index():
    """Unnamed summary index becomes selectable ``cycle_index`` (#668 / #658)."""
    hdr = get_headers_summary()
    cells = ["cell_a", "cell_b"]
    cycles = [1, 2, 3]

    def _frame(name, values):
        df = pd.DataFrame(
            {cell: values for cell in cells},
            index=cycles,
        )
        df.index.name = None  # reproduce post-join_summaries state
        df.name = name
        return df

    charge = f"{hdr.charge_capacity}_gravimetric"
    discharge = f"{hdr.discharge_capacity}_gravimetric"
    farms = [
        _frame(charge, [1.0, 0.9, 0.8]),
        _frame(discharge, [0.95, 0.85, 0.75]),
        _frame(hdr.coulombic_efficiency, [95.0, 94.0, 93.0]),
    ]
    pages = pd.DataFrame(index=cells)
    experiment = SimpleNamespace(memory_dumped={"summary_engine": farms})

    out = generate_summary_frame_for_plotting(pages, experiment)
    assert hdr.cycle_index in out.columns
    assert set(out[hdr.cycle_index].unique()) == {1, 2, 3}


@pytest.mark.essential
@pytest.mark.parametrize("nested_mode", [["anode"], [["anode"]]])
def test_make_summary_with_nested_cycle_mode(
    cellpy_data_instance, parameters, nested_mode
):
    """Nested list-boxed cycle_mode must not crash make_summary (#668)."""
    c = cellpy_data_instance
    c.set_instrument("arbin_res")
    c.from_raw(parameters.res_file_path)
    c.mass = 1.0
    c.make_step_table()
    # Bypass the setter so meta stays nested (as after a bad cellpy-file load).
    c.data.meta_test_dependent.cycle_mode = nested_mode

    c.make_summary(find_ir=True, find_end_voltage=True)

    assert c.data.meta_test_dependent.cycle_mode == "anode"
    assert c.cycle_mode == "anode"
    assert c.data.summary is not None
    assert not c.data.summary.empty


@pytest.mark.essential
def test_summary_engine_reuses_cached_frames_on_soft_reset():
    """Soft reset must not wipe update() cache when cells are stubs (#668)."""
    exp = _stub_experiment(cached_summary=_minimal_summary_frame())
    farms, barn = summary_engine(experiments=[exp], reset=False)
    assert barn == "batch_dir"
    assert farms
    assert len(farms[0]) == 3
    # Cache must remain the non-empty frames (not replaced by stub empties).
    assert not exp.summary_frames["cell_a"].empty


@pytest.mark.essential
def test_summary_engine_hard_reset_rebuilds_from_cells():
    """``reset=True`` rebuilds from cells even when a cache exists (#668)."""
    exp = _stub_experiment(cached_summary=_minimal_summary_frame())
    with pytest.raises(NullData, match="summary tables"):
        summary_engine(experiments=[exp], reset=True)


@pytest.mark.essential
def test_summary_engine_empty_cell_names_message():
    """Empty cell_data_frames → actionable NullData (#668)."""
    exp = SimpleNamespace(
        selected_summaries=["coulombic_efficiency"],
        summary_frames=None,
        cell_names=[],
        data={},
    )
    with pytest.raises(NullData, match="no cells loaded"):
        summary_engine(experiments=[exp], reset=False)
