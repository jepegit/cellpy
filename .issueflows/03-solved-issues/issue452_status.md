# Issue #452 — status

- [x] Done

## What's done

- Plan accepted (2026-07-14).
- Branch `452-pydantic-config-stack`.
- Added `pydantic-settings` + `platformdirs` deps; lock regenerated.
- New `cellpy/config/` package: models, types, loader, sources, session, migrate, lazy `__init__`.
- Inventory parity vs #430 (`tests/config_support.py`); SQL→secrets divergences documented.
- Tests: `tests/test_config.py` (11 tests, 4 essential); `isolated_config` autouse reset in module.
- `tests/README.md` config subsection.
- Essential gate green: `uv run pytest -m essential` (90 passed).

## Remaining work

- `/iflow-close` (HISTORY, commit, PR).
