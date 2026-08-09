# Issue #845 — status

Branch: `845-atomic-cellpy-writes`

- [x] Done

## What's done

- **`cellpy/readers/cellpy_file/atomic.py`** (new) — `atomic_write(path,
  verify=...)` context manager: stages `<name>.tmp<pid>` in the destination's own
  directory (same filesystem, so `os.replace` stays atomic), unlinks the staged
  file if the write raises, and runs an optional `verify` before replacing.
  Per the confirmed decision, a failing `os.replace` (locked destination on
  Windows) **keeps** the staged file and logs critical with its path.
- **`v9.save`** — writes the zip through `atomic_write` and verifies the staged
  archive holds every required member (`meta.json`, raw/steps/summary parquet,
  plus `fid.parquet` when written) from the central directory only, so an
  incomplete-but-openable zip is rejected before it can replace a good file.
- **`write.save` (v8/HDF5)** — same staging, `HDFStore(staged, mode="w")`.
- **`CellpyCell.save`** — dropped the pre-write `os.remove` that destroyed the
  old file before the writer even started; kept the `overwrite=False` refusal and
  the locked-file "log critical + return" UX (now via `PermissionError` around
  the writer calls). Docstring documents the atomicity guarantee.
- **Docs** — `docs/getting_started/agents.md` notes that `save` is atomic, so
  app builders (this came from cellpy-simple-gui) don't need per-file staging.
- **Tests** (`tests/test_cellpy_file_v9.py`, 4 new): failed re-save keeps the old
  file bit-for-bit + reloads; failed first save leaves no file; incomplete
  archive rejected before replace; HDF5 re-save keeps the old file. First three
  marked `essential`. Verified they **fail on the pre-fix code** and pass after.

## Test results

- `uv run pytest tests/test_cellpy_file_v9.py -m ""` → 7 passed.
- `uv run pytest -m essential` (merge gate) → 679 passed, 1 skipped.
- Full default suite → 1525 passed, 3 failed: `test_search_for_files`,
  `test_search_for_files_with_dirs`, `test_search_for_files_recursive` —
  **pre-existing**, reproduced on the stashed baseline. Same for the three
  `slowtest` `cellpy new` cookiecutter failures seen with `-m ""`.
- Note: the conda env `cellpy_dev_313` has a broken `pyarrow` DLL
  (`ImportError: DLL load failed while importing lib`), so tests were run through
  `uv run` / `.venv` instead. Unrelated to this issue, but worth repairing.
- `flake8`/`black` findings on the touched files are the repo's pre-existing
  E501-at-79 and F401 noise; the new module is black-clean.

## Remaining work

- `HISTORY.md` changelog bullet — owned by `/iflow-close`.
- Out of scope (candidates for a follow-up issue): other writers that still
  write in place (`to_csv`, batch journal JSON, exporters).
