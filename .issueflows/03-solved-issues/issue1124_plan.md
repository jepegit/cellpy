# Issue #1124 — plan

Branch: `cursor/1124-fileref-skip-stat-ae40` (cloud-agent branch policy; the
issue-flow `<N>-<slug>` form is not available here). Repo: `jepegit/cellpy`.

## Goal

A cell (or batch cell) that came from a metadata-source record carrying
`FileRef.size` / `FileRef.mtime` skips the remote `stat` in
`CellpyCell.update()` when those values equal what cellpy already loaded.
Everything without such values behaves exactly as today.

## Constraints

- Follow [metadata-sources.md](../04-designs-and-guides/metadata-sources.md)
  and [incremental-load-protocol.md](../04-designs-and-guides/incremental-load-protocol.md):
  `ExternalLink.to_dict()` must stay byte-identical for documents that carry
  no new data (omit the new key when empty); `raw` payloads never persisted.
- `checksum` is informational only — no hashing of remote files.
- `force=True` already bypasses change detection; keep that. `recalc` /
  `RAW_ONLY` live on the `cellpy.get` / batch-load path, which this change
  does not touch.
- No cellpycore change; no new dependency.
- KISS: one dataclass field, one comparison helper, one hook in
  `_raw_sources_changed`. No new module.

### Prior art

- `CellpyCell._raw_sources_changed` / `_refresh_fid` (`readers/cellreader.py`)
  — the stat-based check `update()` uses today; the hook goes here.
- `ds.FileID.populate` (`readers/data_structures.py`) — `size` (int) and
  `last_modified` (epoch float from `st_mtime`) are what "cellpy already
  loaded" means. Coexist.
- `MetaRecord.link(files=…)` / `ExternalLink.files` (`metadata_sources/contract.py`)
  — the back-link that already records opened URIs; extend, do not replace.
- `batch/source.py::pages_from_records` — already derives
  `raw_file_size` / `raw_file_mtime` journal columns from the refs and builds
  the link dicts stamped by `Batch._stamp_external_links`. Reuse: links built
  there pick up the new field automatically.
- `check_file_ids` (raw-vs-cellpy stat on first batch load) — same stats, but
  a different path; out of scope here (see Open questions).
- Toolbox (`00-tools/`): nothing relevant. Graph: `graphify-out/` absent.

## Approach

1. **Persist the hints on the back-link** (`contract.py`).
   `ExternalLink.file_refs: tuple[FileRef, ...] = ()` — the record's `raw`
   refs that carry `size` and/or `mtime`. `to_dict` writes `"file_refs"`
   (list of `FileRef.to_dict()`) only when non-empty; `from_dict` reads it
   back. `MetaRecord.link(files=…)` fills it from `raw_files()` restricted to
   the given URIs (when `files` is empty: every raw ref with a stat). This is
   the "pick one, document it" answer: the link, not `Data._provenance`,
   because the link already is the per-source persisted object and
   `_stamp_external_links` / `apply_meta_document` / `from_cell` all copy it.
2. **Cell path** (`cellreader.py`): `_apply_meta_record(record, files=())`
   unchanged in signature; when `files` is empty (a later `c.fetch_meta(...)`
   on an already loaded cell) match the record's raw refs against the cell's
   `raw_data_files` full names so a re-fetch refreshes the hints.
3. **Change detection** (`cellreader.py`): in `_raw_sources_changed`, before
   building `ds.FileID(fid.full_name)` ask `_source_file_hint(fid)` — scan
   `data.external_links[*].file_refs` for a ref whose
   `OtherPath(uri).full_path` equals `fid.full_name` (fallback: same `name`
   when unique). If a hint exists and `_hint_matches_loaded(hint, fid)` is
   true, log at debug (`"update: <name> unchanged per <source> record; stat
   skipped"`) and treat that file as unchanged. Otherwise fall through to the
   stat path exactly as today.
   `_hint_matches_loaded`: every value the ref carries must match — `size`
   as `int ==`; `mtime` via `_mtime_epoch(value)` (int/float epoch, or ISO
   8601 through `datetime.fromisoformat`; naive → UTC) compared with
   `fid.last_modified` within 1 s. A ref with neither value, an unparsable
   mtime, or a `fid` without stats never matches.
4. **Batch**: `pages_from_records` already calls `record.link(files=used)`, so
   the session link dicts gain `file_refs`; `_stamp_external_links` restores
   them onto loaded cells; `Batch.refresh()` / `poll()` call `c.update()` and
   so skip the stat per cell. No facade change needed beyond a docstring
   line. Re-fetching to refresh the hints is `c.fetch_meta(...)` (step 2) or
   a new `batch.from_source(...)`; no extra API.
5. **Docs**: new row in `metadata-sources.md` (decision + comparison rule);
   one line in `docs/agents/index.md` and the `AGENTS.md` quick fact for
   `c.update()`; `update()` docstring step 1. HISTORY entry at close.

## Files to touch

- `src/cellpy/readers/metadata_sources/contract.py` — `ExternalLink.file_refs`,
  dict round trip, `MetaRecord.link` filling it.
- `src/cellpy/readers/cellreader.py` — `_source_file_hint`,
  `_hint_matches_loaded` (+ `_mtime_epoch` helper), hook in
  `_raw_sources_changed`, `_apply_meta_record` re-fetch matching, docstring.
- `src/cellpy/batch/facade.py` — `refresh` docstring note only.
- `tests/test_metadata_source_files.py` (or new `tests/test_source_file_hints.py`
  if it grows past ~120 lines) — see test strategy.
- `.issueflows/04-designs-and-guides/metadata-sources.md`,
  `docs/agents/index.md`, `AGENTS.md` — one row / one line each.
- `.issueflows/01-current-issues/issue1124_status.md`.

## Test strategy

`uv run pytest tests/test_metadata_source_files.py tests/test_cell_update.py tests/test_batch_from_source.py tests/test_batch_live.py`
then `uv run pytest -m essential`. Fixture: `DictMetadataSource` records with
`FileRef(size=<res stat size>, mtime=<res stat mtime as ISO UTC>)`; monkeypatch
`cellpy.internals.otherpath.OtherPath.stat` to raise `AssertionError`.

- matching `size`+`mtime` → `c.update()` is `False`, `stat` not called.
- `size` off by one → `stat` called (falls back; file unchanged → `False`).
- `mtime` only, matching → skipped; `mtime` unparsable → `stat` called.
- record without `size`/`mtime` → `stat` called (today's behaviour).
- `update(force=True)` still reloads (existing test in `test_cell_update.py`
  stays green).
- round trip: `c.save()` → `cellpy.get(.cellpy)` keeps `file_refs`; old
  `ExternalLink.to_dict()` without refs has no `"file_refs"` key.
- batch: `Batch.from_source` session link carries `file_refs`; after
  `update()` the loaded cell's link has them and `b.refresh()` skips `stat`.
- re-fetch on a loaded cell (`c.fetch_meta`) replaces the hints.

## Open questions

- `check_file_ids` (raw-vs-cellpy stat on first batch load / `cellpy.get`
  with a cellpy file) could use the same journal `raw_file_size` /
  `raw_file_mtime`. Recommendation: separate follow-up issue; this one is
  scoped to `update()` / `refresh()` / `poll()` as titled.
- mtime tolerance 1 s and naive-ISO-means-UTC: recommended defaults; a
  mismatch only costs one `stat`, never a wrong skip in the other direction
  except a source whose clock is off by < 1 s.
