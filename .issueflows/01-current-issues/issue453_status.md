# Issue #453 — status

- [ ] Done

## What's done

- Plan accepted (2026-07-14).
- Branch `453-prms-shim-swap`.
- **Milestone 1 (shim + legacy load):**
  - `cellpy/config/legacy.py` — YAML discovery, ingest, export
  - `cellpy/config/loader.py` — legacy YAML fallback, None stripping
  - `cellpy/parameters/_shim.py` — deprecated section proxies (+ Arbin SQL compat)
  - `cellpy/parameters/prms.py` — section singletons removed; module `__getattr__` shim
  - `cellpy/parameters/prmreader.py` — delegates to config stack; YAML export adapter
  - Tests: `tests/test_prms_shim.py`; `test_deprecation_conventions` adjusted for shim noise
  - Essential gate green: `uv run pytest -m essential` (92 passed)

## Remaining work

- **Milestone 2:** mechanical `prms.*` → `cellpy.config.*` migration (~35 files)
- **Milestone 3:** remove import-time `initialize()` from `cellpy/__init__.py` + import-io test
- `/iflow-close`
