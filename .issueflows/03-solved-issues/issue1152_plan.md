# Issue #1152 plan — skip bad cells in `ica_collector`

## Goal

`ica_collector` / `collect_ica` keeps going when one cell has no usable cycle curve. Name that cell, record it on the collection, and return the cells that did produce dQ/dV. A single-cell `dqdv` call still raises the same `ValueError`.

## Why the error happens

`ica_collector` calls `collect_ica`, which calls `dqdv` per cell. `dqdv` raises

`ValueError: cycle frame is empty. The requested cycle may be missing from the source data.`

when `get_cap` returns no rows for the requested cycles (`cellpy/ica.py`, #971). That is the right failure for one cell. In a batch, `_collect_derivative` lets the exception escape, so one empty cell aborts every other cell.

Two quieter leave-outs already exist and do not name the cell: a requested cycle list with no overlap for that cell, and a `dqdv` frame with height 0. `meta.cells_included` is currently every cell in the batch, including those.

## Constraints

- Single-cell `dqdv` / `dvdq` stay strict. Existing essential tests in `tests/test_ica_api.py` keep raising on an empty frame and on a missing cycle.
- Catch only that empty-frame `ValueError`. A missing-column error, a bad `direction`, or any other exception still aborts.
- Warn with `UserWarning`, same channel as `collect_summaries` (#939). No `print`.
- `dva_collector` / `collect_dva` share `_collect_derivative`, so they get the same skip. Docstrings say so.
- If every cell is left out, return an empty collection and still warn.
- Scope stays on the collector. No change to how `get_cap` decides a frame is empty.

### Prior art

- `collect_summaries` + `_warn_left_out` in `src/cellpy/collect/summary.py`: `UserWarning` names cells that contributed no rows; `meta.cells_included` is the list that remains. Mirror the warning. Leave the summary collector unchanged.
- `CollectionMeta.cells_skipped` in `src/cellpy/collect/collection.py` exists and is unused. Fill it here so the bad labels are on the collection, not only in the warning text.
- `_collect_derivative` in `src/cellpy/collect/ica.py` already `continue`s on no cycle overlap and on an empty curve. Those paths join the named skip.
- Toolbox: nothing in `.issueflows/00-tools/` applies. `graphify-out/` is absent in this worktree.

## Approach

1. In `_collect_derivative`, keep a per-cell result of included vs skipped.
2. On the empty-frame `ValueError`, on no overlapping requested cycles, and on an empty derivative frame: append the cell label to skipped and continue.
3. After the loop, if skipped is non-empty, emit one `UserWarning` that lists the labels (cap the listed names the way `_warn_left_out` does) and says the cell had no cycle curve for this collection.
4. Set `meta.cells_included` to the cells that contributed rows and `meta.cells_skipped` to the left-out labels.
5. Document the skip on `ica_collector`, `dva_collector`, `collect_ica`, and `collect_dva`. Add one sentence beside the `collect_summaries` leave-out note in `docs/agents/index.md` and the matching ICA bullet in `AGENTS.md`.

## Files to touch

- `src/cellpy/collect/ica.py` — catch, warn, set `cells_included` / `cells_skipped`.
- `src/cellpy/collect/collector.py` — docstring on `ica_collector` and `dva_collector`.
- `docs/agents/index.md` and `AGENTS.md` — one sentence each: a bad ICA/DVA cell is named and skipped.
- `tests/test_collect.py` (or `tests/test_collect_ica_options.py` if the fixture fits better) — essential test below.

## Test strategy

`uv run pytest -m essential` on the new test, plus the existing empty-frame `dqdv` tests so the single-cell raise stays.

New essential test, same shape as `test_collect_summaries_warns_about_cells_it_leaves_out`:

- One cell with a real curve, one cell whose `get_cap` returns an empty frame (cycle number may still be listed).
- `collect_ica` warns with the bad label, the frame contains only the good cell, `meta.cells_included` and `meta.cells_skipped` match.
- A healthy batch does not warn.
- Parametrize the same assertion over `collect_dva`, or call both from one test, since they share the helper.

## Open questions

- None. All-cells-bad returns an empty collection plus the warning.
