# Plotting backends (formation layout + render)

## Context

Epic #567 Stage 1 needs one layout engine and prepare→spec→render for
`summary_plot`, with two public backends (`plotly` | `matplotlib`). Stage 2
(#646) adds a second render branch for `cycles_plot`.

## Decision

- **Formation layout lives in** `cellpy/plotting/backends/plotly.py`
  (`configure_formation_layout`).
- **`Backend` protocol** in `backends/base.py`; `get_backend(name)` resolves
  `"plotly"` / `"matplotlib"`.
- **Interactive path:** `PlotlyBackend.render(frame, spec)` (#638).
- **Static path:** `MatplotlibBackend.render(frame, spec)` (#639). Seaborn is
  used only for palette/style/faceting helpers (`relplot`); it is **not** a
  public backend name. `SeabornPlotBuilder` is deleted.
- **Public switch:** `summary_plot(..., backend="plotly"|"matplotlib")` and
  `cycles_plot(..., backend=...)`. `interactive=` is a `warn_once` alias
  (removal 2.1) on both.
- **Family dispatch (#646):** when `spec.extras.get("kind") == "cycles"`,
  both backends take the voltage–capacity render path (ported from the old
  private `_cycles_plotter_*` helpers). Otherwise they keep the summary path.

## Links

- Issues #646, #639, #638, #637, #636; epic #567
- Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md` §3.1
