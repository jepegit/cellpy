# Issue #784 status (M1 — read path)

- [x] Done

## What's done

- `cellpy/readers/metadata_sources/` package: `MetadataSource` /
  `SupportsMetadataPush` Protocols, `MetaQuery`, `MetaRecord`, `ExternalLink`,
  `validate_record`, error hierarchy (`MetadataSourceError`,
  `MetadataSourceAuthError`, `UnknownMetadataSource`); entry-point registry
  (`cellpy.metadata_sources`, `register`, `names`, `get_source`); null-object
  `fetch_meta`; conformance kit `testing.check_metadata_source` +
  `DictMetadataSource`.
- `MetaResolver.resolve(external=…)` (and `resolve_cell_meta` /
  `resolve_test_meta` / `resolve_from_loader_result`): external records join
  the journal/db layer below the journal row; `Resolution.origins`,
  `origin_of`, `fields_from_origin`, `explain()` name the source.
- `CellpyCell.fetch_meta(...)` + `external_links`; `Data.external_links`;
  v9 `meta.json` `"external_links"` round-trip; clone copy in `from_cell`.
- Tests: `tests/test_metadata_sources.py` (36; 6 essential). Full suite
  1757 passed / 187 skipped; `-m essential` 959 passed.
- Docs: HISTORY, `docs/api/readers.md`, `docs/agents/index.md`, `AGENTS.md`
  agents section, `metadata-sources.md` design note, test registry.
- `CellMeta.uuid` filed core-first as cellpy/cellpy-core#151 (model lives in
  cellpy-core; needs release + re-pin).

## Remaining work

None on the cellpy side for the read path. Review the PR (non-yolo). Follow-ups:
cellpy/cellpy-connectors#2 (BatBase adapter, M2), cellpy/cellpy-core#151,
M3 push (2.3), `batch.from_source` / multi-source config (design §4 item 5).
