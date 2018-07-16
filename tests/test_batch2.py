import pytest
import tempfile
import logging
from cellpy import log
from cellpy import prms
import cellpy.utils.batch_engines as batch_engines
from . import fdv

log.setup_logging(default_level=logging.DEBUG)


@pytest.fixture()
def clean_dir():
    new_path = tempfile.mkdtemp()
    return new_path


def test_initial():
    print(batch_engines)
    print(dir(batch_engines))


def test_base_exporter():
    base_exporter = batch_engines.BaseExporter()
    base_exporter._assign_engine()
    base_exporter._assign_dumper()


def test_base_journal():
    base_journal = batch_engines.BaseJournal()
    base_journal.from_db()
    base_journal.from_file("experiment_001.json")
    base_journal.to_file("experiment_001.json")
    base_journal.generate_file_name()
    base_journal.look_for_file()


def test_base_experiment():
    base_experiment = batch_engines.BaseExperiment()
