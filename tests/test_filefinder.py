import os
import tempfile
import shutil
import datetime
import pytest
import logging

import cellpy.readers.core
from cellpy.exceptions import DeprecatedFeature
from cellpy import filefinder
from cellpy import log
from . import fdv

log.setup_logging(default_level="DEBUG")


def test_search_for_files_with_dirs():
    import os
    raw_files, cellpy_file = filefinder.search_for_files(
        fdv.run_name,
        raw_file_dir=fdv.raw_data_dir,
        cellpy_file_dir=fdv.output_dir
    )

    assert fdv.res_file_path in raw_files
    assert os.path.basename(cellpy_file) == fdv.cellpy_file_name


def test_search_for_files_default_dirs():
    raw_files, cellpy_file = filefinder.search_for_files(
        fdv.run_name,
    )

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
        cache=None,
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
        cache=None,
    )
    assert len(raw_files) == 0


def test_search_for_files_using_custom_prms_file():
    # this is not enabled
    raw_files, cellpy_file = filefinder.search_for_files(
        fdv.run_name,
        prm_filename=fdv.default_prm_file,
    )


