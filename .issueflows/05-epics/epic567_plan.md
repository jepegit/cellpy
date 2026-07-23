# Epic #567: Stage 3.10 — plotting redesign

Anchor: https://github.com/jepegit/cellpy/issues/567
Status: confirmed

## Goal

Make `cellpy.plotting` the **single plotting home**: every figure goes through
`prepare → spec → render` with a declarative figure registry; duplicated figure
IO / legend helpers stay gone; collectors' drawing half and `Batch.plot()`
delegate into that home; `batch_plotters.py` is deleted.

Done when:

- Every figure previously producible by `batch_plotters` (and today's
  `plotutils` / collectors plotters) is producible through `cellpy.plotting`,
  verified against committed figure-spec snapshots (`tests/data/figure_specs.json`
  and its batch-input extension).
- No duplicated figure-IO or legend-helper implementations remain (already true
  after #595; must stay true).
- `Batch.plot()` works unchanged from the user's point of view while calling
  outward into plotting.
- Public entry points that change shape carry `warn_once` shims registered in
  `DEPRECATIONS.md`.

## Constraints

- **Plan of record:** `architecture-plan/cellpy2-plotting-redesign-plan.md`
  (plus batch redesign §4.7 and collectors redesign §3.3 for the hand-offs).
  Filters stay in `cellpy/filters/`
  (`.issueflows/04-designs-and-guides/filters-and-plot-filtering.md`).
- **Already landed under this epic (do not re-issue):**
  - Phase 0 — figure oracle + four regressions (#593); nightly plotting CI (#594).
  - Phase 1 — single copies in `cellpy/plotting/{figures,labels,theme}.py` (#595).
  - Phase 2a — dead `summary_plot_legacy` body removed; name kept as `warn_once`
    delegate (#596).
- **Prerequisite met:** `units_label()` exists (#564, unit plan Phase 4).
- **Out of scope (anchor text):** batch v3 and the collectors *collection*
  redesign — deferred to 2.1 behind facades. This epic only re-bases the
  *drawing* half of collectors.
- **Package path decided by #595:** real home is `cellpy.plotting`;
  `cellpy.utils.plotutils` remains a permanent re-export of the public plot
  entry points.
- **Backend policy (adopt plan defaults unless overturned before Stage 1):**
  `backend="plotly" | "matplotlib"` everywhere; `interactive=` kept as deprecated
  alias; seaborn becomes styling inside the matplotlib backend (not a third
  backend); bokeh dies with `batch_plotters` (Batch already overrides
  bokeh→plotly today).
- **`register_family`:** provisional (`_register_family`) in 2.0; promote to
  public only after a release of use.
- **`cycle_info_plot` multi-cycle:** keep today's asymmetry (matplotlib =
  single-cycle) unless a Stage 2 issue explicitly expands it — behaviour change
  is out of the default port.
- **Parity gate:** every drawing PR must keep `tests/test_figure_specs.py` green
  (regenerate `figure_specs.json` in the same commit when an intentional visual
  change is made). Plotting tests run under `MPLBACKEND=Agg`.
- **Normal lifecycle:** each issue below is one branch / one PR targeting the
  repo default for v2 work (`master` per the `v2` label description).

## Stage 1 — Spec pipeline for `summary_plot`

Proves the prepare → spec → render architecture on the largest and most-loved
surface (`summary_plot` + named y-sets). Retires the private faceting engine
and the seaborn-as-backend fork. Highest risk; everything later reuses this
skeleton.

### Issue: Add FigureSpec dataclasses and a PlotFamily registry

- Spec: Create `cellpy/plotting/spec.py` (`FigureSpec` / `PanelSpec` /
  `AxisSpec`) and `cellpy/plotting/registry.py` by mechanically translating
  today's `SummaryPlotInfo._create_col_info` if/elif chain into `PlotFamily`
  records for every current named y-set. Expose `plotting.families()` (list +
  descriptions) and provisional `_register_family(...)`. `summary_plot` still
  draws via the existing builders in this issue — only the column-set selection
  moves behind the registry (old path calls `registry.get(y)`). Acceptance:
  every y-set currently accepted by `summary_plot` resolves to a family;
  unknown y raises a clear error listing known families; figure-spec oracle
  unchanged; `_create_col_info` if/elif chain deleted or reduced to a thin
  adapter over the registry.
- Depends on: none
- yolo: yes — mechanical translation of an existing table, oracle-guarded, no
  figure-path rewrite yet.
- Published: #636

### Issue: Generic plotly panel/formation layout backend

- Spec: Add `cellpy/plotting/backends/base.py` (render protocol) and
  `backends/plotly.py` with **one** generic panel/formation/facet layout
  engine that replaces the four
  `PlotlyPlotBuilder._configure_formation_{1,2,3,4}_rows` methods. Wire a
  thin adapter so `PlotlyPlotBuilder` (or a parallel path behind a feature
  flag / internal switch) can render from `(tidy_frame, FigureSpec)`. Do not
  flip the public `summary_plot` default yet if parity is incomplete — ship
  behind an internal switch or keep dual-path until the next issue's gate.
  Acceptance: formation figures with 1–4 rows match the oracle structurally;
  no per-row-count method remains in the hot path once the switch is on;
  `tests/test_figure_specs.py` green for plotly summary cases.
- Depends on: #636
- yolo: no — layout-engine design with visual blast radius.
- Published: #637

### Issue: Port summary prepare path and flip `summary_plot` to prepare→spec→render

- Spec: Add `cellpy/plotting/prepare/summary.py` by extracting/reusing
  `SummaryPlotDataPreparer` (filters, rate rescaling, normalization, formation
  marking, CV partitioning → tidy long frame + `FigureSpec`). Point public
  `summary_plot` at context adapter → registry → prepare → backend.render.
  Preserve the user-facing signature and defaults (including named `y=`
  strings and `return_data=True` frame shape). Acceptance: figure-spec oracle
  green for all summary families × both backends currently covered; `return_data`
  frame columns/dtypes match today's builder output on the oracle cell;
  `SummaryPlotDataPreparer` / `PlotlyPlotBuilder` live code either becomes the
  prepare/backend implementation or is deleted in this PR — no third parallel
  summary path left.
- Depends on: #637
- yolo: no — flag-day for the main plot entry; needs careful parity.
- Published: #638

### Issue: Matplotlib backend; retire SeabornPlotBuilder; unify `backend=`

- Spec: Add `cellpy/plotting/backends/mpl.py` that renders the same
  `FigureSpec` (seaborn used only for palette/style helpers, not as a separate
  backend). Delete `SeabornPlotBuilder`. Public API: `backend="plotly"|"matplotlib"`
  on `summary_plot`; keep `interactive=` as a `warn_once` alias registered in
  `DEPRECATIONS.md` (removal 2.1). Acceptance: matplotlib summary oracle cases
  green and describe to the same structural shape family-for-family as plotly
  where the snapshot already compares them; no `SeabornPlotBuilder` class
  remains; calling `interactive=True/False` warns once and maps to the right
  backend.
- Depends on: #638
- yolo: no — static-output engine change; seaborn-loyalist surface.
- Published: #639

## Stage 2 — Other plot families on the same skeleton

Extends prepare→spec→render to the rest of the single-cell menu already in the
figure oracle. No collectors/batch work yet.

### Issue: Port `cycles_plot` to prepare→spec→render

- Spec: Add `prepare/curves.py` (voltage–capacity; prefer `cellpycore.curves`
  output, with fallback to `c.get_cap` if needed — same trick as the validation
  notebooks). Route `cycles_plot` through registry/spec/backends. Collapse
  `x_range`/`y_range` vs `xlim`/`ylim` to one spelling; keep the other as
  `warn_once` aliases in `DEPRECATIONS.md`. Acceptance: `cycles_plot` oracle
  cases green both backends; deprecated range kwargs warn and behave
  identically; no private layout fork left inside `cycles_plot`.
- Depends on: #639
- yolo: no — dual kwargs + curves adapter choices.
- Published: #646

### Issue: Port `raw_plot` and `cycle_info_plot`

- Spec: Add `prepare/raw.py` and `prepare/steps.py`; route both public
  functions through the shared backends. Keep `cycle_info_plot`'s matplotlib
  single-cycle limitation unless expanding it is trivial and oracle-covered.
  Axis/legend text goes through `units_label()` via `plotting.labels` (extend
  `labels.py` beyond legend/marker helpers as needed). Acceptance: oracle cases
  for both functions × both backends green; no hand-composed unit f-strings
  remain in these two code paths; header lookups use the public schema/header
  helpers (no new hard-coded legacy names).
- Depends on: #646
- yolo: no — two families, header/unit sensitivity (Phase 0 already found bugs
  here).
- Published: #647

### Issue: Add `ica_plot` / `dva_plot` families on the new pipeline

- Spec: Register ICA/DVA figure families that consume the specced long frames
  from `cellpy.ica` (`dqdv` / `dvdq` — see ICA redesign #566 / migration notes).
  Implement prepare modules that do not re-invent the math. Public entry points
  `ica_plot` / `dva_plot` (names may live as `cellpy.plotting` exports and
  re-exports). Add corresponding cases to the figure-spec snapshot. Acceptance:
  new oracle cases committed and green; plots honour cell-centric `direction`;
  no dependency on deleted `Converter` / wide-frame helpers.
- Depends on: #647
- yolo: no — new public surface; needs snapshot design choices.
- Published: #648

## Stage 3 — Collectors drawing half, Batch.plot, retire batch_plotters

Closes the epic acceptance criteria: one drawing home, batch facade unchanged,
`batch_plotters.py` gone.

### Issue: Re-base collectors' drawing half onto `cellpy.plotting`

- Spec: Delete collectors' plotter implementations (`sequence_plotter`,
  `summary_plotter`, `cycles_plotter`, `spread_plot` drawing bodies) and local
  templates; `BatchCollector.plot` / render path calls `cellpy.plotting.*` with
  the already-collected tidy frame (`cell`/`group`/`sub_group` columns). Fold
  fig-per-cell / fig-per-cycle / film / spread capabilities into plotting options
  (`layout=`, `kind=`) as needed for parity. Collection, caching, autonaming,
  and frame persistence stay in collectors (out of scope to redesign).
  Acceptance: collector-driven figures that the maintainers' docs/tutorials
  exercise match the oracle (add collector/batch-input cases to
  `figure_specs.json` as needed); collectors no longer define figure IO,
  legend helpers, or plotly templates locally; `import cellpy.utils.collectors`
  stays safe without the `batch` extra for non-plot imports.
- Depends on: stage 2 issue 2
- yolo: no — large behavioural surface; collection API must not break.
- Published: #657

### Issue: Wire `Batch.plot()` to plotting and delete `batch_plotters.py`

- Spec: Change `Batch.plot()` to delegate to `cellpy.plotting.summary_plot`
  (or equivalent) with the tidy summaries frame; preserve user-visible defaults
  where possible (plotly primary; capacity specifics; CE/IR/rate panels). Delete
  `cellpy/utils/batch_tools/batch_plotters.py` and remove imports/wiring from
  `batch.py` / farm machinery. Map obsolete backends (`bokeh`, bare `seaborn`)
  to clear errors or deprecated aliases pointing at `backend=`. Extend the
  figure-spec snapshot with at least one batch-input summary case that covers
  what `batch_plotters` used to produce. Acceptance: `Batch.plot()` produces
  oracle-matching summary figures without importing `batch_plotters`; the
  module file is gone; no remaining in-tree imports of it; DEPRECATIONS/migration
  docs mention the backend triage.
- Depends on: stage 3 issue 1
- yolo: no — deletes a 1.5k-line module; user-facing batch entry.
- Published: #658

## Later (unstaged)

- Promote `_register_family` to public documented API after one release of use.
- Remove `interactive=`, `xlim`/`ylim`, and `summary_plot_legacy` shims on the
  2.1 cadence (already registered where introduced).
- Optional: unify `cycle_info_plot` matplotlib to multi-cycle (behaviour change).
- Collectors *collection* redesign and batch v3 — separate epics / 2.1
  (`cellpy2-collectors-redesign-plan.md`, `cellpy2-batch-redesign-plan.md`).
- Move residual `_check_*` smoke helpers out of `plotutils.py` into `dev/` +
  tests if any remain after the ports.
- Docs pass: `docs/api/plotting.md` grows with prepare/registry/backends once
  Stage 1 lands; migration guide plotting section updated when Stage 3 deletes
  `batch_plotters`.
