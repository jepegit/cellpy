# Issue #804: Per-panel y-limits (and clearer share_y) for collected summary facet plots

Source: https://github.com/jepegit/cellpy/issues/804

## Original issue text

## Problem / context

Collected summary plots facet variables (capacity, CE, …) with `_cycles_plotter(match_axes=True)` by default, so all rows share one y-scale. CE outliers (~1e6) crush other panels. Downstream apps (e.g. cellpy-simple-gui) need independent auto-scale and per-panel fixed limits.

`match_axes=False` already unmatches axes. `AxisSpec.range` / `PanelSpec.y_axis` exist, and some render paths have `y_range` / `ce_range`, but there is no clear, documented API to set **per-facet-row** y-limits on the collected summary path and have the Plotly backend apply them reliably.

**Companion (cellpy-simple-gui):** https://github.com/cellpy/cellpy-simple-gui/issues/2

## Spec

- Document and stabilize `match_axes` / `share_y` for summary facets (independent vs shared).
- Support per-panel (per-variable) y-range on collected summary figures end-to-end (spec → backend), not only a single global `y_range`.
- Prefer keeping auto-range per panel when limits are omitted.

## Acceptance criteria

- [ ] Public API (kwargs or FigureSpec/PanelSpec) can set independent y-scales for summary facets.
- [ ] Public API can set per-panel y-limits; Plotly (and ideally MPL) honor them.
- [ ] Tests cover shared vs independent and per-panel range application.
- [ ] Docs/examples show Capacity+CE with a CE limit or independent scales.

## Context

Requested while improving cellpy-simple-gui summary plotting.
