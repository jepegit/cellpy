import logging
import os
import tempfile
import time

import pytest

from cellpy import log

from . import fdv

log.setup_logging(default_level="DEBUG", testing=True)


@pytest.mark.skip(reason="this is not needed in CI/CD pipeline")
def test_example_data():
    from cellpy.utils import example_data

    a = example_data.raw_file(testing=True)
    c = example_data.cellpy_file(testing=True)
    c.make_summary()

    assert a.data.summary.shape == (18, 61)
    assert c.data.summary.shape == (304, 61)


@pytest.mark.skip(reason="this is not needed in CI/CD pipeline")
def test_example_path_data():
    from cellpy.utils import example_data

    filepath = example_data.cellpy_file_path()
    assert filepath.is_file()


@pytest.mark.skip(reason="this is not needed in CI/CD pipeline")
def test_example_path_download_data():
    from cellpy.utils import example_data

    filepath = example_data.old_cellpy_file_path()
    assert filepath.is_file()


@pytest.mark.skip(reason="this is not needed in CI/CD pipeline")
def test_example_data_missing_file():
    from cellpy.utils import example_data
    import requests

    with pytest.raises(requests.HTTPError):
        example_data._download_if_missing("non_existing_file.txt")


@pytest.mark.skip(reason="this is not needed in CI/CD pipeline")
def test_example_data_remove_and_download():
    from cellpy.utils import example_data
    import requests

    filename = example_data.cellpy_file_path()
    assert filename.is_file()
    example_data._remove_file(filename.name)
    assert not filename.is_file()
    example_data._download_if_missing(filename.name)
    assert filename.is_file()


@pytest.mark.skip(reason="this is not needed in CI/CD pipeline")
def test_download_all_and_then_remove():
    from cellpy.utils import example_data

    example_data._download_all_files()
    for f in example_data.ExampleData:
        assert (example_data.DATA_PATH / f.value).is_file()
        example_data._remove_file(f.value)


@pytest.mark.skip(reason="this is not needed in CI/CD pipeline")
def test_download_all():
    from cellpy.utils import example_data

    example_data.download_all_files()
    for f in example_data.ExampleData:
        assert (example_data.DATA_PATH / f.value).is_file()


@pytest.mark.skip(reason="this is not needed in CI/CD pipeline")
def test_remove_all():
    from cellpy.utils import example_data

    example_data._remove_all_files()
    for f in example_data.ExampleData:
        assert not (example_data.DATA_PATH / f.value).is_file()
