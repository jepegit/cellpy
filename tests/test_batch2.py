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
    base_exporter._assign_engine(batch_engines.cycles_engine)
    base_exporter._assign_dumper(batch_engines.csv_dumper)


def test_base_journal():
    base_journal = batch_engines.BaseJournal()


def test_base_experiment():
    base_experiment = batch_engines.BaseExperiment()

