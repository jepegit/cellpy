# Plan: issue #465 — conda CI retry for transient conda-forge 502s

## Goal

Harden `ci-scheduled.yml` against transient conda-forge metadata/download failures (502 Bad Gateway) during `setup-miniconda`, without changing test scope.

## Approach

Wrap each `conda-incubator/setup-miniconda@v3` step in `Wandalen/wretry.action@v3.5.0` (3 attempts, 30s delay). Failures were infra flakiness on `linux-64` repodata fetch — retry is the durable fix recommended in the issue.

## Files to touch

- `.github/workflows/ci-scheduled.yml` — three miniconda setup sites (`conda-pytest`, `nbmake-linux`, `conda-forge`)

## Test strategy

- YAML change only; no runtime code paths.
- Verify workflow file parses; rely on GHA on merge.
