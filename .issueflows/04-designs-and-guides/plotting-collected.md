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

## Links

- Issue #657; epic #567; plan
  `architecture-plan/cellpy2-plotting-redesign-plan.md` §3.3 / Phase 4
- Related: `plotting-prepare.md`, `plotting-backends.md`
