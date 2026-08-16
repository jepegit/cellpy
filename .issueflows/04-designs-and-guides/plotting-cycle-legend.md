# Cycle legend vs colorbar

## Context

Multi-cycle figures (ICA/DVA #648, and likely `cycles_plot` later) colour by
cycle. A discrete legend overflows once there are many cycles.

## Decision

Shared policy in `cellpy/plotting/cycle_legend.py`:

- `resolve_cycle_legend_mode(n)` → `"legend"` if `n ≤ 8`, else `"colorbar"`
- Overrides: `legend_cycle_limit`, `force_colorbar`, `force_legend`
  (`force_nonbar` alias)
- Backend helpers: `add_matplotlib_cycle_colorbar`, `add_plotly_cycle_colorbar`

First consumer: `ica_plot` / `dva_plot` render branches. `cycles_plot` still
has its own threshold constant; can migrate later.

Second consumer (#928): the **collected** per-cell layouts
(`sequence_plotter`, `method="fig_pr_cell"` — reached by
`cycles_collector(b).plot(layout="per_cell")` and the ICA/DVA line paths).
`pop_cycle_legend_options(None, kwargs)` runs once near the top of
`sequence_plotter`, so the knobs are consumed whatever the method and never
leak into `px.line`. In colorbar mode the per-cycle trace colours are kept,
every trace gets `showlegend=False`, and `add_plotly_cycle_colorbar` adds the
scale widget. A non-numeric cycle column falls back to the legend rather than
raising.

## Links

- Issue #648, epic #567
- Issue #928 (collected per-cell layouts) — see `plotting-collected.md`
