"""Tests for the cellpy.collect foundation (collectors redesign, #705)."""

import polars as pl
import pytest

import cellpy
from cellpy.batch import Batch, Journal
from cellpy.batch.journal import FILENAME
from cellpy.batch.store import CellStore
from cellpy.collect import (
    Collection,
    CollectionMeta,
    SummaryOptions,
    collect_cycles,
    collect_summaries,
    load_collection,
)
from tests import fdv


def _batch_with_cells(cells: dict, pages: pl.DataFrame) -> Batch:
    b = Batch(Journal(name="b", project="p", pages=pages))
    b._store = CellStore.from_cells(cells)
    return b


# ---- options ------------------------------------------------------------


def test_summary_options_replace_is_immutable():
    opts = SummaryOptions()
    changed = opts.replace(group_it=True)
    assert opts.group_it is False
    assert changed.group_it is True


# ---- Collection product -------------------------------------------------


def test_collection_save_load_roundtrip_and_wide(tmp_path):
    frame = pl.DataFrame(
        {"cell": ["a", "a"], "cycle_num": [1, 2], "charge_capacity": [1.0, 2.0]}
    )
    col = Collection(frame, "summary", "test", CollectionMeta(kind="summary", batch_name="b"))

    written = col.save(tmp_path, formats=("parquet", "csv"))
    assert any(p.suffix == ".json" for p in written)
    assert (tmp_path / "test.parquet").is_file()

    loaded = load_collection(tmp_path / "test.parquet")
    assert loaded.data.equals(frame)
    assert loaded.meta.batch_name == "b"

    wide = col.to_wide(values="charge_capacity", index="cycle_num", columns="cell")
    assert "a" in wide.columns


def test_collection_save_requires_directory():
    col = Collection(pl.DataFrame({"a": [1]}), "summary", "x", CollectionMeta(kind="summary"))
    with pytest.raises(ValueError, match="explicit directory"):
        col.save(None)


# ---- collect_summaries (on batch.aggregate) -----------------------------


@pytest.fixture(scope="module")
def real_batch():
    cell = cellpy.get(cellpy_file=fdv.cellpy_file_path, testing=True)
    return _batch_with_cells(
        {"c45": cell}, pl.DataFrame({FILENAME: ["c45"], "group": [1], "sub_group": [1]})
    )


def test_collect_summaries(real_batch):
    col = collect_summaries(real_batch)
    assert col.kind == "summary"
    assert col.data.height > 0
    for key in ("cell", "group", "sub_group"):
        assert key in col.data.columns
    assert col.meta.cells_included == ["c45"]


def test_collect_summaries_column_selection(real_batch):
    col = collect_summaries(real_batch, columns=("charge_capacity",))
    assert "charge_capacity" in col.data.columns
    assert "cell" in col.data.columns  # keys always kept


# ---- collect_cycles: the cross-cell narrowing bug is fixed by design ----


class _FakeCell:
    """A cell with a fixed set of available cycles."""

    def __init__(self, cycles):
        self._cycles = list(cycles)

    def get_cycle_numbers(self):
        return list(self._cycles)

    def get_cap(self, cycle):
        return pl.DataFrame({"capacity": [0.0, float(cycle)], "voltage": [0.1, 0.2]})


def test_collect_cycles_per_cell_isolation():
    """cell_a lacks cycle 3; cell_b must still keep it (collectors.py:1609 bug)."""
    pages = pl.DataFrame(
        {FILENAME: ["a", "b"], "group": [1, 1], "sub_group": [1, 2]}
    )
    b = _batch_with_cells(
        {"a": _FakeCell([1, 2]), "b": _FakeCell([1, 2, 3])}, pages
    )

    col = collect_cycles(b, cycles=(1, 2, 3))
    data = col.data

    a_cycles = set(data.filter(pl.col("cell") == "a")["cycle_num"].to_list())
    b_cycles = set(data.filter(pl.col("cell") == "b")["cycle_num"].to_list())
    assert a_cycles == {1, 2}
    # the bug: after cell_a narrowed the shared list, cell_b lost cycle 3
    assert b_cycles == {1, 2, 3}
