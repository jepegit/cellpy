# Issue #1008 status — nom cap specific lost (batch, xlsx db)

- [x] Done

Branch: `1008-batch-nom-cap-specifics`. Plan accepted 2026-09-08 (warn-only variant).

## What's done

- Diagnosis: pipeline keeps the value (verified db → journal → spec →
  `cellpy.get` → cell, incl. `.cellpy` reload and journal autoload). `null`
  in `b.pages` comes from a cached `cellpy_batch_<name>.json` shadowing the
  db (INFO-only before), or from a configured-vs-sheet column-name mismatch
  swallowed in `Reader._pick_info`.
- `cellpy/readers/dbreader.py`: `_warn_missing_column` — one `UserWarning`
  per missing sheet header per reader, naming the `config.db_cols.<key>`.
- `cellpy/batch/facade.py`: `_load_after_progress` warns when the journal is
  autoloaded but `db` / `db_reader` / `batch_col` / `reader_path` / other db
  kwargs were given.
- Tests (essential): `test_dbreader.py::test_missing_column_warns_once`,
  `::test_nom_cap_specifics_column_reaches_pages`;
  `test_batch_v3_facade.py::test_load_warns_when_journal_autoload_shadows_db`,
  `::test_load_autoload_without_db_args_is_quiet`.
- Docs: `docs/getting_started/agents.md` batch recipe + `AGENTS.md` mirror.
- Follow-up filed: #1017 (`skip_file_search=True` crashes with Excel reader).

## Remaining work

- None.
