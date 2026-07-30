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
- **Summary facet y-axes (#804):** prefer `share_y=` (alias `match_axes=`).
  Shared (`True`) = one y-scale across facet rows; independent (`False`, the
  **default for summary**) = per-row autorange. Per-panel fixed limits:
  `y_ranges={"coulombic_efficiency": [0, 110], ...}` (variable → `[lo, hi]`).
  Non-empty `y_ranges` forces independent axes. Plotly is the supported
  backend for `y_ranges`; seaborn/matplotlib are best-effort and ignore it.

### Example — Capacity + CE without crushing panels

```python
collection.plot(
    family_kind="summary",
    share_y=False,  # default for summary
    y_ranges={"coulombic_efficiency": [0, 110]},
)
```

## Links

- Issue #657; epic #567; plan
  `architecture-plan/cellpy2-plotting-redesign-plan.md` §3.3 / Phase 4
- Related: `plotting-prepare.md`, `plotting-backends.md`
- Issue #804 (per-panel y-limits / `share_y`)
