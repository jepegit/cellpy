"""Tests for batch v3 aggregate/qc/outputs (#701)."""

import polars as pl
import pytest

import cellpy
from cellpy.batch import combine_summaries, outputs, qc
from cellpy.batch.journal import FILENAME, Journal
from tests import fdv


@pytest.fixture(scope="module")
def loaded_cells():
    cell = cellpy.get(cellpy_file=fdv.cellpy_file_path, testing=True)
    return {"c45": cell}


# ---- aggregate.combine_summaries ----------------------------------------


def test_combine_summaries_tidy(loaded_cells):
    frame = combine_summaries(loaded_cells)
    assert isinstance(frame, pl.DataFrame)
    assert frame.height > 0
    for key in ("cell", "group", "sub_group"):
        assert key in frame.columns
    assert set(frame["cell"].unique().to_list()) == {"c45"}


def test_combine_summaries_uses_journal_groups(loaded_cells):
    journal = Journal(
        pages=pl.DataFrame(
            {FILENAME: ["c45"], "group": [2], "sub_group": [5]}
        )
    )
    frame = combine_summaries(loaded_cells, journal)
    assert frame["group"].unique().to_list() == [2]
    assert frame["sub_group"].unique().to_list() == [5]


def test_combine_summaries_empty():
    assert combine_summaries({}).height == 0


# ---- qc.check -----------------------------------------------------------


def test_qc_check(loaded_cells):
    frame = qc.check(loaded_cells)
    assert isinstance(frame, pl.DataFrame)
    assert frame.height == 1
    row = frame.row(0, named=True)
    assert row["cell"] == "c45"
    assert row["empty"] is False
    assert row["n_summary"] and row["n_summary"] > 0
    assert row["pass"] is True


# ---- outputs (pure writers) ---------------------------------------------


def test_outputs_roundtrip(tmp_path):
    frame = pl.DataFrame({"a": [1, 2], "b": ["x", "y"]})

    csv_path = outputs.write_csv(frame, tmp_path / "f.csv")
    assert csv_path.is_file()
    assert pl.read_csv(csv_path).equals(frame)

    pq_path = outputs.write_parquet(frame, tmp_path / "f.parquet")
    assert pq_path.is_file()
    assert pl.read_parquet(pq_path).equals(frame)

    xlsx_path = outputs.write_excel(frame, tmp_path / "f.xlsx")
    assert xlsx_path.is_file()


def test_outputs_do_not_create_dirs(tmp_path):
    frame = pl.DataFrame({"a": [1]})
    missing = tmp_path / "does_not_exist" / "f.csv"
    with pytest.raises((FileNotFoundError, OSError)):
        outputs.write_csv(frame, missing)
