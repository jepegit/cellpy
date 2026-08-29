# Status: #950 `mark_as_bad` / `drop_cells_marked_bad` not working

- [x] Done

## What's done

- Plan accepted 2026-08-29 (see [issue950_plan.md](issue950_plan.md)).
- **Verified the reported crash is already fixed on `master`** by #952 and
  merely unreleased (latest tag `v2.1.3.post1`; the reporter ran 2.1.3).
  Replaying the issue's flow against `master` succeeds for a loaded store and
  for a lazy loader store.
- `Batch.mark_as_bad` raises `ValueError` for a label that is not in
  `journal.cell_names`, naming the known cells.
- `Batch.drop` warns (`UserWarning`) and no-ops for an unknown label instead of
  silently doing nothing.
- Regression test for #950's exact path: loaded batch → two `mark_as_bad` →
  `drop_cells_marked_bad()` → `combine_summaries()` and the `b.experiment`
  adapter (the `plot()` crash site). This path had **no** coverage before:
  `test_drop_cells_marked_bad` used a journal-only batch with an empty store,
  and `test_drop_loaded_cell_forgets_store_label` covers `drop`, not
  `drop_cells_marked_bad`.
- Tests for the unknown-label raise/warn and for the quiet-reload case.
- Docs: `docs/getting_started/agents.md` drop recipe, root `AGENTS.md` batch
  bullet, feedback contract in
  [batch-load-orchestrator.md](../04-designs-and-guides/batch-load-orchestrator.md),
  two rows in [test-registry.md](../04-designs-and-guides/test-registry.md).
- `MPLBACKEND=Agg uv run pytest -m essential`: 781 passed, 58 skipped.

## Deviation from the plan

The plan had `drop_cells_marked_bad()` warn about `bad_cells` entries it could
not drop. **Dropped** during implementation after checking the round-trip:
`write_journal` persists `session`, so a cell dropped in one session is still
listed in `bad_cells` after `save()` + reload, and `_finalize` calls
`drop_cells_marked_bad()` on **every** `batch.load`. That warning would have
fired on a completely normal round-trip (verified: reloaded journal has
`bad_cells == ["gone"]` with `gone` absent from pages). Rejecting unknown
labels in `mark_as_bad` closes the hole at the source instead, so the drop path
stays quiet. `test_drop_cells_marked_bad_is_quiet_about_already_dropped_cells`
pins this.

- `MPLBACKEND=Agg uv run pytest` (full suite, `--extra batch`): 1737 passed,
  17 skipped, 15 xfailed, 1 xpassed.
- `HISTORY.md` bullet under `## [Unreleased]`.

## Remaining work

- None. The reporter is worth asking to re-confirm on the next release, since
  their crash was fixed by #952 rather than by this PR.

## Notes

- `session["bad_cells"]` is deliberately not pruned on a successful drop — it
  is the record a later `load(drop_bad_cells=True)` replays.
- The environment needed `unixodbc` (`libodbc.so.2`) installed before
  `pytest -m essential` could even collect `test_arbin_variants_two_stage.py`.
  GitHub runners ship it; this cloud VM did not. Unrelated to this issue, but
  it is the same class of problem as open issue #938.
