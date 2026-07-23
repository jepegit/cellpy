# Plotting prepare (summary)

## Context

`SummaryPlotDataPreparer` lived in `cellpy/utils/plotutils.py` and fed both
`PlotlyPlotBuilder` and `SeabornPlotBuilder`. Epic #567 Stage 1 needs
prepare → `FigureSpec` → backend.render as the only summary path.

## Decision

- **Prepare lives in** `cellpy/plotting/prepare/summary.py`.
  `prepare(ctx, family, config) -> (frame, FigureSpec)`.
- **`SummaryPlotDataPreparer`** moved there (implementation detail); deleted
  from `plotutils`.
- **`FigureSpec.extras`** carries `prepared_data_info` (seaborn bridge) and
  `render` (plotly knobs including precomputed formation / no-formation
  layout). First-class panel/axis fields grow as later issues need them.
- **`CellContext`** in `cellpy/plotting/context.py` is the thin cell adapter;
  BatchContext waits for collectors rebase.
- Public `summary_plot` stays in `plotutils` but only orchestrates
  context → registry → prepare → render.

## Links

- Issue #638; epic #567
- Related: `plotting-registry.md`, `plotting-backends.md`
