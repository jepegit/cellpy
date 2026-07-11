# Issue #459: Stage 1: behavior-preserving construction for cellpy 2 (tracking issue)

Source: https://github.com/jepegit/cellpy/issues/459

## Original issue text

## Goal

Complete **Stage 1 â€” behavior-preserving construction**: every refactor and parallel
build that can land on master with the full v1.x suite green, so that the Stage-2 flip
(native headers + polars, one flag-day) becomes a small, well-oracled step instead of a
rewrite. Nothing in Stage 1 changes user-visible behavior; everything is guarded by the
Stage-0 characterization suites and oracles (#439).

## Why

The plans in `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) are all shaped around the same move:
*build the new thing next to the old thing, prove parity, then swap*. Stage 1 is the
"build next to" phase across five workstreams: cellpy-file I/O, configuration, units,
header translation, and de-indexing â€” plus the additive cellpy-core modules
(units helpers, mapping extensions, meta mapping, curves) they consume.

## Issues by workstream

**cellpy-file I/O** (`architecture-plan/cellpy-file-loading-refactor-plan.md`)
- [ ] jepegit/cellpy#446 â€” Stage 1.1: constants purge + `cellpy_file/format.py` (shared with config plan)
- [ ] jepegit/cellpy#447 â€” Stage 1.2: stateless helpers + selector/limits de-stating
- [ ] jepegit/cellpy#448 â€” Stage 1.3: read + write paths move into `cellpy_file/`
- [ ] jepegit/cellpy#449 â€” Stage 1.4: out-of-band redirects, typed errors, `cellpy convert` CLI

**Units** (`architecture-plan/unit-handling-cellpy2-plan.md`)
- [ ] jepegit/cellpy#450 â€” Stage 1.5: one spec, one registry, rename the `core` alias
- [ ] cellpy/cellpy-core#115 â€” Stage 1.13: `convert_value`, `calculate_scaler`, `validate_units`
- [ ] jepegit/cellpy#451 â€” Stage 1.6: delegate the duplicated converters

**Configuration** (`architecture-plan/cellpy2-configuration-and-parameters-plan.md`)
- [ ] jepegit/cellpy#452 â€” Stage 1.7: pydantic-settings stack built in parallel
- [ ] jepegit/cellpy#453 â€” Stage 1.8: prms shim swap, call-site migration, no import-time init
- [ ] jepegit/cellpy#454 â€” Stage 1.9: `cellpy setup` rewrite + migrate UX

**Headers** (`architecture-plan/cellpy2-native-headers-migration-plan.md`)
- [ ] jepegit/cellpy#455 â€” Stage 1.10: hard-coded header-literal cleanup (priorities 1â€“3)
- [ ] cellpy/cellpy-core#116 â€” Stage 1.14: mapping extensions (postfix expansion + attribute table)
- [ ] jepegit/cellpy#458 â€” Stage 1.15: dormant `translate.py` (to_native/to_legacy) + bridge extraction

**Polars preparation** (`architecture-plan/cellpy2-polars-port-execution-plan.md`)
- [ ] jepegit/cellpy#457 â€” Stage 1.12: Phase A de-indexing (raw/summary/journal) + warn-only lint

**Conventions**
- [ ] jepegit/cellpy#456 â€” Stage 1.11: deprecation helper + exception tree (implementation of #437)

**cellpy-core additive modules**
- [ ] cellpy/cellpy-core#117 â€” Stage 1.16: legacyâ‡„core metadata field mapping (+ G9/volume decisions)
- [ ] cellpy/cellpy-core#118 â€” Stage 1.17: `cellpycore.curves` (spec'd extraction layer; gated on #438 decision 2)

## Sequencing constraints (the ones that bite)

1. **#450 before #447/#448** â€” the `core`-alias rename must not interleave with the
   cellreader code moves (agreed in both plans' risk tables).
2. **Core-first merge order** for additions: #115 â†’ release + re-pin â†’ #451;
   #116 â†’ release + re-pin â†’ #458 (release plan Â§3).
3. **#456 before #449 and #453** (they import the conventions machinery).
4. **#436 baselines before #457** (de-indexing is where perf could silently move).
5. #446 is the shared step of two plans â€” whoever lands it, the other rebases.
6. #455 and #452 are independent and can start immediately.

## Exit criteria (Stage 1 done â‡’ Stage 2 flip may be scheduled)

- All Stage-0 characterization suites still green, unmodified except where a change is
  deliberate and documented (typed errors in #449, config divergences in #452).
- `cellpy_file/` owns all cellpy-file I/O; `CellpyCell.load/save` are thin wrappers.
- One pint registry (interop test hard-passes); no duplicated converter bodies.
- Config: no import-time I/O; parity contract green; old conf migrates.
- `translate.py` round-trip (v8 â†’ native â†’ v8) green; value-parity comparator (#434)
  green against the bridge.
- De-indexing done; benchmarks (#436) within band vs the v1.x baselines.
- Core releases tagged and re-pinned for #115/#116/#117/#118.


