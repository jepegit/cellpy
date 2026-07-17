(cellpy-objects)=

# Main cellpy objects

:::{note}
This chapter would benefit from some more love and care. Any help
on that would be highly appreciated.
:::

(cellpycell-object)=

## The `CellpyCell` object

```{eval-rst}
.. graphviz::

   digraph {
      "CellpyCell" -> "Data";
      "CellpyCell" -> "session metadata";
      "CellpyCell" -> "cellpy metadata";
      "CellpyCell" -> "methods";
   }


```

The `CellpyCell` object contains the main methods as well as the actual data:

```
cellpy_instance = CellpyCell(...)
```

Data is stored within an instance of the `Data` class.

```{eval-rst}
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

```

The `Data` instance can be reached using the `data` property:

```
cell_data = cellpy_instance.data
```

(data-object)=

## The `Data` object

The `Data` object contains the data and the meta-data for the cell characterisation experiment(s).

(cellpy-file-object)=

## The cellpy file format

As default (cellpy 2.x / file version 9), cellpy stores files as a zip of
parquet tables plus ``meta.json`` (``.cellpy``). Older HDF5 layouts (v4–v8)
remain readable; pass a ``.h5`` path or ``cellpy_file_format="hdf5"`` to write
HDF5. See {doc}`../../getting_started/migration_v1_to_v2`.
