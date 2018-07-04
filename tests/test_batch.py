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
    prms.Paths["db_filename"] = fdv.test_db_filename
    prms.Paths["cellpydatadir"] = fdv.test_data_dir_cellpy
    prms.Paths["outdatadir"] = clean_dir
    prms.Paths["rawdatadir"] = fdv.test_data_dir_raw
    prms.Paths["db_path"] = fdv.test_data_dir_db
    prms.Paths["filelogdir"] = clean_dir
    return batch.init()


def test_init():
    b = batch.init()
    assert b.summaries is None
    assert b.project is None


def test_read_excel_db(batch_instance):
    name = "test"
    project = "ProjectOfRun"
    log_level = "INFO"
    print("creating batch instance")
    b = batch.init(name, project, default_log_level=log_level, batch_col=5)
    print("creating info df")
    b.create_info_df()
    print("creating folder structure")
    b.create_folder_structure()
    print("saving info df")
    b.save_info_df()
    info_file = b.info_file
    print("loading")
    print(info_file)
    b.load_info_df(info_file)
    print("loading and saving raw-files")
    b.load_and_save_raw()
    print("making summaries")
    b.make_summaries()


if __name__ == "__main__":

    prms = batch.prms
    prms.Paths["db_filename"] = fdv.test_db_filename
    prms.Paths["cellpydatadir"] = fdv.test_data_dir_cellpy
    prms.Paths["outdatadir"] = clean_dir()
    prms.Paths["rawdatadir"] = fdv.test_data_dir_raw
    prms.Paths["db_path"] = fdv.test_data_dir_db
    prms.Paths["filelogdir"] = clean_dir()
    b = batch.init(default_log_level="DEBUG")
    test_read_excel_db(b)
