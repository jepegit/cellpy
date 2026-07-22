# Plotting backends (formation layout)

## Context

`PlotlyPlotBuilder` had four nearly-copied
`_configure_formation_{1,2,3,4}_rows` methods (~350 lines) that set facet
axis domains/matches/ranges for formation figures. Epic #567 Stage 1 needs
one layout engine before prepare→spec→render (#638).

## Decision

- **Formation layout lives in** `cellpy/plotting/backends/plotly.py`
  (`configure_formation_layout`). `PlotlyPlotBuilder._configure_formation_axes`
  is a thin adapter that computes domains/ranges and calls it.
- **Per-row-count methods are deleted.** Specials stay as parameters/helpers:
  N=1 annotation y; optional `top_row_label` domains; 
  `configure_fullcell_standard_domains` for fullcell 4-row titles.
- **`Backend` protocol** in `backends/base.py`; `PlotlyBackend.render` exists
  for #638. Public `summary_plot` does **not** flip yet.
- **Provisional full-render flag:** env `CELLPY_SUMMARY_PLOTLY_SPEC=1`
  (default off). Layout engine itself is always on.
- **No-formation path** stays on `PlotlyPlotBuilder` until #638.

## Links

- Issues #637, #636; epic #567
- Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md` §3.1
