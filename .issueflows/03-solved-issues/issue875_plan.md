# Issue #875 — Plan: hover on `spread_plot` mean traces

Status: **confirmed** (2026-08-10) — Accept; Q1=(A) std via customdata; Q2=literal `Cycle (n.)`.

## Goal

Give `spread_plot` informative `hovertemplate` on mean traces (parity with `group_it` summary hover) and skip hover on Upper/Lower Bound band artefacts so spread mode is usable in apps.

## Constraints

- Patch-scoped (milestone **v.2.1.2**): touch `spread_plot` (+ tests/docs). No rewrite of `summary_plotter` px path; no full “replace express” migration (issue suggestion 3 = follow-up only).
- Keep `series_col` behaviour (`cell` vs `group`, #785).
- Prefer Plotly-native `hoverinfo="skip"` on bounds (not post-hoc app surgery).
- Design doc: [plotting-collected.md](../04-designs-and-guides/plotting-collected.md).

### Prior art

| Hit | Where | Relation |
| --- | --- | --- |
| `spread_plot` | [`cellpy/plotting/collected.py`](../../cellpy/plotting/collected.py) ~L142 | Builds mean + upper + lower `go.Scatter`; no hover today |
| `summary_plotter` + `group_it` | same file | px attaches hover: `group=…`, `variable=…`, `Cycle (n.)=%{x}`, `mean=%{y}` |
| `_group_avg_summary_frame` + spread axis tests | [`tests/test_collected_summary_axes.py`](../../tests/test_collected_summary_axes.py) | Ready fixture (`mean`/`std`/`group`/`variable`/`cycle`) |
| `hoverinfo="skip"` | [`cycle_legend.py`](../../cellpy/plotting/cycle_legend.py) | Same pattern for non-data traces |
| Toolbox / graphify | — | None needed |

## Approach

1. **Mean trace** — when adding the mean `go.Scatter`, set:
   - `customdata=sub_data["std"]` (if `std` column present; else omit std line)
   - `hovertemplate` patterned after `group_it`, e.g.  
     `{series_col}={cell}<br>variable={variable}<br>Cycle (n.)=%{x}<br>mean=%{y}<br>std=%{customdata}<extra></extra>`  
     (drop the `std=` line when no std column).
   - Use the same `series_col` label (`cell` or `group`) as the groupby key so per-cell and group-avg frames stay consistent.

2. **Band traces** — on Upper Bound and Lower Bound: `hoverinfo="skip"` (keep names/legendgroup/fill as today so apps that still key off naming keep working).

3. **Docs** — one bullet in `plotting-collected.md` under summary / spread: mean hover + bounds skipped.

4. **Tests** — extend `test_collected_summary_axes.py` (or thin sibling): `summary_plotter(..., spread=True)` on `_group_avg_summary_frame()`; assert at least one mean-named trace has `hovertemplate` containing `mean=` and `variable=`; assert every `"Upper Bound"` / `"Lower Bound"` trace has `hoverinfo == "skip"` (or equivalent Plotly representation).

## Files to touch

| Path | Change |
| --- | --- |
| [`cellpy/plotting/collected.py`](../../cellpy/plotting/collected.py) | `spread_plot` hovertemplate + skip on bounds |
| [`.issueflows/04-designs-and-guides/plotting-collected.md`](../04-designs-and-guides/plotting-collected.md) | Spread hover note |
| [`tests/test_collected_summary_axes.py`](../../tests/test_collected_summary_axes.py) | Essential hover assertions |

## Test strategy

```bash
MPLBACKEND=Agg uv run pytest tests/test_collected_summary_axes.py -q -k spread
MPLBACKEND=Agg uv run pytest -m essential -q
```

## Open questions

1. **Include `std` in mean hover?** **(A) yes via `customdata`** (recommend — spread’s point) vs **(B) mean-only** to match `group_it` px hover exactly?
2. **X-axis label in template** — keep literal `Cycle (n.)` like px group_it (**recommend**) vs pull from `plotly_arguments["labels"]` when present?
