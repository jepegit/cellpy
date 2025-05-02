import collections
import datetime
import logging
# import capsys
import os
import pathlib
import shutil
import tempfile

import pytest

import cellpy.readers.core
from cellpy import log, prms
from cellpy.exceptions import DeprecatedFeature, WrongFileVersion
from cellpy.parameters.internal_settings import get_headers_summary
from cellpy.internals.core import OtherPath

log.setup_logging(default_level="DEBUG", testing=True)


def test_create_cellpyfile(cellpy_data_instance, tmp_path, parameters, capsys):
    # create a cellpy file from the res-file (used for testing)
    cellpy_data_instance.from_raw(parameters.res_file_path)
    with capsys.disabled():
        print("\nHERE IS THE DATA:")
        print(f"data type: {type(cellpy_data_instance.data)}")
    cellpy_data_instance.set_mass(1.0)
    cellpy_data_instance.make_summary(find_ir=True, find_end_voltage=True)
    name = pathlib.Path(tmp_path) / pathlib.Path(parameters.cellpy_file_path).name
    logging.info(f"trying to save the cellpy file to {name}")
    cellpy_data_instance.save(name)