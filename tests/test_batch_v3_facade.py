"""Tests for the batch v3 facade (#702)."""

import polars as pl
import pytest

from cellpy.batch import Batch, combine_summaries, from_journal, load
from cellpy.batch.journal import FILENAME, Journal
from cellpy.batch.policy import LoadPolicy, SourcePreference
from tests import fdv
from cellpy import config

# the surface the characterization net (#697) pinned on the old Batch
FACADE_MUST_KEEP = (
    "pages", "cell_names", "cells", "summaries", "update", "load", "save",
    "report", "combine_summaries", "make_summaries", "mark_as_bad", "drop",
    "link", "recalc", "create_journal", "paginate", "journal", "export_journal",
    "plot",
)


def _one_cell_batch():
    journal = Journal(
        name="t",
        project="p",
        pages=pl.DataFrame(
            {FILENAME: ["c45"], "cellpy_file_name": [str(fdv.cellpy_file_path)]}
        ),
    )
    return Batch(journal, LoadPolicy(source=SourcePreference.CELLPY_ONLY))


def test_facade_public_surface():
    b = Batch(Journal(name="t", project="p", pages=pl.DataFrame({FILENAME: []})))
    for name in FACADE_MUST_KEEP:
        assert hasattr(b, name), f"Batch lost `{name}`"


def test_from_journal(parameters):
    b = from_journal(parameters.journal_file_json_path)
    assert isinstance(b, Batch)
    assert len(b.pages) == 5
    assert len(b.cell_names) == 5


def test_update_then_summaries_parity():
    b = _one_cell_batch()
    result = b.update()
    assert result["c45"].ok
    assert set(b.cells) == {"c45"}

    summaries = b.summaries
    assert summaries.height > 0
    assert "cell" in summaries.columns
    # the facade must not distort values: same as aggregate over the same cells
    assert summaries.equals(combine_summaries(b.cells, b.journal))


def test_report_pass():
    b = _one_cell_batch()
    b.update()
    assert b.report().row(0, named=True)["pass"] is True


def test_mark_as_bad_and_drop():
    b = _one_cell_batch()
    b.mark_as_bad("c45")
    assert "c45" in b.journal.session["bad_cells"]

    b2 = _one_cell_batch()
    b2.drop("c45")
    assert len(b2.pages) == 0
    assert b2.cell_names == []


def test_save_roundtrip(tmp_path):
    b = _one_cell_batch()
    out = b.save(tmp_path / "j.json")
    assert out.is_file()
    reloaded = from_journal(out)
    assert reloaded.cell_names == b.cell_names


def test_load_from_frame():
    frame = pl.DataFrame({FILENAME: ["a", "b"], "mass": [1.0, 2.0]})
    b = load(name="n", project="p", frame=frame)
    assert isinstance(b, Batch)
    assert b.cell_names == ["a", "b"]
    assert b.journal.name == "n" and b.journal.project == "p"


# ---- db path (#703) -----------------------------------------------------


@pytest.fixture
def db_env(parameters, tmp_path, monkeypatch):
    from cellpy import prms

    monkeypatch.chdir(tmp_path)
    config.paths.db_filename = parameters.db_file_name
    config.paths.cellpydatadir = str(tmp_path)
    config.paths.outdatadir = str(tmp_path)
    config.paths.rawdatadir = parameters.raw_data_dir
    config.paths.db_path = parameters.db_dir
    config.paths.instrumentdir = parameters.instrument_dir
    config.batch.auto_use_file_list = False
    return parameters


_DB_CELLS = {"20160805_test001_46_cc", "20160805_test001_47_cc"}


def test_batch_from_db(db_env):
    b = Batch.from_db(
        "test", "ProjectOfRun", db_reader="simple_excel_reader", batch_col="b01"
    )
    assert set(b.cell_names) == _DB_CELLS


def test_create_journal_reads_db(db_env):
    # the legacy init() -> create_journal() flow via deferred _db config
    b = Batch(
        Journal(name="test", project="ProjectOfRun"),
        _db={"db_reader": "simple_excel_reader", "batch_col": "b01"},
    )
    assert b.cell_names == []
    b.create_journal()
    assert set(b.cell_names) == _DB_CELLS
