# Issue #447 — status

- [x] Done

## What's done

- **Commit 1:** Stateless helpers moved to `cellpy_file/{keys,meta,fids,dtype}.py` with one-line `CellpyCell` delegators.
- **Commit 2:** `LoadSelector` / `LoadLimits` in `cellpy_file/selectors.py`; extractors thread explicit limits; `load()` assigns `self.limit_*` from returned limits.
- Tests: `uv run pytest -m essential` (82 passed) + `tests/test_cellpy_file_roundtrip.py` (10 passed).
- Acceptance grep: `self.limit_*` in `cellreader.py` only in `__init__`, repr, and `load()`.
- PR #482 opened against `master`.

## Remaining work

- None.
