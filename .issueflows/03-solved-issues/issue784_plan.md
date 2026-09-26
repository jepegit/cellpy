# Plan: #784 MetadataSource Protocol + resolver hook (M1, read path)

Non-yolo (public Protocol + resolver precedence). Executed under the
maintainer's "start" after M0 shipped; the PR is the review point and is
**not** auto-merged.

## Scope (from epic783 M1 spec)

`MetadataSource` Protocol, `cellpy.metadata_sources` entry-point registry,
`MetaResolver` journal/db-layer hook with provenance naming the source,
null-object on failure, back-link (`external_id` / `source_uri`). No push.

## Approach

1. `cellpy/readers/metadata_sources/` — `contract.py` (Protocols, `MetaQuery`,
   `MetaRecord`, `ExternalLink`, errors, `validate_record`), `registry.py`
   (entry points, `register`, `get_source`, `fetch_meta`), `testing.py`
   (`check_metadata_source`, `DictMetadataSource`).
2. `meta_resolver.py`: `external=` on `resolve*`; `Resolution.origins`.
3. `CellpyCell.fetch_meta` + `external_links`; `Data.external_links`;
   v9 `meta.json` `"external_links"` round-trip; clone copy.
4. Tests `tests/test_metadata_sources.py` (essential markers on the
   precedence / null-object / cell-surface checks).
5. Docs: HISTORY, `docs/api/readers.md`, `docs/agents/index.md`, `AGENTS.md`
   agents section, design note `metadata-sources.md`, test registry.

## Deviations from the issue text

- `CellMeta.uuid` is a cellpy-core model field → filed as a core-first issue
  instead of a cellpy change (see status). Back-link lands on the cellpy
  side (`ExternalLink`) and is persisted.
- `batch.from_source`, vocabulary normalisation, cache/TTL: deferred (design
  §4 items 4–5; M3+).
