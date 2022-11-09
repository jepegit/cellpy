import logging
from pathlib import Path

import pandas as pd
import pytest

from cellpy import log
from cellpy.exceptions import NullData
from cellpy.utils import easyplot
from cellpy.utils.batch_tools.batch_journals import LabJournal

log.setup_logging(default_level=logging.DEBUG, testing=True)


def test_import():
    pass


def test_easyplot_from_journal(parameters):
    journal_file_xlsx = Path(parameters.journal_dir) / parameters.journal_file_full_xlsx
    assert journal_file_xlsx.is_file()
    ezplt = easyplot.EasyPlot(None, journal=journal_file_xlsx, save_journal=False)
    # ezplt.plot()  can not be tested easily yet - need to find a smart way to define file paths so
    # that tests don't fail when changing platform


def test_journal_loading_json(parameters):
    journal_file_json = Path(parameters.journal_dir) / parameters.journal_file_json
    assert journal_file_json.is_file()

    journal = LabJournal(db_reader=None)
    journal.from_file(journal_file_json, paginate=False)
    assert journal.file_name == journal_file_json
    assert not journal.pages.empty
    assert "starred" in journal.session.keys()
    assert "bad_cells" in journal.session.keys()
    assert "bad_cycles" in journal.session.keys()
    assert "notes" in journal.session.keys()


def test_journal_loading_xlsx_only_pages(parameters):
    journal_file_xlsx = Path(parameters.journal_dir) / parameters.journal_file_xlsx
    assert journal_file_xlsx.is_file()

    journal = LabJournal(db_reader=None)
    journal.from_file(journal_file_xlsx, paginate=False)
    assert journal.file_name == journal_file_xlsx
    assert not journal.pages.empty
    assert "starred" in journal.session.keys()
    assert "bad_cells" in journal.session.keys()
    assert "bad_cycles" in journal.session.keys()
    assert "notes" in journal.session.keys()


def test_journal_loading_xlsx(parameters):
    journal_file_xlsx = Path(parameters.journal_dir) / parameters.journal_file_full_xlsx
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


def test_journal_saving_xlsx(parameters):
    import tempfile

    temporary_directory = tempfile.mkdtemp()
    journal_file_xlsx = Path(parameters.journal_dir) / parameters.journal_file_full_xlsx
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

    journal.to_file(
        journal_file_out_xlsx,
        to_project_folder=False,
        paginate=False,
        duplicate_to_local_folder=False,
    )


def test_journal_saving():
    pass
