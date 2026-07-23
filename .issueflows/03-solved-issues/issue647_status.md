# Issue #647 — Status

- [x] Done

## What's done

- Plan accepted; implemented on `647-port-raw-and-cycle-info-plot`.
- Moved `LiveHeaders` to `cellpy/plotting/headers.py` (re-exported as `plotutils._LiveHeaders`).
- Extended `plotting.labels` with `quantity_label` / `units_quantity_label`.
- Added `prepare/raw.py` + `prepare/steps.py`; registered `"raw"` / `"cycle_info"`.
- Backend `kind` branches for raw + cycle_info; thin public APIs + `interactive=` deprecations.
- Tests (`test_raw_cycle_info_prepare.py`), oracle harness `backend=`, design notes updated.
- Focused suite + essential gate green (oracle unchanged — no snapshot regen).
- HISTORY.md Unreleased bullet; closed via `/iflow-close`.

## Remaining work

- None (PR merge + `/iflow-cleanup` after merge).
