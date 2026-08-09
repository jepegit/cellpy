# Issue #845 — plan: atomic `.cellpy` / `.h5` writes

Source: https://github.com/jepegit/cellpy/issues/845
Milestone: v.2.1.2 · Labels: bug, v2

## Goal

A failed or interrupted `CellpyCell.save()` must never leave a half-written
cellpy-file, and must never destroy the previously-good file. Writers stage into
a same-directory temp file and `os.replace()` it into place only after the
archive is complete.

## Constraints

- **Two destructive spots, not one.** Besides the non-atomic zip write in
  `v9.save`, `CellpyCell.save` already `os.remove(...)`s the destination
  *before* calling the writer
  ([`cellreader.py:1663-1676`](../../cellpy/readers/cellreader.py)). Fixing only
  the writer still loses the old file on failure — the pre-delete must go.
- **Dropping the pre-delete forces the v8/HDF5 path in too.** `write.save` opens
  `pandas.HDFStore(path)` in default mode `"a"`; without the pre-delete it would
  *append into* an existing file instead of replacing it. So v8 must become
  atomic in the same change — not scope creep, a correctness consequence.
- Keep `overwrite=False` semantics: existing file → refuse and return (no write).
- Keep the legacy locked-file UX: a `PermissionError` on a locked destination
  logs critical and returns rather than raising out of `save()`.
- Remote save is already rejected upstream (`outfile_all.is_external` →
  `ValueError`), so writers only ever see local paths. `OtherPath` implements
  `__fspath__`, so `Path(outfile_all)` is safe.
- Same filesystem required for atomicity — temp file goes in the **destination's
  own directory**, never `TMPDIR`.
- Cross-platform: `os.replace` is atomic on POSIX and overwrites on Windows, but
  raises `PermissionError` if the destination is open in another process.

### Prior art

- `.issueflows/00-tools/` (README index) — nothing about file IO; no reuse.
- Grep `os.replace` / `atomic` / `.tmp` across `cellpy/` — **no existing atomic
  write helper**; this is the first one.
- `cellpy/readers/cellpy_file/v9.py` `save` — the writer to wrap.
- `cellpy/readers/cellpy_file/write.py` `save` — v8/HDF5 writer, same pattern.
- `cellpy/internals/otherpath.py` `OtherPath` — provides `__fspath__`,
  `with_name`, `is_file`; no staging/replace logic to mirror.
- graphify: `graphify-out/` present but not consulted for this narrow IO fix.

## Approach

1. **New helper** `cellpy/readers/cellpy_file/atomic.py` — one context manager:

   ```python
   @contextlib.contextmanager
   def atomic_write(path, *, verify=None):
       """Yield a same-dir temp path; os.replace() it onto `path` on success."""
   ```

   - temp name `f"{path.name}.tmp{os.getpid()}"` in `path.parent`, removed first
     if a stale one exists (so the writer, not the helper, creates the file —
     `HDFStore` and `ZipFile` both want to create it themselves);
   - `path.parent.mkdir(parents=True, exist_ok=True)` before yielding;
   - on exception inside the block: unlink the temp, re-raise (destination
     untouched);
   - on success: run `verify(tmp)` if given, then `os.replace(tmp, path)`;
   - if `os.replace` itself fails (locked destination on Windows): **keep** the
     temp file, log critical with its path so the data is recoverable, re-raise.

2. **`v9.save`** — wrap the `zipfile.ZipFile(...)` block in `atomic_write`, and
   pass a `verify` that reopens the temp zip and asserts the required members
   (`meta.json`, `raw/steps/summary.parquet`, plus `fid.parquet` when written)
   are in `namelist()`. Cheap (central-directory read only, no `testzip()`
   decompression of the whole raw table).

3. **`write.save` (v8/HDF5)** — same wrap; `HDFStore(tmp, mode="w", …)`. No
   member verification (would mean reopening the store).

4. **`CellpyCell.save`** — the `outfile_all.is_file()` branch keeps the
   `overwrite=False` refusal but **stops deleting** the file when
   `overwrite=True`; the writers now replace it. Wrap the two writer calls so a
   `PermissionError` still logs critical + returns instead of propagating.

## Files to touch

| Path | Change |
|---|---|
| `cellpy/readers/cellpy_file/atomic.py` | **new** — `atomic_write` context manager (~40 lines incl. docstring) |
| `cellpy/readers/cellpy_file/v9.py` | `save` writes through `atomic_write` + member verification |
| `cellpy/readers/cellpy_file/write.py` | `save` writes through `atomic_write`, `HDFStore(tmp, mode="w")` |
| `cellpy/readers/cellreader.py` | drop pre-write `os.remove`; keep overwrite refusal; `PermissionError` guard around writer calls |
| `tests/test_cellpy_file_v9.py` | new interrupt/atomicity tests (`@pytest.mark.essential`) |
| `HISTORY.md` | changelog entry at `/iflow-close` |

## Test strategy

Command: `conda activate cellpy_dev_313 && pytest` (project rule); merge gate is
`pytest -m essential`. Targeted runs:
`pytest tests/test_cellpy_file_v9.py tests/test_cellpy_file_roundtrip.py -m ""`.

New tests (fault injection by monkeypatching
`v9._frame_to_parquet_bytes` to raise on the summary frame, i.e. after
`meta.json` + `raw.parquet` are already inside the temp zip):

1. **Old file survives a failed re-save** — save a good `.cellpy`, snapshot it,
   make the second `save(..., overwrite=True)` blow up, then assert the file
   still loads with identical frames.
2. **No debris** — after that failure, no `*.tmp*` left in the directory.
3. **Failed first save leaves no file** — a fresh destination that fails
   mid-write must not exist afterwards (no more "opens but missing
   `raw.parquet`" `CorruptCellpyFile`).
4. **Member verification** — an incomplete-but-successful zip (patch the writer
   to skip `summary.parquet`) is rejected before `os.replace`, leaving the old
   file intact.
5. **HDF5 path** — same "old file survives" check for
   `cellpy_file_format="hdf5"`, skipped when HDF5 support is unavailable.

Marker: `essential` for 1–3 (data-loss guard, cheap); 4–5 plain.

## Open questions

1. **Keep or discard the staged temp file when `os.replace` fails?** Plan keeps
   it + logs critical (recoverable data, small debris risk on a locked file).
   Alternative: always unlink for a spotless directory.
2. **v8/HDF5 in this PR?** Plan says yes — required once the pre-delete is
   dropped. Splitting it out would mean keeping a v8-only pre-delete branch.
3. **Other writers out of scope** (`to_csv`, batch journal JSON, exporters) —
   confirm they stay for a follow-up issue.
