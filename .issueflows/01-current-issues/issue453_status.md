# Issue #453 — status

- [ ] Done

## What's done

- Plan accepted (2026-07-14).
- **Milestone 1 (shim + legacy load)** — merged via PR #494 on `master`.
- **Milestone 2 (internal call-site migration)** — branch `453-prms-m2-migrate`:
  - Mechanical `prms.<Section>` → `cellpy.config.<section>` in ~32 files under `cellpy/`
  - `cellpy/parameters/internal_settings.py` — dataclass defaults use lazy `default_factory`
  - `cellpy/readers/instruments/arbin_sql_config.py` — shared Arbin SQL credential resolution
  - `arbin_sql.py` / `arbin_sql_7.py` — lazy SQL settings via `arbin_sql_value()`
  - Instrument `default_model` — attribute access on pydantic models
  - `easyplot.py` — `set_arbin_sql_value()` for SQL mutation
  - Fixed broken multi-line imports from codemod (`prmreader`, `helpers`, batch tools)
  - Fixed circular import: `connections.py` defers `cellpy.config` import
  - Helper: `.issueflows/00-tools/migrate_prms_calls.py`
  - Essential gate green: `uv run pytest -m essential` (93 passed)

## Remaining work

- **Milestone 3:** remove import-time `initialize()` from `cellpy/__init__.py` + import-io test
- `/iflow-close`
