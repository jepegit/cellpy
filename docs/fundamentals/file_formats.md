# File formats

The `cellpy`-file format stores the contents of the **Data** object (frames +
metadata) together with a file-version stamp.

## Default: v9 `.cellpy`

In cellpy **2.x**, `save()` writes **v9** by default: a zip archive of parquet
tables (`raw` / `steps` / `summary`, and optional file-id members) plus typed
metadata in `meta.json`. The usual extension is `.cellpy`.

```python
c.save("my_run.cellpy")                 # v9 zip-of-parquet
c.load("my_run.cellpy")                 # sniffs v9 vs HDF5
```

## Legacy HDF5

Older **v8** (and, with care, earlier) **HDF5** layouts remain readable.
To write HDF5 explicitly:

```python
c.save("my_run.h5")                     # extension selects HDF5
c.save("out.cellpy", cellpy_file_format="hdf5")
```

On pip, reading/writing legacy HDF5 needs the optional extra
`cellpy[legacy-files]` (PyTables). Conda packages still ship `pytables`.
Prefer converting once to v9 (`cellpy convert old.h5`) if you can drop the
extra.

Full support matrix and convert recipes:
[Migrating from cellpy 1.x to 2.x](../getting_started/migration_v1_to_v2.md#support-matrix-files).

## Tabular exports

Simple exports to CSV (`c.to_csv(out_folder)`) or Excel
(`c.to_excel(out_folder)`) are also available.
