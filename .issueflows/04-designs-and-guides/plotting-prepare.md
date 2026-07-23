# Plotting prepare (summary)

## Context

`SummaryPlotDataPreparer` lived in `cellpy/utils/plotutils.py` and fed both
plotly and seaborn builders. Epic #567 Stage 1 needs prepare → `FigureSpec` →
backend.render as the only summary path.

## Decision

- **Prepare lives in** `cellpy/plotting/prepare/summary.py`.
  `prepare(ctx, family, config) -> (frame, FigureSpec)`.
- **`SummaryPlotDataPreparer`** moved there (implementation detail); deleted
  from `plotutils`.
- **`FigureSpec.extras`** carries `prepared_data_info` and `render` (plotly
  knobs including precomputed formation / no-formation layout). For the
  matplotlib backend, `summary_plot` also attaches live `config` / `cell` on
  `extras` so seaborn styling knobs remain available without a second prepare.
- **`CellContext`** in `cellpy/plotting/context.py` is the thin cell adapter;
  BatchContext waits for collectors rebase.
- Public `summary_plot` stays in `plotutils` and orchestrates
  context → registry → prepare → `get_backend(backend).render`.

## Links

- Issues #639, #638; epic #567
- Related: `plotting-registry.md`, `plotting-backends.md`
