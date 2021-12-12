import pytest
from cellpy import filefinder
from cellpy import log

log.setup_logging(default_level="DEBUG")


@pytest.fixture
def env(parameters):
    from cellpy.parameters import prms

    prms.Paths["outdatadir"] = parameters.output_dir
    prms.Paths["rawdatadir"] = parameters.raw_data_dir
    prms.Paths["cellpydatadir"] = parameters.cellpy_data_dir
    prms.Paths["db_path"] = parameters.db_dir
    prms.Paths["db_filename"] = parameters.db_file_name


def test_search_for_files_with_dirs(parameters):
    import os

    raw_files, cellpy_file = filefinder.search_for_files(
        parameters.run_name, raw_file_dir=parameters.raw_data_dir, cellpy_file_dir=parameters.output_dir
    )

    assert parameters.res_file_path in raw_files
    assert os.path.basename(cellpy_file) == parameters.cellpy_file_name


def test_search_for_files_default_dirs(env, parameters):
    raw_files, cellpy_file = filefinder.search_for_files(parameters.run_name)

    assert parameters.res_file_path in raw_files


def test_search_for_res_files(parameters):
    raw_files, cellpy_file = filefinder.search_for_files(
        parameters.run_name,
        raw_extension="res",
        cellpy_file_extension=None,
        raw_file_dir=parameters.raw_data_dir,
        cellpy_file_dir=parameters.output_dir,
        prm_filename=None,
        file_name_format=None,
    )

    assert parameters.res_file_path in raw_files


def test_search_for_strange_files(parameters):
    raw_files, cellpy_file = filefinder.search_for_files(
        parameters.run_name,
        raw_extension="STRANGE-FILE-THAT-DOES-NOT-EXIST",
        cellpy_file_extension=None,
        raw_file_dir=parameters.raw_data_dir,
        cellpy_file_dir=parameters.output_dir,
        prm_filename=None,
        file_name_format=None,
    )
    assert len(raw_files) == 0


def test_search_for_files_using_custom_prms_file(parameters):
    # this is not enabled
    raw_files, cellpy_file = filefinder.search_for_files(
        parameters.run_name, prm_filename=parameters.default_prm_file
    )
