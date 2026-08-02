"""Tests for the batch v3 facade (#702)."""

from pathlib import Path

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


def test_load_from_frame(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    frame = pl.DataFrame({FILENAME: ["a", "b"], "mass": [1.0, 2.0]})
    # No cellpy paths on the frame; persist fills defaults under cellpydatadir.
    b = load(name="n", project="p", frame=frame, journal_dir=tmp_path)
    assert isinstance(b, Batch)
    assert b.cell_names == ["a", "b"]
    assert b.journal.name == "n" and b.journal.project == "p"
    assert (tmp_path / "cellpy_batch_n.json").is_file()


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


# ---- custom / BatBase JSON + file search (#345) -------------------------

_FIXTURES = Path(__file__).parent / "fixtures"

_CUSTOM_COLUMN_MAP = {
    "cell_id": "filename",
    "mass_mg": "mass",
    "total_mass_mg": "total_mass",
    "instrument_name": "instrument",
}


def test_load_custom_json_with_file_search(parameters):
    """Blessed cellpy.batch.load routes custom JSON through from_db + find_files."""
    fixture = _FIXTURES / "custom_json_batch_like.json"
    assert fixture.is_file()

    b = load(
        name="test_batch",
        project="test_project",
        journal_file=str(fixture),
        db_reader="custom_json_reader",
        column_map=_CUSTOM_COLUMN_MAP,
        raw_file_dir=parameters.raw_data_dir,
        cellpy_file_dir=parameters.cellpy_data_dir,
    )
    assert isinstance(b, Batch)
    assert b.cell_names == ["20160805_test001_45_cc"]
    assert "raw_file_names" in b.pages.columns
    assert "cellpy_file_name" in b.pages.columns


def test_load_custom_json_reader_alias(parameters):
    """reader= is accepted as an alias for db_reader=."""
    fixture = _FIXTURES / "custom_json_batch_like.json"
    b = load(
        name="test_batch",
        project="test_project",
        journal_file=str(fixture),
        reader="custom_json_reader",
        column_map=_CUSTOM_COLUMN_MAP,
        raw_file_dir=parameters.raw_data_dir,
        cellpy_file_dir=parameters.cellpy_data_dir,
    )
    assert b.cell_names == ["20160805_test001_45_cc"]


def test_load_batbase_json_with_file_search(parameters):
    fixture = _FIXTURES / "cellpy_batbase_like.json"
    assert fixture.is_file()

    b = load(
        name="test_batch",
        project="test_project",
        journal_file=str(fixture),
        db_reader="batbase_json_reader",
        raw_file_dir=parameters.raw_data_dir,
        cellpy_file_dir=parameters.cellpy_data_dir,
    )
    assert isinstance(b, Batch)
    assert b.cell_names == ["20160805_test001_45_cc"]
    assert "raw_file_names" in b.pages.columns


def test_load_json_db_requires_name_and_project():
    fixture = _FIXTURES / "custom_json_batch_like.json"
    with pytest.raises(ValueError, match="name and project"):
        load(
            journal_file=str(fixture),
            db_reader="custom_json_reader",
            column_map=_CUSTOM_COLUMN_MAP,
        )


def test_load_conflicting_db_reader_and_reader_alias():
    with pytest.raises(ValueError, match="conflicting"):
        load(
            name="n",
            project="p",
            journal_file="x.json",
            db_reader="custom_json_reader",
            reader="batbase_json_reader",
        )
