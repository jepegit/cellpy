# Issue #439: Stage 0: foundations for cellpy 2 (tracking issue)

Source: https://github.com/jepegit/cellpy/issues/439

## Original issue text

## Goal

Complete **Stage 0** of the cellpy 2 effort: pin current behavior with characterization
tests, golden fixtures and performance baselines, and put the shared test/convention
machinery in place — so that every subsequent stage (file-loading refactor, config rework,
unit consolidation, header/polars flip, loader port, utils migration) starts against a
trusted oracle instead of vigilance.

## Why

The cellpy 2 plans live in the **`architecture-plan`** repository
(`cellpy-workspace/architecture-plan/`, alongside `cellpy` and `cellpy-core`).
*(They used to sit in `code-reviews/`; that folder is no longer the home for these plans.)*
Those plans follow the same doctrine the cellpy-core integration proved out: *defend the
seam with tests, not vigilance*. Stage 0 is the collected Step-0 / Phase-0 work of those
plans plus the cross-cutting gaps found in
`architecture-plan/cellpy2-plans-gap-analysis.md`. Nothing in Stage 0 changes behavior;
all of it makes behavior change safe.

## Issues

**Test framework & fixtures**
- [ ] jepegit/cellpy#428 — golden-fixture convention + regeneration tooling (F8) — **focus issue** ([local](issue428_original.md))
- [ ] jepegit/cellpy#437 — conventions bootstrap: deprecation helper, exception tree, DEPRECATIONS registry (G6)

**Characterization suites (pin current behavior)**
- [ ] jepegit/cellpy#429 — cellpy-file round-trip + legacy version matrix (file plan Step 0)
- [ ] jepegit/cellpy#430 — configuration system (config plan Step 0)
- [ ] jepegit/cellpy#431 — unit handling: registry interop (strict xfail), converter parity, pint-optional guard (unit plan §6)
- [ ] jepegit/cellpy#432 — per-loader golden snapshots (loader plan Step 0)
- [ ] jepegit/cellpy#433 — curve-extraction golden snapshots (extraction plan §5)

**Oracles & baselines for the later flips**
- [ ] jepegit/cellpy#434 — value-parity comparator through the header mapping (native-headers plan Phase-3 oracle)
- [ ] jepegit/cellpy#436 — benchmark harness + v1.x baselines (release plan §4)

**Inventory & decisions**
- [ ] jepegit/cellpy#435 — extend consumer scans to filters/, exporters/, internals/ (G5)
- [ ] jepegit/cellpy#438 — decision register: timezone rule, curve-schema home, v9 container, IR semantics, easyplot, maintenance window
- [ ] cellpy/cellpy-core#114 — doc-sync pass over the guiding documents (F7)

## Suggested order

#428 first (everything with fixtures depends on it) and #114/#438 in parallel (cheap,
unblock decisions); then the characterization suites (#429–#433) and #434/#436 in any
order; #435 and #437 whenever.

## Exit criteria (Stage 0 done ⇒ Stage 1 may start)

- All characterization suites green on master, fast subsets marked `essential`.
- Goldens regenerate deterministically via the script; no hand-edited fixtures.
- Benchmark baselines committed **before** any de-indexing/refactor PR merges.
- Value-parity comparator passes trivially against the current bridge.
- The six decisions in #438 recorded in their plan documents.
