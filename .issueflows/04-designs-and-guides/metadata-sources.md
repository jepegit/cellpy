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
| Not done here | `CellMeta.uuid` (lives in cellpy-core → core-first issue), multi-source priority config, cache/TTL, push, BattINFO vocabulary map |

## File pointers (M4, #1107)

| Topic | Decision |
| --- | --- |
| Shape | `FileRef(kind, uri, order=0, size, mtime, checksum, loader, location)`; `MetaRecord.files: tuple[FileRef, ...] = ()` (dicts coerced in `__post_init__`); helpers `raw_files()` (kind `raw`, by `order`) / `cellpy_file()` (first `cellpy`). `validate_record` rejects non-`FileRef`s, unknown kinds (`FILE_KINDS`), empty or duplicate URIs. Provenance rule unchanged: `raw_file_names` / `source_uri` stay forbidden in `cell`/`test`; files travel on `.files`. |
| Cell path | `cellpy.get(source=, key=, kind=, project=, source_extra=, strict=)` (+ `CellpyCell.from_source` alias). `_resolve_from_source` fills `filename` / `cellpy_file` / `instrument` **only where the caller gave nothing**, then the existing raw-vs-cellpy branch (`check_file_ids`) runs. No pointers ⇒ `filefinder.search_for_files(record cell_name)`. Record applied via `_apply_meta_record` *before* `_update_meta`, so kwargs > source > raw file. `.cellpy` branch calls `refresh_after()` only when fields were applied and a summary exists. |
| Strict default | `strict = filename is None and cellpy_file is None` — when the source is the only way to find the data an unreachable/unknown source raises; with a filename it is enrichment and degrades to a warning. No record: `NoDataFound` without a filename, warning with one. Auth errors propagate always. |
| Back-link | `ExternalLink.files: tuple[str, ...]` = URIs cellpy opened because the record pointed at them; `to_dict` omits the key when empty so pre-#1107 `meta.json` documents are byte-identical. |
| Batch path | `Batch.from_source(source, key, *, kind="tag", project, name, policy, file_search=True, file_search_kwargs, strict=True, **extra)`; module `batch.from_source` + `utils.batch` shim. `batch/source.py::pages_from_records` builds one row per record (`filename`/`label` = `test.cell_name` → `external_id` → `cell_NNN`, de-duplicated with `_2` suffixes; mass/area/loading/nom_cap/nom_cap_specifics/cycle_mode; `instrument` = first raw `loader`; `raw_file_names` / `cellpy_file_name`; `raw_file_size` / `raw_file_mtime` when known; `external_id`, `source_uri`). Rows without pointers ⇒ `_dbengine.find_files` (the `journal_from_db` call) on just those rows; `file_search=False` leaves `None` (#1017 rule). `project` defaults to the source name (no `project` field on `CellMeta`); `name` to `<source>_<kind>_<key>` slug. |
| Batch provenance | Links kept in `journal.session["external_links"]` (`{label: ExternalLink.to_dict()}`, survives `write_journal`); `Batch.update()` → `_stamp_external_links()` copies them onto loaded cells. Values are **not** re-applied (journal precedence intact); per-field `Resolution.origin_of` stays a cell-path feature. |
| Deferred | cellpy-connectors adapter mapping BatBase `files[]` → `FileRef` (follow-up issue there). |

## Stat skip on `update()` (#1124)

| Topic | Decision |
| --- | --- |
| Where the hints live | `ExternalLink.file_refs: tuple[FileRef, ...]` — the record's **raw** refs that carry `size` and/or `mtime`, restricted to the URIs cellpy opened (`MetaRecord.link(files=…)`). Chosen over `Data._provenance` because the link is already the per-source persisted object that `_stamp_external_links`, `apply_meta_document` and `from_cell` copy. `to_dict` writes `"file_refs"` only when non-empty, so pre-#1124 `meta.json` stays byte-identical. `ExternalLink.file_ref_for(uri)` looks one up. |
| Check | `CellpyCell._raw_sources_changed` asks `_source_file_hint(fid)` (URI equal to `fid.full_name`, or `OtherPath(uri).full_path` equal; else a *single* ref with the same basename) before building `ds.FileID(...)`. `_source_hint_matches_loaded(ref, fid)`: every value the ref carries must match — `size` as `int ==`, `mtime` as epoch (number, or ISO-8601 via `fromisoformat`; naive ⇒ UTC) within `SOURCE_MTIME_TOLERANCE` (1 s) of `fid.last_modified`. A ref with neither value, an unparsable mtime or a fid without stats never matches ⇒ stat as before. `force=True` bypasses the whole check (unchanged). `checksum` is never used. |
| Re-fetch | `c.fetch_meta(source, key, kind=…)` on a loaded cell rebuilds the link; with no opened-URI list the refs are filtered to those pointing at `raw_data_files` (`_ref_points_at`), so the source's fresher `size`/`mtime` become the new hints. Batch: `pages_from_records` → session links → `_stamp_external_links` → `refresh()` / `poll()` benefit without facade changes; a new `batch.from_source(...)` is the batch-side re-fetch. |
| Not done | `check_file_ids` (raw-vs-cellpy stat on the first `cellpy.get` / batch load) could consult the journal `raw_file_size` / `raw_file_mtime` the same way — separate follow-up. |

Semantics: the source is the system of record for the file. While its
recorded stats equal what cellpy loaded, cellpy trusts it and does not touch
the share; a tester that keeps writing is noticed once the source re-scans
(and cellpy re-fetches) or when `force=True`.

Alternatives rejected: a new `Layer` for "source files" (files are not metadata; they select *what to load*); re-running `_apply_meta_record` per batch cell (would put the source above journal overrides); always writing `files` into `ExternalLink.to_dict()` (breaks byte-for-byte stability of old documents for no gain).

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
