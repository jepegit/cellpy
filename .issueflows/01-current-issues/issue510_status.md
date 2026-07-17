# Issue #510 — status

- [ ] Done

## What's done

- Plan confirmed (2026-07-17): v9 zip-of-parquet + `.cellpy`, default write v9, native cols; three milestones A→B→C.
- **Milestone A (V2-13)** — implemented:
  - `CELLPY_FILE_VERSION = 9`, `HDF5_FILE_VERSION = 8`
  - `cellpy/readers/cellpy_file/v9.py` — zip-of-parquet writer/reader + `meta.json` (full `TestMetaCollection`, units/limits, schema stamps)
  - On-disk native headers via `translate.to_native` / `to_legacy` I/O adapter
  - `load` sniffs zip magic vs HDF5; `.h5` suffix still writes v8
  - Default `CellpyCell.save` → `.cellpy` / v9
  - Essential tests in `tests/test_cellpy_file_v9.py` (v8→v9→read, extras persist, `.h5` escape)
  - `uv run pytest -m essential` green

## Remaining work

- **B (V2-14):** cellpy-owned meta archive helpers (`save_meta_archive` / `load_meta_archive`) + merged two-test campaign round-trip fixture
- **C (V2-15):** exact `cellpycore==` pin + migration guide + release procedure
