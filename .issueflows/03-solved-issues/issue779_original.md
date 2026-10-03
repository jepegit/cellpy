# Issue #779: L1: SupportsIncrementalLoad protocol + LoadMarker/IncrementalChunk (cellpy-hosted)

Source: https://github.com/jepegit/cellpy/issues/779

## Original issue text

Epic L (live/incremental) of **cellpy 2.2 (Stage 5)**. Design: [live-incremental](https://github.com/cellpy/architecture-plan/blob/main/cellpy2-live-incremental-design.md) §3.

Add the optional loader capability **in cellpy** (not cellpycore — the contract is only between loaders and `CellpyCell.update()`; core's `update_data` never sees it):

- `@runtime_checkable class SupportsIncrementalLoad(Protocol): load_since(source, marker) -> IncrementalChunk`
- `LoadMarker` (last `source_datapoint_num` / byte_offset / row_count) and `IncrementalChunk` (new_raw, marker, complete)

Marker semantics match core `update_data` (new_raw may overlap the tail; overlap trimmed on `source_datapoint_num`). Loaders that can't do cheap partial reads simply don't implement it → `update()` falls back to full reload.
