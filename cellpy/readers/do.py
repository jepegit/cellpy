"""Modifiers for cellpy.CellPyCell objects.

This module is used for modifying cellpy.CellPyCell objects after they have been created.
All modifiers should take a cellpy.CellPyCell object as input and return a new cellpy.CellPyCell object.
This is to ensure that the original cellpy.CellPyCell object is not modified in place and that the
raw data is not changed (unless explicitly requested).
"""

from copy import deepcopy


def say_hello(c_old):
    c = deepcopy(c_old)
    print(f"Hello {c.cell_name}!")
    return c


def copy(c_old):
    c = deepcopy(c_old)
    return c
