# -*- coding: utf-8 -*-

"""

"""

__author__ = "Jan Petter Maehlen", "Asbjoern Ulvestad", "Muhammad Abdelhamid"
__email__ = "jepe@ife.no", "Asbjorn.Ulvestad@ife.no", "Muhammad.Abdelhamid@ife.no"

import logging
import warnings
from cellpy.readers import cellreader
from cellpy.readers import dbreader
from cellpy.readers import filefinder
from cellpy.parameters import prmreader
from cellpy.parameters import prms  # TODO: this might give circular ref
import cellpy._version

__version__ = cellpy._version.__version__

logging.getLogger(__name__).addHandler(logging.NullHandler())

try:
    prmreader._read_prm_file(prmreader._get_prm_file())
except FileNotFoundError:
    warnings.warn("Could not find the config-file")
except UserWarning:
    warnings.warn("Could not read the config-file")

get = cellreader.get
__all__ = ["cellreader", "dbreader", "prmreader", "prms", "filefinder", "get"]
