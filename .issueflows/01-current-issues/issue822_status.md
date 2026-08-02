# Status — #822

- [ ] Done

## Notes

Implemented orchestrated `cellpy.batch.load` per confirmed grill plan.

- Helpers: `_resolve_policy`, `_persist_cells`, `_journal_path`, `Batch.drop_cells_marked_bad`
- Shim `utils.batch.load` forwards to facade orchestrator
- Essential + load tests green
- Design note: `.issueflows/04-designs-and-guides/batch-load-orchestrator.md`
- Also restored `_LegacyExperimentAdapter` farm layout for plotter

## Remaining

Close via `/iflow-close` (HISTORY/PR merge) when ready.
