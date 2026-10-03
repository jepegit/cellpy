# Plan: #949 `b.plot` IR panel (re-open)

## Goal

`b.plot(rate=True, ir=True, direction=…)` shows an IR panel when the batch
summaries have IR, for both charge and discharge. If they do not, the user
sees a clear warning — not a silent missing facet. Then close GitHub #949.

## Constraints

- Stay in `cellpy.plotting.batch_summary` and the `Batch.plot` / facade farm
  path. Do not rebase onto collectors / `collected_plot`.
- Do not change `make_summary(find_ir=…)` defaults unless reproduction proves
  that default is why 2.1.4 still has no panel (see open question 1).
- First-pass pick/fallback stays; this pass finds why 2.1.4 still fails.
- Docs-on-master; `HISTORY.md` Unreleased only at `/iflow-close`.
- `uv run` toolchain. No conda for pytest.

### Prior art

- First pass (archived under `03-solved-issues/issue949_*`, shipped in 2.1.4):
  [`cellpy/plotting/batch_summary.py`](../../cellpy/plotting/batch_summary.py)
  `_select_ir_column` / `_pick_optional_summary`; tests in
  [`tests/test_batch_summary_ir.py`](../../tests/test_batch_summary_ir.py);
  decision in
  [plotting-batch-summary.md](../04-designs-and-guides/plotting-batch-summary.md).
- Facade farms: [`cellpy/batch/facade.py`](../../cellpy/batch/facade.py)
  `_LegacyExperimentAdapter` dumps every summary variable (including IR if
  present) into `memory_dumped["summary_engine"]`.
- `make_summary(find_ir=False)` vs load `find_ir=True`
  ([`cellreader.py`](../../cellpy/readers/cellreader.py)).
- Toolbox: no IR/plot helper in `00-tools/`. Graph: `graphify-out/` absent
  in this worktree.

## Approach

1. Reproduce through the real path, not only `_frame()`:
   load example / test batch cells, inspect `b.summaries` and farm names for
   `ir_charge` / `ir_discharge`, then `b.plot(ir=True, direction=…)` for both
   directions. Record whether the skip warning fires.
2. Branch on evidence:
   - **IR columns in summary, missing on figure** — plotter/frame filter bug
     (name mismatch, melt, all-NaN drop). Fix in `batch_summary.py`; add a
     test that builds farms like the facade, not only synthetic `_farms`.
   - **No IR columns in summary** — document + keep the skip warning; if
     default `make_summary(find_ir=False)` is the cause of a normal `b.update`
     path, fix that path only (do not flip the public `make_summary` default
     without the open-question yes).
   - **Already works on master** — add the facade-farm test if missing, comment
     on #949, close with `Closes #949`.
3. Update `plotting-batch-summary.md` only if behaviour changes.

## Files to touch

- `cellpy/plotting/batch_summary.py` — only if a plotter/frame bug remains.
- `cellpy/batch/facade.py` — only if farms drop IR.
- `tests/test_batch_summary_ir.py` — facade-farm / `Batch.plot` coverage.
- `.issueflows/04-designs-and-guides/plotting-batch-summary.md` — if behaviour changes.
- `HISTORY.md` — close step.

## Test strategy

- Execute a snippet: example or test-batch cells → `b.plot(ir=True)` both
  directions (`uv run`).
- New/updated essential tests for the path that actually failed.
- `uv run pytest tests/test_batch_summary_ir.py -m essential` then
  `uv run pytest -m essential`.

## Open questions

1. **If summaries lack IR because `make_summary(find_ir=False)`**, flip that
   default / the batch update path? Recommended: **no** unless the default
   load/`update` path is the one dropping IR. Prefer a targeted batch path
   or a clearer warning (“summary has no IR — remake with `find_ir=True`”).
2. **Close GitHub if master already plots IR** and 2.1.4 was just the first
   fix not noticed? Recommended: **yes**, after the facade-farm test and a
   comment pointing at 2.1.4+ / current master.
