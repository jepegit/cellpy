"""Parked NDA loader (tier-3 decision, #561).

Neware NDA files are supported through ``instrument="neware_nda"``, which uses
the bundled ``fastnda`` reader (``cellpy.libs.local_fastnda``). This module was
an experimental wrapper around a separately-installed third-party
``nda_reader`` and never became production-ready — its load path returned mock
data (a ``load_nda`` stub that printed its arguments and returned ``None``),
so a "successful" load produced an empty cell.

Per the loader plan's tier-3 decision it is **parked, not silently broken**:
selecting it raises a typed :class:`~cellpy.exceptions.LoaderError` naming the
replacement. Removal in 2.1 unless users object.
"""

from cellpy.exceptions import LoaderError
from cellpy.readers.instruments.base import BaseLoader

_PARKED_MESSAGE = (
    "the 'ext_nda_reader' loader is parked in cellpy 2.0: it was never "
    "production-ready (its load path returned mock data, so it produced empty "
    "cells). Neware NDA files are supported via instrument='neware_nda' "
    "(the bundled fastnda reader). The standalone nda_reader by Frederik Huld "
    "remains available as a separate package for scripted use."
)


class DataLoader(BaseLoader):
    """Parked. Use ``instrument="neware_nda"`` instead."""

    # The old module claimed instrument_name "neware_nda", colliding with the
    # real fastnda-backed loader of that name. The parked stub answers to its
    # own module name only.
    instrument_name = "ext_nda_reader"
    raw_ext = "nda"

    def __init__(self, *args, **kwargs):
        raise LoaderError(_PARKED_MESSAGE)

    @staticmethod
    def get_params(parameter=None):
        params = {"raw_ext": "nda"}
        if parameter is not None:
            return params[parameter]
        return params

    @staticmethod
    def get_raw_units() -> dict:
        raise LoaderError(_PARKED_MESSAGE)

    def get_raw_limits(self) -> dict:
        raise LoaderError(_PARKED_MESSAGE)

    def loader(self, *args, **kwargs) -> list:
        raise LoaderError(_PARKED_MESSAGE)
