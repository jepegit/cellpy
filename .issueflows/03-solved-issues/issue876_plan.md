# Issue #876 — Plan: one unambiguous CI gate

Status: **confirmed** (2026-08-11) — use the issue's simplest alternative.

## Goal

Make each required Tier-1 check name resolve to one real test result for PRs
targeting `master`, including mixed code/docs and docs-only changes.

## Approach

1. Remove PR/push path filters from `.github/workflows/ci.yml` while preserving
   its `master` branch scope and required job display names.
2. Delete `.github/workflows/ci-dummy.yml` so no same-named no-op jobs remain.
3. Update adjacent workflow comments, the CI tier guide, and `HISTORY.md`.

## Validation

- `actionlint` on changed workflows.
- Verify one producer file for each required job display name.
- Verify `ci.yml` has PR/push triggers with no path filters.
- `git diff --check`.
