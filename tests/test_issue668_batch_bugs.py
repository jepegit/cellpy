"""Regression tests for issue #668 (v1.x batch plot + nested cycle_mode)."""

from types import SimpleNamespace

import pandas as pd
import pytest

from cellpy.parameters.internal_settings import get_headers_summary
from cellpy.readers.cellpy_file.meta import unwrap_meta_value
from cellpy.utils.batch_tools.batch_plotters import generate_summary_frame_for_plotting


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
