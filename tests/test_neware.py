import logging
import shutil
import tempfile

import pytest

from cellpy import get, log, prms

log.setup_logging(default_level=logging.DEBUG, testing=True)


def test_get_neware_from_csv(parameters):
    c = get(
        filename=parameters.nw_file_path,
        instrument="neware_txt",
        model="UIO",
        mass=2.08,
    )
    assert len(c.cell.raw) == 9065
    assert len(c.cell.summary) == 4

