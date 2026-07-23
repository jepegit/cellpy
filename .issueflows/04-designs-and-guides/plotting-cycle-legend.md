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

## Links

- Issue #648, epic #567
