# Issue #574 status

- [ ] Done

## Decisions (Accept 2026-07-26)

- Ship stable **now** after D1 green (rc1+rc2 soak treated as enough).
- **#687** does **not** block: document workaround; fix as follow-up.
- **#691** / **#655** non-blocking.

## What's done

### Phases A–C (prior)

- Plan confirmed (rc1 path); #655 non-blocking; feedstock with stable.
- Phase A audit (rc1): CI essential+full ✅, Docs ✅, Benchmarks fail-band ✅;
  load/summary warn accepted for rc1.
- Phase B readiness PR #671 merged.
- Phase C: `v2.0.0rc1` + later `v2.0.0rc2` tagged/published from `master`.

### Phase D1 — re-audit (2026-07-26)

| Gate | Result |
| --- | --- |
| CI `essential` + `full` on `master` | ✅ [run 30204611332](https://github.com/jepegit/cellpy/actions/runs/30204611332) (#692) |
| Benchmarks fail-band | ✅ [run 30204611339](https://github.com/jepegit/cellpy/actions/runs/30204611339) |
| Benchmarks warn-band | ⚠ `single_cell_pipeline` **1.227**, `batch_summary_collection` **1.204** — accepted for stable (rc1 carry-forward). |
| Pin | ✅ `cellpycore==0.2.4` |
| Migration + `DEPRECATIONS.md` | ✅ |
| Stage-3 open | only #574 + tracking #575 |

### Phase D2 — readiness PR content

- `HISTORY.md`: `## [2.0.0] - 2026-07-26` (+ support / #687 known limitation).
- Docs: `remote_paths.md` Host-alias workaround; migration + configuration pointers.
- Guiding docs: branching checklist ticks; release-procedure examples.
- `/iflow-close`: essential tests green; readiness PR opened (see below).

## Remaining work

- Merge readiness PR → clean `master`
- Tag **`v2.0.0`**, watch `release.yml` → PyPI
- conda-forge **cellpy-feedstock** bump to `2.0.0`
- Announce 12-month `v1.x` window; tick remaining branching-checklist boxes;
  close #574 / update #575
- Optional: mark GitHub release `v2.0.0rc2` as prerelease

## Paused on

- **Date:** 2026-07-26
- **Why:** D2 in PR; D3 tag/feedstock after merge
