# -*- coding: utf-8 -*-

"""

"""

__author__ = 'Tor Kristian Vara', 'Jan Petter Maehlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'

import logging
from cellpy.readers import cellreader
from cellpy.readers import dbreader
from cellpy.readers import filefinder
from cellpy.parametres import prmreader


__all__ = ["cellreader", "dbreader", "prmreader", "filefinder"]

logging.getLogger(__name__).addHandler(logging.NullHandler())

# I wonder if adding prmreader.read() here makes the prms available as cellpy.parameters ?
