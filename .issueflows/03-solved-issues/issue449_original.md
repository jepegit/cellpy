# Issue #449: Stage 1.4: File-loading — out-of-band redirects, typed errors, `cellpy convert` CLI

Source: https://github.com/jepegit/cellpy/issues/449

## Original issue text

> Part of **Stage 1 — behavior-preserving construction** (see the Stage-1 tracking issue). Stage 0: jepegit/cellpy#439. Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Everything in Stage 1 lands on master with the full suite green; nothing flips user-visible behavior.

## Goal

File plan Steps 6 + 7:

- `batch_helpers.look_up_and_get()` → `cellpy_file.read_table(path, table, max_cycle=…)`
  (deletes the hard-coded `"/CellpyData"`, the duplicated cycle filter, and its
  unclosed-store edge); `_check_cellpy_file()` → `cellpy_file.read_fid_table()` (owns the
  external-path temp copy).
- Typed exceptions: `CorruptCellpyFile(IOError)` replaces the bare
  `Exception("OH MY GOD! ...")`; narrow the blanket `except AttributeError` in `load()`
  that turns any attribute bug into "file version not supported". Import the tree from
  Stage 1.11's conventions module.
- `cellpy convert <old.h5> [<new.h5>]` CLI: thin wrapper around
  `load(accept_old=True)` + `save()` — the one-time upgrade path the legacy-freeze
  decision requires (v<8 files stop being readable in cellpy 2).

## Why

The out-of-band readers are the drift that bites during any format change; the error
handling currently swallows real corruption (file plan §2.5); and the convert CLI must
exist *before* 2.0 messaging tells users to run it.

## Links

- `architecture-plan/cellpy-file-loading-refactor-plan.md` (Steps 6–7, §7.2)
- `architecture-plan/cellpy2-conventions-plan.md` (§1 exception tree)
- `architecture-plan/cellpy2-release-and-branching-plan.md` (§1 support matrix)
- Depends on: Stage 1.3, Stage 1.11.

## Acceptance

- Batch link mode keeps single-table reads (no full `load()` regression — perf test).
- Failure-mode characterization from #429 updated deliberately for the new types.
- `cellpy convert` round-trips a v4 file to v8 on the testdata set.

