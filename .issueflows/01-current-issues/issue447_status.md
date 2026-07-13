# Issue #447 — status

- [ ] Done

## What's done

- Plan confirmed (`issue447_plan.md`).

## Remaining work

- Commit 1: move stateless helpers to `cellpy_file/` with delegators.
- Commit 2: `LoadSelector` / `LoadLimits`; kill `self.limit_*` side channel in extractors.
- Run essential + cellpy-file roundtrip tests after each commit.
- Acceptance grep on `self.limit_*` in `cellreader.py`.
