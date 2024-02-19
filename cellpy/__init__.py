# -*- coding: utf-8 -*-

"""

"""

__author__ = "Jan Petter Maehlen", "Asbjoern Ulvestad", "Muhammad Abdelhamid"
__email__ = "jepe@ife.no", "Asbjorn.Ulvestad@ife.no", "Muhammad.Abdelhamid@ife.no"

import logging
import warnings

import cellpy._version
from cellpy.parameters import prms  # TODO: this might give circular ref
from cellpy.parameters import prmreader
from cellpy.readers import cellreader, dbreader, filefinder, do
from cellpy.readers.core import Q, ureg

__version__ = cellpy._version.__version__

logging.getLogger(__name__).addHandler(logging.NullHandler())

init = prmreader.initialize
init()

get = cellreader.get

__all__ = [
    "cellreader",
    "dbreader",
    "prmreader",
    "prms",
    "filefinder",
    "get",
    "do",
    "init",
    "ureg",
    "Q",
]
