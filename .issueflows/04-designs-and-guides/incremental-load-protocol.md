# Incremental load protocol

**Issue:** [#779](https://github.com/jepegit/cellpy/issues/779)
**Status:** decided with the #779 plan.

## Context

Epic L needs an optional way for a loader to return rows since a marker.
Core `update_data` already trims overlap. The marker must not become a
cellpycore type.

## Decision

- Host `SupportsIncrementalLoad`, `LoadMarker`, and `IncrementalChunk` in
  cellpy `readers/instruments/contract.py`.
- `IncrementalChunk.new_raw` is a polars `DataFrame`, the same type as
  `LoaderResult.raw` and `update_data`'s `new_raw`.
- The protocol is methods-only, so `issubclass` works. It is not part of
  `InstrumentLoader`. Loaders that omit `load_since` stay valid.
- cellpycore is unchanged. Overlap trimming stays in `update_data`.

## Alternatives

- Put the protocol in cellpycore so `update_data` could take a marker.
  Rejected: the issue and the live-incremental design keep the contract
  between loaders and a future `CellpyCell.update()`.
- Use pandas for `new_raw` because some cellpy frames are still pandas.
  Rejected: the core merge primitive and the loader result are polars.

## Link

Design §3 in `cellpy-design-and-development/active/cellpy2-live-incremental-design.md`.
Loaders that implement `load_since` are #780. `CellpyCell.update()` is #164.
