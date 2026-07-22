# Issue #453 — status

- [x] Done

## What's done

- Plan accepted (2026-07-14).
- **Milestone 1 (shim + legacy load)** — merged via PR #494 on `master`.
- **Milestone 2 (internal call-site migration)** — merged via PR #495 on `master`.
- **Milestone 3 (kill import-time init)** — merged via PR #496 on `master`.
  - Removed import-time `initialize()` from `cellpy/__init__.py`
  - Added `test_import_cellpy_no_file_io` (subprocess; no config file reads on import)
- GitHub issue closed 2026-07-14 by @jepegit (complete; follow-up UX in #454).
- Local bookkeeping close-out 2026-07-22: status marked Done; files moved to
  `.issueflows/03-solved-issues/`. Essential gate green (`uv run pytest -m essential`:
  545 passed).

## Remaining work

- None.
