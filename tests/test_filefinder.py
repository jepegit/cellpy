import pathlib

import pytest

from cellpy import config, filefinder, log

log.setup_logging(default_level="DEBUG", testing=True)


@pytest.mark.essential
@pytest.mark.parametrize(
    "name, project, expected",
    [
        ("20240922_SAL12", "SAL", 12),
        ("20240922_SAL12_cc.cellpy", "SAL", 12),
        ("20240922_sal15.res", "SAL", 15),
        ("/data/cells/20240922_SAL12.cellpy", "sal", 12),
        ("20240922_SAL9", "BAT", None),
        ("notes_SAL12.txt", "SAL", None),
        ("20240922_SALAMANDER12", "SAL", None),
        ("20240922_SAL12", "", None),
    ],
)
def test_parse_project_run_number(name, project, expected):
    assert filefinder.parse_project_run_number(name, project) == expected


def _sal_tree(tmp_path):
    cellpy_dir = tmp_path / "cellpyfiles"
    raw_dir = tmp_path / "raw"
    cellpy_dir.mkdir()
    raw_dir.mkdir()
    for n in (9, 10, 12, 15, 16):
        (cellpy_dir / f"20240922_SAL{n}.cellpy").write_text("x")
    (cellpy_dir / "20240922_BAT11.cellpy").write_text("x")
    (raw_dir / "20240922_SAL12.res").write_text("x")
    (raw_dir / "20240922_SAL14.res").write_text("x")
    return cellpy_dir, raw_dir


@pytest.mark.essential
def test_find_by_project_cellpy_range(tmp_path, config_guard):
    config_guard("paths")
    cellpy_dir, raw_dir = _sal_tree(tmp_path)
    config.paths.cellpydatadir = str(cellpy_dir)
    config.paths.rawdatadir = str(raw_dir)
    hits = filefinder.find_by_project("SAL", 10, 15, kind="cellpy")
    assert [h["number"] for h in hits] == [10, 12, 15]
    assert all(h["kind"] == "cellpy" for h in hits)
    assert all(h["name"].endswith(".cellpy") for h in hits)


@pytest.mark.essential
def test_find_by_project_empty(tmp_path, config_guard):
    config_guard("paths")
    empty = tmp_path / "empty_cellpy"
    empty.mkdir()
    config.paths.cellpydatadir = str(empty)
    assert filefinder.find_by_project("SAL", 10, 15, kind="cellpy") == []


@pytest.mark.essential
def test_find_by_project_raw_ignores_cellpy_dir(tmp_path, config_guard):
    config_guard("paths")
    cellpy_dir, raw_dir = _sal_tree(tmp_path)
    config.paths.cellpydatadir = str(cellpy_dir)
    config.paths.rawdatadir = str(raw_dir)
    hits = filefinder.find_by_project("SAL", 10, 15, kind="raw")
    assert [h["number"] for h in hits] == [12, 14]
    assert all(h["kind"] == "raw" for h in hits)
    assert all(h["name"].endswith(".res") for h in hits)


@pytest.mark.essential
def test_find_by_project_unknown_kind():
    with pytest.raises(ValueError, match="kind"):
        filefinder.find_by_project("SAL", 10, 15, kind="journal")


@pytest.mark.essential
def test_find_by_project_otherpath_local(tmp_path, config_guard):
    from cellpy.internals.connections import OtherPath

    config_guard("paths")
    cellpy_dir, _raw_dir = _sal_tree(tmp_path)
    hits = filefinder.find_by_project(
        "sal", 10, 15, kind="cellpy", root=OtherPath(cellpy_dir)
    )
    assert [h["number"] for h in hits] == [10, 12, 15]


@pytest.fixture
def env(parameters, config_guard):
    from cellpy.parameters import prms

    config_guard("paths")
    config.paths.outdatadir = parameters.output_dir
    config.paths.rawdatadir = parameters.raw_data_dir
    config.paths.cellpydatadir = parameters.cellpy_data_dir
    config.paths.db_path = parameters.db_dir
    config.paths.db_filename = parameters.db_file_name


def test_search_for_files_with_dirs(parameters, default_file_names):
    import os

    raw_files, cellpy_file = filefinder.search_for_files(
        parameters.run_name,
        raw_file_dir=parameters.raw_data_dir,
        cellpy_file_dir=parameters.output_dir,
    )

    assert parameters.res_file_path in raw_files
    assert os.path.basename(cellpy_file) == f"{parameters.run_name}.cellpy"


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


def test_search_for_files_using_prms(parameters, config_guard):
    from cellpy import prms

    # without the guard the "txt" extension leaks into every later test module
    config_guard("file_names")
    config.file_names.reg_exp = ""
    config.file_names.raw_extension = "txt"
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


def test_search_for_files_recursive(raw_tree, default_file_names):
    raw_dir, cellpy_dir = raw_tree
    raw_files, cellpy_file = filefinder.search_for_files(
        "runA", raw_extension="res", raw_file_dir=raw_dir, cellpy_file_dir=cellpy_dir
    )
    names = sorted(pathlib.Path(f).name for f in raw_files)
    assert names == ["runA_01.res", "runA_02.res", "runA_03.res"]
    # the default extension, pinned by the fixture - not the developer's own
    assert cellpy_file.endswith("runA.cellpy")


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


@pytest.fixture
def rglob_spy(monkeypatch):
    """Record the kwargs ``search_for_files`` hands to ``OtherPath.rglob``."""
    from cellpy.internals.connections import OtherPath

    calls = []
    original = OtherPath.rglob

    def _spy(self, glob_str, *args, **kwargs):
        calls.append(kwargs)
        return original(self, glob_str, *args, **kwargs)

    monkeypatch.setattr(OtherPath, "rglob", _spy)
    return calls


def test_search_for_files_recursive_uses_files_only(raw_tree, rglob_spy):
    """Per-cell search must take the files_only / find -L path (#899)."""
    raw_dir, cellpy_dir = raw_tree
    raw_files, _ = filefinder.search_for_files(
        "runA", raw_extension="res", raw_file_dir=raw_dir, cellpy_file_dir=cellpy_dir
    )
    assert rglob_spy, "search_for_files did not use rglob"
    assert all(call.get("files_only") is True for call in rglob_spy)
    names = sorted(pathlib.Path(f).name for f in raw_files)
    assert names == ["runA_01.res", "runA_02.res", "runA_03.res"]


def test_search_for_files_no_sub_folders_does_not_rglob(raw_tree, rglob_spy):
    raw_dir, cellpy_dir = raw_tree
    filefinder.search_for_files(
        "runA",
        raw_extension="res",
        raw_file_dir=raw_dir,
        cellpy_file_dir=cellpy_dir,
        sub_folders=False,
    )
    assert rglob_spy == []


def test_search_for_files_within_file_list_does_not_rglob(raw_tree, rglob_spy):
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
    assert rglob_spy == []


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


def test_find_in_raw_file_directory_files_only(raw_tree, caplog):
    """Directories matching ``*`` must not be counted as files (#688)."""
    import logging

    raw_dir, _ = raw_tree
    with caplog.at_level(logging.INFO):
        file_list = filefinder.find_in_raw_file_directory(raw_file_dir=raw_dir)
    names = sorted(pathlib.Path(f).name for f in file_list)
    assert "sub" not in names
    assert "runA_01.res" in names
    assert "runA_03.res" in names
    assert any("Found " in r.message and "files" in r.message for r in caplog.records)


def test_find_in_raw_file_directory_empty_warns(tmp_path, caplog):
    import logging

    empty = tmp_path / "empty_raw"
    empty.mkdir()
    with caplog.at_level(logging.CRITICAL):
        file_list = filefinder.find_in_raw_file_directory(raw_file_dir=empty)
    assert file_list == []
    assert any("No files found" in r.message for r in caplog.records)


def test_find_in_raw_file_directory_remote_no_isfile_stat(
    monkeypatch, mock_env_cellpy_key_filename
):
    """Remote dump must not call is_file() per path (#690)."""
    from tests.test_otherpath_symlink_rglob import _FakeFS, _FakeUPath

    shared_fs = _FakeFS()

    class _BoundFakeUPath(_FakeUPath):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, fs=shared_fs, **kwargs)

    monkeypatch.setattr("cellpy.internals.otherpath.UPath", _BoundFakeUPath)
    # filefinder does not pass testing=True; skip real key-file existence check.
    monkeypatch.setattr(
        "cellpy.internals.otherpath._credentials_from_env",
        lambda *, testing=False: {},
    )

    from cellpy.internals.connections import OtherPath

    calls = {"is_file": 0}
    original = OtherPath.is_file

    def _counting_is_file(self, *args, **kwargs):
        calls["is_file"] += 1
        return original(self, *args, **kwargs)

    monkeypatch.setattr(OtherPath, "is_file", _counting_is_file)

    root = OtherPath("sftp://user@host/home/user/projects")
    file_list = filefinder.find_in_raw_file_directory(raw_file_dir=root)
    assert any("20250709_lol079_01_cc_01.h5" in p for p in file_list)
    assert any(p.endswith("other.h5") for p in file_list)
    assert calls["is_file"] == 0
    assert shared_fs.isfile_calls == 0


def test_find_in_raw_file_directory_large_n_warns(tmp_path, caplog, monkeypatch):
    import logging

    monkeypatch.setattr(filefinder, "_LARGE_FILE_LIST_WARN", 2)
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "a.res").write_text("x")
    (raw / "b.res").write_text("y")
    (raw / "c.res").write_text("z")
    with caplog.at_level(logging.WARNING):
        file_list = filefinder.find_in_raw_file_directory(raw_file_dir=raw)
    assert len(file_list) == 3
    assert any("huge shared" in r.message or "project-scoped" in r.message for r in caplog.records)
