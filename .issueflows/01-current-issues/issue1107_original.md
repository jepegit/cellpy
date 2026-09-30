# Issue #1107: Epic M: consume file pointers from external metadata sources (skip filefinder)

Source: https://github.com/jepegit/cellpy/issues/1107

## Original issue text

## Context

Epic M read path is in place: `MetadataSource` Protocol + `MetaResolver` hook (#784, merged via #1106) and the BatBase adapter (cellpy/cellpy-connectors#2). BatBase is getting pointers to the actual data files on each experiment (ife-bat/batbase#474: `files: [{kind, uri, order, size, mtime, checksum, …}]` on the journal API).

Today cellpy still finds raw files and `.cellpy` archives with `filefinder` (glob over `rawdatadir` / `cellpydatadir` by cell name). When the metadata source already knows where the files are, that step is wasted — slow on network shares and brittle across machines.

## Spec

1. **Contract:** add `MetaRecord.files: tuple[FileRef, ...]` (`FileRef(kind, uri, order=0, size=None, mtime=None, checksum=None, loader=None)`). `validate_record` accepts it; `raw_file_names` / `source_uri` stay provenance (forbidden for sources). `ExternalLink` records that files were supplied.
2. **Cell path:** `cellpy.get(source="batbase", key=…)` (or `CellpyCell.from_source`) — fetch the record, open `files[kind=="cellpy"]` if present and fresh, else `files[kind=="raw"]` (ordered) with the loader hint, else fall back to today's filefinder. Uses `OtherPath` for remote URIs. Apply the metadata as `fetch_meta` does.
3. **Batch path:** `batch.from_source("batbase", tag=…, project=…)` builds the journal pages from the records (filename(s) from `files`, mass / area / nom_cap / label / cell_type / cycle_mode from the record); missing `files` ⇒ `filefinder` per cell as now. Provenance names the source per field (`Resolution.origin_of`).
4. **Change detection:** when `size`/`mtime` are present, `update()` / `batch.refresh()` may use them to skip stat-ing the raw file.
5. Adapter side (cellpy-connectors): map BatBase `files` → `FileRef`s (follow-up issue there once #474 ships).

Everything must keep working when a source returns no `files`.

## Acceptance

- A record with `files` loads a cell without touching `filefinder` (asserted with a monkeypatched finder).
- A record without `files` behaves exactly as today.
- `batch.from_source` produces pages equivalent to the current journal for a tagged set, offline against `DictMetadataSource`.

## Related

#784, #783 (Epic M), cellpy/cellpy-connectors#2, ife-bat/batbase#474, ife-bat/batbase#473. Pairs with M3 (push: cellpy registering the files it loaded back into BatBase).
