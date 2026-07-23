# Batch cycle-life summary plotting (#658)

## Context

Epic #567 Stage 3 closes with `Batch.plot` delegating into `cellpy.plotting`
and deleting `batch_plotters.py`.

## Decision

- Home: `cellpy.plotting.batch_summary` (`batch_summary_plot`).
- Not single-cell `summary_plot` / not `collected_plot` — Batch cycle-life is
  a multi-panel CE/capacity/IR/rate figure with its own frame melt.
- Backends: `plotly` | `matplotlib`. `seaborn` → `warn_once` → matplotlib;
  `bokeh` → hard error.
- Facade: thin `_BatchPlotterHolder` keeps `b.plotter.figure` / `.farms`.
- Frame prep names an unnamed summary index `cycle_index` before `reset_index`
  (join_summaries farms often leave the index unnamed).

## Links

- Issue #658; epic #567; batch plan §4.7.
