import pytest
import tempfile
import logging
import time
import pandas

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

from cellpy.utils import batch as batch
from . import fdv

log.setup_logging(default_level="INFO")


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
    logging.info(f"using pandas {pandas.__version__}")
    cycling_experiment.update()
    return cycling_experiment


def test_csv_exporter(updated_cycling_experiment):
    logging.info(f"using pandas {pandas.__version__}")
    exporter = batch_exporters.CSVExporter()
    exporter.assign(updated_cycling_experiment)
    exporter.do()

# TODO: fix me
@pytest.mark.slowtest
def test_update_time(cycling_experiment):
    t0 = time.time()
    cycling_experiment.update(all_in_memory=True)
    cycling_experiment.status()
    names = cycling_experiment.cell_names
    for name in names:
        # print(name)
        cell = cycling_experiment.data[name]
        cycles = cell.get_cycle_numbers()

        for cycle in cycles:
            capacity, voltage = cell.get_cap(
                cycle=cycle,
            )
            try:
                l = len(capacity)
            except TypeError as e:
                print(e)
    t1 = time.time()
    dt = t1-t0
    print(f"This took {dt} seconds")


@pytest.mark.slowtest
def test_link_time(cycling_experiment):
    t0 = time.time()
    cycling_experiment.link()
    cycling_experiment.status()
    names = cycling_experiment.cell_names
    for name in names:
        cell = cycling_experiment.data[name]
        cycles = cell.get_cycle_numbers()

        for cycle in cycles:
            capacity, voltage = cell.get_cap(
                cycle=cycle,
            )
            try:
                l = len(capacity)
            except TypeError as e:
                print(e)
    t1 = time.time()
    dt = t1-t0
    print(f"This took {dt} seconds")


def test_link(cycling_experiment):
    cycling_experiment.link()
    print(cycling_experiment)
    cycling_experiment.status()
    names = cycling_experiment.cell_names
    print(names)


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
    capacity_voltage_df = updated_cycling_experiment.data[name].get_cap(
        cycle=1,
    )
    assert len(capacity_voltage_df) == 1105


def test_cycling_summary_plotter(populated_batch):
    populated_batch.make_summaries()
    populated_batch.plot_summaries()
