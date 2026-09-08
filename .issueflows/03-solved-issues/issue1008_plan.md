# Plan — issue #1008: nom cap specific lost (batch, xlsx db)

Branch: `1008-batch-nom-cap-specifics`. Milestone `v2.1.4.post`.

## Diagnosis (2026-09-08)

Traced db → journal → spec → `cellpy.get` on master with the reporter's own
config (`cellpy.toml`: `db_cols.nom_cap_specifics = "nom_cap_specifics"`) and db
(`2025_Cell_Analysis_db_001.xlsx`, 976 gravimetric / 28 areal rows):

- `Reader.get_nom_cap_specifics(id)` returns the sheet value.
- `_dbengine._create_pages_dict` → `Journal.pages["nom_cap_specifics"]` →
  `policy.resolve_specs` → `runner._get_kwargs` → `cellpy.get(nom_cap_specifics=…)`
  keeps the value; journal JSON round-trip keeps it.
- `batch.load()` end-to-end on the test db with an `areal` column: cells get
  `nom_cap_specifics="areal"`, `cellpy_units.nominal_capacity="mAh/cm**2"` on
  raw load, `.cellpy` AUTO reload and journal autoload.

So the value is not lost by the pipeline itself. Two ways it shows up as `null`
in `b.pages`, both silent today:

1. **Journal autoload shadows the db.** `batch.load(name, project, …)` with
   `allow_from_journal=True` (default) reuses `cwd/cellpy_batch_<name>.json`
   when present and never opens the xlsx — logged at INFO only. A journal
   written before the db column was filled (or by an older cellpy that did not
   emit the column, e.g. `cellpy_batch_celf_mar.json` from July has no
   `nom_cap_specifics` key) reads back as a `null` column. Even when the user
   passes `db_reader=` / `batch_col=`, the stale journal still wins.
2. **Configured column name ≠ sheet header.** `Reader._pick_info` swallows the
   `KeyError` at `logging.debug` and returns `None` for every cell → `null`
   column → default `gravimetric` at load. No warning.

Side finding (out of scope, file follow-up): `journal_from_db(…, skip_file_search=True)`
with the Excel reader crashes in `simple_db_engine` (`pd.DataFrame(pages_dict)`:
`All arrays must be of the same length` — `raw_file_names` / `cellpy_file_name`
stay `[]`).

## Approach (KISS, no behaviour change on the happy path)

1. `cellpy/readers/dbreader.py` — `_pick_info`: on missing column emit
   `warnings.warn(...)` **once per column per reader instance** (keep the
   `None` return so batches still build). Message names the configured key
   (`config.db_cols.<field>`) and the sheet header it expected.
2. `cellpy/batch/facade.py` — `_load_after_progress`: when the journal is
   autoloaded **and** the caller signalled a db read (`db`, `db_reader`,
   `reader`, `batch_col` or `reader_path` given), `warnings.warn` that the
   database was not consulted and that `allow_from_journal=False` re-reads it.
   Plain `batch.load(name, project)` keeps the INFO log (fast-path reopen).
3. Tests (essential):
   - `tests/test_batch_v3_facade.py`: autoload + `db_reader=` → `UserWarning`;
     autoload without db args → no warning.
   - `tests/test_dbreader.py` (or nearest existing dbreader test module):
     `Reader(db_frame=…)` missing the configured column → one `UserWarning`,
     second pick of same column silent; and a regression check that a present
     `nominal_capacity_specifics` column flows into `_create_pages_dict`.
4. Docs: `HISTORY.md` bullet (close step); one line in
   `docs/getting_started/agents.md` batch bullet + `AGENTS.md` mirror:
   "`batch.load` reuses `cellpy_batch_<name>.json` in cwd when present;
   `allow_from_journal=False` forces a db read."
5. Follow-up GitHub issue for the `skip_file_search=True` Excel crash.

## Files

- `cellpy/readers/dbreader.py`, `cellpy/batch/facade.py`
- `tests/test_batch_v3_facade.py`, `tests/test_dbreader*.py`
- `docs/getting_started/agents.md`, `AGENTS.md`, `HISTORY.md`

## Constraints

- No change to journal schema or defaults; `null` stays `null` (honest).
- Warnings, not exceptions — batches must still build with a partial db.

### Prior art

- `_dbengine.find_files` filefinder-miss `UserWarning` (#964) — same style.
- `#1000` journal `version` warning path in `journal.read_journal`.

## Open questions

- Should `db_reader=`/`batch_col=` given explicitly make the db **win** over the
  autoloaded journal instead of just warning? Plan says warn only (smaller,
  no surprise reload); flip to "db wins" if preferred.
