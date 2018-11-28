import pytest
import tempfile
import logging

from cellpy.utils.batch_tools import (
    batch_experiments,
    batch_exporters,
    batch_journals,
    batch_plotters,
    dumpers,
    engines,
)

from cellpy import log
from cellpy import prms

from cellpy.utils import batch2 as batch
from . import fdv

log.setup_logging(default_level="DEBUG")


@pytest.fixture(scope="module")
def clean_dir():
    new_path = tempfile.mkdtemp()
    return new_path


@pytest.fixture(scope="module")
def batch_instance(clean_dir):
    prms.Paths["db_filename"] = fdv.db_file_name
    prms.Paths["cellpydatadir"] = fdv.cellpy_data_dir
    prms.Paths["outdatadir"] = clean_dir
    prms.Paths["rawdatadir"] = fdv.raw_data_dir
    prms.Paths["db_path"] = fdv.db_dir
    prms.Paths["filelogdir"] = clean_dir
    return batch


@pytest.fixture(scope="module")
def populated_batch(batch_instance):
    b = batch_instance.init(
        "test", "ProjectOfRun",
        default_log_level="DEBUG",
        batch_col="b01"
    )
    b.create_info_df()
    b.create_folder_structure()
    b.load_and_save_raw()
    return b


@pytest.fixture(scope="module")
def cycling_experiment(batch_instance):
    experiment = batch_experiments.CyclingExperiment()
    experiment.journal.project = "ProjectOfRun"
    experiment.journal.name = "test"
    experiment.export_raw = True
    experiment.export_cycles = True
    experiment.export_ica = True
    experiment.journal.from_db()
    return experiment


@pytest.fixture(scope="module")
def updated_cycling_experiment(cycling_experiment):
    cycling_experiment.update()
    return cycling_experiment


def test_csv_exporter(updated_cycling_experiment):
    exporter = batch_exporters.CSVExporter()
    exporter.assign(updated_cycling_experiment)
    exporter.do()


def test_load_from_file(batch_instance):
    experiment = batch_experiments.CyclingExperiment()
    pages = fdv.pages
    experiment.journal.from_file(pages)


def test_csv_exporter_modified(updated_cycling_experiment):
    exporter = batch_exporters.CSVExporter()
    exporter.assign(updated_cycling_experiment)
    exporter._assign_engine(engines.dq_dv_engine)
    exporter._assign_dumper(dumpers.screen_dumper)


def test_lab_journal(batch_instance):
    lab_journal = batch_journals.LabJournal()


def test_cycling_experiment_to_file(cycling_experiment):
    cycling_experiment.journal.to_file()


def test_interact_with_cellpydata_get_cap(updated_cycling_experiment):
    name = fdv.run_name
    capacity, voltage = updated_cycling_experiment.data[name].get_cap(
        cycle=1,
    )
    assert len(capacity) == len(voltage)
    assert len(capacity) == 1105


def test_cycling_summary_plotter(updated_cycling_experiment):
    plotter = batch_plotters.CyclingSummaryPlotter()
