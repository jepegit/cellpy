# Issue #574 status

- [ ] Done

## Done so far

- Plan confirmed: ship **`v2.0.0rc1`** first; #655 non-blocking; feedstock with stable; audit `master` first.
- **Phase A audit (master @ #667 / 2026-07-24):** CI essential+full ✅, Docs ✅, Benchmarks fail-band ✅; load/summary warn-band intermittent (+21–32%), explained as single-round GHA noise and **accepted for rc1**.
- **Phase B:** guiding docs synced (pin-gate `==0.2.3`, branching rc soak, release-procedure, this-project).
- Readiness PR: https://github.com/jepegit/cellpy/pull/671 (`Refs #574`)
- Close commit: `HISTORY.md` Unreleased bullet; essential tests 624 passed.

## Remaining work

- Merge PR #671
- **Phase C:** clean `master` → `gh release create v2.0.0rc1 --target master` → watch `release.yml` / PyPI `--pre`
- **Planned tag (tag-derived):** `v2.0.0rc1` (create after merge from clean `master`, not from feature branch)
- Later: soak → re-audit → stable `v2.0.0` + feedstock + start 12-month `v1.x` window

## Paused on

- **Date:** 2026-07-24
- **Branch:** `574-release-checklist`
- **Why:** readiness docs landed; tag/publish still open (issue not fully done)
