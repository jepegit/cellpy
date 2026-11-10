# Issue #1193 — plan

## Goal

`summary_collector(...).plot()` (line and `spread=True`) lets a click hide
charge, discharge, or both, while a series click still hides that experiment
in both directions.

## Constraints

- Plotly gives each trace one `legendgroup`. The series legend and a Direction
  legend cannot both toggle by group. Direction becomes two toggle buttons.
  The series legend keeps `legendgroup`.
- A direction button sets `visible` on that direction's traces only. A later
  series click can show those traces again (Plotly group toggle writes the
  whole group). Accepted.
- Coulombic efficiency and any other direction-less series stay visible when
  Charge or Discharge is hidden.
- Lone charge or lone discharge stays solid, with no Direction control
  (#1096). `combine_directions=False` stays one facet per variable and no
  Direction control (#1009).
- Seaborn / matplotlib summary paths stay as they are (no `legend2`).
- Legacy `b.plot()` / `plot_cycle_life_summary_plotly` stays untouched.

### Prior art

- `split_direction`, `_combine_direction_panels`, `_styled_directions`,
  `_DIRECTION_DASH`, `_dedupe_direction_names`, `_add_direction_legend`,
  `spread_plot` / `_add_spread_traces` in
  `src/cellpy/plotting/collected.py` — extend. Dash styling stays.
- `legend_replacer` in `src/cellpy/plotting/labels.py` — already rewrites
  `group, direction, subgroup` to the cell name (#983). It drops the
  direction token before dedupe; stash it on `meta` first.
- `_select_direction` is the ICA/cycles filter, not this summary legend.
- Design: `plotting-collected.md` (combined panels), #1009 (style-only
  `legend2`), #1096 (legend only when both directions share a panel).
- Toolbox: none. No `graphify-out/`.

## Approach

Two separate failures:

1. **Direction control does nothing.** `_add_direction_legend` adds dummy
   `Scatter` traces (`x=[None]`) on `legend2`. A click toggles the dummy, not
   the data. The repro uses `spread=True`, which still adds that legend and
   does not link it to the mean or the ±std bands.
2. **Series click can hide charge only** (line plot, not spread). `px.line`
   sets `legendgroup` to `"cell, charge"` / `"cell, discharge"`.
   `_dedupe_direction_names` renames both to the series but keeps the old
   group (`legendgroup=trace.legendgroup or name`). The visible entry is the
   charge trace, so the click hides charge. Discharge stays, and both
   Direction swatches still look selected. That matches the comment.
   `spread=True` already sets `legendgroup` to the series, so experiment
   clicks hide both directions there.

Fix:

1. While the trace name still contains `charge` / `discharge`, store
   `meta={"direction": ...}` (`""` when there is no token).
   `legend_replacer` does this before it renames a 3-part summary/ICA name.
   `_dedupe_direction_names` does it for names that still have the token.
   `_add_spread_traces` sets the same `meta` on the mean line and both band
   traces.
2. `_dedupe_direction_names` always sets `legendgroup` to the series name
   (cell or group label), not the px name `"series, direction"`.
3. Replace the `legend2` dummies with one `updatemenus` button group titled
   by an annotation `Direction`, placed where `legend2` sits now
   (`x=1.02`, bottom). Two buttons, `showactive=False`:
   - **Charge** — restyle `visible=False` on charge indices; second click
     `visible=True` (`args` / `args2`).
   - **Discharge** — same for discharge indices.
   Indices come from `meta["direction"]`. Direction-less traces are omitted.
   Same gate as today: buttons only when a panel actually draws both
   directions (`styled`). No buttons and no `legend2` otherwise.
4. Dash stays: charge solid, discharge dash, only on mixed panels.

## Files to touch

- `src/cellpy/plotting/collected.py` — meta, series `legendgroup`, direction
  buttons instead of dummy `legend2`; docstring on `summary_plotter`.
- `src/cellpy/plotting/labels.py` — `legend_replacer` copies a direction token
  into `meta` before renaming.
- `tests/test_collected_summary_directions.py` — series group contains both
  dashes; Charge button indices are the charge traces only; Discharge
  likewise; CE omitted; spread mean + bands included. Update `legend2`
  assertions to the button control. Lone-direction / opt-out tests assert
  no buttons.
- `tests/test_collected_summary_groups.py` — grouped plot asserts the
  Direction buttons instead of `legend2` names.
- `docs/agents/index.md`, root `AGENTS.md` (batch bullet), `HISTORY.md`
  `[Unreleased]`.
- `.issueflows/04-designs-and-guides/plotting-collected.md` — Direction
  control is a toggle, not a style-only legend. Link #1193.
- `.issueflows/04-designs-and-guides/test-registry.md` — new essential rows.

## Test strategy

`uv run pytest -m essential tests/test_collected_summary_directions.py tests/test_collected_summary_groups.py tests/test_collected_summary_axes.py`

Plotly is not in the default `uv sync` env here; use the `batch` extra
(`uv sync --extra batch`) if those tests skip.

## Open questions

- None.
