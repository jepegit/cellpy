# Issue #429: Stage 0.2: Characterization tests — cellpy-file round-trip + legacy version matrix

Source: https://github.com/jepegit/cellpy/issues/429

## Original issue text

> Part of **Stage 0 — foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/code-reviews/` (alongside the `cellpy` and `cellpy-core` repos).

## Goal

Lock in current cellpy-file (HDF5) behavior before the reader/saver refactor:

- v8 round-trip: load `testdata/hdf5/*_v8.h5` → save → reload → equality on raw/steps/summary
  frames, meta dicts, fid list, units and limits.
- Legacy matrix: parametrized loads of the `_v4/_v5/_v6/_v7` files (shapes, key columns
  post-rename, meta fields); `_v0` asserting the too-old failure mode.
- Selector: `load(..., selector={"max_cycle": N})` truncates summary/raw/steps consistently
  and sets `limit_data_points`.
- Failure modes: missing required store key → current exception type/message.
- **The limits-prefix trap**: `prms._cellpyfile_raw_limit_pre_id == ""` and the inverted
  key/prefix loop in `_create_infotable` (cellreader.py:2452–2455) only work because the
  prefix is empty — pin that limits are stored **unprefixed**.

## Why

The file-loading refactor is behavior-preserving, and these tests are the definition of
"behavior" (its Step 0). They are also the base the header-migration importer tests
(Phase 1) build on, and the cellpy-file module is our designated backwards-compatibility
tool — it must be the best-tested code in the repo before we touch it.

## Links

- `code-reviews/cellpy-file-loading-refactor-plan.md` (Step 0 — this issue implements it)
- `code-reviews/cellpy2-native-headers-migration-plan.md` (Phase 1 tests extend these)
- Depends on Stage 0.1 (fixture convention).

## Acceptance

- `tests/test_cellpy_file_roundtrip.py` green on master; fast subset marked `essential`.
- Every method in the file plan's §1.1 inventory is exercised by at least one test.
