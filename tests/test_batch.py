import pytest
import tempfile
import logging
from cellpy import log
from cellpy.utils import batch
from . import fdv


log.setup_logging(default_level=logging.DEBUG)


@pytest.fixture()
def clean_dir():
    new_path = tempfile.mkdtemp()
    return new_path


@pytest.fixture
def batch_instance(clean_dir):
    prms = batch.prms
    prms.Paths["db_filename"] = fdv.db_file_name
    prms.Paths["cellpydatadir"] = fdv.cellpy_data_dir
    prms.Paths["outdatadir"] = clean_dir
    prms.Paths["rawdatadir"] = fdv.raw_data_dir
    prms.Paths["db_path"] = fdv.db_dir
    prms.Paths["filelogdir"] = clean_dir
    return batch.init()


@pytest.fixture
def populated_batch(batch_instance):
    b = batch.init("test", "ProjectOfRun", default_log_level="INFO",
                   batch_col=5)
    b.create_info_df()
    b.create_folder_structure()
    b.load_and_save_raw()
    return b


def test_init():
    b = batch.init()
    assert b.summaries is None
    assert b.project is None


def test_read_excel_db(batch_instance):
    name = "test"
    project = "ProjectOfRun"
    log_level = "INFO"
    b = batch.init(name, project, default_log_level=log_level, batch_col=5)
    b.create_info_df()
    b.create_folder_structure()
    b.save_info_df()
    info_file = b.info_file
    b.load_info_df(info_file)
    b.load_and_save_raw()
    b.make_summaries()


@pytest.mark.parametrize("test_input,expected", [
    (12, 24),
    (2, 4),
    (None, 2*fdv.tot_cycles)
])
def test_last_cycle(batch_instance, test_input, expected):
    import os, pandas
    b = batch.init("test", "ProjectOfRun", default_log_level="DEBUG",
                   batch_col=5)
    b.create_info_df()
    b.create_folder_structure()
    b.export_cycles = True
    b.last_cycle = test_input
    b.load_and_save_raw()
    o_file = os.path.join(b.raw_dir, fdv.example_file_for_batch)
    cycles = pandas.read_csv(o_file, sep=";")
    assert cycles.shape[-1] == expected


if __name__ == "__main__":

    prms = batch.prms
    prms.Paths["db_filename"] = fdv.db_file_name
    prms.Paths["cellpydatadir"] = fdv.cellpy_data_dir
    prms.Paths["outdatadir"] = clean_dir()
    prms.Paths["rawdatadir"] = fdv.raw_data_dir
    prms.Paths["db_path"] = fdv.db_dir
    prms.Paths["filelogdir"] = clean_dir()
    b = batch.init(default_log_level="DEBUG")
    test_read_excel_db(b)
