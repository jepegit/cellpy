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

from cellpy.readers import cellreader, dbreader, filefinder, do

# from cellpy.readers.data_structures import Q, ureg

logging.getLogger(__name__).addHandler(logging.NullHandler())

# Config loads lazily on first ``cellpy.config`` / ``config.*`` access, or via
# ``cellpy.parameters.prmreader.initialize()`` (issue #453).

# TODO: (v2.0) remove this and enforce using `cellpy.get` (or `cellpy.cellreader.get`) instead:
get = cellreader.get
print_instruments = readers.cellreader.print_instruments

__all__ = [
    "cellreader",
    "dbreader",
    "prmreader",
    "prms",
    "filefinder",
    "get",
    "do",
    # "ureg",
    # "Q",
]
