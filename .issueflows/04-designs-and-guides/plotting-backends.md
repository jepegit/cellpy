# Plotting backends (formation layout + render)

## Context

Epic #567 Stage 1 needs one layout engine and prepare→spec→render for
`summary_plot`, with two public backends (`plotly` | `matplotlib`). Stage 2
adds further render branches for `cycles_plot` (#646), `raw_plot` /
`cycle_info_plot` (#647), and `ica_plot` / `dva_plot` (#648).

## Decision

- **Formation layout lives in** `cellpy/plotting/backends/plotly.py`
  (`configure_formation_layout`).
- **`Backend` protocol** in `backends/base.py`; `get_backend(name)` resolves
  `"plotly"` / `"matplotlib"`.
- **Interactive path:** `PlotlyBackend.render(frame, spec)` (#638).
- **Static path:** `MatplotlibBackend.render(frame, spec)` (#639). Seaborn is
  used only for palette/style/faceting helpers (`relplot`); it is **not** a
  public backend name. `SeabornPlotBuilder` is deleted.
- **Public switch:** `summary_plot(..., backend="plotly"|"matplotlib")`,
  `cycles_plot(..., backend=...)`, `raw_plot(..., backend=...)`,
  `cycle_info_plot(..., backend=...)`, `ica_plot(..., backend=...)`,
  `dva_plot(..., backend=...)`. `interactive=` is a `warn_once` alias
  (removal 2.1) on all of them.
- **Family dispatch:** `spec.extras.get("kind")` selects the render branch:
  - `"cycles"` — voltage–capacity (#646)
  - `"raw"` — raw time-series (#647)
  - `"cycle_info"` — raw + step annotations (#647; matplotlib single-cycle)
  - `"ica"` / `"dva"` — dQ/dV vs V / dV/dQ vs capacity (#648); one trace per
    `(cycle, direction)`, cycle colour, shared linestyle; plotly hover shows
    direction. Cycle colour key uses
    `cellpy.plotting.cycle_legend.resolve_cycle_legend_mode` (legend if
    ≤8 cycles, else colorbar; overridable via `legend_cycle_limit` /
    `force_colorbar` / `force_legend`).
  - otherwise — summary path

## Links

- Issues #648, #647, #646, #639, #638, #637, #636; epic #567
- Plan of record: `cellpy-design-and-development/archive/redesigns/cellpy2-plotting-redesign-plan.md` §3.1
