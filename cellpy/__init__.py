# -*- coding: utf-8 -*-

"""

"""

__author__ = 'Tor Kristian Vara', 'Jan Petter Maehlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'

import logging
import warnings
from cellpy.readers import cellreader
from cellpy.readers import dbreader
from cellpy.readers import filefinder
from cellpy.parameters import prmreader, prms



__all__ = ["cellreader", "dbreader", "prmreader", "prms", "filefinder"]

logging.getLogger(__name__).addHandler(logging.NullHandler())

try:
    prmreader._read_prm_file(prmreader._get_prm_file())
except:
    warnings.warn("obs! could not load the config-file")


