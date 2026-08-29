# Plan: #950 `mark_as_bad` / `drop_cells_marked_bad` not working

## Goal

Close the gap behind [#950](https://github.com/jepegit/cellpy/issues/950): the
reported `KeyError` crash is already fixed on `master` but unreleased, and the
flow that produced it is still untested. Add the missing regression cover and
remove the remaining reason a user reports this as "not working" — marking or
dropping an unknown label is a completely silent no-op.

## Findings (verified on `master`, not assumed)

1. **The reported crash no longer reproduces.** #952 gave `CellStore` a real
   `remove` and pointed `Batch.drop` at it. Replaying #950's flow (mark three
   cells bad → `drop_cells_marked_bad()` → `summaries` / `experiment` adapter)
   on `master` succeeds for both a loaded store (`Batch.from_cells`) and a lazy
   loader store.
2. **The fix is unreleased.** Latest tag is `v2.1.3.post1`; the #952 bullet sits
   under `## [Unreleased]` in `HISTORY.md`. The reporter's traceback comes from
   `envs/cellpy213`, i.e. 2.1.3 — before the fix. #950 and #952 are the same
   crash seen from different versions.
3. **#950's exact path is untested.** `test_drop_cells_marked_bad`
   (`tests/test_batch.py`) uses a journal-only batch with an empty store and
   asserts `cell_names` only. `test_drop_loaded_cell_forgets_store_label`
   (`tests/test_batch_v3_facade.py`) covers `drop`, not
   `drop_cells_marked_bad`, and does not touch `combine_summaries`. Nothing
   exercises *marked-bad drop on a loaded batch → summaries / plot adapter*, so
   the #952 fix can regress on precisely the reported flow without CI noticing.
4. **A real, still-unfixed defect: silent no-op on an unknown label.**
   `b.mark_as_bad("typo")` accepts any string, warns nothing, and records it in
   `session["bad_cells"]`. `drop_cells_marked_bad()` then skips it (guarded by
   `if label in self.journal.cell_names`) and returns silently — nothing
   dropped, no exception, no warning, no log line. `b.drop("typo")` is likewise
   a silent no-op. With cell names like `20260515_sig002_04_fccc`, a mistyped
   or stale label is the most likely way a user reaches "it does not work"
   without a traceback.
5. **Stale `bad_cells` after a drop is *not* a bug.** Dropped labels stay in
   `session["bad_cells"]` by design: `mark_as_bad` is the persistent record
   that `batch.load(..., drop_bad_cells=True)` replays on the next session.
   Pruning it would break that documented contract.

## Constraints

- `mark_as_bad` stays a session flag: it must not drop, load, or flip
  `selected` (contract set by #952).
- `_finalize` calls `drop_cells_marked_bad()` on **every** `batch.load` with
  `drop_bad_cells=True` (the default). Anything raised from that method breaks
  loading a journal whose `bad_cells` names an already-removed cell, so the
  drop path must stay non-fatal.
- Do not prune `session["bad_cells"]` (finding 5).
- No collectors / plot-adapter rewrite — that stays Epic B.
- New merge-gating tests carry `@pytest.mark.essential` and get rows in
  [test-registry.md](../04-designs-and-guides/test-registry.md).
- Public batch-surface change → update
  [`docs/getting_started/agents.md`](../../docs/getting_started/agents.md) and
  the short root `AGENTS.md` batch bullet in the same PR (#682 convention from
  [this-project.md](../04-designs-and-guides/this-project.md)).
- Test command is `uv run pytest`; no conda.

### Prior art

- `CellStore.remove` / `unload` — [`cellpy/batch/store.py`](../../cellpy/batch/store.py):
  `remove` drops `_cache` / `_loaders` / `_labels`, `unload` is cache-only.
  Both treat a missing label as a no-op. Reuse as is; the new feedback belongs
  in the facade, which knows the journal, not in the store.
- `Batch.drop` / `drop_cells_marked_bad` / `mark_as_bad` —
  [`cellpy/batch/facade.py`](../../cellpy/batch/facade.py): the three call
  sites to change.
- `_finalize` — same file: the load-path caller that forces "warn, never
  raise" on the drop side.
- `summary_collector` unknown-family rejection —
  `collect/collector.py::_family_options`, registered as
  `test_summary_collector_rejects_an_unknown_family` (#927): the codebase
  already raises `ValueError` with a valid-name list for a bad user-supplied
  key. Mirror that shape rather than inventing a new one.
- Anti-silent-failure line of work — #961 (named `env_file` in remote-auth
  errors), #962 (`load` no longer treats a filefinder miss as success),
  and open #938 / #939. This change is the batch-facade instance of the same
  theme; match their wording style (say what happened, name the labels, point
  at what to inspect).
- `warn_once` — [`cellpy/_deprecation.py`](../../cellpy/_deprecation.py): for
  deprecations, not for per-call user feedback. Use a plain `UserWarning` with
  `stacklevel=2`, as `_finalize` does.
- Toolbox: nothing in `.issueflows/00-tools/` applies. Graph: no
  `graphify-out/`, so grep-only.

## Approach

1. **Regression test for the reported flow** (the part that guards #952 on
   #950's exact path): loaded three-cell batch → `mark_as_bad` twice →
   `drop_cells_marked_bad()` → assert `cell_names`, `list(b.cells)` and
   `pages` agree, and that `combine_summaries()` and the `b.experiment`
   adapter (the `plot()` crash site) both succeed. Essential.
2. **Fail fast on the mark side.** `mark_as_bad(label)` raises `ValueError`
   when `label` is not in `journal.cell_names`, naming the label and listing
   the known names (truncated for large batches). This is direct interactive
   user input, it is not on the load path, and nothing downstream benefits
   from flagging a cell that does not exist.
3. **Warn, never raise, on the drop side.** `drop_cells_marked_bad()` emits one
   `UserWarning` naming any `bad_cells` entries it could not drop, and returns
   normally — safe inside `_finalize`. `drop(label)` warns on an unknown label
   for the same reason (it is also called internally).
4. **Record the contract** in
   [batch-load-orchestrator.md](../04-designs-and-guides/batch-load-orchestrator.md),
   next to the existing #952 "same-session `drop` vs `unload`" subsection.
5. **Docs**: one line in the `agents.md` mark/drop recipe and the root
   `AGENTS.md` batch bullet describing the raise-vs-warn split.
6. **`HISTORY.md`**: `[Unreleased]` bullet for #950 at `/iflow-close`. The
   crash itself is already covered by the #952 bullet — do not double-report
   it as a second fix.

## Files to touch

| Path | Change |
| --- | --- |
| `cellpy/batch/facade.py` | `mark_as_bad` raises on unknown label; `drop` / `drop_cells_marked_bad` warn instead of silently skipping. |
| `tests/test_batch_v3_facade.py` | #950 regression (loaded marked-bad drop → summaries + adapter); unknown-label raise / warn tests. |
| `.issueflows/04-designs-and-guides/batch-load-orchestrator.md` | Feedback contract next to the #952 note. |
| `.issueflows/04-designs-and-guides/test-registry.md` | Rows for the new essential tests. |
| `docs/getting_started/agents.md` | Mark / drop recipe gains the error-behaviour line. |
| `AGENTS.md` | Batch bullet, only if it stays short. |
| `HISTORY.md` | `[Unreleased]` bullet (written at close). |

## Test strategy

```bash
uv run pytest tests/test_batch_v3_facade.py tests/test_batch.py -k "drop or mark or bad"
uv run pytest -m essential
```

The second command is the CI Tier-1 merge gate. `test_drop_cells_marked_bad`
(`tests/test_batch.py`) and `test_mark_as_bad_and_drop`
(`tests/test_batch_v3_facade.py`) both mark labels that exist, so step 2 should
leave them green; if either goes red, that is a signal the raise is too strict
and the open question below needs the other answer.

## Open questions

1. **Raise or warn when `mark_as_bad` gets an unknown label?** Recommended:
   **raise `ValueError`** — fail fast on user input (KISS rule), matching the
   `summary_collector` unknown-family precedent, and safe because the load path
   never calls `mark_as_bad`. The alternative (warn, keep recording) is gentler
   for anyone who marks cells before the journal is populated, but it leaves
   the same "nothing happened" ending that this issue is about.
2. **Confirm the crash is really gone for the reporter.** The plan treats the
   `KeyError` as fixed by #952 based on a local replay against `master`. Worth
   asking the reporter to re-run on `master` (or the next release) before #950
   is closed, in case their journal reaches the store through a path the replay
   did not cover.
3. **Scope check:** #949 (`b.plot` ignores `ir=True`) came from the same
   session and the same notebook line as this traceback. Keep it a separate
   issue — it is a plotting-argument bug, not a store/journal one.
