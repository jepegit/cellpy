# Issue #572 — status

- [ ] Done

## What's done

- Plan accepted (2026-07-22).
- Expanded `docs/getting_started/migration_v1_to_v2.md` (support matrix,
  frames/`c.schema`, config, plotting, ICA, deps, loaders, a5 caveats, Δ table
  TBD rows, deprecations pointer). Polars: documented as not yet the default
  user-facing frame API.
- `HISTORY.md` Unreleased: migration-guide bullet + accumulated comment items
  (#580/#581, #566/#591, #569, #593, #570, loader-author harmonize notes).
- Loader-author section in `docs/other/writing_a_loader_plugin.md`.
- `DEPRECATIONS.md` regenerates with no diff; ICA entries already present.
- Tests: `tests/test_deprecation_conventions.py` 5 passed; essential 535 passed.

## Remaining work

- `/iflow-close` (note: docs/`HISTORY`/issueflows-only PRs are `paths-ignore`d
  by `ci.yml` — may need a tiny non-md touch for required checks, as on #632).
