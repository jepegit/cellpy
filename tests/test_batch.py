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
from cellpy.utils import helpers

from . import fdv

log.setup_logging(default_level="DEBUG")


# TODO: I think these tests saves new versions of cellpyfiles each time. Fix that.
# TODO: Most likely some of these tests also saves an updated batch json file. Fix that.

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
    prms.Paths["batchfiledir"] = fdv.batch_file_dir
    prms.Paths["notebookdir"] = clean_dir
    return batch


@pytest.fixture(scope="module")
def populated_batch(batch_instance):
    b = batch_instance.init(
        "test", "ProjectOfRun", default_log_level="DEBUG", batch_col="b01"
    )
    b.create_journal()
    b.paginate()
    b.update()
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
    # warning: this test uses the same cellpy file that some of the other
    # tests updates from time to time. so if one of those tests fails and corrupts
    # the cellpy file, this test might also fail
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
            capacity, voltage = cell.get_cap(cycle=cycle)
            try:
                l = len(capacity)
            except TypeError as e:
                print(e)
    t1 = time.time()
    dt = t1 - t0
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
            capacity, voltage = cell.get_cap(cycle=cycle)
            try:
                l = len(capacity)
            except TypeError as e:
                print(e)
    t1 = time.time()
    dt = t1 - t0
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
    capacity_voltage_df = updated_cycling_experiment.data[name].get_cap(cycle=1)
    assert len(capacity_voltage_df) == 1105


def test_cycling_summary_plotter(populated_batch):
    populated_batch.make_summaries()
    populated_batch.plot_summaries()


def test_concatinator(populated_batch):
    cellnames = populated_batch.cell_names
    c = populated_batch.experiment.data[cellnames[0]]
    cf = helpers.concatenate_summaries(
        populated_batch, columns=["charge_capacity"], rate=0.04, group_it=True,
    )
    print(cf.head(5))


def test_concatinator_yanked(populated_batch):
    b_yanked = helpers.yank_outliers(populated_batch, remove_indexes=[3, 4, 5], keep_old=False)
    c1 = b_yanked.experiment.data[b_yanked.cell_names[0]]
    print(c1.cell.summary.head(10))
    cf1 = helpers.concatenate_summaries(
        b_yanked, columns=["charge_capacity"], rate=0.04, group_it=True,
    )
    cf2 = helpers.concatenate_summaries(
        b_yanked, columns=["charge_capacity"], rate=0.04, group_it=True, inverted=True,
    )
    print(cf1.head())
    print(cf2.head())


def test_report(populated_batch):
    print(populated_batch.report)


# def test_iterate_folder(batch_instance):
# # Since the batch-files contains full paths I need to figure out how to make a custom json-file for the test.
#     folder_name = prms.Paths.batchfiledir
#     batch.iterate_batches(folder_name, default_log_level="CRITICAL")
