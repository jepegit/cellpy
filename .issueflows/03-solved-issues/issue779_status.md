# Issue #779 status

- [x] Done

## What's done

- `LoadMarker`, `IncrementalChunk`, and `SupportsIncrementalLoad` in
  `cellpy/readers/instruments/contract.py`.
- Essential tests in `tests/test_incremental_protocol.py` (5 passed) plus
  the existing loader-contract essential tests (21 passed).
- Registry rows and `incremental-load-protocol.md`.

## Remaining work

- None in this issue. `load_since` on real loaders is #780.
  `CellpyCell.update()` is #164.
