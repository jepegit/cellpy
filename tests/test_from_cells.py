"""Building a batch from in-memory cells (#787)."""

from __future__ import annotations

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
