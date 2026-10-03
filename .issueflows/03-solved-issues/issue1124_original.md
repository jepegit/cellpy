# Issue #1124: Epic M: use FileRef size/mtime from the metadata source to skip stat-ing raw files on update()

Source: https://github.com/jepegit/cellpy/issues/1124

## Original issue text

## Context

#1107 (PR #1119) added `FileRef(size, mtime, checksum, …)` on `MetaRecord.files`, and `batch.from_source` already carries them into the journal pages as `raw_file_size` / `raw_file_mtime`. Nothing consumes them yet: `CellpyCell.update()` / `Batch.refresh()` still `stat` every raw file (slow on `scp://`/SFTP shares) to decide whether anything changed.

## Spec

1. When a cell was loaded via a source record whose raw `FileRef`s carry `size` and/or `mtime`, store them next to the back-link (`ExternalLink` or `Data` provenance — pick one, document it) so they survive save/load.
2. `update()` / `refresh()` / `poll()`: if the source's recorded `size`+`mtime` equal what cellpy already loaded, skip the remote `stat` and treat the file as unchanged. A changed value, or a missing one, falls back to today's `stat`-based path. `checksum` is informational only (no hashing of remote files).
3. Batch: `Batch.refresh()` may consult `raw_file_size` / `raw_file_mtime` the same way; `batch.from_source(...).update()` followed by a second `from_source` fetch can short-circuit per cell.
4. Never skip when the user forces a reload (`recalc=True`, `RAW_ONLY`, explicit `update(force=…)` if that exists).

## Acceptance

- A cell loaded from a `DictMetadataSource` record with `size`/`mtime` does not call the path `stat` on `update()` when the values match (monkeypatched `OtherPath.stat` asserts not called), and does when they differ.
- Records without `size`/`mtime` behave exactly as today.
- Round-trip: the recorded values survive `.cellpy` save/load.

## Related

#1107, #783 (Epic M), ife-bat/batbase#474 (`size`/`mtime` on `TestDataFile`), incremental-load protocol (#779 / #164).
