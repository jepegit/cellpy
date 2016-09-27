# -*- coding: utf-8 -*-

"""

"""

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'
__version__ = '0.1.0'


__requires__ = [
    'pandas',
    'tables',
    'adodbapi',
    'tempfile',
    'csv',
    'itertools',
]

from cellpy.readers import arbinreader
from cellpy.readers import dbreader
from cellpy.parametres import prmreader