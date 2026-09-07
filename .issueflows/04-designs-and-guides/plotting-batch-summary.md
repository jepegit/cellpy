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
- **IR + `direction=` (#949):** `ir=True` (plotly default) picks
  `ir_discharge` when `direction="discharge"`, else `ir_charge`. If that
  column is missing, the other IR column is used and a `UserWarning` names
  both. If neither column is in the melted frame, warn and skip the panel
  (no debug-only skip). `ir=False` omits IR even when the columns exist.
  All-NaN values still keep the panel.

## Links

- Issue #658; epic #567; batch plan §4.7.
