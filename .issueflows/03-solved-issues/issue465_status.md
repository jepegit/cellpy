# Issue #465 — status

- [x] Done

## What's done

- Wrapped all three `setup-miniconda` steps in `ci-scheduled.yml` with `Wandalen/wretry.action` (3 attempts, 30s delay) for transient conda-forge 502s.
