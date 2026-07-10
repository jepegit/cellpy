# Issue #437: Stage 0.10: Conventions bootstrap — deprecation helper, exception tree, DEPRECATIONS registry

Source: https://github.com/jepegit/cellpy/issues/437

## Original issue text

> Part of **Stage 0 — foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos).

## Goal

Land the shared conventions machinery every later shim imports:

- `cellpy._deprecation.warn_once(name, replacement, removal="2.1")` (once-per-site registry,
  `stacklevel` correct),
- self-registering deprecation table rendered to `DEPRECATIONS.md`,
- exception-tree skeleton: `cellpy/exceptions.py` re-exports `cellpycore.exceptions.CellpyError`
  as the root; `CorruptCellpyFile`, `ConfigurationError`, `UnitsError`, `LoaderError` stubs,
- test-convention checklist line ("warnings emitted once, registered in DEPRECATIONS.md")
  added to the contributing docs.

Logging changes (no import-time config) are **not** in this issue — they ride with the
config plan's import-time-I/O removal.

## Why

The config, header-migration, unit and utils plans all introduce shims with warnings. If the
helper does not exist before the first shim lands, we get four ad-hoc warning styles and a
deprecation table that is stale on arrival (conventions plan §5).

## Links

- `architecture-plan/cellpy2-conventions-plan.md` (§1, §3, §5)

## Acceptance

- Helper + registry in tree with tests (warn exactly once; registry renders).
- First consumer wired (can be an existing deprecation, e.g. `helpers.make_new_cell`).

## Comments (curated summary)

- **Clarifications / constraints**: #456 (Stage 1.11) describes the same deliverable from the Stage-1 side — implement here and close both together.
- **Superseded / retracted**: (none)

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-07-09._
