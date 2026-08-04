# Collected-frame plotting (`layout=` / `kind=`)

## Context

Epic #567 Stage 3 / issue #657 re-bases collectors' drawing half onto
`cellpy.plotting`. Collection, caching, and autonaming stay in
`cellpy.utils.collectors`; drawing uses an already-tidy multi-cell frame.

## Decision

- **`FrameContext`** / **`from_frame`** in `cellpy.plotting.context` wrap a
  collected frame plus light metadata (`family_kind`, `units`, `journal`).
- **Public orchestrator:** `cellpy.plotting.collected_plot(frame, *,
  family_kind, layout=…, kind=…, backend=…)`.
- Legacy collector knobs map as:
  - `method`/`plot_type` `fig_pr_cell` → `layout="per_cell"`
  - `fig_pr_cycle` → `layout="per_cycle"`
  - `film` → `kind="film"`
  - `spread=True` → `kind="spread"`
  - default → `kind="line"`
- Flow: resolve layout/kind → `FigureSpec(extras["kind"]="collected", …)` →
  `get_backend(...).render` → collected layout engines (plotly primary;
  `seaborn` / `matplotlib` → historical seaborn collector path, best-effort).
- **`BatchCollector.render`** (and thin **`plot`** alias) call
  `collected_plot`; custom `plotter=` callables still work if provided.
- Collector plotly templates remain in `cellpy.plotting.theme`
  (`make_collector_templates`).
- **Cycle column:** capacity-curve frames use native `cycle_num`; ICA frames
  use `cycle`. Plotters must use the `z` (cycle-column) argument for counts and
  filters — never hardcode `cycle_num` or `.cycle` on the curve/ICA paths (#679).
- **Summary facet y-axes (#804 / #817):** prefer `share_y=` (alias `match_axes=`).
  Shared (`True`) = one y-scale across facet rows; independent (`False`, the
  **default for summary**) = per-row autorange. Same rules apply to
  `kind="spread"` / `spread=True` (group-avg mean±std bands). Per-panel fixed
  limits: `y_ranges={"coulombic_efficiency": [0, 110], ...}` (variable →
  `[lo, hi]`). Non-empty `y_ranges` forces independent axes. Plotly is the
  supported backend for `y_ranges`; seaborn/matplotlib are best-effort and
  ignore it.
- **App chrome (#801):** `plotly_template=` overrides the default
  `plotly+{method}` combo; `layout_updates=` is a shallow
  `fig.update_layout(**…)` after collector styling. Summary facet strips no
  longer keep raw `variable=…` text by default — pretty y-axis titles are
  built automatically (`y_label_mapper=` overrides). Height:
  `height=` (absolute) or `height_per_panel=` (alias of `sub_fig_min_height`;
  summary default 300 px/panel) plus optional `figure_border_height=`.
- **Cycles / ICA facet chrome (#820):** Plotly `layout="per_cell"` /
  `"per_cycle"` (and legacy `fig_pr_*` / `film`) rewrite facet strips to
  `Cycle N` / cell label by default — strips stay visible (unlike summary's
  clear→y-title path). Prefer `layout=` over `method="fig_pr_*"`.
- **ICA `direction=` (#821):** `charge` / `discharge` / `both` on line layouts
  (`layout="per_cell"|"per_cycle"`) and `kind="film"`, not only film. Default
  for collected ICA remains `charge`. `both` overlays half-cycles; on Plotly
  line plots, `line_dash` separates directions so lobes do not join. Invalid
  values warn and coerce to `charge`.

### Example — Capacity + CE without crushing panels

```python
collection.plot(
    family_kind="summary",
    share_y=False,  # default for summary
    y_ranges={"coulombic_efficiency": [0, 110]},
)
```

### Example — drop into an app shell

```python
collection.plot(
    family_kind="summary",
    plotly_template="plotly_white",
    layout_updates={"paper_bgcolor": "#f7f7f7", "margin": dict(l=60, r=20, t=40, b=40)},
    height_per_panel=220,
    y_ranges={"coulombic_efficiency": [0, 110]},
)
```

### Example — cycles facets without `cycle_num=` / `cell=` chrome

```python
collection.plot(
    family_kind="cycles",
    layout="per_cell",  # prefer over method="fig_pr_cell"
)
# Facet strips: cell labels only. layout="per_cycle" → "Cycle 1", "Cycle 2", …
```

## Links

- Issue #657; epic #567; plan
  `cellpy-design-and-development/archive/redesigns/cellpy2-plotting-redesign-plan.md` §3.3 / Phase 4
- Related: `plotting-prepare.md`, `plotting-backends.md`
- Issue #804 (per-panel y-limits / `share_y`)
- Issue #801 (theme / label / height hooks)
- Issue #820 (cycles / ICA pretty facet strips)
