# Issue #345 plan — batch custom JSON + file search after read

## Goal

Make **custom / BatBase-style JSON** a first-class way to build a batch journal on the
blessed `cellpy.batch` API, including **file search after read** so `raw_file_names` /
`cellpy_file_name` are populated like `Batch.from_db(...)` already does for Excel/BatBase.

## Constraints

- Patch-scoped (`v.2.1.2`): additive; no Stage 5 / live-incremental work.
- Reuse existing machinery — do **not** reimplement file search.
- Keep cellpy journal JSON (`read_journal` / `from_journal`) behavior unchanged (paths already in pages; no forced re-search).
- Back-compat: `cellpy.utils.batch.load(..., reader="custom_json_reader")` and
  `Batch.from_db(db_reader="custom_json_reader"|"batbase_json_reader", ...)` must keep working.

### Prior art

| Hit | Role | Plan |
|---|---|---|
| `cellpy/batch/journal.py` — `read_custom_json` / `journal_from_custom_json` | Read-only custom JSON → pages/`Journal` | Keep; optionally document that file search needs the db path |
| `cellpy/readers/json_dbreader.py` — `CustomJSONReader` / `BatBaseJSONReader` | DB-reader adapters + `column_map` | Keep as the search-enabled path |
| `cellpy/batch/_dbengine.py` — `simple_db_engine` / `find_files` | Post-read file search | Reuse; expose `skip_file_search` if useful |
| `cellpy/batch/db.py` — `journal_from_db` | Orchestrates reader → engine → `Journal` | Prefer this as the single integration path |
| `cellpy/utils/batch.py` — `load(..., reader=...)` | Legacy shim already routes custom JSON → `Batch.from_db` | Mirror on blessed `Batch.load` / document |
| `tests/test_batch.py` — custom JSON + file search via shim | Fixture-backed acceptance pattern | Mirror for `cellpy.batch` facade |
| `tests/test_batch_v3.py` — `read_custom_json` unit tests | Read-only coverage | Keep; add facade+search test |

Toolbox / graph: no dedicated helper; reuse `_dbengine.find_files` + `filefinder.search_for_files`.

## Approach

**Problem today:** Custom JSON is half-wired — `read_custom_json` exists on batch v3 but
does **not** run file search; search only happens when going through
`Batch.from_db` / `journal_from_db` + `CustomJSONReader`. Blessed `Batch.load(journal_file=...)`
does not route custom/BatBase JSON the way the utils shim does.

**Do this:**

1. **Blessed load path** — Extend `Batch.load` / `from_journal` (whichever is the public
   “path to journal” entry) so that when the caller asks for a JSON db reader
   (`db_reader` / `reader` / `filetype` — pick one public name, prefer aligning with
   existing `db_reader=` on `from_db`), a JSON file is loaded via `journal_from_db` →
   `simple_db_engine` → `find_files`, not via bare `read_journal` / `read_custom_json`.
2. **Expose kwargs** — Forward `column_map`, `raw_file_dir` / project paths, and
   `skip_file_search` through `journal_from_db` → engine (engine already supports skip
   internally; make it a public opt-out for JSON that already carries paths).
3. **BatBase download story** — Ensure `db_reader="batbase_json_reader"` + `db_file=<download>`
   (or `Batch.load(..., db_reader=...)`) is documented and covered by a facade-level test
   (reader already exists).
4. **Optional thin wrapper** — If useful for discoverability, add
   `journal_from_custom_json(..., *, search_files=True, column_map=..., **dirs)` that
   delegates to `journal_from_db` instead of only `read_custom_json`. Prefer one path over
   two divergent implementations.
5. **Docs** — Short note in batch docs / migration note: custom JSON needs `column_map` +
   the db-reader/load path for file search; native cellpy journal JSON does not re-search.

**Out of scope:** new JSON schemas beyond what `CustomJSONReader` / `BatBaseJSONReader`
already accept; GUI work; #799/#800.

## Files to touch

| Path | Change |
|---|---|
| `cellpy/batch/facade.py` | Route `load` / public entry for custom & BatBase JSON → `from_db` / `journal_from_db` |
| `cellpy/batch/db.py` | Forward `skip_file_search` (+ any missing path kwargs) |
| `cellpy/batch/_dbengine.py` | Only if public kwargs need a small glue fix |
| `cellpy/batch/journal.py` | Optional: `journal_from_custom_json` search flag → db path |
| `tests/test_batch_v3_facade.py` (or sibling) | Facade test: custom JSON → pages + populated `raw_file_names` / `cellpy_file_name` |
| Batch docs / HISTORY (close step) | Document the load pattern |

## Test strategy

- Project: `uv run pytest` (or conda `cellpy_dev_313` per project rules when running locally).
- Add facade-level test mirroring `tests/test_batch.py` custom-JSON + search case, using
  `tests/fixtures/custom_json_batch_like.json` (and BatBase fixture if cheap).
- Keep existing `read_custom_json` unit tests green.
- Essential gate: `uv run pytest -m essential` before close if the change is small enough;
  otherwise targeted batch tests + a note in status.

## Open questions

1. **Public API shape for `Batch.load`:** prefer `db_reader=` (match `from_db`), or a
   separate `filetype=` / `reader=` alias? **Resolved (Accept):** `db_reader=` canonical;
   `reader=` alias.
2. **Should `journal_from_custom_json` gain search-by-default?** **Resolved (Accept):** no —
   keep it read-only; searching stays on `from_db` / `load(..., db_reader=...)`.
3. **BatBase-only vs generic custom in this PR?** **Resolved (Accept):** ship both
   (`custom_json_reader` + `batbase_json_reader`).
