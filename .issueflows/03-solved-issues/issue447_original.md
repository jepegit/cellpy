# Issue #447: Stage 1.2: File-loading — stateless helpers out, selector/limits side-channel dead

Source: https://github.com/jepegit/cellpy/issues/447

## Original issue text

> Part of **Stage 1 — behavior-preserving construction** (see the Stage-1 tracking issue). Stage 0: jepegit/cellpy#439. Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos). Everything in Stage 1 lands on master with the full suite green; nothing flips user-visible behavior.

## Goal

File plan Steps 2 + 3 (separate commits, one issue):

1. Move the stateless helpers verbatim into `cellpy_file/` (`_check_keys_in_cellpy_file`,
   `_extract_from_meta_dictionary`, `_convert2fid_list/table`, `_get_cellpy_file_version`,
   `_fix_dtype_step_table`), leaving one-line delegating methods behind.
2. Introduce `LoadSelector` / `LoadResult` and rewrite `_hdf5_cycle_filter` +
   `_extract_summary/raw/steps_from_cellpy_file` to take an explicit selector and
   **return** limits instead of writing `self.limit_*` — killing the hidden-mutable-state
   channel where extraction order (summary before raw/steps) is load-bearing and a
   selector leaks between loads on the same instance.

## Why

Step 3 is "the riskiest, most valuable step" of the file plan (§4): it must be
done while the code still sits inside the class, guarded by the Stage-0 selector
characterization tests (#429). Every later move (Stage 1.3) is cut-paste once state is
explicit.

## Links

- `architecture-plan/cellpy-file-loading-refactor-plan.md` (Steps 2–3, §2.2, §3.2)
- Depends on: #429; Stage 1.1; **Stage 1.5 (units Phase 1) should land first** — it
  renames the `core` alias across cellreader.py, and interleaving that with code moves
  makes rebasing miserable (sequencing row in both plans).

## Acceptance

- Suite green after each of the two commits; selector tests from #429 pass unchanged.
- `grep "self.limit_loaded_cycles\|self.limit_data_points" cellpy/readers/cellreader.py`
  shows only the assignment in `load()` from the returned result.

