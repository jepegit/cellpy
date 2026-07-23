# Issue #658: Wire `Batch.plot()` to plotting and delete `batch_plotters.py`

Source: https://github.com/jepegit/cellpy/issues/658

## Original issue text

## Context

Part of epic #567 (Stage 3 — Collectors drawing half, Batch.plot, retire batch_plotters). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md` (batch redesign §4.7). Closes the epic acceptance criteria together with #657: one drawing home, batch facade unchanged, `batch_plotters.py` gone.

## Scope

Change `Batch.plot()` to delegate to `cellpy.plotting.summary_plot` (or equivalent) with the tidy summaries frame; preserve user-visible defaults where possible (plotly primary; capacity specifics; CE/IR/rate panels). Delete `cellpy/utils/batch_tools/batch_plotters.py` and remove imports/wiring from `batch.py` / farm machinery. Map obsolete backends (`bokeh`, bare `seaborn`) to clear errors or deprecated aliases pointing at `backend=`. Extend the figure-spec snapshot with at least one batch-input summary case that covers what `batch_plotters` used to produce. DEPRECATIONS/migration docs mention the backend triage.

## Acceptance

- `Batch.plot()` produces oracle-matching summary figures without importing `batch_plotters`.
- The module file is gone; no remaining in-tree imports of it.
- DEPRECATIONS/migration docs mention the backend triage.

## Depends on

#657

Part of epic #567.
