# Issue #668 — Plan (v2: remaining `NullData` after #670)

Supersedes the #670 plan (cycle_index + nested `cycle_mode`). Those fixes shipped
in [PR #670](https://github.com/jepegit/cellpy/pull/670). This plan covers the
**post-merge** failure only.

## Goal

Make `b.plot(...)` succeed (or fail with an actionable error) on `v1.x` when the
batch has been loaded via the standard template — specifically eliminate
`NullData: No summaries available to join` from `summary_collector` /
`join_summaries`.

## Constraints

- **Target branch:** `v1.x` (`v1x` label). PR against `v1.x`, not `master`.
- **Branch:** `668-batch-summaries` (from `origin/v1.x`).
- Fixes-only on `v1.x` — no batch redesign, no `cellpycore` pin bump unless proven
  necessary (durable `cycle_mode` hardening stays on
  [cellpy-core#142](https://github.com/cellpy/cellpy-core/issues/142)).
- Do not change public `Batch.plot` / journal API.
- Keep #670 regressions green (`tests/test_issue668_batch_bugs.py`).

### Prior art

- **`summary_engine` / `_load_summaries`** —
  [`cellpy/utils/batch_tools/engines.py`](../../cellpy/utils/batch_tools/engines.py):
  on `reset=True` (always used by `Batch.plot` when `summary_engine` not in
  `memory_dumped`), **discards** `experiment.summary_frames` and rebuilds from
  `experiment.data[label].data.summary` for each `cell_names` entry.
- **`join_summaries`** —
  [`cellpy/utils/batch_tools/batch_helpers.py`](../../cellpy/utils/batch_tools/batch_helpers.py):
  `NullData("No summaries available to join")` only when `summary_frames` is
  falsy (empty dict / None) — **not** when frames exist but are empty DataFrames.
- **`CyclingExperiment.update`** —
  [`batch_experiments.py`](../../cellpy/utils/batch_tools/batch_experiments.py):
  fills `self.summary_frames` with real summaries; with default
  `all_in_memory=False` stores **stubs** in `cell_data_frames` (steps only).
  Lazy reload via `Data.__look_up__` needs a readable cellpy file.
- **`cell_names`** — keys of `cell_data_frames` only (not journal pages). Empty
  `cell_data_frames` → `_load_summaries` → `{}` → exact `NullData` seen in the
  issue comment.
- **#670** — index-name + `cycle_mode` unwrap; did **not** touch engines /
  summary_collector. Original KeyError path implied collector once succeeded.
- Toolbox / graphify: nothing specific for this collector path.

## Approach

### 0. Diagnose (read-only / small repro) before coding the fix

Reproduce on `668-batch-summaries` with the loader-notebook sequence (or a minimal
batch fixture). Record:

| Probe | Implication if true |
|-------|---------------------|
| `b.experiment.cell_names` empty / `cell_data_frames == {}` | Never updated, or all cells failed load → UX / load errors, not plotter |
| `summary_frames` from `update` non-empty, but `reset=True` reload yields `{}` | Collector discards good cache; stubs + failed look-up |
| Cells present, summaries empty after look-up | File/link/`save_cellpy` path; improve `_load_summaries` fallback |
| Plot called before `update` | Clearer error; optional doc note in template |

Primary hypothesis to confirm/falsify: **`plot` → `summary_collector.do(reset=True)`
throws away `update()`'s `summary_frames` and rebuilds from stub cells; when
look-up cannot restore summaries (or `cell_names` is empty), join raises
`NullData`.**

### 1. Fix (choose after diagnose; prefer smallest)

**Likely fix A — prefer cached frames on reset (recommended if hypothesis holds):**

In `summary_engine` / `_load_summaries`:

- If `experiment.summary_frames` already has non-empty entries, **reuse** them on
  `reset` unless an explicit force-reload flag is set (or only rebuild missing
  labels).
- Else load from `experiment.data[label].data.summary` as today.
- If still empty: raise `NullData` with a message that distinguishes
  “no cells loaded (`cell_names` empty — run `b.update()`)” vs
  “cells present but no summary tables”.

**Likely fix B — harden `_load_summaries` only:**

- Iterate journal page index (or `cell_names`), lazy-load via `.data[label]`,
  and fall back to `experiment.summary_frames[label]` when the in-memory cell
  summary is missing/empty.
- Same clearer `NullData` text.

Do **not** do both large redesigns; pick A or B after the probe table.

### 2. Tests

Extend `tests/test_issue668_batch_bugs.py` (keep `@pytest.mark.essential`):

- Stub experiment mimicking post-`update` / `all_in_memory=False`:
  `summary_frames` populated, `cell_data_frames` stubs without summaries →
  `summary_engine(..., reset=True)` must still produce joinable farms (or the
  chosen fallback behaviour).
- Empty `cell_names` → `NullData` message mentions update / no cells (not a
  vague join failure).
- Keep existing #670 tests green.

### 3. Out of scope

- cellpy-core#142 bridge hardening.
- master / `cellpy.plotting` (already on #658 path).
- Full batch redesign / collectors v3.

## Files to touch

| Path | Change |
|------|--------|
| [`cellpy/utils/batch_tools/engines.py`](../../cellpy/utils/batch_tools/engines.py) | Reuse / fallback summary frames; clearer empty case |
| [`cellpy/utils/batch_tools/batch_helpers.py`](../../cellpy/utils/batch_tools/batch_helpers.py) | Optional: richer `NullData` message only if raised here |
| [`tests/test_issue668_batch_bugs.py`](../../tests/test_issue668_batch_bugs.py) | New collector / stub-memory cases |
| `HISTORY.md` | Unreleased bullet for the follow-up fix |

## Test strategy

```bash
uv run pytest -m essential
uv run pytest tests/test_issue668_batch_bugs.py -q
```

(On this machine, conda `cellpy_dev_313` is also fine if that is the usual v1.x env — match whatever the branch already uses.)

## Open questions

_All resolved 2026-07-25 — plan **Accepted** with defaults._

1. **Notebook probes:** none provided — diagnose during `/iflow-build` via
   unit repro (stub `all_in_memory=False` experiment) instead of waiting on
   a live notebook session.
2. **Force-reload semantics:** **yes** — `Batch.plot(reload_data=True)` /
   hard reset rebuilds from cells/files; plain first plot / soft `reset`
   reuses non-empty cached `experiment.summary_frames` (Fix A).
3. **Plan file:** replace #670 plan in place — confirmed.

## Status

- **Confirmed:** 2026-07-25
- **Next:** `/iflow-build` (implement Fix A + tests)
