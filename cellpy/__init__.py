# -*- coding: utf-8 -*-

""" """

__author__ = (
    "Jan Petter Maehlen",
    "Asbjoern Ulvestad",
    "Muhammad Abdelhamid",
    "Julia Wind",
)
__email__ = (
    "jepe@ife.no",
    "Asbjorn.Ulvestad@ife.no",
    "Muhammad.Abdelhamid@ife.no",
    "julia.wind@ife.no",
)

import logging

import cellpy._version

from cellpy import parameters
from cellpy import readers
from cellpy.parameters import prms  # TODO: this might give circular ref
from cellpy.parameters import prmreader

__version__ = cellpy._version.__version__

from cellpy.readers import cellreader, dbreader, filefinder, do, data_structures

# from cellpy.readers.data_structures import Q, ureg

logging.getLogger(__name__).addHandler(logging.NullHandler())

# Config loads lazily on first ``cellpy.config`` / ``config.*`` access, or via
# ``cellpy.parameters.prmreader.initialize()`` (issue #453).

# Sanctioned top-level API (v2, issue #509): ``cellpy.get`` is the primary
# entry point; ``cellpy.merge_cells`` and ``cellpy.print_instruments`` are the
# supporting conveniences. ``cellpy.read_meta`` peeks cellpy-file metadata
# without loading frames (issue #799). Everything else is reached via explicit
# module paths (``cellpy.cellreader``, ``cellpy.config`` / ``cellpy.config.session``).
get = cellreader.get
merge_cells = cellreader.merge_cells
print_instruments = readers.cellreader.print_instruments
list_instruments = readers.data_structures.list_instruments
instrument_meta_schema = readers.data_structures.instrument_meta_schema


def read_meta(path):
    """Read cellpy-file metadata without loading raw/steps/summary frames.

    See ``cellpy.readers.cellpy_file.read_meta`` for details.
    """
    from cellpy.readers.cellpy_file import read_meta as _read_meta

    return _read_meta(path)


__all__ = [
    "cellreader",
    "dbreader",
    "prmreader",
    "prms",
    "filefinder",
    "get",
    "merge_cells",
    "print_instruments",
    "list_instruments",
    "instrument_meta_schema",
    "read_meta",
    "do",
    # "ureg",
    # "Q",
]
