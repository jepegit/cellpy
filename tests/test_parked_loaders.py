"""Parked tier-3 loaders raise a typed error naming the replacement (#561).

Shipping 2.0 with a loader silently half-working is worse than shipping it
documented as parked. `ext_nda_reader` is the live case: its load path
returned mock data (`load_nda()` printed its arguments and returned None),
so a "successful" load produced an empty cell.
"""

from __future__ import annotations

import logging

import pytest

from cellpy import log
from cellpy.exceptions import LoaderError

log.setup_logging(default_level=logging.DEBUG, testing=True)


@pytest.mark.essential
def test_ext_nda_reader_is_parked_with_a_pointer():
    from cellpy.readers.instruments.ext_nda_reader import DataLoader

    with pytest.raises(LoaderError, match="neware_nda"):
        DataLoader()


@pytest.mark.essential
def test_the_parked_message_names_the_status():
    from cellpy.readers.instruments.ext_nda_reader import _PARKED_MESSAGE

    assert "parked" in _PARKED_MESSAGE
    assert "neware_nda" in _PARKED_MESSAGE


@pytest.mark.essential
def test_ext_nda_reader_no_longer_claims_the_live_instrument_name():
    """It used to claim instrument_name "neware_nda" - the *real* fastnda
    loader's name - so the zombie and the live loader collided."""
    from cellpy.readers.instruments import ext_nda_reader, neware_nda

    assert ext_nda_reader.DataLoader.instrument_name == "ext_nda_reader"
    assert neware_nda.DataLoader.instrument_name == "neware_nda"


@pytest.mark.essential
def test_ext_nda_reader_stays_out_of_the_instrument_listing():
    from cellpy.readers.data_structures import LOADERS_NOT_READY_FOR_PROD

    assert "ext_nda_reader" in LOADERS_NOT_READY_FOR_PROD
