# Issue #452: Stage 1.7: Config — build the pydantic-settings stack in parallel

Source: https://github.com/jepegit/cellpy/issues/452

## Original issue text

> Part of **Stage 1 â€” behavior-preserving construction** (see the Stage-1 tracking issue). Stage 0: jepegit/cellpy#439. Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Everything in Stage 1 lands on master with the full suite green; nothing flips user-visible behavior.

## Goal

Config plan Step 2: the `cellpy/config/` package built next to the old system, nothing
importing it yet â€” models mirroring today's sections (`paths`, `file_names`, `reader`,
`db`, `batch`, `instruments` as typed models, `defaults` (ScienceDefaults, values in
cellpy units by convention), **`units`** (new, validated against
`cellpycore.units.CellpyUnits` keys), `secrets` (SecretStr, env-only)); layered loader
(defaults â†’ user `cellpy.toml` via platformdirs â†’ project-local walk-up â†’ env/`.env` â†’
runtime); provenance (`sources()`); YAMLâ†’TOML converter; `override()` context manager +
`isolated_config` pytest fixture.

## Why

The parallel build is what makes the Step-3 swap a flag-day with a small diff. The
inventory parity test from #430 asserts new defaults == old, field by field â€” including
deliberate fixes surfaced by validation (the `limit_loaded_cycles` int-vs-list lie gets a
proper union type here). The `units:` section is the home the unit plan's Phase 5
depends on (config plan Â§3.2, added in the 2026-07-09 cross-check).

## Links

- `architecture-plan/cellpy2-configuration-and-parameters-plan.md` (Steps 2, Â§3)
- `architecture-plan/unit-handling-cellpy2-plan.md` (Phase 5)
- Depends on: #430 (inventory contract); Stage 1.1 (constants already purged).

## Acceptance

- Parity test green: every (section, field, default) triple matches or carries a
  documented, deliberate divergence note.
- `override()` fixture demonstrated in one test; provenance answers "where did this
  value come from" for all four layers.

