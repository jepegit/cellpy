import logging
import shutil
import tempfile

import pytest

from cellpy import get, log, prms

log.setup_logging(default_level=logging.DEBUG, testing=True)


def test_get_data_from_arbin_sql_h5(parameters):
    c = get(
        filename=parameters.arbin_sql_h5_path,
        instrument="arbin_sql_h5",
        testing=True,
        auto_summary=False,
    )
    assert len(c.data.raw) == 47
    c.make_summary()
    assert len(c.data.summary) == 1
    # The core-backed summary prunes duplicate raw rows as a side effect
    # (issue #385: verified value-identical to the removed legacy engine,
    # which kept all 47 rows).
    assert len(c.data.raw) == 34
