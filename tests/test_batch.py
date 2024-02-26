import ast
import logging
import os
import pathlib
import tempfile
import time

import pandas
import pytest

from cellpy import log, prms
from cellpy.utils import batch as batch
from cellpy.utils import helpers
from cellpy.utils.batch_tools import (
    batch_experiments,
    batch_exporters,
    batch_journals,
    batch_plotters,
    dumpers,
    engines,
)
from cellpy.utils.batch_tools.batch_core import get_headers_journal

log.setup_logging(default_level="DEBUG", testing=True)

hdr_journal = get_headers_journal()

# TODO: I think these tests saves new versions of cellpyfiles each time. Fix that.
# TODO: Most likely some of these tests also saves an updated batch json file. Fix that.


@pytest.fixture(scope="module")
def clean_dir():
    new_path = tempfile.mkdtemp()
    return new_path


@pytest.fixture
def batch_instance(clean_dir, parameters):
    prms.Paths.db_filename = parameters.db_file_name
    prms.Paths.cellpydatadir = clean_dir
    prms.Paths.outdatadir = clean_dir
    prms.Paths.rawdatadir = parameters.raw_data_dir
    prms.Paths.db_path = parameters.db_dir
    prms.Paths.filelogdir = clean_dir
    prms.Paths.batchfiledir = clean_dir
    prms.Paths.notebookdir = clean_dir
    prms.Paths.instrumentdir = parameters.instrument_dir
    prms.Paths.templatedir = parameters.template_dir
    prms.Paths.examplesdir = parameters.examples_dir
    prms.Batch.auto_use_file_list = False
    return batch


@pytest.fixture
def populated_batch(batch_instance):
    b = batch_instance.init(
        "test", "ProjectOfRun", default_log_level="DEBUG", batch_col="b01", testing=True
    )

    b.create_journal(duplicate_to_local_folder=False)
    b.paginate()
    b.update(testing=True)
    return b


@pytest.fixture
def cycling_experiment(batch_instance):
    experiment = batch_experiments.CyclingExperiment()
    experiment.journal.project = "ProjectOfRun"
    experiment.journal.name = "test"
    experiment.export_raw = True
    experiment.export_cycles = True
    experiment.export_ica = True
    experiment.journal.from_db()
    return experiment


@pytest.fixture
def updated_cycling_experiment(cycling_experiment):
    # warning: this test uses the same cellpy file that some of the other
    # tests updates from time to time. so if one of those tests fails and corrupts
    # the cellpy file, this test might also fail
    logging.info(f"using pandas {pandas.__version__}")
    cycling_experiment.update(testing=True)
    return cycling_experiment


def test_reading_db(batch_instance):
    b = batch_instance.init(
        "test", "ProjectOfRun", default_log_level="DEBUG", batch_col="b01", testing=True
    )

    b.create_journal(duplicate_to_local_folder=False)


def test_reading_cell_specs(batch_instance):
    # For the simple excel dbreader, cell specs are given in the
    # columns "argument" as str.
    # The argument str must be on the form:
    #    "keyword-1=value-1;keyword-2=value2"

    b = batch_instance.init(
        "test", "ProjectOfRun", default_log_level="DEBUG", batch_col="b02", testing=True
    )
    b.create_journal(duplicate_to_local_folder=False)
    hdr = hdr_journal["argument"]
    with_argument = b.pages.iloc[0][hdr]
    with_several_arguments = b.pages.iloc[1][hdr]
    without_argument = b.pages.iloc[2][hdr]
    assert with_argument["recalc"].upper() == "TRUE"
    assert with_several_arguments["recalc"].upper() == "FALSE"
    assert ast.literal_eval(with_several_arguments["data_points"]) == (1, 10_000)
    assert not without_argument


def test_load_journal_json(parameters, batch_instance):
    b = batch_instance.from_journal(parameters.journal_file_json_path, testing=True)
    assert len(b.pages) == 5
    assert hdr_journal["argument"] in b.pages.columns


def test_load_limited_journal_excel(parameters, batch_instance):
    b = batch_instance.from_journal(parameters.journal_file_xlsx_path, testing=True)
    assert len(b.pages) == 2
    assert hdr_journal["argument"] in b.pages.columns


def test_load_full_journal_excel_and_check_headers_generated(
    parameters, batch_instance
):
    index_name = "filename"
    b = batch_instance.from_journal(
        parameters.journal_file_full_xlsx_path, testing=True
    )
    assert len(b.pages) == 2
    missing = [hdr for hdr in hdr_journal.values() if hdr not in b.pages.columns]
    assert len(missing) == 1
    assert b.pages.index.name == index_name
    assert (
        missing[0] == index_name
    )  # this is the only missing column since it is now the index


def test_load_full_journal_excel_from_labjournal_class(parameters):
    from cellpy.utils.batch_tools.batch_journals import LabJournal

    journal = LabJournal(db_reader="off")
    journal.from_file(parameters.journal_file_full_xlsx_path, paginate=False)
    assert len(journal.pages) == 2


def test_load_journal_json_from_labjournal_class(parameters):
    from cellpy.utils.batch_tools.batch_journals import LabJournal

    journal = LabJournal(db_reader="off")
    journal.from_file(parameters.journal_file_json_path, paginate=False)
    assert len(journal.pages) == 5


# TODO: make this test
def test_update_with_cellspecs(parameters, batch_instance):
    # from journal and as argument (see batch_experiment.py, update).
    pass


def test_load_save_journal_roundtrip_cell_specs(parameters, clean_dir, batch_instance):
    b = batch_instance.from_journal(parameters.journal_file_json_path, testing=True)
    out = pathlib.Path(clean_dir) / "j.json"
    b.experiment.journal.to_file(
        file_name=out, to_project_folder=False, duplicate_to_local_folder=False
    )
    spec_1 = b.pages[hdr_journal["argument"]].iloc[0]
    assert spec_1 == "recalc=False"
    assert out.is_file()
    b2 = batch_instance.from_journal(out, testing=True)
    assert len(b.pages) == 5
    assert hdr_journal["argument"] in b.pages.columns
    assert b2.pages[hdr_journal["argument"]].iloc[0] == spec_1


# TODO: make this test
def test_load_save_journal_roundtrip_excel(batch_instance):
    pass


# TODO: make this test
def test_load_save_journal_roundtrip_json(batch_instance):
    pass


def test_load_journal_dataframe(batch_instance):
    import pandas as pd
    from cellpy.utils.batch_tools.batch_journals import LabJournal
    from cellpy.internals.core import OtherPath

    _frame = {
        "filename": ["a", "b", "c"],
        "argument": ["recalc=True", "recalc=False", "recalc=False"],
        "keep": ["True", "False", "True"],
        "mass": ["1.0", "2.0", "3.0"],
        "area": ["1.0", "2.0", "3.0"],
        "total_mass": ["1.0", "2.0", "3.0"],
        "loading": ["1.0", "2.0", "3.0"],
        "nom_cap": ["1.0", "2.0", "3.0"],
        "experiment": ["cycling", "cycling", "cycling"],
        "cell_type": ["anode", "anode", "anode"],
        "instrument": ["arbin_res", "neware_txt", "maccor_txt::1"],
        "comment": ["", "", ""],
        "fixed": [0, 0, False],
        "label": ["", "cell2", ""],
        "cellpy_file_name": [
            pathlib.Path("data/cellpyfiles/20160805_test001_45_cc.cellpy"),
            OtherPath("data/cellpyfiles/20160805_test001_46_cc.cellpy"),
            "data/cellpyfiles/20160805_test001_47_cc.cellpy",
        ],
        "raw_file_names": [
            [
                "data/raw/20160805_test001_45_cc_01.res",
                "data/raw/20160805_test001_45_cc_02.res",
            ],
            "data/raw/20160805_test001_46_cc_01.txt",
            OtherPath("ssh://user@server.in.no/data/raw/20160805_test001_47_cc_01.txt"),
        ],
        "group": [1, 1, 1],
        "sub_group": [1, 2, 3],
    }
    frame = pd.DataFrame(_frame)
    journal = LabJournal(db_reader="off")
    journal.from_frame(frame, paginate=False)
    assert isinstance(journal.pages.raw_file_names.iloc[0], list)
    assert isinstance(journal.pages.raw_file_names.iloc[1], str)
    assert isinstance(journal.pages.raw_file_names.iloc[2], OtherPath)
    assert journal.pages.group.iloc[0] == 1
    assert len(journal.pages) == 3


# TODO: make this test
def test_load_journal_custom_db_reader(batch_instance):
    pass


def test_csv_exporter(updated_cycling_experiment):
    logging.info(f"using pandas {pandas.__version__}")
    exporter = batch_exporters.CSVExporter()
    exporter.assign(updated_cycling_experiment)
    exporter.do()


def test_query():
    def mock_reader_method(cell_id):
        spec = {
            1: "recalc=True",
            2: "recalc=False;other=12",
        }
        return spec[cell_id]

    from cellpy.utils.batch_tools import engines

    cell_ids = [1, 2]
    out = engines._query(mock_reader_method, cell_ids)
    assert "=" in out[0]
    assert ";" in out[1]


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


def test_load_from_file(batch_instance, parameters):
    experiment = batch_experiments.CyclingExperiment()
    pages = parameters.pages
    experiment.journal.from_file(pages)


def test_csv_exporter_modified(updated_cycling_experiment):
    exporter = batch_exporters.CSVExporter()
    exporter.assign(updated_cycling_experiment)
    exporter._assign_engine(engines.dq_dv_engine)
    exporter._assign_dumper(dumpers.screen_dumper)


def test_lab_journal(batch_instance):
    lab_journal = batch_journals.LabJournal()


def test_cycling_experiment_to_file(cycling_experiment):
    cycling_experiment.journal.to_file(duplicate_to_local_folder=False)


def test_interact_with_cellpydata_get_cap(updated_cycling_experiment, parameters):
    name = parameters.run_name_2
    capacity_voltage_df = updated_cycling_experiment.data[name].get_cap(cycle=1)
    assert len(capacity_voltage_df) == 1105


def test_cycling_summary_plotter(populated_batch):
    populated_batch.combine_summaries()
    populated_batch.plot()


def test_concatinator(populated_batch):
    cellnames = populated_batch.cell_names
    c = populated_batch.experiment.data[cellnames[0]]
    cf = helpers.concatenate_summaries(
        populated_batch, columns=["charge_capacity"], rate=0.04, group_it=True
    )
    print(cf.head(5))


def test_concatinator_yanked(populated_batch):
    removed = helpers.yank_outliers(
        populated_batch, remove_indexes=[3, 4, 5], keep_old=False
    )
    print(removed)
    c1 = populated_batch.experiment.data[populated_batch.cell_names[0]]
    print(c1.data.summary.head(10))
    cf1 = helpers.concatenate_summaries(
        populated_batch, columns=["charge_capacity"], rate=0.04, group_it=True
    )
    cf2 = helpers.concatenate_summaries(
        populated_batch,
        columns=["charge_capacity"],
        rate=0.04,
        group_it=True,
        inverted=True,
    )
    print(cf1.head())
    print(cf2.head())


def test_report(populated_batch):
    print(populated_batch.report)


def test_batch_update(parameters, batch_instance):
    b = batch_instance.init(
        "test", "ProjectOfRun", default_log_level="DEBUG", batch_col="b01", testing=True
    )
    b.create_journal(duplicate_to_local_folder=False)
    b.paginate()
    b.update(testing=True)


# def test_iterate_folder(batch_instance):
# # Since the batch-files contains full paths I need to figure out how to make a custom json-file for the test.
#     folder_name = prms.Paths.batchfiledir
#     batch.iterate_batches(folder_name, default_log_level="CRITICAL")
