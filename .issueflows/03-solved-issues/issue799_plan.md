# Issue #799 — plan

## Goal

Add a cheap `read_meta(path)` that returns cellpy-file metadata **without** loading raw/steps/summary frames, so project browsers can show mass/area (and similar) quickly.

## Approach

- **v9 `.cellpy` (zip):** read only the `meta.json` zip member (same document as full load).
- **Standalone `*.meta.json`:** delegate to existing `load_meta_archive`.
- **Legacy HDF5 `.cellpy`/`.h5`:** read `/info` (and test-dependent if present) into a browser-friendly dict with a top-level `cell` map of scalar fields — no frames.
- **Out of scope:** `#cycles` (not in meta; needs summary peek) — document in docstring.
- Export as `cellpy.readers.cellpy_file.read_meta` and top-level `cellpy.read_meta`.

## Files to touch

- `cellpy/readers/cellpy_file/v9.py` — `read_meta` for zip
- `cellpy/readers/cellpy_file/meta_archive.py` — dispatcher + HDF5 helper (or thin `read_meta` module)
- `cellpy/readers/cellpy_file/__init__.py` — export
- `cellpy/__init__.py` — top-level export
- `tests/test_read_meta.py` — essential tests
- `docs/getting_started/agents.md` — one recipe line
- `HISTORY.md` — Unreleased bullet (at close)

## Test strategy

- Save v8 fixture → v9 `.cellpy` in `tmp_path`; `read_meta` equals zip `meta.json`; monkeypatch parquet reader to fail if called.
- HDF5 fixture: `read_meta` returns `cell.mass` without requiring full `get`.
- Missing file / non-cellpy → clear errors.
