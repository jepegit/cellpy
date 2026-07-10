# Issue #437 — status

- [x] Done

## What's done

- Branch `437-conventions-bootstrap` created from `master`.
- Plan confirmed in `issue437_plan.md`.
- Added `cellpy/_deprecation.py` with `warn_once`, registry, and `DEPRECATIONS.md` renderer.
- Extended `cellpy/exceptions.py`: re-export `CellpyError` / `NoDataFound`, stub exceptions.
- Wired `helpers.make_new_cell` as first `warn_once` consumer.
- Added `tests/test_deprecation_conventions.py` (5 essential tests).
- Committed `DEPRECATIONS.md` and contributing checklist line in `CONTRIBUTING.md`.

## Remaining work

- None.
