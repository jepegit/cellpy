# Issue #434: Stage 0.7: Value-parity comparator — the mapped-columns oracle harness

Source: https://github.com/jepegit/cellpy/issues/434

## Original issue text

> Part of **Stage 0 — foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos).

## Goal

A reusable test utility (e.g. `tests/parity.py::assert_value_parity(legacy, native, family)`)
that compares legacy-named frames against native-named frames **through
`cellpycore.legacy.mapping`**: values equal on all mapped columns (dtype-tolerant,
column-order independent), with an explicit, named exception list per call site (for
documented intentional differences).

Prove it now against today's bridge: run the current pipeline, take the legacy output,
rename via the mapping, compare with the native engine's output — this must pass trivially.

## Why

The native-headers migration replaces the byte-for-byte oracle with value-parity-through-
the-mapping at its Phase 3 flip. Building and trusting the comparator **now**, when it must
pass by construction, means the flip is judged by a proven tool instead of one written
during the crisis. The explicit exception mechanism is also where the IR-semantics switch
(gap item F4) gets recorded when decided, and the loader plan's end-to-end tests reuse the
same helper.

## Links

- `architecture-plan/cellpy2-native-headers-migration-plan.md` (Phase 3 oracle, §4 test plan)
- `architecture-plan/legacy-cellpy-core-header-swapping.md` (what the mapping guarantees)
- `architecture-plan/cellpy2-plans-gap-analysis.md` (F4)
- Depends on Stage 0.1; pairs with Stage 0.11 decision (4).

## Acceptance

- Comparator handles raw/steps/summary families incl. the `{col}_{mode}` specific columns.
- Trivial-pass test against the current bridge is green in CI.
- Exception list is a named argument, not a comment — an unlisted mismatch always fails.
