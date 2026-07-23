# Issue #657 — Plan

## Goal

Re-base collectors' drawing half onto `cellpy.plotting`: already-collected tidy
frames (`cell` / `group` / `sub_group`) render through prepare→spec→render with
`layout=` / `kind=` options; delete local plotter bodies; keep collection,
caching, autonaming, and frame persistence in collectors.

## Constraints

- Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md` §3.3 /
  Phase 4; collectors hand-off in
  `architecture-plan/cellpy2-collectors-redesign-plan.md` §3.3.
- Collection redesign (options dataclasses, elevated-args collapse, recipes) is
  **out of scope** — leave `data_collector` / `plotter_arguments` wiring; only
  swap the draw callee.
- `#658` (`Batch.plot` + delete `batch_plotters`) depends on this landing; do
  not touch `batch_plotters.py` here.
- Filters stay in `cellpy/filters/`
  (`.issueflows/04-designs-and-guides/filters-and-plot-filtering.md`).
- Parity gate: keep `tests/test_figure_specs.py` green; extend
  `figure_specs.json` with collector/batch-input cases in the same commit as
  intentional visual changes. Plotting tests under `MPLBACKEND=Agg`.
- `import cellpy.utils.collectors` must stay safe without the `batch` extra for
  **non-plot** imports (no import-time plotly attribute use; defer heavy plot
  deps).
- Public collector UX (`Batch*Collector`, `render` / `show` / `update`,
  `plot_type` → `method`) stays working; notebooks must not break.

### Prior art

- `BatchCollector.render` → `self.plotter(self.data, …)` —
  [`cellpy/utils/collectors.py`](cellpy/utils/collectors.py) (~L421); plotters
  `sequence_plotter` / `summary_plotter` / `cycles_plotter` / `ica_plotter` /
  `spread_plot` (~L1765–2912). **Migrate** draw bodies out; keep collect path.
- `CellContext` / `from_source` —
  [`cellpy/plotting/context.py`](cellpy/plotting/context.py); docstring already
  reserves Batch/frame adapters for this issue. **Extend**.
- Prepare → `FigureSpec` → `get_backend().render` —
  [`cellpy/plotting/prepare/`](cellpy/plotting/prepare/),
  [`backends/`](cellpy/plotting/backends/); design notes in
  `.issueflows/04-designs-and-guides/plotting-prepare.md` +
  `plotting-backends.md`. **Mirror** for collected frames.
- Collector plotly templates already in
  [`cellpy/plotting/theme.py`](cellpy/plotting/theme.py)
  (`make_collector_templates`, names `fig_pr_cell` / `fig_pr_cycle` / `film` /
  `summary`). **Reuse**; stop treating collectors as template owner.
- Figure IO / legend helpers already in `plotting.figures` / `plotting.labels`
  (Phase 1 / #595); collectors re-export. **Keep** re-exports or thin imports;
  delete any remaining local exporter duplication that is purely drawing.
- Oracle:
  [`tests/test_figure_specs.py`](tests/test_figure_specs.py) +
  [`tests/figure_spec_support.py`](tests/figure_spec_support.py) — single-cell
  only today. **Extend** with collector/frame cases.
- Smoke:
  [`tests/test_collectors.py`](tests/test_collectors.py) — E2E autorun for
  summary / cycles / ICA (+ film). **Keep green**.
- Toolbox (`00-tools/`): nothing that builds collector figures. Graph communities
  35/58/163 (collectors) and plotting prepare/backends hubs.

## Approach

**Recommended: frame-in adapter + multi-cell render in `cellpy.plotting`, then
delete collectors plotters.** Do not leave `sequence_plotter` as a permanent
public API under a new path; fold behaviour into backends/`layout`/`kind`.

### 1. Frame context

- Add `FrameContext` (name flexible) in `context.py`: holds the tidy
  `DataFrame` plus optional `units` / `journal` / collector `kind`
  (`summary` | `cycles` | `ica`).
- Extend `from_source` (or add `from_frame`) so a collected frame is a first-class
  plotting input without requiring a live `CellpyCell` per subplot.
- Do **not** implement full `Batch` → collect inside plotting; collectors keep
  owning collection.

### 2. Collected-frame plot API in plotting

- Add one orchestrator used by collectors, e.g.
  `cellpy.plotting.collected_plot(frame, *, family_kind, layout=…, kind=…,
  backend=…, **opts)` (exact name bikeshed OK; keep it package-private or
  public-but-narrow).
- Map today's collector knobs:
  - `method` / `plot_type`: `fig_pr_cell` → `layout="per_cell"`;
    `fig_pr_cycle` → `layout="per_cycle"`; `film` → `kind="film"` (+ layout);
    `summary` → summary collected path.
  - `spread=True` → `kind="spread"`.
  - Default line plots → `kind="line"`.
- Build a `FigureSpec` (panels / extras carrying layout+kind+labels) from the
  already-tidy frame; skip single-cell prepare that expects `CellContext`.
- Render via existing `get_backend(backend)` with new multi-cell branches in
  plotly (primary). Port the behavioural core of `sequence_plotter` /
  `spread_plot` / summary melt path into those branches (mechanical move +
  rename to `layout`/`kind`, not a redesign of collection).

### 3. Wire collectors

- `BatchCollector.render` (and optionally `plot` as a thin alias for redesign
  §3.3 naming) calls the plotting orchestrator with `self.data` + mapped
  options; drop `self.plotter` callable requirement **or** replace subclass
  plotter defaults with a sentinel that means “use plotting”.
- Subclasses keep elevated `plot_type` / collector args; only the draw target
  changes.
- Figure save / PNG / SVG paths use `plotting.figures` (delete duplicate local
  plotly exporters if still present as bodies).
- Templates: call `theme.make_collector_templates()` from plotting/orchestrator
  (or once on first collected render); collectors stop owning template setup
  beyond a no-op or re-export.

### 4. Delete drawing bodies

Remove from `collectors.py` (or reduce to deprecated shims that forward one
release if something external imported them — prefer delete if only used
internally):

- `sequence_plotter`, `_cycles_plotter`, `summary_plotter`, `cycles_plotter`,
  `ica_plotter`, `spread_plot`, film helpers that exist only for drawing
  (`histogram_equalization` / `_hist_eq` as needed).
- Keep: collectors, `pick_named_cell`, `*_collector` frame builders,
  persistence, autoname, units parsing.

### 5. Import hygiene

- Keep plotly import guarded; ensure no import-time `go`/`px`/`pio` use outside
  functions (existing `test_plotting_package` AST guard).
- Soften hard `matplotlib` import at collectors module top if it blocks
  non-plot import paths; match the plotly pattern where practical.

### 6. Docs / deprecations

- If any public plotter name was importable from `cellpy.utils.collectors`,
  register a `warn_once` shim in `DEPRECATIONS.md` pointing at the plotting
  API — only if grep shows external/doc usage; otherwise delete cleanly.
- Short note in
  `.issueflows/04-designs-and-guides/plotting-prepare.md` (or new
  `plotting-collected.md`): FrameContext + `layout`/`kind` contract.

### Ordering inside the PR

1. FrameContext + collected orchestrator + plotly multi-cell render (dual-path
   behind collectors still calling old plotters until green).
2. Flip `BatchCollector.render` to the new path; run collector + oracle tests.
3. Delete old plotter bodies; regenerate `figure_specs.json` for new cases.
4. Import hygiene + design-doc touch-up.

## Files to touch

| Path | Change |
|------|--------|
| `cellpy/plotting/context.py` | `FrameContext` (+ `from_frame` / extend `from_source`) |
| `cellpy/plotting/` (new module, e.g. `collected.py` or `prepare/collected.py`) | Orchestrator: frame → FigureSpec → backend |
| `cellpy/plotting/backends/plotly.py` | Multi-cell `layout` / `kind` render branches |
| `cellpy/plotting/backends/mpl.py` | Parity only where collectors already support seaborn/mpl today; else document plotly-primary for collected layouts |
| `cellpy/plotting/theme.py` | Ensure collector templates registered from plotting side |
| `cellpy/plotting/__init__.py` | Export new public/narrow API as needed |
| `cellpy/utils/collectors.py` | `render`/`plot` → plotting; delete plotter bodies; import hygiene |
| `tests/figure_spec_support.py` + `tests/data/figure_specs.json` | Collector/batch-input cases + snapshot |
| `tests/test_figure_specs.py` / `dev/snapshot_figure_specs.py` | Wire new cases if needed |
| `tests/test_collectors.py` | Stay green; adjust imports if plotters vanish |
| `tests/test_plotting_package.py` | Re-exports / no import-time plotly |
| `DEPRECATIONS.md` | Only if public shims needed |
| `.issueflows/04-designs-and-guides/plotting-*.md` | Record FrameContext / layout/kind decision |

## Test strategy

```bash
MPLBACKEND=Agg uv run pytest tests/test_collectors.py tests/test_plotting_package.py tests/test_figure_specs.py -q
MPLBACKEND=Agg uv run pytest -m essential -q
```

- Extend oracle with a **minimum** collector column (recommend): summary default
  (plotly), cycles `per_cell` (plotly), ICA `film` (plotly), and one `spread`
  summary if `standard_gravimetric_collector` / spread path is still public.
- Keep existing `test_collectors.py` E2E autorun assertions.
- Regenerate snapshot via `uv run python dev/snapshot_figure_specs.py` when
  structure intentionally changes.

## Decisions (confirmed)

1. **Backend parity:** plotly-complete for all `layout`/`kind` modes;
   `backend="seaborn"` → matplotlib backend with best-effort parity (or
   `warn_once` + plotly fallback if parity is incomplete).
2. **Frame-in API:** narrow public `cellpy.plotting.collected_plot` (name OK to
   adjust slightly) so #658 can call it without `BatchCollector`.
3. **`plot` alias:** add `BatchCollector.plot` as a thin alias of `render`.
4. **Scope:** one PR, full delete of collectors plotter bodies (phased commits
   inside the PR).

## Status

- [x] Plan accepted — ready for `/iflow-build`
