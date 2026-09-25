# Issue #1096 — plan

## Goal

`cap_summaries.plot()` should not grow a second "Direction" legend, and the
lines should stay solid, when a panel shows only charge or only discharge.
Dash (and that legend) stay for a panel that actually draws both.

## Constraints

- Keep #1009 panel merging: `charge_capacity_*` and `discharge_capacity_*`
  still share one facet when both are collected. `combine_directions=False`
  still means one facet per variable.
- Same rule as ICA overlays (#862): dash only when both directions are on
  the same panel. A lone discharge series is solid.
- Plotly summary path is the reported bug (`fig = cap_summaries.plot()`).
  Apply the same dash rule in `spread_plot` so `spread=True` does not keep
  a dashed discharge-only line.
- Seaborn / matplotlib summary backends are out of scope (they do not add
  `legend2`).

### Prior art

- `split_direction`, `_combine_direction_panels`, `_DIRECTION_DASH`,
  `_add_direction_legend` in `cellpy/plotting/collected.py` — keep; change
  when dash and `legend2` turn on.
- ICA Plotly/matplotlib backends already skip the dash when only one
  direction is present (`both_directions = nunique() > 1`, #862) — mirror
  that, do not invent a second legend style.
- Toolbox: none. No `graphify-out/`.

## Approach

1. After the panel rewrite, a direction style is active only for panels
   whose rows contain both `charge` and `discharge`.
2. Plotly `line_dash="direction"` and `_add_direction_legend` run only
   then. Legend entries are the directions that actually share a panel
   (Charge solid, Discharge dash), not every direction token in the frame.
3. A panel with a single direction (the usual discharge-only
   `summary_collector`) gets solid lines and no `legend2`. Its y-title
   still keeps the direction word (`Discharge Capacity …`) via the existing
   "no merge partner → keep the variable name" rule.
4. `spread_plot` uses solid for a one-direction panel and dash for
   discharge only when that panel has both.

## Files to touch

- `cellpy/plotting/collected.py` — gate dash + `legend2`; docstring on
  `summary_plotter`.
- `tests/test_collected_summary_directions.py` — lone-direction case:
  solid traces, no `legend2`, y-title still starts with `Charge` /
  `Discharge`. Both-directions case stays as it is.
- `docs/agents/index.md`, root `AGENTS.md` (batch bullet), `HISTORY.md`
  `[Unreleased]`, `.issueflows/04-designs-and-guides/test-registry.md` if
  the lone-direction test note changes.

## Test strategy

`uv run pytest -m essential tests/test_collected_summary_directions.py tests/test_collected_summary_groups.py tests/test_collected_summary_axes.py`

## Open questions

- None. Direction legend stays when both directions share a panel; it is
  what makes solid vs dash readable.
