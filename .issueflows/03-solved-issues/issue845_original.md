# Issue #845: Non-atomic v9 .cellpy writes can corrupt (and destroy) the file on interrupt

Source: https://github.com/jepegit/cellpy/issues/845

## Original issue text

## Problem
The v9 writer saves straight onto the destination path:

```python
# cellpy/readers/cellpy_file/v9.py
with zipfile.ZipFile(path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
    ...  # meta.json -> raw.parquet -> steps / summary / fid
```

Mode `"w"` truncates `path` **immediately**, then members are appended in
order. An interrupt / kill / exception mid-write (common when parquet-serialising
large raw tables) leaves a zip that still opens but is missing members:

```
cellpy.exceptions.CorruptCellpyFile: missing zip member 'raw.parquet'
```

Because the write is in place, this also **destroys the previously-good file** —
a re-save that fails halfway loses the old data too.

## How it surfaced
Building cellpy-simple-gui, a project save (many `cell.save(..., overwrite=True)`)
was interrupted. One `.cellpy` contained only `meta.json` (~1 KB); later cells
were never written and the partially-written one no longer loaded. The app now
stages the *project folder* atomically, but each individual `cell.save()` can
still truncate a good `.cellpy` in place — the app can't protect a single file.

## Suggested fix
Write to a same-directory temp file, then atomically replace:

```python
tmp = path.with_suffix(path.suffix + ".tmp")
with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zf:
    ...
# optional: verify required members are present in tmp
os.replace(tmp, path)   # atomic on the same filesystem
```

so a reader never sees a half-written archive and a failed save leaves the
previous file intact. `v8`/older writers, if they share this pattern, would
benefit too.


---
*Found while building [cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui) on cellpy 2.1.1.post7. Context: [CELLPY_PAINPOINTS.md §19](https://github.com/cellpy/cellpy-simple-gui/blob/main/CELLPY_PAINPOINTS.md).*
