# Issue #952: Batch.drop leaves a ghost cell in the store so plot and summaries raise KeyError

Source: https://github.com/jepegit/cellpy/issues/952

## Original issue text

### Problem / context

`Batch.mark_as_bad(label)` only appends to `journal.session["bad_cells"]`. The cell stays in `pages`, the store, and plots.

`Batch.drop(label)` (and `drop_cells_marked_bad`) removes the row from `pages` and calls `CellStore.unload(label)`, then clears the cached summaries. `unload` only evicts the cache. The label stays in `_labels` (and `_loaders` if present).

After a user drops a cell on an already-loaded batch and then calls `b.plot()`, `_LegacyExperimentAdapter` iterates `store.items()` and raises `KeyError` for the ghost label. Same crash on `b.summaries`, `b.combine_summaries()`, and `b.report()`.

`b.cell_names` / `b.pages` omit the cell; `list(b.cells)` can still include it. `update()` rebuilds the store and hides the bug. `batch.load(..., drop_bad_cells=True)` is safe because it drops **then** updates. Same-session `drop` → `plot` is not.

`unload` should stay cache-only (reload next access). `drop` needs a real remove.

### Spec

1. Add `CellStore.remove(label)` (or equivalent) that drops the label from `_labels`, `_cache`, and `_loaders`. Keep `unload` as cache eviction.
2. `Batch.drop` must call that remove, not `unload`.
3. After `drop` on a loaded batch, `plot()`, `.summaries`, `combine_summaries()`, and `report()` work without `update()`. Remaining cells stay loaded.
4. Tests: loaded multi-cell batch → `drop` one label → store keys / `cell_names` / `pages` agree; `summaries` and `report()` do not raise; ghost label is gone. Mark `essential`.
5. Short user note (batch tutorial or `docs/getting_started/agents.md`):
   - `mark_as_bad` is a session flag; `drop` / `drop_cells_marked_bad` removes now.
   - After mark, `save()` then next `batch.load()` (default `drop_bad_cells=True`) drops before update.
   - After same-session `drop`, plot/summaries should work immediately; `save()` still needed to persist the journal.

### Acceptance criteria

- [ ] `b.drop(label)` on a loaded batch: label gone from `pages`, `cell_names`, and `list(b.cells)`.
- [ ] `b.plot()`, `b.summaries`, and `b.report()` after that drop do not raise `KeyError`.
- [ ] `CellStore.unload` still only evicts cache (label remains, next access reloads).
- [ ] `mark_as_bad` still only writes `session["bad_cells"]` (no silent drop).
- [ ] Essential test covers the drop-then-summaries/report path.
- [ ] User-facing note documents mark vs drop and the save/reload path.

### Out of scope

- Changing `batch.load` defaults (`drop_bad_cells=True`).
- Making `mark_as_bad` auto-drop or flip `selected`.
- Rewriting the plot adapter / collectors (Epic B).
- Migrating remaining `experiment` shims.
