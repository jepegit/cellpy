# Issue #431: Stage 0.4: Unit-handling test groundwork — registry interop, converter parity, pint-optional guard

Source: https://github.com/jepegit/cellpy/issues/431

## Original issue text

> Part of **Stage 0 — foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/code-reviews/` (alongside the `cellpy` and `cellpy-core` repos).

## Goal

Three test deliverables that make the unit consolidation safe to start:

1. **Registry-interop test**: multiply a `Q` from `cellpy.readers.data_structures` with a
   `Q` from `cellpycore.units` — this **fails today** (two pint registries in one process).
   Land as `xfail(strict=True)`: it is the executable statement of unit plan Phase 1's
   target, and flips to a hard pass when the registries are unified.
2. **Converter parity fixtures**: `get_converter_to_specific` and
   `nominal_capacity_as_absolute` — legacy (cellreader) vs `cellpycore.units` — equal on
   golden data for gravimetric / areal / absolute modes.
3. **pint-optional guard** (cellpy-core side): importing `cellpycore` and running the
   step/summary engine works with pint **not installed**; helpers raise a clear
   `ModuleNotFoundError` only when called. Verify whether this already exists in core CI
   before writing (the roadmap status is stale — see Stage 0.12).

## Why

Unit plan Phase 2 deletes cellpy's duplicated converter bodies; parity fixtures are the
precondition. The interop test documents the two-registry trap so nobody passes Quantities
across the boundary before Phase 1 lands. These are also the STEP-12 success criteria in the
core integration roadmap.

## Links

- `code-reviews/unit-handling-cellpy2-plan.md` (§6 testing strategy, §7 risk 1)
- `cellpy-core/.issueflows/04-designs-and-guides/cellpy-core-integration-roadmap.md` (STEP-12)
- Depends on Stage 0.1 (fixtures).

## Acceptance

- Interop test in tree as strict xfail with a comment pointing at unit plan Phase 1.
- Parity fixtures committed + green; pint-optional guard confirmed or added in cellpy-core.

