# Atomic cellpy-file writes

**Context.** The v9 writer opened `zipfile.ZipFile(path, mode="w")` directly on the
destination, and `CellpyCell.save` deleted the destination before calling the
writer. An interrupted save therefore both left a file that still opened but was
missing members (`CorruptCellpyFile: missing zip member 'raw.parquet'`) and
destroyed the previously-good file. Found while building
[cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui) (issue
[#845](https://github.com/jepegit/cellpy/issues/845)).

**Decision.** All cellpy-file writers stage through
`cellpy/readers/cellpy_file/atomic.py::atomic_write`:

- The staged file lives in the **destination's own directory**
  (`<name>.tmp<pid>`), never `TMPDIR` — a cross-filesystem `os.replace` would
  degrade to a copy and lose atomicity.
- The caller creates the staged file, so writers that own file creation
  (`zipfile.ZipFile`, `pandas.HDFStore`) still work unchanged.
- An exception inside the block unlinks the staged file and leaves the
  destination untouched.
- An optional `verify` callback runs before the replace. v9 uses it to assert the
  staged archive holds every required member, reading only the zip central
  directory (no `testzip()` decompression of a large `raw.parquet`).
- **If `os.replace` itself fails** (typically a destination locked by another
  process on Windows), the staged file is **kept** and its path logged at
  critical level, so the newly written data is recoverable. Chosen over a
  spotless directory because losing a completed write is worse than one leftover
  file.

`CellpyCell.save` no longer deletes the destination first; it keeps the
`overwrite=False` refusal and still logs critical + returns on `PermissionError`
rather than raising.

**Consequence for the HDF5 (v8) writer.** Once the pre-delete was gone,
`pandas.HDFStore(path)` (default mode `"a"`) would have appended into an existing
file, so the v8 writer had to move to staging in the same change
(`HDFStore(staged, mode="w")`). Not scope creep — a correctness requirement.

**Alternatives considered.** Fixing only `v9.save` (rejected: the pre-delete in
`CellpyCell.save` still destroys the old file); app-side staging of whole project
folders (what cellpy-simple-gui does — it cannot protect an individual
`cell.save()`).

**Not covered.** Other writers that still write in place: `to_csv`, batch journal
JSON, exporters. Candidates for a follow-up issue.
