# Plotting backends (formation layout + render)

## Context

`PlotlyPlotBuilder` had four nearly-copied
`_configure_formation_{1,2,3,4}_rows` methods (~350 lines) that set facet
axis domains/matches/ranges for formation figures. Epic #567 Stage 1 needs
one layout engine and a real prepare→spec→render path for `summary_plot`.

## Decision

- **Formation layout lives in** `cellpy/plotting/backends/plotly.py`
  (`configure_formation_layout`).
- **Per-row-count methods are deleted.** Specials stay as parameters/helpers:
  N=1 annotation y; optional `top_row_label` domains;
  `configure_fullcell_standard_domains` for fullcell 4-row titles.
- **`Backend` protocol** in `backends/base.py`; public interactive
  `summary_plot` calls `PlotlyBackend.render(frame, spec)` (#638).
- **No-formation path** also lives on `PlotlyBackend` (layout knobs come from
  `FigureSpec.extras['render']` produced by prepare).
- **`PlotlyPlotBuilder` deleted.** `CELLPY_SUMMARY_PLOTLY_SPEC` provisional
  dual-path removed — single interactive path.
- **`SeabornPlotBuilder`** remains until #639; it consumes the same prepared
  frame / `prepared_data_info` from prepare.

## Links

- Issues #638, #637, #636; epic #567
- Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md` §3.1
