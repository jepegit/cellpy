# Issue #1107 — status

Branch: `1107-file-pointers-from-source` (worktree `../cellpy-1107`).
Plan accepted 2026-09-30 with all recommendations (defer change detection;
`NoDataFound` on no record; stamp `ExternalLink` after batch `update()`;
`batch.from_source` default `kind="tag"`; connectors adapter follow-up after
merge).

- [x] Done

## What's done

- Contract: `FileRef` (+ `FILE_KINDS`, dict round-trip), `MetaRecord.files`
  with dict coercion and `raw_files()` / `cellpy_file()` helpers,
  `validate_record` file checks, `ExternalLink.files` (omitted from
  `to_dict` when empty). Exported from `cellpy.readers.metadata_sources`.
- Cell path: `cellpy.get(source=, key=, kind=, project=, source_extra=,
  strict=)` via `_resolve_from_source` (fills only what the caller left
  empty; `filefinder` fallback; strict-by-default when no filename;
  `NoDataFound` on no record), `CellpyCell.from_source` alias,
  `_apply_meta_record(record, files=)` returns applied fields; `.cellpy`
  branch refreshes the summary when fields were applied.
- Batch path: `src/cellpy/batch/source.py` (`pages_from_records`,
  `journal_from_records`, `default_batch_name`, `SESSION_KEY`),
  `Batch.from_source` + module `batch.from_source` + `utils.batch` shim,
  `Batch._stamp_external_links()` after `update()`.
- Tests: `tests/test_metadata_source_files.py` (14), `tests/test_batch_from_source.py`
  (12); 5 + 4 marked essential. `uv run pytest -m essential`: green
  (557 passed). Docs build (`zensical build`): no issues.
- Docs: guide step 5 + batch section in `docs/guides/metadata_sources.md`,
  `docs/agents/index.md`, `AGENTS.md`, `docs/api/readers.md`,
  `docs/api/batch.md` (`cellpy.batch.source`), HISTORY `[Unreleased]`.
- Design note `metadata-sources.md` "File pointers (M4)" section;
  test-registry rows.

## Remaining work

- None for this issue. Full `uv run pytest`: 1986 passed, 3 failed — all
  plotly/kaleido image-export timeouts (headless Chromium unavailable in the
  local sandbox; unrelated, CI covers them).
- Follow-ups (separate issues): change detection via `size`/`mtime` in
  `update()`; cellpy-connectors adapter mapping BatBase `files[]` →
  `FileRef` (file issue there after merge).

## Notes

- Pre-existing `black --check` drift in `cellreader.py`, `facade.py`,
  `contract.py` left untouched (present on `master` before this branch).
