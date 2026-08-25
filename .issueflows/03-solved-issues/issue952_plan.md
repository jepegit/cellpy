# Plan: #952 Batch.drop ghost cell

## Goal

After `Batch.drop` (or `drop_cells_marked_bad`) on a loaded batch, the store
must forget the label so `plot` / `summaries` / `report` work without
`update()`. Keep `CellStore.unload` as cache-only eviction.

## Constraints

- `mark_as_bad` stays a session flag only (no silent drop, no `selected` flip).
- `batch.load(..., drop_bad_cells=True)` default unchanged.
- No plot-adapter / collectors rewrite (Epic B).
- Tests that must gate merge: `@pytest.mark.essential`; run via `uv run pytest`.
- Public batch surface note goes in `docs/getting_started/agents.md` (and the
  short AGENTS.md batch bullet if it stays one line).

### Prior art

- `CellStore.unload` — [`cellpy/batch/store.py`](../../cellpy/batch/store.py):
  cache pop only. Keep; do not overload.
- `Batch.drop` / `drop_cells_marked_bad` — [`cellpy/batch/facade.py`](../../cellpy/batch/facade.py):
  pages filter + `unload`. Switch to a real store remove.
- `test_cellstore_is_lazy` — [`tests/test_batch_v3_runner.py`](../../tests/test_batch_v3_runner.py):
  asserts `unload` leaves the label. Extend, do not change that contract.
- `test_mark_as_bad_and_drop` — [`tests/test_batch_v3_facade.py`](../../tests/test_batch_v3_facade.py):
  drops an **unloaded** one-cell batch (empty store). Does not catch the ghost.
- `_finalize` / `drop_bad_cells` — [`batch-load-orchestrator.md`](../04-designs-and-guides/batch-load-orchestrator.md):
  load path already drops then `update()`. Same-session drop is the hole.
- Toolbox: no helper applies. Graph: no `graphify-out/GRAPH_REPORT.md`.

## Approach

1. Add `CellStore.remove(label)`: pop `_cache`, `_loaders`, and the entry in
   `_labels`. Missing label is a no-op (same as `unload`).
2. `Batch.drop` calls `self._store.remove(label)` instead of `unload`. Still
   filters `pages` and clears `_summaries`.
3. Tests:
   - Store: `unload` still keeps the key (reload on next access); `remove`
     drops the key (`label not in store`, `__getitem__` raises).
   - Facade: `Batch.from_cells` with two stub cells that expose `data.summary`
     → `drop` one → `list(b.cells) == b.cell_names`, label gone from `pages`;
     `b.summaries` and `b.report()` do not raise; remaining cell still loaded.
     Building `b.experiment` (adapter) must not `KeyError` — that is the
     `plot()` crash site. Do **not** require a live `b.plot()` in essential
     (plotly / display). Mark both new tests `essential`.
4. Docs: short mark vs drop vs save/reload note in the agents.md batch
   recipe. One subsection on `batch-load-orchestrator.md` so the store
   contract is recorded.

## Files to touch

| Path | Change |
| --- | --- |
| `cellpy/batch/store.py` | Add `remove`. |
| `cellpy/batch/facade.py` | `drop` → `remove`. |
| `tests/test_batch_v3_runner.py` | `remove` vs `unload` essential test. |
| `tests/test_batch_v3_facade.py` | Loaded two-cell drop → summaries/report/adapter. |
| `docs/getting_started/agents.md` | Mark / drop / save recipe. |
| `AGENTS.md` | One-line batch pointer only if it still fits. |
| `.issueflows/04-designs-and-guides/batch-load-orchestrator.md` | Drop vs unload note. |

## Test strategy

```bash
uv run pytest -m essential tests/test_batch_v3_runner.py tests/test_batch_v3_facade.py
```

## Open questions

None — spec already chose `remove` + keep `unload` + docs in agents.md.
