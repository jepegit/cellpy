import pathlib

import pytest

from cellpy import filefinder, log

log.setup_logging(default_level="DEBUG", testing=True)


@pytest.fixture
def env(parameters):
    from cellpy.parameters import prms

    prms.Paths.outdatadir = parameters.output_dir
    prms.Paths.rawdatadir = parameters.raw_data_dir
    prms.Paths.cellpydatadir = parameters.cellpy_data_dir
    prms.Paths.db_path = parameters.db_dir
    prms.Paths.db_filename = parameters.db_file_name


def test_search_for_files_with_dirs(parameters):
    import os

    raw_files, cellpy_file = filefinder.search_for_files(
        parameters.run_name,
        raw_file_dir=parameters.raw_data_dir,
        cellpy_file_dir=parameters.output_dir,
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


def test_search_for_files_using_prms(parameters):
    from cellpy import prms

    prms.FileNames.reg_exp = ""
    prms.FileNames.raw_extension = "txt"
    raw_files, cellpy_file = filefinder.search_for_files(
        parameters.run_name_maccor,
        raw_file_dir=parameters.raw_data_dir,
        cellpy_file_dir=parameters.output_dir,
    )
    assert parameters.mcc_file_path in raw_files


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


# ----------------------------------------------------------------------
# Fixture-free tests on a synthetic tmp_path raw-file tree (issue #372).
# ----------------------------------------------------------------------


@pytest.fixture
def raw_tree(tmp_path):
    """A small fake raw-data directory with a subdirectory."""
    (tmp_path / "sub").mkdir()
    for name in ["runA_01.res", "runA_02.res", "runB_01.res", "notes.txt"]:
        (tmp_path / name).touch()
    (tmp_path / "sub" / "runA_03.res").touch()
    cellpy_dir = tmp_path / "cellpyfiles"
    cellpy_dir.mkdir()
    return tmp_path, cellpy_dir


def test_search_for_files_recursive(raw_tree):
    raw_dir, cellpy_dir = raw_tree
    raw_files, cellpy_file = filefinder.search_for_files(
        "runA", raw_extension="res", raw_file_dir=raw_dir, cellpy_file_dir=cellpy_dir
    )
    names = sorted(pathlib.Path(f).name for f in raw_files)
    assert names == ["runA_01.res", "runA_02.res", "runA_03.res"]
    assert cellpy_file.endswith("runA.h5")


def test_search_for_files_no_sub_folders(raw_tree):
    raw_dir, cellpy_dir = raw_tree
    raw_files, _ = filefinder.search_for_files(
        "runA",
        raw_extension="res",
        raw_file_dir=raw_dir,
        cellpy_file_dir=cellpy_dir,
        sub_folders=False,
    )
    names = sorted(pathlib.Path(f).name for f in raw_files)
    assert names == ["runA_01.res", "runA_02.res"]


def test_search_for_files_within_file_list(raw_tree):
    raw_dir, cellpy_dir = raw_tree
    raw_files, _ = filefinder.search_for_files(
        "runA",
        raw_extension="res",
        raw_file_dir=raw_dir,
        cellpy_file_dir=cellpy_dir,
        file_list=["runA_01.res", "runB_01.res"],
        with_prefix=False,
    )
    assert raw_files == ["runA_01.res"]


def test_search_for_files_missing_raw_dir_warns(tmp_path):
    cellpy_dir = tmp_path / "cellpyfiles"
    cellpy_dir.mkdir()
    with pytest.warns(UserWarning, match="cannot be accessed"):
        raw_files, _ = filefinder.search_for_files(
            "runA",
            raw_extension="res",
            raw_file_dir=tmp_path / "does-not-exist",
            cellpy_file_dir=cellpy_dir,
        )
    assert raw_files == []


def test_list_raw_file_directory_extension_filter(raw_tree):
    raw_dir, _ = raw_tree
    file_list = filefinder.list_raw_file_directory(raw_file_dir=raw_dir, extension="res")
    names = sorted(pathlib.Path(f).name for f in file_list)
    assert names == ["runA_01.res", "runA_02.res", "runB_01.res"]


def test_list_raw_file_directory_only_filename(raw_tree):
    raw_dir, _ = raw_tree
    file_list = filefinder.list_raw_file_directory(
        raw_file_dir=raw_dir, extension="res", only_filename=True
    )
    assert sorted(str(f) for f in file_list) == [
        "runA_01.res",
        "runA_02.res",
        "runB_01.res",
    ]
