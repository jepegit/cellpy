# Issue #453: Stage 1.8: Config — swap the engine under prms, migrate call sites, kill import-time init

Source: https://github.com/jepegit/cellpy/issues/453

## Original issue text

> Part of **Stage 1 — behavior-preserving construction** (see the Stage-1 tracking issue). Stage 0: jepegit/cellpy#439. Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Everything in Stage 1 lands on master with the full suite green; nothing flips user-visible behavior.

## Goal

Config plan Steps 3 + 4:

- Re-point `cellpy.parameters.prms` onto the new stack via a `__getattr__` shim
  (attribute reads/writes forwarded, `DeprecationWarning` once per name via the
  Stage-1.11 helper); delete `_update_prms`/`_pack_prms`/file-glob discovery.
- Mechanically rewrite the 383 internal `prms.X.y` call sites to `cellpy.config.x.y`.
- Remove `prmreader.initialize()` from `cellpy/__init__.py` (the marked v2.0 TODO);
  lazy loading on first access takes over.

## Why

This is the config flag-day, kept safe by the Step-0 characterization (#430) and the
Step-2 parity contract. Killing import-time I/O is a stated cellpy 2 requirement
(no side effects on `import cellpy`) and the same principle the conventions plan applies
to logging.

## Links

- `architecture-plan/cellpy2-configuration-and-parameters-plan.md` (Steps 3–4, §3.5 shim)
- Depends on: Stage 1.7, Stage 1.11 (warn_once).

## Acceptance

- Full suite green with the shim in place; then green again after call-site migration.
- `python -c "import cellpy"` performs zero file reads (assert via monkeypatched opener
  in a test).
- User-facing mutation patterns (`prms.Reader.cycle_mode = ...`) still work, warn once.

## Comments (curated summary)

- **Clarifications / constraints**:
  - Maintainer closed the issue as complete: M1 (#494), M2 (#495), and M3 (#496) all merged to master and verified green; `import cellpy` no longer reads config files at import time; `prms.*` remains the external shim with the documented deprecation cadence.
  - Follow-up UX work (TOML generation + `setup migrate`) stays in #454 — out of scope for closing #453.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-07-14._

