# TODO: remove dependencies on conftest and fdv


import logging
import pathlib
import tempfile

import pandas
import pytest

from cellpy import log, prms
from cellpy.utils import batch as batch

from cellpy.utils.batch_tools import (
    batch_exporters,
    batch_experiments,
)
from cellpy.utils.batch_tools.batch_core import get_headers_journal

log.setup_logging(default_level="DEBUG", testing=True)

hdr_journal = get_headers_journal()


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
    b = batch_instance.init("test", "ProjectOfRun", default_log_level="DEBUG", batch_col="b01", testing=True)

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


def test_csv_exporter(updated_cycling_experiment):
    logging.info(f"using pandas {pandas.__version__}")
    exporter = batch_exporters.CSVExporter()
    exporter.assign(updated_cycling_experiment)
    exporter.do()


def test_create_cellpyfile(cellpy_data_instance, tmp_path, parameters, capsys):
    # create a cellpy file from the res-file (used for testing)
    cellpy_data_instance.set_instrument("arbin_res")
    cellpy_data_instance.from_raw(parameters.res_file_path)
    with capsys.disabled():
        print(f"\nFilename: {parameters.res_file_path}")
        print("\nHERE IS THE DATA:")
        print(cellpy_data_instance.data)
    cellpy_data_instance.mass = 1.0
    cellpy_data_instance.make_summary(find_ir=True, find_end_voltage=True)
    name = pathlib.Path(tmp_path) / pathlib.Path(parameters.cellpy_file_path).name
    logging.info(f"trying to save the cellpy file to {name}")
    cellpy_data_instance.save(name)


def test_generate_absolute_summary_columns(cellpy_data_instance, capsys, parameters):
    from cellpy.slim import summarizers, selectors

    nom_cap = 1.0
    mass = 1.0
    cellpy_data_instance.from_raw(parameters.res_file_path)

    nom_cap_abs = cellpy_data_instance.nominal_capacity_as_absolute(nom_cap, mass, "gravimetric")

    with capsys.disabled():
        print(cellpy_data_instance)
    cellpy_data_instance.make_step_table()
    data = cellpy_data_instance.core.data
    selector = selectors.create_selector(data)
    cellpy_data_instance.core.make_core_summary(data, selector, find_ir=True, find_end_voltage=True)

    # data = summarizers.generate_absolute_summary_columns(data)
    # cellpy_data_instance.core.generate_absolute_summary_columns(find_ir=True, find_end_voltage=True)
    # cellpy_data_instance.core.add_scaled_summary_columns(nom_cap_abs=1.0, normalization_cycles=[1, 2, 3])
