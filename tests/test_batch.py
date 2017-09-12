import os
import pytest
import tempfile

# -------- defining overall path-names etc ----------
current_file_path = os.path.dirname(os.path.realpath(__file__))
relative_test_data_dir = "../testdata"
test_data_dir = os.path.abspath(os.path.join(current_file_path, relative_test_data_dir))

test_data_dir_raw = os.path.join(test_data_dir, "data")
test_data_dir_out = os.path.join(test_data_dir, "out")
test_data_dir_cellpy = os.path.join(test_data_dir, "hdf5")
test_data_dir_db = os.path.join(test_data_dir, "db")

test_cellpy_file = "20160805_test001_45_cc.h5"
test_cellpy_file_full = os.path.join(test_data_dir_cellpy,test_cellpy_file)

test_cellpy_file_tmp = "tmpfile.h5"
test_cellpy_file_tmp_full = os.path.join(test_data_dir_cellpy,test_cellpy_file_tmp)

test_db_filename = "cellpy_db.xlsx"
test_db_filename_full = os.path.join(test_data_dir_db,test_db_filename)

test_run_name = "20160805_test001_45_cc"

test_res_file = "20160805_test001_45_cc_01.res"
test_res_file_full = os.path.join(test_data_dir_raw,test_res_file)


import logging
from cellpy import log
from cellpy.utils import batch

log.setup_logging(default_level=logging.DEBUG)


@pytest.fixture()
def clean_dir():
    new_path = tempfile.mkdtemp()
    return new_path


@pytest.fixture
def batch_instance(clean_dir):
    prms = batch.prms
    prms.Paths["db_filename"] = test_db_filename
    prms.Paths["cellpydatadir"] = test_data_dir_cellpy
    prms.Paths["outdatadir"] = clean_dir
    prms.Paths["rawdatadir"] = test_data_dir_raw
    prms.Paths["db_path"] = test_data_dir_db
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
    prms.Paths["db_filename"] = test_db_filename
    prms.Paths["cellpydatadir"] = test_data_dir_cellpy
    prms.Paths["outdatadir"] = clean_dir()
    prms.Paths["rawdatadir"] = test_data_dir_raw
    prms.Paths["db_path"] = test_data_dir_db
    prms.Paths["filelogdir"] = clean_dir()
    b = batch.init(default_log_level="DEBUG")
    test_read_excel_db(b)
