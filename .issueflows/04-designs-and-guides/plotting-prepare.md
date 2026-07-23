# Plotting prepare (summary + curves + raw + cycle_info + ica/dva)

## Context

`SummaryPlotDataPreparer` lived in `cellpy/utils/plotutils.py` and fed both
plotly and seaborn builders. Epic #567 Stage 1 needs prepare → `FigureSpec` →
backend.render as the only summary path. Stage 2 extends the same contract to
`cycles_plot` (#646), `raw_plot` / `cycle_info_plot` (#647), then `ica_plot` /
`dva_plot` (#648).

## Decision

- **Summary prepare** lives in `cellpy/plotting/prepare/summary.py`.
  `prepare(ctx, family, config) -> (frame, FigureSpec)`.
- **`SummaryPlotDataPreparer`** moved there (implementation detail); deleted
  from `plotutils`.
- **`FigureSpec.extras`** carries `prepared_data_info` and `render` (plotly
  knobs including precomputed formation / no-formation layout). For the
  matplotlib backend, `summary_plot` also attaches live `config` / `cell` on
  `extras` so seaborn styling knobs remain available without a second prepare.
- **Curves prepare** lives in `cellpy/plotting/prepare/curves.py` (#646).
  Same `(frame, FigureSpec)` contract; `spec.extras["kind"] == "cycles"` plus
  form/rest frames and styling knobs. Curve load seam defaults to
  `c.get_cap` (oracle-stable); `cellpycore.curves` preferred path can land
  later behind `_load_curve_frame`.
- **Raw prepare** lives in `cellpy/plotting/prepare/raw.py` (#647).
  `spec.extras["kind"] == "raw"`; predefined `plot_type` menus and synthetic
  time columns are resolved here. Axis labels use `plotting.labels`
  (`units_quantity_label` / `quantity_label`) against `raw_units`.
- **Cycle-info prepare** lives in `cellpy/plotting/prepare/steps.py` (#647).
  `spec.extras["kind"] == "cycle_info"`. Plotly path emits a merged scaled
  frame; matplotlib keeps the single-cycle asymmetry and stashes the step
  table on `extras["steps"]`.
- **ICA/DVA prepare** lives in `cellpy/plotting/prepare/ica.py` (#648).
  Calls `cellpy.ica.dqdv` / `dvdq` only (never `Converter` / `to_wide`).
  `kind` is `"ica"` or `"dva"`; drops deprecated `dq` column from the plotting
  frame. When `direction="both"`, both halves stay on one figure; backends draw
  one series per `(cycle, direction)` with cycle-keyed colour and shared line
  style (plotly hover carries `direction`).
- **`LiveHeaders`** lives in `cellpy/plotting/headers.py` (re-exported as
  `plotutils._LiveHeaders`).
- **`CellContext`** in `cellpy/plotting/context.py` is the thin cell adapter.
  Collected multi-cell frames use **`FrameContext`** / **`collected_plot`**
  (`layout=` / `kind=`) — see `plotting-collected.md` (#657).
- Public `summary_plot` / `cycles_plot` / `raw_plot` / `cycle_info_plot` /
  `ica_plot` / `dva_plot` stay in `plotutils` and orchestrate context →
  registry → prepare → `get_backend(backend).render`.

## Links

- Issues #648, #647, #646, #639, #638; epic #567
- Related: `plotting-registry.md`, `plotting-backends.md`
