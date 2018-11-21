import pytest
import tempfile
import logging

import cellpy.utils.dumpers
import cellpy.utils.engines
from cellpy import log
from cellpy import prms
import cellpy.utils.batch_core as batch_engines
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
    base_exporter._assign_engine(cellpy.utils.engines.cycles_engine)
    base_exporter._assign_dumper(cellpy.utils.dumpers.csv_dumper)


def test_base_journal():
    base_journal = batch_engines.BaseJournal()


def test_base_experiment():
    base_experiment = batch_engines.BaseExperiment()

