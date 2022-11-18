=======================
Main ``cellpy`` objects
=======================

The ``CellpyCell`` object
-------------------------

The ``CellpyCell`` object contains the main methods as well as the actual data::

    cellpy_instance = CellpyCell(...)

Data is stored as ``Data`` instances within the list ``cells``.
Even though one ``CellpyCell`` instance can contain several ``Data`` instances,
it is (currently) recommended to only use one.

The ``Data`` instance can be reached using the ``data`` property::

    cell_instance = cellpy_instance.data

The ``Data`` object
-------------------

The ``Data`` object contains the data and the meta-data for the cell characterisation experiment(s).


The cellpy file format
----------------------

As default, cellpy stores files in the hdf5 format.
