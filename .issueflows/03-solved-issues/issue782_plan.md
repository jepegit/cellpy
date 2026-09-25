# Plan: #782 batch live refresh

Autonomous run under #783 (user: "process the issues").

1. `Batch.refresh(labels=None, raise_errors=False, **update_kwargs)` →
   `{label: changed | Exception}` over loaded cells; clears summary cache on
   change.
2. `Batch.update(live=True, **kw)` delegates to `refresh` and returns the
   existing `BatchResult` (no reload).
3. `Batch.poll(interval, on_update, until, max_polls, timeout,
   stop_when_complete, raise_errors, sleep, **update_kwargs)` reusing
   `cellpy.utils.live.PollStatus`; on change rebuild `summaries`, recompute
   `report()` → `last_report`, call `on_update(batch, outcome)`.
4. Tests `tests/test_batch_live.py` on a `from_cells` batch of two truncated
   neware copies.
5. Docs: `docs/agents/index.md`, root `AGENTS.md`, design doc section,
   HISTORY, registry.
