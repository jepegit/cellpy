# Issue #453 — status

- [ ] Done

## What's done

- Plan accepted (2026-07-14).
- **Milestone 1 (shim + legacy load)** — merged via PR #494 on `master`.
- **Milestone 2 (internal call-site migration)** — PR #495 on `453-prms-m2-migrate`.
- **Milestone 3 (kill import-time init)** — branch `453-prms-m3-no-import-init`:
  - Removed `init()` call and `init` from `cellpy/__init__.py`
  - Added `test_import_cellpy_no_file_io` (subprocess; no config file reads on import)
  - Essential gate green: `uv run pytest -m essential` (93 passed)

## Remaining work

- Merge M2 PR #495, then M3 PR (stacked)
- `/iflow-close`
