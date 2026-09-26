# Readers

The data containers behind the cell object, and how cellpy resolves metadata.
The cell object itself (`CellpyCell`) has [its own page](cell.md).

::: cellpy.readers.data_structures

## Metadata resolution

::: cellpy.readers.meta_resolver

::: cellpy.readers.provenance

::: cellpy.readers.journal_layer

## External metadata sources

Pluggable lab databases / APIs as a journal-level metadata layer (#784).
Adapters satisfy the `MetadataSource` Protocol and declare a
`cellpy.metadata_sources` entry point; `CellpyCell.fetch_meta` pulls a record
onto a cell.

::: cellpy.readers.metadata_sources.contract

::: cellpy.readers.metadata_sources.registry

::: cellpy.readers.metadata_sources.testing
