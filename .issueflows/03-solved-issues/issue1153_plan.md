# Issue #1153 — plan

## Goal

Document every argument of `Batch.plot`, including arguments that only arrive through `**kwargs`, so `direction`, `rate`, and the rest of the cycle-life plot options are visible on the function the issue names.

## Constraints

- Docs only. Do not change plot behavior, defaults, or which kwargs each backend reads.
- Chat add-on: every parameter must be described, including ones forwarded with `**kwargs`. A "forwarded to the plotter" line is not enough.
- Google-style docstrings (project rule).
- The rendered Batch API page (`docs/api/batch.md`) pulls `::: cellpy.batch.facade.Batch`, so the public docstring is the page. Do not hand-edit that markdown.
- `docs/agents/index.md` already shows `b.plot(ir=True, rate=True, direction="discharge")`. No new public surface, so leave it.
- Matplotlib cycle-life plotting stays deprecated. Say so in its docstring. Do not revive it.

### Prior art

- `Batch.plot` in `src/cellpy/batch/facade.py` forwards `**kwargs` to `batch_summary_plot`. Current docstring names only `backend` and `show`.
- `batch_summary_plot` in `src/cellpy/plotting/batch_summary.py` documents `**kwargs` as a short forward note.
- `plot_cycle_life_summary_plotly` pops the plotly options (`direction` default `"charge"`, `rate` default `False`, plus the rest listed under Approach). One-line docstring.
- `generate_summary_frame_for_plotting` reads `trim_pages`, `capacity_specifics`, and `only_selected`. No docstring.
- `plot_cycle_life_summary_matplotlib` reads `ir`, `direction`, and `marker_size` from `**kwargs`, plus explicit `width`, `height`, `height_fractions`, and `legend_option`. Deprecation warning only.
- Batch processing page (`docs/examples/batch_utility/cellpy_batch_processing.md`) already mentions `rate=True`. Leave that page alone.
- Toolbox: none for docstring coverage. Graph: not consulted (the kwargs are local `pop`/`get` calls).

## Approach

List each consumed name, its default, and what it does. Split plotly vs matplotlib where a name is ignored by one backend.

Canonical list on both `Batch.plot` and `batch_summary_plot` (the two functions that accept the public `**kwargs`). Each leaf documents only the names it reads.

Plotly path (`plot_cycle_life_summary_plotly`, and frame prep where noted):

| Name | Default | Effect |
| --- | --- | --- |
| `direction` | `"charge"` | Capacity and C-rate panel use charge columns. `"discharge"` uses discharge columns. IR follows the same direction (`ir_discharge`, else `ir_charge` with a warning). |
| `rate` | `False` | `True` adds the C-rate panel when that column exists. |
| `ir` | `True` | Include the IR panel when the column exists. |
| `capacity_specifics` | `"gravimetric"` | Which capacity columns (`gravimetric`, `areal`, `absolute`, or `raw`). Also read while building the frame. |
| `ce_range` | `None` | Fixed y-range for the coulombic-efficiency panel. |
| `min_cycle` / `max_cycle` | `None` | Drop cycles outside the bounds. |
| `title` | `"Cycle Summary"` | Figure title. |
| `x_label` | `"Cycle Number"` | X-axis title. |
| `x_range` | `None` | Fixed x-range. |
| `width` | `1000` | Figure width in pixels. |
| `color_map` | Plotly `Set1` | Qualitative sequence, or the name of one on `plotly.express.colors.qualitative`. |
| `base_template` | `"plotly"` | Plotly template name, combined with the axes-border template. |
| `group_legends` | `True` | Legend entries grouped by journal group. |
| `inverted_mode` | `False` | Swap group color and sub-group symbol. |
| `filter_by_group` | `None` | Keep these journal group ids (one id or a sequence). |
| `filter_by_name` | `None` | Keep cells whose label contains this string. |
| `trim_pages` | `False` | Frame prep only. Keep a fixed set of journal columns before the merge. |
| `only_selected` | `False` | Frame prep only. Keep journal rows with `selected` > 0. |

Matplotlib path only (`batch_summary_plot` pops these before the deprecated renderer; plotly ignores them):

| Name | Default | Effect |
| --- | --- | --- |
| `height` | `config.batch.summary_plot_height` | Figure height passed into the matplotlib renderer. |
| `height_fractions` | `config.batch.summary_plot_height_fractions` | Relative subplot heights. |
| `marker_size` | `None` | Marker size in the style dicts. |
| `legend_option` | `"all"` | Legend text: `"clean"`, `"mass"`, `"loading"`, or `"all"`. |

On the matplotlib path, `width` uses `config.batch.summary_plot_width` instead of `1000`. `rate`, filters, title, and the other plotly-only names do nothing there. Say that next to those names on `Batch.plot` and `batch_summary_plot`.

`plot_cycle_life_summary_matplotlib` documents its own parameters (`info`, `summaries`, `width`, `height`, `height_fractions`, `legend_option`, `ir`, `direction`, `marker_size`) and keeps the deprecation note.

No behavior change if a caller passes an unknown keyword: it stays ignored, same as today.

## Files to touch

- `src/cellpy/batch/facade.py` — expand `Batch.plot` docstring with the tables above (prose Args, not a markdown table).
- `src/cellpy/plotting/batch_summary.py` — same full list on `batch_summary_plot`; subset on `plot_cycle_life_summary_plotly`, `generate_summary_frame_for_plotting`, and `plot_cycle_life_summary_matplotlib`.
- `tests/test_batch.py` — one essential test: each consumed name appears in the docstring of the function that reads it (`Batch.plot`, `batch_summary_plot`, and the three leaves).

## Test strategy

`uv run pytest -m essential tests/test_batch.py -k plot_docstring` from the worktree. No figure snapshot update.

## Open questions

- None. Scope stays on `Batch.plot` and the plot functions it calls. `Collection.plot` / collector `plot` are a different API.
