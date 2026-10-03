# Plan: #781 `live.poll` and retire `processor.py`

Autonomous run under #783 (user: "process the issues").

1. `cellpy/utils/live.py`: `poll(cell_or_path, interval=30, on_update=None,
   stop_when_complete=True, until=None, max_polls=None, timeout=None,
   raise_errors=False, sleep=time.sleep, **get_kwargs)`; returns the cell;
   run bookkeeping in `PollStatus` on `cell.poll_status`.
2. `CellpyCell.source_complete` set from `IncrementalChunk.complete` in
   `_update_incremental` so `stop_when_complete` has a signal.
3. `git rm cellpy/utils/processor.py`; `batch.runner` already provides the
   threads executor. `utils/batch_tools/` no longer exists → no `lstrip` fix.
4. Tests `tests/test_live_poll.py` with a fake clock that grows the file.
5. Docs: folder-structure page, `docs/agents/index.md`, design doc section,
   HISTORY, test registry.
