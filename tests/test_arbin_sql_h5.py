import logging
import shutil
import tempfile

import pytest

from cellpy import get, log, prms

log.setup_logging(default_level=logging.DEBUG, testing=True)


def test_get_data_from_arbin_sql_h5(parameters):
    # TODO: @jepe -> @asbjørn: this test fails for the new make_summary method (has fewer raw-lines than
    #  47; probably due to duplicates pruned in the new method). I have disabled the new method for now (see below).
    #  We need to figure out what is happening before re-enabling using the new method
    c = get(
        filename=parameters.arbin_sql_h5_path,
        instrument="arbin_sql_h5",
        testing=True,
        auto_summary=False,
    )
    assert len(c.data.raw) == 47
    c.make_summary(old=True)
    assert len(c.data.summary) == 1
