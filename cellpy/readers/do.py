"""Modifiers for cellpy.CellPyCell objects.

This module is used for modifying cellpy.CellPyCell objects after they have been created.
All modifiers should take a cellpy.CellPyCell object as input and return a new cellpy.CellPyCell object.
"""

from copy import deepcopy


def say_hello(c_old):
    c = deepcopy(c_old)
    print(f"Hello {c.cell_name}!")
    return c


def copy(c_old):
    c = deepcopy(c_old)
    return c
