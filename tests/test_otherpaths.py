import logging
import os
import pathlib
import shutil

import dotenv
import fabric
import pytest

from cellpy.readers import core
from cellpy import log, prms

log.setup_logging(default_level=logging.DEBUG, testing=True)


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (r"C:\scripting\cellpy\testdata\data\20160805_test001_45_cc_01.res", False),
        (
            r"ssh://jepe@server.ife.no/home/jepe/cellpy/testdata/data/20160805_test001_45_cc_01.res",
            True,
        ),
        (
            r"ssh://jepe@server.ife.no/~/cellpy/testdata/data/20160805_test001_45_cc_01.res",
            True,
        ),
        (
            r"sftp://jepe@server.ife.no/home/jepe/cellpy/testdata/data/20160805_test001_45_cc_01.res",
            True,
        ),
        (r"", False),
        (r".", False),
        (r"..\data\20160805_test001_45_cc_01.res", False),
        (None, False),
    ],
)
def test_is_external(test_input, expected):
    p1 = core.OtherPath(test_input)
    assert p1.is_external == expected
    p1 = core.OtherPath(p1)
    assert p1.is_external == expected
    if test_input is not None:
        p2 = pathlib.Path(test_input)
        p3 = core.OtherPath(p2)
        assert p3.is_external == expected
        p4 = core.OtherPath(p3)
        assert p4.is_external == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (r"C:\scripting\cellpy\testdata\data\20160805_test001_45_cc_01.res", ""),
        (
            r"ssh://jepe@server.ife.no/home/jepe/cellpy/testdata/data/20160805_test001_45_cc_01.res",
            "ssh://",
        ),
        (
            r"ssh://jepe@server.ife.no/~/cellpy/testdata/data/20160805_test001_45_cc_01.res",
            "ssh://",
        ),
        (
            r"sftp://jepe@server.ife.no/home/jepe/cellpy/testdata/data/20160805_test001_45_cc_01.res",
            "sftp://",
        ),
        (r"", ""),
        (r".", ""),
        (r"..\data\20160805_test001_45_cc_01.res", ""),
        (None, ""),
    ],
)
def test_url_prefix(test_input, expected):
    p1 = core.OtherPath(test_input)
    assert p1.uri_prefix == expected
    p1 = core.OtherPath(p1)
    assert p1.uri_prefix == expected
    if test_input is not None:
        p2 = pathlib.Path(test_input)
        p3 = core.OtherPath(p2)
        assert p3.uri_prefix == expected
        p4 = core.OtherPath(p3)
        assert p4.uri_prefix == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (r"C:\scripting\cellpy\testdata\data\20160805_test001_45_cc_01.res", ""),
        (
            r"ssh://jepe@server.ife.no/home/jepe/cellpy/testdata/data/20160805_test001_45_cc_01.res",
            "jepe@server.ife.no",
        ),
        (
            r"ssh://jepe@server.ife.no/~/cellpy/testdata/data/20160805_test001_45_cc_01.res",
            "jepe@server.ife.no",
        ),
        (
            r"sftp://jepe@server.ife.no/home/jepe/cellpy/testdata/data/20160805_test001_45_cc_01.res",
            "jepe@server.ife.no",
        ),
        (r"", ""),
        (r".", ""),
        (r"..\data\20160805_test001_45_cc_01.res", ""),
        (None, ""),
    ],
)
def test_location(test_input, expected):
    p1 = core.OtherPath(test_input)
    assert p1.location == expected
    p1 = core.OtherPath(p1)
    assert p1.location == expected
    if test_input is not None:
        p2 = pathlib.Path(test_input)
        p3 = core.OtherPath(p2)
        assert p3.location == expected
        p4 = core.OtherPath(p3)
        assert p4.location == expected


@pytest.mark.parametrize(
    "test_input,expected",
    [
        (
            r"C:\scripting\cellpy\testdata\data\20160805_test001_45_cc_01.res",
            "C:/scripting/cellpy/testdata/data/20160805_test001_45_cc_01.res",
        ),
        (
            r"ssh://jepe@server.ife.no/home/jepe/cellpy/testdata/data/20160805_test001_45_cc_01.res",
            "/home/jepe/cellpy/testdata/data/20160805_test001_45_cc_01.res",
        ),
        (
            r"ssh://jepe@server.ife.no/~/cellpy/testdata/data/20160805_test001_45_cc_01.res",
            "/~/cellpy/testdata/data/20160805_test001_45_cc_01.res",
        ),
        (
            r"sftp://jepe@server.ife.no/home/jepe/cellpy/testdata/data/20160805_test001_45_cc_01.res",
            "/home/jepe/cellpy/testdata/data/20160805_test001_45_cc_01.res",
        ),
        (r"", "."),
        (r".", "."),
        (
            r"..\data\20160805_test001_45_cc_01.res",
            "../data/20160805_test001_45_cc_01.res",
        ),
        (None, "."),
    ],
)
def test_raw_path(test_input, expected):
    p1 = core.OtherPath(test_input)
    assert p1.raw_path == expected
    p1 = core.OtherPath(p1)
    assert p1.raw_path == expected
    if test_input is not None:
        p2 = pathlib.Path(test_input)
        p3 = core.OtherPath(p2)
        assert p3.raw_path == expected
        p4 = core.OtherPath(p3)
        assert p4.raw_path == expected
        print("--------------------------")
        print(p4._original)


def test_check_strange_name():
    p = r"/home/jepe/cellpy/testdata/data/20160805_test001_45_cc_01.res"
    p1 = core.OtherPath(p)
    print()
    for t in dir(p1):
        print(f"{t=}: {getattr(p1, t, 'MISSING!!!')}")


def test_check_strange_name():
    p = r"/home/jepe/cellpy/testdata/data/20160805_test001_45_cc_01.res"
    p1 = core.OtherPath(p)
    print()
    for t in dir(p1):
        print(f"{t=}: {getattr(p1, t, 'MISSING!!!')}")


def test_check_env_host(parameters, mock_env_cellpy_host):
    assert os.getenv("CELLPY_HOST") == parameters.env_cellpy_host


def test_check_env_user(parameters, mock_env_cellpy_user):
    assert os.getenv("CELLPY_USER") == parameters.env_cellpy_user


def test_check_env_key_filename(parameters, mock_env_cellpy_key_filename):
    assert os.getenv("CELLPY_KEY_FILENAME") == parameters.env_cellpy_key_filename


def test_check_env_password(parameters, mock_env_cellpy_password):
    assert os.getenv("CELLPY_PASSWORD") == parameters.env_cellpy_password


def test_load_environment(parameters):
    env_file = parameters.env_file
    config = dotenv.dotenv_values(env_file)
    assert config.get("CELLPY_USER") == parameters.env_cellpy_user
    assert config.get("CELLPY_PASSWORD") == parameters.env_cellpy_password
    assert config.get("CELLPY_KEY_FILENAME") == parameters.env_cellpy_key_filename
    assert config.get("CELLPY_HOST") == parameters.env_cellpy_host


def test_copy_local(parameters, tmp_path):
    p1 = core.OtherPath(parameters.res_file_path)
    p2 = p1.copy()
    assert p2.is_file()
    assert p1 is not p2
    assert p2.name == p1.name
    assert p2.parent != p1.parent


def test_copy_remote_simple(
    parameters,
    tmp_path,
    monkeypatch,
    mock_env_cellpy_host,
    mock_env_cellpy_user,
    mock_env_cellpy_key_filename,
):
    def mock_return(n, _host, _connect_kwargs, _destination):
        # TODO: include more realistic ssh session
        #   with mock password authentication etc
        if os.name == "nt":
            # hack to allow running tests on Windows:
            shutil.copy2(n._raw_other_path.lstrip("/"), _destination)
        else:
            shutil.copy2(n.raw_path, _destination)

    monkeypatch.setattr(core.OtherPath, "_copy_with_fabric", mock_return)

    p1 = str(parameters.res_file_path)
    host = os.getenv("CELLPY_HOST")
    user = os.getenv("CELLPY_USER")
    p2 = f"ssh://{user}@{host}/{p1}"
    remote_file_path = core.OtherPath(p2)
    local_file_path = remote_file_path.copy(testing=True)
    assert local_file_path.is_file()
    assert remote_file_path is not local_file_path
    assert isinstance(local_file_path, pathlib.Path)
    # cellpy version 1.0.0 will not support copying to a remote location
    #   therefore, the returned object will always be a pathlib.Path object
    assert not isinstance(local_file_path, core.OtherPath)
