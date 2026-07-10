# Issue #446: Stage 1.1: Purge non-config constants from prms.py; create readers/cellpy_file/ with format.py

Source: https://github.com/jepegit/cellpy/issues/446

## Original issue text

> Part of **Stage 1 — behavior-preserving construction** (see the Stage-1 tracking issue). Stage 0: jepegit/cellpy#439. Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Everything in Stage 1 lands on master with the full suite green; nothing flips user-visible behavior.

## Goal

The shared first step of the file-loading and configuration plans, done once:

- Create `cellpy/readers/cellpy_file/` with `format.py`: a frozen `CellpyFileFormat`
  dataclass (root, table keys, meta dirs, unit/limit prefixes, complib/complevel,
  per-table pandas formats), one instance per historical file version (v3/4–v8).
- Move the `_cellpyfile_*` constants out of `prms.py` onto the spec; keep
  `prms._cellpyfile_*` as aliases during the deprecation window.
- Move template-registry and example-data URL constants to their owning modules;
  delete `_globals_status`/`_globals_errors` in favor of explicit returns.

## Why

Constants are not configuration (config plan §1.3.4); the format spec scattered between
`prms.py` and kwarg defaults inside `_load_hdf5_v7` is drift-prone duplication (file plan
§1.2, §2.4). Both plans name this as their Step 1 and agreed it is one shared step —
whoever lands it, the other rebases. **Beware the limits-prefix trap pinned by
jepegit/cellpy#429**: `_cellpyfile_raw_limit_pre_id == ""` masks an inverted loop in
`_create_infotable` (cellreader.py:2452–2455); `format.py` must carry the empty prefix
verbatim or fix the loop deliberately, never both silently.

## Links

- `architecture-plan/cellpy-file-loading-refactor-plan.md` (Step 1, §3.2 format.py)
- `architecture-plan/cellpy2-configuration-and-parameters-plan.md` (Step 1)
- Depends on: #429 (characterization green first).

## Acceptance

- Full suite green; zero behavior change (aliases only).
- `format.py` is the single source for layout knowledge; grep shows no remaining
  literal `"/CellpyData"` outside it except `batch_helpers.look_up_and_get` (Stage 1.4).
