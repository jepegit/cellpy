.. _cellpy-objects:

Main ``cellpy`` objects
=======================

.. note:: This chapter would benefit from some more love and care. Any help
    on that would be highly appreciated.

.. _CellpyCell-object:

The ``CellpyCell`` object
-------------------------

.. graphviz::

   digraph {
      "CellpyCell" -> "Data";
      "CellpyCell" -> "session metadata";
      "CellpyCell" -> "cellpy metadata";
      "CellpyCell" -> "methods";
   }



The ``CellpyCell`` object contains the main methods as well as the actual data::

    cellpy_instance = CellpyCell(...)

Data is stored within an instance of the ``Data`` class.

.. graphviz::

   digraph {
    "CellpyCell" -> "Data";
        "Data" -> "cell metadata (cell)";
        "Data" -> "cell metadata (test)";
        "Data" -> "methods";
        "Data" -> "raw";
        "Data" -> "steps";
        "Data" -> "summary";
   }


The ``Data`` instance can be reached using the ``data`` property::

    cell_data = cellpy_instance.data

.. _Data-object:

The ``Data`` object
-------------------

The ``Data`` object contains the data and the meta-data for the cell characterisation experiment(s).

.. _cellpy-file-object:

The cellpy file format
----------------------

As default, cellpy stores files in the hdf5 format.
