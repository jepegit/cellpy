=======================
Main ``cellpy`` objects
=======================

The ``CellpyData`` object
-------------------------

The ``CellpyData`` object contains the main methods as well as the actual data::

    cellpy_instance = CellpyData(...)

Data is stored as ``Data`` instances within the list ``cells``.
Even though one ``CellpyData`` instance can contain several ``Data`` instances,
it is (currently) recommended to only use one.

The ``Data`` instance can be reached using the ``cell`` property::

    cell_instance = cellpy_instance.cell

The ``Data`` object
-------------------

The ``Data`` object contains the data and the meta-data for the cell characterisation experiment(s).


The cellpy file format
----------------------

As default, cellpy stores files in the hdf5 format.
