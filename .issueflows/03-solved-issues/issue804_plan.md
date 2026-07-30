# Issue #804 — Plan: Per-panel y-limits for collected summary facets

Status: **confirmed** (2026-07-30) — open questions resolved as recommended:
summary default `share_y=False`; `y_ranges` keyed by variable name; MPL best-effort.

## Goal

Give collected summary facet plots a clear public API for **independent vs shared y-scales** and **per-variable y-limits**, so Capacity+CE (and similar) do not crush each other under a shared axis — Plotly end-to-end, with tests and a short docs example.

## Constraints

- Patch release (`v.2.1.2`); keep scope to the **collected summary** path (`Collection.plot` / `collected_plot` → `summary_plotter` → `_cycles_plotter`). Do not rework single-cell `summary_plot` prepare→render (already has `share_y`, `y_range`, `ce_range`, `row_y_ranges`).
- Collected path today builds a thin `FigureSpec` (extras only; **no panels**) and still renders via legacy plotters — do **not** force a full prepare→PanelSpec migration in this issue. Prefer kwargs that flow through `render_opts`, optionally mirrored onto `PanelSpec` later if cheap.
- Prefer keeping **auto-range** when a panel’s limits are omitted.
- Companion: [cellpy/cellpy-simple-gui#2](https://github.com/cellpy/cellpy-simple-gui/issues/2) (consumer; no code change there in this PR).
- Design docs: [plotting-collected.md](../04-designs-and-guides/plotting-collected.md), [plotting-backends.md](../04-designs-and-guides/plotting-backends.md).

### Prior art

| Hit | Where | Relation |
| --- | --- | --- |
| `match_axes` → `fig.update_yaxes(matches=None)` | [`cellpy/plotting/collected.py`](../../cellpy/plotting/collected.py) `_cycles_plotter` | Direct seam for share/independent |
| `summary_plotter` → `_cycles_plotter(..., method="summary")` | same file | Public collected summary entry |
| `share_y` + `row_y_ranges` / `ce_range` | [`prepare/summary.py`](../../cellpy/plotting/prepare/summary.py), [`backends/plotly.py`](../../cellpy/plotting/backends/plotly.py) | Single-cell pattern to **mirror naming**, not copy formation layout |
| Issue #391 | `BatchSummaryCollector` default `match_axes=False` | Intent: summary facets independent by default; class is now a shim — **default never reached** via `Collection.plot` |
| `AxisSpec.range` / `PanelSpec` | [`cellpy/plotting/spec.py`](../../cellpy/plotting/spec.py) | Contract exists; collected render ignores panels today |
| Toolbox | `.issueflows/00-tools/` | None for plotting ranges |
| Graphify | communities around `PanelSpec` / prepare summary | Confirms dual paths; no collected-range helper |

## Approach

1. **Naming (document + alias)**  
   - On the collected path, treat `share_y` as the preferred public name (aligned with `summary_plot`).  
   - Keep `match_axes` as a synonym (`share_y` wins if both set; document both).  
   - Docstring + short design-doc note in `plotting-collected.md`: shared = one y-scale across facet rows; independent = per-row autorange (or per-row fixed limits).

2. **Default for summary facets**  
   - For `method=="summary"` only: default **independent** y-axes (`share_y=False` / `match_axes=False`).  
   - Leave `_cycles_plotter` default for non-summary methods (`fig_pr_cell` / `fig_pr_cycle` / `film`) as today (`match_axes=True`).  
   - Rationale: restores #391 intent for the modern `Collection.plot` entry; Capacity+CE is the motivating case.

3. **Per-panel y-limits API**  
   - Add kwarg `y_ranges: Mapping[str, Sequence[float]]` (variable name → `[lo, hi]`), forwarded via `collected_plot` / `Collection.plot` → `summary_plotter` → applied after the Plotly figure is built.  
   - Resolve panel order from the facet row variable (`variable` column / category order). Unknown keys: warn once and ignore.  
   - Application order: (a) unmatch axes when not sharing; (b) for each known variable with a range, set that row’s y-axis `range` and `autorange=False`; omitted variables keep autorange.  
   - When `share_y=True`, either refuse conflicting per-panel ranges (raise/warn) or apply only if a single shared range is intended — **recommend:** if `y_ranges` is non-empty, force independent axes (unmatch) then apply per-panel ranges (document this).

4. **Do not** plumb a second global `y_range` that stomps all facets (that already exists on single-cell summary and is wrong for Capacity+CE). Optional later: honor `FigureSpec.panels[i].y_axis.range` if callers build panels — out of scope unless trivial to read from `spec.panels` in `render_collected`.

5. **Matplotlib / seaborn**  
   - Best-effort: if the seaborn collector path can set per-facet `ylim` cheaply, do it; otherwise document Plotly as the supported backend for `y_ranges` (issue says “ideally MPL”).

6. **Docs**  
   - Example: Capacity + CE with `share_y=False` and `y_ranges={"coulombic_efficiency": [0, 110]}` (or equivalent header). Prefer a short addition under existing plotting/collect docs or `docs/getting_started/` — not a new guide unless needed. Update `plotting-collected.md` decision bullets.

## Files to touch

| Path | Change |
| --- | --- |
| [`cellpy/plotting/collected.py`](../../cellpy/plotting/collected.py) | Alias `share_y`↔`match_axes`; summary default independent; apply `y_ranges` on Plotly after build; docstrings |
| [`.issueflows/04-designs-and-guides/plotting-collected.md`](../04-designs-and-guides/plotting-collected.md) | Document `share_y` / `match_axes` / `y_ranges` |
| `docs/…` (small example) | Capacity+CE independent / CE limit |
| `tests/test_collected_summary_axes.py` (new) or nearby collector/plotting test | Synthetic long frame: shared vs independent; per-variable range on Plotly layout |

## Test strategy

```bash
uv run pytest tests/test_collected_summary_axes.py -q
# or whatever file is chosen; mark essential only if cheap and guards the public API
MPLBACKEND=Agg uv run pytest -m essential   # smoke before close
```

- Build a minimal long DataFrame (`cycle`, `cell`, `variable`, `value`) with capacity-like and CE-like scales.  
- Assert Plotly: with `share_y=True`, y-axes match; with `share_y=False`, `matches` cleared; with `y_ranges={ce: [0, 110]}`, that row’s axis range is set and capacity row still autoranges.  
- No golden figure PNG required — layout dict / axis props are enough.

## Open questions

Resolved on Accept:

1. Summary default `share_y=False` — **yes**.
2. `y_ranges` keyed by variable name — **yes**.
3. MPL — **best-effort** (Plotly is the supported path for `y_ranges`).
