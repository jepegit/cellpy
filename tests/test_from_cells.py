"""Building a batch from in-memory cells (#787)."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

import cellpy
from cellpy.batch import Batch
from cellpy.batch.journal import FILENAME
from cellpy.collect import collect_summaries, from_cells

# reuse the lightweight fake summary cell from the collect tests
from tests.test_collect import _SummaryCell


def test_from_cells_dict_builds_batch_contract():
    cells = {"A": _SummaryCell([10.0, 20.0]), "B": _SummaryCell([20.0, 40.0])}
    b = from_cells(cells)

    assert isinstance(b, Batch)
    assert list(b.cells) == ["A", "B"]
    assert b.journal.name == "in_memory"
    # pages is polars, keyed by filename, matching the cell keys
    assert isinstance(b.journal.pages, pl.DataFrame)
    assert b.journal.pages[FILENAME].to_list() == ["A", "B"]
    for col in ("group", "sub_group", "label", "selected"):
        assert col in b.journal.pages.columns


def test_from_cells_feeds_collect_summaries():
    cells = {"A": _SummaryCell([10.0, 20.0]), "B": _SummaryCell([20.0, 40.0])}
    b = from_cells(cells, groups={"A": 1, "B": 1})
    col = collect_summaries(b, group_it=True, columns=("charge_capacity",))
    # a real grouped average happened (2 cells in group 1)
    for key in ("group", "cycle_num", "variable", "mean", "std"):
        assert key in col.data.columns


def test_from_cells_list_derives_and_dedupes_labels():
    b = from_cells([_SummaryCell([1.0]), _SummaryCell([2.0])])
    # no cell_name -> deterministic fallback labels
    assert list(b.cells) == ["cell_001", "cell_002"]


def test_from_cells_honours_groups_and_selected():
    cells = {"A": _SummaryCell([1.0]), "B": _SummaryCell([2.0])}
    b = from_cells(cells, groups={"A": 1, "B": 2}, selected={"B": False})
    pages = b.journal.pages
    lookup = {row[FILENAME]: row for row in pages.iter_rows(named=True)}
    assert lookup["A"]["group"] == 1 and lookup["B"]["group"] == 2
    assert lookup["A"]["selected"] is True and lookup["B"]["selected"] is False


def test_from_cells_available_on_batch_collect_and_classmethod():
    cells = {"A": _SummaryCell([1.0])}
    # three entry points, same result contract
    for maker in (from_cells, cellpy.batch.from_cells, Batch.from_cells):
        b = maker(cells)
        assert isinstance(b, Batch)
        assert list(b.cells) == ["A"]


@pytest.mark.essential
def test_from_cells_rejects_values_that_are_not_cells():
    """#939: a path or an int used to vanish downstream without a word."""
    cells = {"good": _SummaryCell([1.0]), "a_path": Path("rate.res"), "an_int": 42}

    with pytest.raises(ValueError) as excinfo:
        from_cells(cells)

    message = str(excinfo.value)
    # every offender is named, once, with the type that actually arrived
    assert "'a_path'" in message
    assert "'an_int'" in message
    assert type(Path("rate.res")).__name__ in message  # PosixPath / WindowsPath
    assert "int" in message
    assert "good" not in message


@pytest.mark.essential
def test_from_cells_error_points_a_path_at_cellpy_get():
    """The reported trap: rate_file() hands back a path, cellpy_file() a cell."""
    with pytest.raises(ValueError, match=r"cellpy\.get\(path\)"):
        from_cells({"a_path": Path("rate.res")})


@pytest.mark.essential
def test_from_cells_validates_the_sequence_form_too():
    with pytest.raises(ValueError, match="not cells"):
        from_cells([_SummaryCell([1.0]), 42])


@pytest.mark.essential
def test_from_cells_accepts_a_cell_that_has_no_data_yet():
    """``CellpyCell.data`` raises ``NoDataFound`` until something is loaded.

    Asking the instance would therefore answer "not a cell" (or raise), so the
    guard has to ask the type.
    """
    from cellpy.readers.cellreader import CellpyCell

    b = from_cells({"empty": CellpyCell()})
    assert list(b.cells) == ["empty"]
