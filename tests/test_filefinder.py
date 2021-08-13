import pytest
from cellpy import filefinder
from cellpy import log
from . import fdv

log.setup_logging(default_level="DEBUG")


@pytest.fixture(scope="module")
def env():
    from cellpy.parameters import prms
    prms.Paths["outdatadir"] = fdv.output_dir
    prms.Paths["rawdatadir"] = fdv.raw_data_dir
    prms.Paths["cellpydatadir"] = fdv.cellpy_data_dir
    prms.Paths["db_path"] = fdv.db_dir
    prms.Paths["db_filename"] = fdv.db_file_name


def test_search_for_files_with_dirs():
    import os

    raw_files, cellpy_file = filefinder.search_for_files(
        fdv.run_name, raw_file_dir=fdv.raw_data_dir, cellpy_file_dir=fdv.output_dir
    )

    assert fdv.res_file_path in raw_files
    assert os.path.basename(cellpy_file) == fdv.cellpy_file_name


def test_search_for_files_default_dirs(env):
    raw_files, cellpy_file = filefinder.search_for_files(fdv.run_name)

    assert fdv.res_file_path in raw_files


def test_search_for_res_files():
    raw_files, cellpy_file = filefinder.search_for_files(
        fdv.run_name,
        raw_extension="res",
        cellpy_file_extension=None,
        raw_file_dir=fdv.raw_data_dir,
        cellpy_file_dir=fdv.output_dir,
        prm_filename=None,
        file_name_format=None,
    )

    assert fdv.res_file_path in raw_files


def test_search_for_strange_files():
    raw_files, cellpy_file = filefinder.search_for_files(
        fdv.run_name,
        raw_extension="STRANGE-FILE-THAT-DOES-NOT-EXIST",
        cellpy_file_extension=None,
        raw_file_dir=fdv.raw_data_dir,
        cellpy_file_dir=fdv.output_dir,
        prm_filename=None,
        file_name_format=None,
    )
    assert len(raw_files) == 0


def test_search_for_files_using_custom_prms_file():
    # this is not enabled
    raw_files, cellpy_file = filefinder.search_for_files(
        fdv.run_name, prm_filename=fdv.default_prm_file
    )
