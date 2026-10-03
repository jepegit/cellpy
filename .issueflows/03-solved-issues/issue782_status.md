# Status: #782 batch live refresh

- [x] Done

## Done

- `Batch.refresh`, `Batch.update(live=True)`, `Batch.poll` in
  `cellpy/batch/facade.py`.
- `tests/test_batch_live.py`: 6 essential tests.
- Docs: `docs/agents/index.md`, root `AGENTS.md`, `incremental-load-protocol.md`
  (#782 section), HISTORY, test registry.

## Notes

- Branch `782-batch-live` stacked on `781-live-poll` (PR #1103).
- Persisting refreshed cells to `.cellpy` left to the caller.

## Remaining

- None. Epic L (#783) code complete pending PR merges #1101 → #1102 → #1103 → #1104.
