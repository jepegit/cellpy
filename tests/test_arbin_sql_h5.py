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
    # #560 Phase C: keep all loader-stage rows through summary. The older
    # core-backed path pruned duplicates as a side effect (47 → 34); the
    # harmonized default path does not.
    assert len(c.data.raw) == 47
