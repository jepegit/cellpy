# External metadata sources (Epic M, read path)

Issue: #784 (M1; stage 4 of #783). Design origin:
`cellpy-design-and-development/active/cellpy2-metadata-source-integration.md`.
Adapter side: `cellpy-connectors` (#1 `BatBaseClient`, #2 adapter).

## Context

cellpy 2 reserved the seam — `MetaResolver` (`kwargs > journal/db > raw file >
config defaults`) with per-field `Resolution` provenance — but nothing outside
the journal fed it, and the resolver is not yet on the raw-load hot path
(`cellreader.from_raw` still fills the legacy meta boxes directly). A lab's
system of record (BatBase first) should contribute mass, area, nominal
capacity, project without cellpy depending on one lab's API.

## Decisions

| Topic | Decision |
| --- | --- |
| Package | `cellpy/readers/metadata_sources/` — `contract.py`, `registry.py`, `testing.py`; re-exported from the package |
| Contract | `MetadataSource` Protocol: `name: ClassVar[str]`, `fetch(MetaQuery) -> tuple[MetaRecord, ...]`. Structural, `runtime_checkable`; no base class. `SupportsMetadataPush.register(record) -> str` declared, unused (M3). |
| Shapes | `MetaQuery(key, kind="cell_name", project, extra)`; `MetaRecord(source_name, external_id, source_uri, cell={CellMeta field: value}, test={TestMeta field: value}, fetched_at, raw)`; `ExternalLink` = persisted back-link |
| Validation | `validate_record`: unknown field names, pre-filled provenance (`uuid`, `source_*`, …) and `None` values are errors — a typo in an adapter's field map fails its conformance test rather than losing a mass |
| Registry | `cellpy.metadata_sources` entry-point group; lazy discovery; entry may be a class (instantiated once, no args) or a zero-arg factory; broken plugins skipped with a warning; `register()` for tests/notebooks and pre-configured instances |
| Null object | `fetch_meta(source, query, strict=False)`: unknown/unreachable source or invalid record ⇒ `()` + warning. **`MetadataSourceAuthError` always propagates** — a refused token is the user's to fix, hiding it would look like "no data". `strict=True` raises everything. |
| Resolver | `MetaResolver.resolve(external=…)`: records join the **journal/db layer below the journal row** (kwargs > journal row > external sources (priority order) > raw file > defaults). `Resolution.origins[field]` names the contributor (`"batbase"`, `"journal"`); `origin_of()`, `fields_from_origin()`, `explain()` show it. Old provenance shape unchanged when no externals are given. |
| Cell surface | `CellpyCell.fetch_meta(source, key=None, *, kind, project, apply=True, strict=False, **extra)`; `key` defaults to `cell_name`. Applies the **first** record (warns if several) through `resolve_*_meta(external=record)` → `test_meta.apply_test_meta_to_legacy` so the engine's live legacy boxes are updated; `external_links[source] = ExternalLink(fields=applied)`. Returns all records. |
| Persistence | `Data.external_links: dict[str, ExternalLink]`; v9 `meta.json` key `"external_links"` (omitted when empty); copied by `CellpyCell.from_cell` clone; `apply_meta_document` restores. `raw` payloads are never persisted. |
| Not done here | `CellMeta.uuid` (lives in cellpy-core → core-first issue), `batch.from_source`, multi-source priority config, cache/TTL, push, BattINFO vocabulary map |

## Precedence rationale

Journal row above external source: a value the user corrected in their
journal is a deliberate local override; the lab database is authoritative
*relative to the cycler file*, not relative to the user. Both beat the raw
file. Revisit when multi-source config lands (design §6).

## Alternatives rejected

- A fifth `Layer.EXTERNAL` between RAW_FILE and JOURNAL — the design says the
  source is a *contributor to the journal/db layer*; a separate layer would
  change `Layer` ordering that existing provenance tests and docs rely on.
  Contributors + `origins` keep the enum stable and still answer "who won".
- Swallowing auth errors like other failures — violates "auth failure
  surfaces a clear error, not a silent empty" (design §3.6).
- `fetch(key) -> MetaRecord | None` (epic wording) — the design's tuple form
  matches the loader contract and lets a tag match several tests.
- Applying all returned records — ambiguous merge order; first-record +
  warning keeps it explicit, adapters narrow the query instead.

## Conformance kit

`metadata_sources.testing.check_metadata_source(source, known=, unknown=)`:
capabilities, unknown key ⇒ `()` (never raises), records validate and carry
`source_name == source.name`, determinism. `DictMetadataSource` is the
in-process fake for adapter tests.
