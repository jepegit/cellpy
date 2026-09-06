# Issue #948 plan

## Goal

`summary_collector(..., group_it=True, custom_group_labels={1: "run-14",
2: "run-15"}).plot(spread=True)` shows **run-14 / run-15** in the Plotly
legend, same as `.plot()` without spread.

## Constraints

- Additive. Non-spread grouped summaries stay as they are (#923 / #947).
- Do not invent a second label API. `custom_group_labels=` on collect +
  `group_label` on the frame is the source of truth.
- Per-panel y-limits stay `y_ranges=` / `share_y=` (#804 / #817). Do not
  teach or copy the thread's `fig.update_yaxes(..., row=N)` workaround.
- Public get/schema/CLI surface unchanged — no agents.md rewrite.

### Prior art

- `cellpy.plotting.collected._spread_series_column` — prefers
  `group_label` when any value is non-null, else `cell`, else `group`.
- `spread_plot` — `make_subplots`; `name` / `legendgroup` = groupby key.
- `summary_plotter` — for `group_it` frames, sets `z` to `group_label`
  when present (px.line path). Spread does **not** use `z`; it calls
  `_spread_series_column` on the frame that reaches `sequence_plotter`.
- `collect_summaries` / `_with_group_label` — writes `group_label` on
  the averaged long frame from `custom_group_labels` (int or str keys).
- Tests already cover **Collection**.plot(spread=True) labels
  (`tests/test_collected_summary_groups.py::test_spread_plot_legend_uses_custom_group_labels`)
  and **summary_collector**.plot() **without** spread
  (`test_summary_collector_plot_uses_custom_group_labels_and_units`).
  The issue snippet — `summary_collector(...).plot(spread=True)` — is
  **not** locked.
- Toolbox: none. Graph: none.

## Approach

1. Add the missing essential test: reuse the `summary_collector` batch
   fixture from `test_summary_collector_plot_uses_custom_group_labels_and_units`,
   call `.plot(spread=True)`, assert legend names are `run-14` / `run-15`
   (mean traces with `showlegend`).
2. Run it. Two outcomes:
   - **Red** — `group_label` is missing or all-null on the frame
     `spread_plot` sees (likely dropped in the summary melt / id-vars
     list, which omits `group_label`). Keep `group_label` as an id
     column, or ensure `_spread_series_column` sees the same `z` that
     `summary_plotter` already resolved. Prefer passing the resolved
     series column into `spread_plot` over a second lookup.
   - **Green** — already fixed on `master` by #923 / #947; keep the
     test as the lock and close.
3. Comment / y-axes: confirm existing
   `tests/test_collected_summary_axes.py` spread + `y_ranges` tests.
   If green, one docstring line on `Collection.plot` / `spread_plot`:
   use `y_ranges=`, not manual `row=`. No start_cell change (spread
   row 1 = top; tests already assert that order).

## Files to touch

- `tests/test_collected_summary_groups.py` — `summary_collector` +
  `spread=True` legend test (`@pytest.mark.essential`).
- `cellpy/plotting/collected.py` — only if the new test is red
  (`spread_plot` / `_spread_series_column` / melt id-vars).
- `cellpy/collect/collection.py` — optional one-line `y_ranges=` note
  on `plot`.
- `.issueflows/04-designs-and-guides/plotting-collected.md` — spread +
  `custom_group_labels` / `y_ranges` sentence if code changes.

## Test strategy

```bash
uv sync --extra batch
MPLBACKEND=Agg uv run pytest tests/test_collected_summary_groups.py tests/test_collected_summary_axes.py -m essential
```

## Open questions

- **Comment scope:** treat the y-axis screenshot as “use `y_ranges=`”
  (recommended) vs also change spread `start_cell` to match the
  workaround’s row numbers (would invert existing facet-order tests —
  reject unless you want that).
