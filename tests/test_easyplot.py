import pytest
import logging
from pathlib import Path

import pandas as pd
from cellpy import log
from cellpy.utils import easyplot
from cellpy.utils.batch_tools.batch_journals import LabJournal
from . import fdv
from cellpy.exceptions import NullData

log.setup_logging(default_level=logging.DEBUG)


def test_import():
    pass


def test_easyplot_from_journal():
    journal_file_xlsx = Path(fdv.journal_dir) / fdv.journal_file_full_xlsx
    assert journal_file_xlsx.is_file()
    ezplt = easyplot.EasyPlot(None, journal=journal_file_xlsx, save_journal=False)
    # ezplt.plot()  can not be tested easily yet - need to find a smart way to define file paths so
    # that tests don't fail when changing platform


def test_journal_loading_json():
    journal_file_json = Path(fdv.journal_dir) / fdv.journal_file_json
    assert journal_file_json.is_file()

    journal = LabJournal(db_reader=None)
    journal.from_file(journal_file_json, paginate=False)
    assert journal.file_name == journal_file_json
    assert not journal.pages.empty
    assert "starred" in journal.session.keys()
    assert "bad_cells" in journal.session.keys()
    assert "bad_cycles" in journal.session.keys()
    assert "notes" in journal.session.keys()


def test_journal_loading_xlsx_only_pages():
    journal_file_xlsx = Path(fdv.journal_dir) / fdv.journal_file_xlsx
    assert journal_file_xlsx.is_file()

    journal = LabJournal(db_reader=None)
    journal.from_file(journal_file_xlsx, paginate=False)
    assert journal.file_name == journal_file_xlsx
    assert not journal.pages.empty
    assert "starred" in journal.session.keys()
    assert "bad_cells" in journal.session.keys()
    assert "bad_cycles" in journal.session.keys()
    assert "notes" in journal.session.keys()


def test_journal_loading_xlsx():
    journal_file_xlsx = Path(fdv.journal_dir) / fdv.journal_file_full_xlsx
    assert journal_file_xlsx.is_file()

    journal = LabJournal(db_reader=None)
    journal.from_file(journal_file_xlsx, paginate=False)
    assert journal.file_name == journal_file_xlsx
    assert not journal.pages.empty
    print(journal.session)
    assert "starred" in journal.session.keys()
    assert "bad_cells" in journal.session.keys()
    assert "bad_cycles" in journal.session.keys()
    assert "notes" in journal.session.keys()


def test_journal_saving_xlsx():
    import tempfile
    temporary_directory = tempfile.mkdtemp()
    journal_file_xlsx = Path(fdv.journal_dir) / fdv.journal_file_full_xlsx
    assert journal_file_xlsx.is_file()
    journal_file_out_xlsx = Path(temporary_directory) / "_tmp_journal.xlsx"

    journal = LabJournal(db_reader=None)
    journal.from_file(journal_file_xlsx, paginate=False)
    assert journal.file_name == journal_file_xlsx
    assert not journal.pages.empty
    assert "starred" in journal.session.keys()
    assert "bad_cells" in journal.session.keys()
    assert "bad_cycles" in journal.session.keys()
    assert "notes" in journal.session.keys()

    journal.to_file(journal_file_out_xlsx, to_project_folder=False, paginate=False)


def test_journal_saving():
    pass
