"""Unit tests for the batch v3 package (#698): journal model + layout."""

import polars as pl
import pytest

from cellpy.batch import (
    BatchPaths,
    Journal,
    ensure_dirs,
    journal_from_frame,
    read_journal,
    write_journal,
)
from cellpy.batch.journal import FILENAME


# ---- journal.py ---------------------------------------------------------


def test_read_journal_json(parameters):
    j = read_journal(parameters.journal_file_json_path)
    assert isinstance(j, Journal)
    assert isinstance(j.pages, pl.DataFrame)
    assert len(j) == 5
    # keys-in-columns law: the cell label is a column, not an index
    assert FILENAME in j.pages.columns
    assert "argument" in j.pages.columns
    assert len(j.cell_names) == 5
    # session always carries the four canonical keys
    assert set(j.session) >= {"starred", "bad_cells", "bad_cycles", "notes"}


def test_journal_json_roundtrip(parameters, tmp_path):
    j1 = read_journal(parameters.journal_file_json_path)
    out = tmp_path / "roundtrip.json"
    returned = write_journal(j1, out)
    assert returned == out and out.is_file()

    j2 = read_journal(out)
    # value parity on the pages after a write -> read cycle
    assert j2.cell_names == j1.cell_names
    assert set(j2.pages.columns) == set(j1.pages.columns)
    order = j1.cell_names
    j1s = j1.pages.sort(FILENAME)
    j2s = j2.pages.sort(FILENAME)
    assert j2s["argument"].to_list() == j1s["argument"].to_list()
    assert j2s[FILENAME].to_list() == sorted(order)


def test_journal_from_frame_polars():
    pages = pl.DataFrame(
        {
            FILENAME: ["cell_a", "cell_b"],
            "argument": ["recalc=True", "recalc=False"],
            "group": [1, 1],
        }
    )
    j = journal_from_frame(pages, name="t", project="p")
    assert j.name == "t" and j.project == "p"
    assert j.cell_names == ["cell_a", "cell_b"]
    assert len(j) == 2


def test_read_journal_rejects_non_journal(tmp_path):
    bad = tmp_path / "notajournal.json"
    bad.write_text('{"hello": "world"}', encoding="utf-8")
    with pytest.raises(ValueError, match="not a cellpy journal"):
        read_journal(bad)


# ---- layout.py ----------------------------------------------------------


def test_batchpaths_is_pure(tmp_path):
    """Computing paths must not create anything on disk."""
    p = BatchPaths.create("mybatch", "myproject", project_dir=tmp_path)
    assert p.batch_dir == tmp_path / "dump"
    assert p.raw_dir == tmp_path / "dump" / "raw_data"
    assert p.journal_file() == tmp_path / "cellpy_batch_mybatch.json"
    # nothing was created just by asking for paths
    assert not p.batch_dir.exists()
    assert not p.raw_dir.exists()


def test_ensure_dirs_is_the_only_mkdir(tmp_path):
    p = BatchPaths.create("mybatch", "myproject", project_dir=tmp_path / "proj")
    assert not p.project_dir.exists()
    made = ensure_dirs(p)
    assert p.project_dir.exists()
    assert p.batch_dir.exists()
    assert p.raw_dir.exists()
    assert set(made) == {p.project_dir, p.batch_dir, p.raw_dir}
    # idempotent
    ensure_dirs(p)
