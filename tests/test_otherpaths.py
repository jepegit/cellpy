import logging
import pathlib

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
