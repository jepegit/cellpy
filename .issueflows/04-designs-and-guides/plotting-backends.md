# Plotting backends (formation layout + render)

## Context

Epic #567 Stage 1 needs one layout engine and prepare→spec→render for
`summary_plot`, with two public backends (`plotly` | `matplotlib`).

## Decision

- **Formation layout lives in** `cellpy/plotting/backends/plotly.py`
  (`configure_formation_layout`).
- **`Backend` protocol** in `backends/base.py`; `get_backend(name)` resolves
  `"plotly"` / `"matplotlib"`.
- **Interactive path:** `PlotlyBackend.render(frame, spec)` (#638).
- **Static path:** `MatplotlibBackend.render(frame, spec)` (#639). Seaborn is
  used only for palette/style/faceting helpers (`relplot`); it is **not** a
  public backend name. `SeabornPlotBuilder` is deleted.
- **Public switch:** `summary_plot(..., backend="plotly"|"matplotlib")`.
  `interactive=` is a `warn_once` alias (removal 2.1).

## Links

- Issues #639, #638, #637, #636; epic #567
- Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md` §3.1
