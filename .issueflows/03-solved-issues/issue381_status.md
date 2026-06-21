# Status for issue #381: Refactor module naming to prevent name clash with cellpy core

- [x] Done

## Summary

Renamed the two modules accidentally named `core` so they no longer clash with the new
`cellpy-core` package:

- `cellpy/readers/core.py` -> `cellpy/readers/data_structures.py`
- `cellpy/internals/core.py` -> `cellpy/internals/connections.py`

The deliberate cellpy-core seam in `cellpy/readers/cellreader.py` (`self.core`,
`OldCellpyCellCore`, `make_core_summary`) was intentionally left unchanged.

## What was done

- Updated all imports across `cellpy/` and `tests/` (45 files). Aliased imports were preserved
  so call sites stayed unchanged (e.g. `from cellpy.readers import data_structures as core`,
  `import cellpy.internals.connections as internals`).
- Updated docs: `docs/source/cellpy.readers.rst`, `docs/source/cellpy.internals.rst`.
- Updated notebook `examples/06_loading_different_formats.ipynb` (alias import).
- Fixed stale module-path references in comments/docstrings (`__init__.py`, `exporters/bdf.py`,
  `cellreader.py`, test docstrings) and the `.issueflows/04-designs-and-guides/bdf-export.md` link.
- Verified zero remaining references to the old module paths in `cellpy/` and `tests/`.

## Verification

- Smoke import of renamed modules/classes succeeds.
- Pickle/serialization back-compat confirmed safe: cellpy saves to HDF5 and rebuilds
  `Data`/`FileID` from DataFrames/metadata (no stored class module paths), so existing `.h5`
  files still load. No compatibility shim added (clean break).
- Test suite run by the user (conda `cellpy_dev_313`): OK.

## Outcome

- Merged via PR #382 (commit `b757f908`) into `master`.
