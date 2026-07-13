# Issue #450: Stage 1.5: Units Phase 1 — one CellpyUnits, one pint registry, rename the `core` alias

Source: https://github.com/jepegit/cellpy/issues/450

## Original issue text

> Part of **Stage 1 — behavior-preserving construction** (see the Stage-1 tracking issue). Stage 0: jepegit/cellpy#439. Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Everything in Stage 1 lands on master with the full suite green; nothing flips user-visible behavior.

## Goal

- `cellpy.parameters.internal_settings.CellpyUnits` becomes a re-export of
  `cellpycore.units.CellpyUnits` (deprecated alias one release).
- Delete `_ureg`/`ureg`/`Q`/`get_ureg` from `cellpy/readers/data_structures.py`;
  re-export `cellpycore.units.Q`. Fix the direct importers
  (`instruments/neware_xlsx.py:18`, `utils/plotutils.py:5045`).
- Rename the `from cellpy.readers import data_structures as core` alias in
  `cellreader.py:33` (it is guaranteed to confuse now that `cellpycore` exists).

## Why

cellpy currently runs **two pint registries in one process** (cellpy's own +
cellpy-core's memoized one); quantities from different registries cannot interoperate —
a latent trap the Stage-0 interop test (#431) documents as a strict xfail. This issue
flips that test to a hard pass. It also makes the #378 contract test a trivial identity.
**Sequencing: land before Stage 1.2/1.3** — this PR touches many cellreader lines and
must not interleave with the code moves.

## Links

- `architecture-plan/unit-handling-cellpy2-plan.md` (Phase 1, §7 risk 1, §8 cross-check 6)
- Depends on: #431 (the xfail exists); blocks: Stage 1.2 by agreed order.

## Acceptance

- Registry-interop test passes (xfail marker removed).
- One `pint.UnitRegistry` per process (assert via `cellpycore.units.converters._get_unit_registry`).
- Full suite green; no numeric changes anywhere.
