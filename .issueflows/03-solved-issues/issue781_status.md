# Status: #781 `live.poll` and retire `processor.py`

- [x] Done

## Done

- `cellpy/utils/live.py`: `poll()` + `PollStatus`.
- `CellpyCell.source_complete` (init + set in `_update_incremental`).
- `cellpy/utils/processor.py` deleted; folder-structure doc updated.
- `tests/test_live_poll.py`: 8 essential tests.
- Docs: `docs/agents/index.md`, `incremental-load-protocol.md` (#781 section),
  HISTORY, test registry.

## Notes

- `batch_core.py` `lstrip` bug: module no longer exists (batch v3) — nothing to fix.
- Branch `781-live-poll` stacked on `164-cell-update` (PR #1102).

## Remaining

- None. #782 (batch live refresh) next.
