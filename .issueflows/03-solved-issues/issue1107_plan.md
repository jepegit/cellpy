# Issue #1107 — plan

Epic M (stage 4 of #783), M4: consume file pointers from external metadata
sources so a source that knows where the files are lets cellpy skip
`filefinder`. Server side shipped (ife-bat/batbase#478: `files[]` on the
journal API); cellpy side is this issue; adapter mapping is a follow-up in
cellpy-connectors.

## Goal

`MetaRecord` can carry `files`. `cellpy.get(source=…, key=…)` and
`batch.from_source(…)` open the pointed-to `.cellpy` / raw files directly,
falling back to today's `filefinder` only when a record has no `files`.
Everything without `files` behaves exactly as today.

## Constraints

- Project rules: `uv run pytest`; `@pytest.mark.essential` on merge-blocking
  tests; forward-slash paths in stored strings; docs on `master`; public
  `cellpy.get` surface change ⇒ update `docs/agents/index.md` + root
  `AGENTS.md` "Using cellpy (for agents)" in the same PR (this-project.md).
- Design doc [metadata-sources.md](../04-designs-and-guides/metadata-sources.md):
  `raw_file_names` / `source_uri` stay **provenance** (forbidden in
  `record.cell`/`record.test`); null-object `fetch_meta` semantics; auth errors
  never swallowed; first-record + warning when several match; `Layer` enum
  unchanged.
- `MetaRecord.files` is **optional**: absent ⇒ identical behaviour to 2.2.
- No writes to the source (M3 is push). No cache/TTL. No multi-source priority.
- Back-compat of `meta.json` v9: only *add* an optional key inside the existing
  `external_links` entries; old files still load.
- Remote URIs go through `OtherPath` like every other filename in `get`.

### Prior art

- `cellpy.get(filename=, cellpy_file=)` already decides raw-vs-cellpy
  (`check_file_ids` similarity) and auto-picks by suffix — **reuse**: the
  source path only fills `filename` / `cellpy_file` / `instrument` and lets the
  existing branch run.
- `CellpyCell.fetch_meta` / `_apply_meta_record`
  (`src/cellpy/readers/cellreader.py` ~2148–2240) — apply a record, stamp
  `external_links`. **Reuse** for the cell path; extend `ExternalLink`.
- `metadata_sources.registry.fetch_meta` (null object, validation,
  `fetched_at`) — **reuse**, add `strict` passthrough.
- Batch v3: pages already carry `raw_file_names` / `cellpy_file_name`;
  `policy.resolve_specs` → `CellSpec.raw_files/cellpy_file`;
  `runner._get_kwargs` honours `LoadPolicy.source`. **Reuse**: `from_source`
  only has to build pages with those columns filled.
- `_dbengine.find_files(info_dict, skip_file_search=…)` — the per-cell
  filefinder call used by `journal_from_db`; **reuse** for rows without
  `files` (#1017 padding rule already handles partially-filled columns).
- `Batch.from_cells` / `journal_from_frame` — pattern for building pages
  in-memory without a journal file. **Mirror**.
- `DictMetadataSource` + `check_metadata_source` (testing.py) — offline fake
  for tests; extend the conformance check to validate `files`.
- Toolbox (`.issueflows/00-tools/`): nothing applicable. Graph: `graphify-out/`
  absent in this worktree; grep only.

## Approach

### 1. Contract (`metadata_sources/contract.py`)

```python
@dataclass(frozen=True)
class FileRef:
    kind: str            # "raw" | "cellpy" | "processed" | "other"
    uri: str             # path or URL; OtherPath-able
    order: int = 0
    size: int | None = None
    mtime: str | None = None      # ISO-8601
    checksum: str | None = None
    loader: str | None = None     # cellpy instrument name hint ("arbin_res")
    location: str | None = None   # free text (BatBase `location`)
```

- `MetaRecord.files: tuple[FileRef, ...] = ()` (post_init coerces
  list/dicts → `FileRef`; given order kept). Helpers `raw_files()`
  (kind=="raw", sorted by `order`) and `cellpy_file()` (first kind=="cellpy").
- `validate_record`: every `files` item is a `FileRef`, `kind` in
  `FILE_KINDS`, `uri` non-empty; duplicates of `uri` are an error.
- `ExternalLink.files: tuple[str, ...] = ()` — URIs the source supplied at
  apply time; `to_dict`/`from_dict` round-trip (key omitted when empty so old
  documents are byte-identical).

### 2. Cell path — `cellpy.get(source=…)`

New keyword-only args on `get`: `source: str | MetadataSource | None`,
`key: str | None`, `kind: str = "cell_name"`, `project: str | None`,
`source_extra: Mapping | None`, `strict: bool | None = None`.

Flow when `source` is given (before the existing "filename is None" branch):

1. `records = fetch_meta(source, MetaQuery(key, kind, project, extra), strict=…)`.
   `strict` default: **True when neither `filename` nor `cellpy_file` was
   given** (the source is the only way to find the data, so an unreachable
   source must surface), else False (enrichment only). Auth errors propagate
   regardless (existing rule).
2. No record: with a filename ⇒ warn and continue as today; without ⇒ raise
   `NoDataFound(f"{source!r} has no record for {query.describe()}")`.
3. Several records ⇒ apply first + warning (existing rule).
4. If `filename`/`cellpy_file` not given: `cellpy_file = record.cellpy_file().uri`
   if any, `filename = [f.uri for f in record.raw_files()]` if any,
   `instrument = instrument or record.raw_files()[0].loader`. Both present ⇒
   the existing `check_file_ids` freshness branch decides. Neither ⇒
   `filefinder.search_for_files(cell_name)` where `cell_name =
   record.test.get("cell_name") or (key if kind == "cell_name")`; nothing ⇒
   `NoDataFound`.
5. Load as today (`load` or `from_raw`), then `cellpy_instance._apply_meta_record(record)`
   **before** `_update_meta(mass=…)` so explicit kwargs keep winning
   (precedence: kwargs > source > raw file). `ExternalLink.files` = URIs used.
6. `CellpyCell.from_source(source, key, **kw)` classmethod = thin alias to
   `get(source=…)` for discoverability (issue wording).

### 3. Batch path — `batch.from_source(...)`

`cellpy.batch.from_source(source, key=None, *, kind="tag", project=None,
name=None, policy=None, file_search=True, strict=True, **extra) -> Batch`
(+ `Batch.from_source` classmethod; `cellpy.utils.batch.from_source` shim).

- `records = fetch_meta(...)`; empty ⇒ raise `NoDataFound`.
- One page row per record: `filename`/`label` = `test.cell_name` (fallback
  `external_id`), `mass`, `area`, `loading`, `nom_cap`, `nom_cap_specifics`
  from `record.cell`; `cycle_mode` from `record.test`; `instrument` = raw
  loader hint; `raw_file_names` = raw URIs (ordered) or `None`;
  `cellpy_file_name` = cellpy URI or `None`; `group`/`sub_group`/`selected`
  defaults as in `from_cells`; `external_id`, `source_uri` as extra columns
  (provenance, informational). `name` defaults to `f"{source}_{kind}_{key}"`
  slug; `project` from arg or the first record's `cell.project`.
- Rows with no `files` and `file_search=True` ⇒ `_dbengine.find_files` on
  just those rows (same call `journal_from_db` makes). `file_search=False`
  leaves them `None` (runner marks FAILED as today for #1017).
- Provenance: `journal.session["external_links"] = {label: link.to_dict()}`;
  after `update()` the facade stamps `cell.data.external_links[source]` on each
  loaded cell (fields = the page columns that came from the record). Per-field
  `Resolution` provenance stays a cell-path feature (documented).
- Pages are built with `journal_from_frame`, so all existing
  `save_cellpy`/journal-persist behaviour applies unchanged.

### 4. Change detection (spec item 4)

**Defer** to a follow-up issue (see Open questions). `size`/`mtime` are
carried on `FileRef` and stored in pages (`raw_file_size`, `raw_file_mtime`
columns when present) so the follow-up is data-complete, but `update()` /
`refresh()` are not touched here.

### 5. Adapter (cellpy-connectors)

Out of this repo. File follow-up "map BatBase `files[]` → `FileRef`" on
cellpy/cellpy-connectors after merge (URIs from `uri`, `kind`, `order`, `size`,
`mtime`, `checksum`, `instrument_loader` → `loader`, `location`).

## Files to touch

| Path | Change |
| --- | --- |
| `src/cellpy/readers/metadata_sources/contract.py` | `FileRef`, `FILE_KINDS`, `MetaRecord.files` + helpers, `validate_record` file checks, `ExternalLink.files` |
| `src/cellpy/readers/metadata_sources/__init__.py` | export `FileRef` |
| `src/cellpy/readers/metadata_sources/testing.py` | `check_metadata_source`: validate `files` on returned records |
| `src/cellpy/readers/cellreader.py` | `get(source=, key=, kind=, project=, source_extra=, strict=)`; `_files_from_record` helper; `CellpyCell.from_source`; `_apply_meta_record(record, files=…)` stamps `ExternalLink.files` |
| `src/cellpy/readers/cellpy_file/meta_archive.py` | none expected (`to_dict`/`from_dict` carry the new key) — verify round-trip test |
| `src/cellpy/batch/facade.py` | `Batch.from_source`, module `from_source`, post-`update()` link stamping |
| `src/cellpy/batch/journal.py` or new `src/cellpy/batch/source.py` | `pages_from_records(records, …)` builder + optional `find_files` fill |
| `src/cellpy/batch/__init__.py`, `src/cellpy/utils/batch.py` | export / shim |
| `tests/test_metadata_sources.py` | `FileRef` validation, `ExternalLink.files` round-trip |
| `tests/test_metadata_source_files.py` (new) | cell path: record with `files` loads without `filefinder` (monkeypatched `search_for_files` raises); record without `files` falls back; kwargs precedence; `NoDataFound` cases; `.cellpy` save/load keeps `external_links[...].files` |
| `tests/test_batch_from_source.py` (new) | offline `DictMetadataSource`: pages equivalent to a journal for a tagged set; rows without files use `find_files`; `file_search=False`; `session["external_links"]` + stamped links after `update()` |
| `docs/guides/metadata_sources.md` | new sections "Let the database find the files" (cell) and "Build a batch from a tag" |
| `docs/agents/index.md`, `AGENTS.md` (outside managed block) | `cellpy.get(source=…)` / `batch.from_source` one-liners |
| `docs/api/...` (metadata sources page if present) | `FileRef` |
| `HISTORY.md` | `[Unreleased]` feature bullet (#1107) |
| `.issueflows/04-designs-and-guides/metadata-sources.md` | new rows: `files`, strict default rule, batch provenance; move `batch.from_source` out of "Not done" |
| `.issueflows/04-designs-and-guides/test-registry.md` | rows for the two new test modules |

## Test strategy

- `uv run pytest tests/test_metadata_sources.py tests/test_metadata_source_files.py tests/test_batch_from_source.py`
- `uv run pytest -m essential` (mark: contract validation, "loads without
  filefinder", fallback parity, `from_source` pages parity).
- `uv run pytest` full before close.
- Fixtures: reuse existing raw test file(s) from `tests/testdata` via
  `DictMetadataSource` rows whose `FileRef.uri` points at them (posix paths).
- Guard: monkeypatch `cellpy.filefinder.search_for_files` to raise
  `AssertionError("filefinder must not run")` in the direct-load tests.

## Open questions

1. **Change detection (spec item 4)** — defer to a follow-up issue as planned
   above, or include a minimal "skip `stat` when `size`+`mtime` match" in
   `update()` now? Recommended: **defer** (touches the incremental-load path
   from #779/#164; separate review).
2. **No-record behaviour in `cellpy.get(source=…)` without a filename** —
   raise `NoDataFound` (recommended, scripting-friendly, matches
   `CellpyCell.data`) vs. `get`'s legacy "print + return None".
3. **Batch provenance** — stamp `ExternalLink` (fields + files) on each loaded
   cell after `update()` (recommended) vs. re-running `_apply_meta_record`
   per cell (would re-order precedence against journal overrides).
4. **`kind` default for `batch.from_source`** — `"tag"` (recommended; the
   BatBase batch use case) vs. `"cell_name"` (cell-path default).
5. Ship the cellpy-connectors adapter mapping in the same session after this
   merges (yes/no)?
