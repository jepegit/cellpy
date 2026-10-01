# Issue #1124 — status

- [x] Done

Branch: `cursor/1124-fileref-skip-stat-ae40` (cloud-agent branch policy; not
the `<N>-<slug>` form). Plan: `issue1124_plan.md` (accepted 2026-10-01,
followed as written).

## What's done

- `ExternalLink.file_refs: tuple[FileRef, ...]` — raw refs with `size` /
  `mtime`, restricted to opened URIs; `to_dict` emits `"file_refs"` only when
  non-empty (pre-#1124 `meta.json` byte-identical); `file_ref_for(uri)`.
  `MetaRecord.link(files=…)` fills it, so `cellpy.get(source=…)`,
  `fetch_meta`, `pages_from_records` → `_stamp_external_links` all carry it.
- `CellpyCell._raw_sources_changed`: `_source_file_hint(fid)` (URI /
  `OtherPath.full_path` / unique basename) + module-level
  `_source_hint_matches_loaded` (`size` int-equal, `mtime` epoch or ISO-8601
  within `SOURCE_MTIME_TOLERANCE` = 1 s, naive ⇒ UTC; every carried value
  must match) skips `ds.FileID(...)` (no `is_file` / `stat`) and logs at
  debug. `force=True` unchanged.
- `_apply_meta_record` on a loaded cell (re-fetch) keeps only refs pointing
  at `raw_data_files`, so fresher source stats replace the hints.
- Tests: `tests/test_source_file_hints.py` (17; 6 essential, registry rows
  added). Related suites green: `test_metadata_source_files`,
  `test_metadata_sources`, `test_cell_update`, `test_batch_from_source`,
  `test_batch_live`, `test_live_poll` (88 passed).
- Docs: `metadata-sources.md` new section; `docs/agents/index.md`,
  `AGENTS.md`, `update()` and `Batch.refresh()` docstrings; HISTORY bullet.

## Verification

- `uv run pytest -m essential --ignore=tests/test_arbin_variants_two_stage.py --ignore=tests/test_load_since.py`:
  953 passed, 74 skipped, 2 failed. Both failures
  (`tests/test_filefinder.py::test_find_by_project_cellpy_range`,
  `::test_find_by_project_otherpath_local`) fail identically on a clean
  `master` checkout in this environment — not from this change. The two
  ignored modules fail to import here (`pyodbc` needs `libodbc.so.2`), also
  environmental.

## Remaining work / follow-ups (not in scope)

- `check_file_ids` (raw-vs-cellpy stat on first `cellpy.get` / batch load)
  could consult journal `raw_file_size` / `raw_file_mtime` the same way —
  separate issue.
