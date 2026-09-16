# Issue #1028: Default cellpy_file_extension is still "h5" while the native v2 format is ".cellpy"

Source: https://github.com/jepegit/cellpy/issues/1028

## Original issue text

## Problem

The shipped default for `file_names.cellpy_file_extension` is still `"h5"`:

```python
# cellpy/config/models.py:85
class FileNamesConfig(BaseModel):
    ...
    cellpy_file_extension: str = "h5"
```

(also `cellpy/parameters/prms.py:120` and
`cellpy/parameters/.cellpy_prms_default.conf:23`, and it is documented as `h5`
in `docs/getting_started/configuration_reference.md`.)

But the native cellpy 2 format is the zipped-parquet v9 file:

```python
# cellpy/readers/cellpy_file/format.py:28
V9_EXTENSION = ".cellpy"
```

and the HDF5 stack is no longer a default dependency — reading or writing the
v4–v8 HDF5 layout raises `OptionalDependencyError` telling the user to
`pip install cellpy[legacy-files]`.

## Why it matters

`filefinder.search_for_files` builds the cellpy-file name from this setting:

```python
# cellpy/readers/filefinder.py:349
cellpy_file = f"{run_name}.{cellpy_file_extension}"
```

So on a **fresh** cellpy 2 install with no user `cellpy.toml` overriding it, a
batch run resolves every cell's `cellpy_file_name` to `<run_name>.h5`. Existing
`.cellpy` files are not found (so every cell is re-read from raw), and saving
back through the batch goes down the legacy HDF5 path — which on a default
`pip install cellpy` is not installed at all.

Users who have been through a `cellpy setup` from an older version tend not to
see this, because their `cellpy.toml` already carries
`cellpy_file_extension = "cellpy"`. It is specifically the new-user path that
is affected.

## Suggested fix

Change the default to `"cellpy"` in `FileNamesConfig`, `prms.py` and
`.cellpy_prms_default.conf`, update the row in
`docs/getting_started/configuration_reference.md`, and note it in `HISTORY.md`
(existing configs are unaffected — they set the value explicitly).

Worth a quick check of whether anything else keys off `"h5"` as the cellpy
extension before flipping it.

## Notes

Found while writing a batch-database how-to guide for #1023.
