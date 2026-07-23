# Plotting prepare (summary + curves)

## Context

`SummaryPlotDataPreparer` lived in `cellpy/utils/plotutils.py` and fed both
plotly and seaborn builders. Epic #567 Stage 1 needs prepare → `FigureSpec` →
backend.render as the only summary path. Stage 2 (#646) extends the same
contract to `cycles_plot`.

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
- **`CellContext`** in `cellpy/plotting/context.py` is the thin cell adapter;
  BatchContext waits for collectors rebase.
- Public `summary_plot` / `cycles_plot` stay in `plotutils` and orchestrate
  context → registry → prepare → `get_backend(backend).render`.

## Links

- Issues #646, #639, #638; epic #567
- Related: `plotting-registry.md`, `plotting-backends.md`
