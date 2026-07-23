# Plotting registry (`PlotFamily`)

## Context

Named `summary_plot(y=...)` sets used to live as an inline column table in
`SummaryPlotInfo._create_col_info` (`cellpy/utils/plotutils.py`). Epic #567
moves selection into `cellpy.plotting.registry`.

## Decision

- **One registry** of frozen `PlotFamily` records in
  `cellpy/plotting/registry.py`. Column names stay header-bound via
  `column_builder(hdr)`.
- **Unknown `y` fails loudly** (`ValueError` listing known names). Undocumented
  raw-column fallthrough (`y_cols.get(y, y)`) is gone; extension is
  `_register_family` (provisional in 2.0).
- **`FigureSpec` / `PanelSpec` / `AxisSpec`** live in `cellpy/plotting/spec.py`.
  Prepare emits a real `FigureSpec` for `summary_plot` (#638); matplotlib
  backend consumption is #639.
- **Oracle menu** (`tests/figure_spec_support.SUMMARY_FAMILIES`) derives from
  `families(entry_point="summary_plot")` so the snapshot menu cannot drift
  from the runtime menu. Non-summary families register with
  `extras={"entry_point": "..."}` and are excluded from the summary oracle:
  `"cycles"` (`cycles_plot`, #646), `"raw"` / `"cycle_info"` (#647).

## Alternatives considered

- Keep raw-column fallthrough when `y` exists on the summary frame — rejected
  for this issue's acceptance criterion; can revisit if a real caller needs it.
- Populate `PlotFamily.panels` fully now — deferred to #638 when prepare emits
  a real `FigureSpec`.

## Links

- Issue #636, epic #567
- Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md` §3.2
