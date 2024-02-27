import logging
import os
import tempfile
import time

import pytest

from cellpy import log

from . import fdv

log.setup_logging(default_level="DEBUG", testing=True)


def test_example_data():
    from cellpy.utils import example_data

    a = example_data.raw_file(testing=True)
    c = example_data.cellpy_file(testing=True)
    c.make_summary()

    assert a.data.summary.shape == (18, 49)
    assert c.data.summary.shape == (304, 49)


def test_example_path_data():
    from cellpy.utils import example_data

    filepath = example_data.cellpy_file_path
    print(f"{filepath=}")
    print(f"{type(filepath)=}")


def test_example_path_download_data():
    from cellpy.utils import example_data

    filepath = example_data.old_cellpy_file_path()
    assert filepath.is_file()
    print(f"{filepath=}")
    print(f"{type(filepath)=}")
