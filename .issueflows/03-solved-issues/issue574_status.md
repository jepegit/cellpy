# Issue #574 status

- [x] Done

## Decisions (Accept 2026-07-26)

- Ship stable **now** after D1 green (rc1+rc2 soak treated as enough).
- **#687** does **not** block: document workaround; fix as follow-up.
- **#691** / **#655** non-blocking.

## What's done

### Phases A–C (prior)

- rc1 + rc2 soak path; readiness PR #671; PyPI pre-releases.

### Phase D

- D1 re-audit green on master tip (#692); warn-band accepted (rc1 carry-forward).
- D2 readiness PR #693 merged (`ce37d9cd`).
- Tagged **`v2.0.0`**: https://github.com/jepegit/cellpy/releases/tag/v2.0.0
- PyPI `cellpy==2.0.0` published.
- conda-forge feedstock **#59** merged (CI green all platforms):
  https://github.com/conda-forge/cellpy-feedstock/pull/59
- Branching checklist “At v2.0 release” fully ticked; 12-month `v1.x` window
  from 2026-07-26 announced in release notes + HISTORY.

## Remaining work

- None for #574. Optional follow-ups outside this issue: mark `v2.0.0rc2` as
  GitHub prerelease; `git branch -D` leftover squash-merged locals; wait for
  anaconda.org CDN if `conda install cellpy=2.0.0` lags the merge briefly.
