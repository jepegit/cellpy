# Issue #574 status

- [ ] Done

## Done so far

- Plan confirmed: ship **`v2.0.0rc1`** first; #655 non-blocking; feedstock with stable; audit `master` first.
- **Phase A audit:** CI essential+full ✅, Docs ✅, Benchmarks fail-band ✅; load/summary warn accepted for rc1.
- **Phase B:** guiding docs synced; readiness PR #671 merged (`955691a0`).
- **Phase C (rc1):** tagged and published
  - Release: https://github.com/jepegit/cellpy/releases/tag/v2.0.0rc1 (prerelease)
  - Publish workflow: https://github.com/jepegit/cellpy/actions/runs/30091209188 — validate ✅ test ✅ publish ✅
  - Install: `pip install --pre cellpy==2.0.0rc1`

## Remaining work

- Soak rc1; re-run gates if needed
- Tag stable **`v2.0.0`** from clean `master`
- conda-forge feedstock bump (stable only)
- Announce 12-month `v1.x` bugfix-only window from stable date (#438-6)
- Close #574 / update #575 when stable ships
- Optional: promote `HISTORY.md` Unreleased #574 bullet into `## [2.0.0rc1] - 2026-07-24` on a small follow-up commit
- `/iflow-cleanup` for local `574-release-checklist` if still present (remote already deleted)

## Paused on

- **Date:** 2026-07-24
- **Branch:** `master` (rc1 shipped)
- **Why:** waiting on rc soak → stable `v2.0.0`
