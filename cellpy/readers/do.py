"""Modifiers for ``cellpy.CellPyCell`` objects.

This module is used for modifying ``cellpy.CellPyCell`` objects after they have been created.
All modifiers should take a ``cellpy.CellPyCell`` object as input and return a new ``cellpy.CellPyCell`` object.
This is to ensure that the original ``cellpy.CellPyCell`` object is not modified in place and that the
raw data is not changed (unless explicitly requested). This is an experimental feature of cellpy and is
not yet fully implemented.

"""

from copy import deepcopy


def copy(c_old):
    c = deepcopy(c_old)
    return c
