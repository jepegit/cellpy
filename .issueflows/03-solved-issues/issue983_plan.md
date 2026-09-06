# Issue #983 plan

## Goal

`ica_collector(...).plot(layout="per_cycle", direction="both")` shows **cell
labels** in the Plotly legend (same as `direction="charge"`), not group
numbers.

## Constraints

- Additive. `direction="charge"` / `"discharge"` stay as they are.
- Plotly is the reported path. Seaborn `fig_pr_cycle` does not use
  `line_dash` — leave it.
- DVA shares `sequence_plotter`; same fix applies, no extra API.
- Do not change default `direction="charge"` or `group_cells` coloring.
- Public `get` / `schema` / CLI surface unchanged — no agents.md rewrite.

### Prior art

- `cellpy.plotting.labels.legend_replacer` — maps Plotly `"group,subgroup"`
  names to `cell`. **Bails when `len(parts) != 2`.** That is the miss.
- `cellpy.plotting.collected.sequence_plotter` — `fig_pr_cycle` +
  `group_cells` calls `legend_replacer`; `direction="both"` also sets
  `px.line(..., line_dash=direction)` (#821) so names become
  `"group, subgroup, charge"`.
- `_cycles_plotter` already sets layout `legend.title` to `"Cell"` for
  `fig_pr_cycle`. The leftover group numbers are **trace / legend-group
  titles**, not that string.
- Tests: `tests/test_plotting_package.py` (`legend_replacer` unit);
  `tests/test_collected_ica_direction.py` (ICA `both` overlay, per-cell
  only — no legend assert). Toolbox: none. Graph: none.

## Approach

1. Confirm on a 2-cell fixture that `px.line` names are
   `"<group>, <subgroup>, <direction>"` and that Plotly’s hierarchical
   legend uses `color` (group id) as `legendgrouptitle`.
2. Teach `legend_replacer` to accept **2 or 3** comma parts. First two
   ints still look up `cell`. Third part (direction) is kept only as
   needed for dash/hover — not as the visible title.
3. On a 3-part name:
   - `name` → cell label
   - `legendgroup` → cell label (mute one cell’s charge+discharge)
   - `legendgrouptitle_text` → cell label (kills the group-number title)
   - hover still prefixes the cell label
4. 2-part names keep today’s `legendgroup=group` when `group_legends=True`.
5. `sequence_plotter` stays the caller; no new public kwargs.

## Files to touch

- `cellpy/plotting/labels.py` — parse 3-part names; set
  `legendgrouptitle_text` / `legendgroup` as above.
- `tests/test_plotting_package.py` — 3-part name → cell; unknown still
  untouched.
- `tests/test_collected_ica_direction.py` — `layout="per_cycle"` /
  `direction="both"` on a two-cell frame: trace names (and
  `legendgrouptitle` if present) are cell labels, not `"1"` / `"1, 1, …"`.
  Mark `@pytest.mark.essential`.
- `.issueflows/04-designs-and-guides/plotting-collected.md` — one line
  under the ICA `direction=` bullet.

## Test strategy

```bash
uv run pytest tests/test_plotting_package.py tests/test_collected_ica_direction.py -m essential
```

No new toolbox script.

## Open questions

- **Mute click:** for `direction="both"`, mute by **cell** (recommended)
  vs keep mute-by-group (`group_legend_muting`). Issue asks for cell
  labels; mute-by-cell matches.
- **Item text:** cell only (direction already in line dash) vs
  `cell (charge)`. Recommend cell only.
