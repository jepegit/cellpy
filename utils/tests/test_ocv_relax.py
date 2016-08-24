# -*- coding: utf-8 -*-

"""
Running nosetests on ocv_relaxation curves
"""

import nose.tools as nt
from ..cell_ocv import foo

__author__ = 'Tor Kristian Vara', 'Jan Petter Mæhlen'
__email__ = 'tor.vara@nmbu.no', 'jepe@ife.no'


def test_print_hello_world():
    """
    checks that the function foo returns a string "Hello world!"
    """
    nt.assert_equal(foo(), "Hello world!")
    nt.assert_is_instance(foo(), str)
