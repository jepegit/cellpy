# Issue #637 — Plan: generic plotly panel/formation layout backend

## Goal

Replace the four `PlotlyPlotBuilder._configure_formation_{1,2,3,4}_rows`
methods with **one** N-row formation/facet layout engine in
`cellpy.plotting.backends`, land a `Backend` render protocol, and wire
`PlotlyPlotBuilder` through it without flipping the public `summary_plot`
default to prepare→spec→render (#638).

## Constraints

- Plan of record: [`architecture-plan/cellpy2-plotting-redesign-plan.md`](../../../architecture-plan/cellpy2-plotting-redesign-plan.md) §3.1 / Phase 2 item 1; epic [`.issueflows/05-epics/epic567_plan.md`](../05-epics/epic567_plan.md) Stage 1 issue 2.
- Depends on #636 (merged): `FigureSpec` / `PanelSpec` / `AxisSpec` + registry exist; builders do not consume them yet ([`plotting-registry.md`](../04-designs-and-guides/plotting-registry.md)).
- Oracle gate: `tests/test_figure_specs.py` plotly summary cases must stay green **without** intentional `figure_specs.json` regen.
- Do **not** flip public `summary_plot` to prepare→spec→render (that is #638). Do **not** add `backends/mpl.py` (that is #639).
- Hot path once the layout switch is on: **no** `_configure_formation_{1,2,3,4}_rows` methods remain.
- Not yolo — layout-engine design with visual blast radius.

### Prior art

- `PlotlyPlotBuilder` — `cellpy/utils/plotutils.py` (~1423–2110). Owns `build_plot`, `_configure_formation_axes` (dispatcher), `_configure_formation_{1,2,3,4}_rows` (~350 lines of duplicated axis-domain/match/range logic), `_configure_fullcell_standard_domains`, `_configure_no_formation_axes`, `_auto_range`.
- Formation pattern (verified): for `N` panel rows × 2 facet columns → `2N` x-axes and `2N` y-axes; odd x-axes share formation domain/`matches="x"`, even share rest domain/`matches="x2"`; y-pairs `(y_{2i-1}, y_{2i})` share ranges via `_auto_range`. Special cases today: N=1 annotation y=`1.02`; N=2 efficiency/rate top-row domains; N=4 fullcell range overrides + domain titles.
- Helpers in same module: `PLOTLY_BLANK_LABEL`, `_plotly_label_dict`, `_plotly_top_row_label` (~329–645).
- `cellpy/plotting/spec.py` — scaffolding from #636; extend via `FigureSpec.extras` / panel `y_axis.range` rather than a parallel layout type if possible.
- `cellpy/readers/instruments/contract.py` — existing `typing.Protocol` style to mirror for `Backend`.
- Toolbox / graphify: nothing relevant.

## Approach

1. **`cellpy/plotting/backends/base.py`**
   - `Backend` protocol: `render(self, frame, spec: FigureSpec) -> Any` (and maybe a small `name` / `supports` if useful). Keep it thin — match the architecture-plan sketch.

2. **`cellpy/plotting/backends/plotly.py`** — the real work:
   - Move/port `_auto_range` and the formation layout into one generic function, e.g. `configure_formation_layout(fig, *, n_rows, x_domains, x_ranges, row_y_ranges, show_y_labels_on_right_pane, formation_header, top_row_label=None, …)`.
   - Encode the N-row axis grid in a loop (no per-N methods). Keep the three behavioural specials as **parameters / post-steps**, not new N-branches that re-copy the grid:
     - annotation blank-count = `2*n_rows - 1`; N=1 uses header y=`1.02`
     - optional top-row domain tweak when `top_row_label` is set (today’s N=2 efficiency/rate case)
     - optional `configure_fullcell_standard_domains(...)` call when `fullcell_standard_*` (today’s N=4 post-step)
   - `PlotlyBackend.render(frame, spec)`: minimal viable renderer that can (a) draw a line figure from a tidy frame using `spec` labels/panels where present, and (b) apply `configure_formation_layout` when `spec.supports_formation` / `spec.extras` say so. Full parity with every `build_plot` knob is **not** required if the public path still uses the adapter below — but `render` must be real enough that #638 can call it.

3. **Wire `PlotlyPlotBuilder` (hot path)**
   - `_configure_formation_axes` becomes a thin adapter: compute domains/ranges (today’s preamble through `x_axis_range_*` / `eff_lim`), then call `configure_formation_layout`.
   - **Delete** `_configure_formation_1_row` … `_configure_formation_4_rows`.
   - Leave `_configure_no_formation_axes` in the builder for this PR unless moving it is nearly free (see Open questions).
   - Default: layout engine **on** (no dual-path for the four methods). Oracle must prove parity.

4. **Internal switch for `(frame, FigureSpec)` render (optional dual-path)**
   - Add a narrow internal flag (env or private kwarg, e.g. `CELLPY_SUMMARY_PLOTLY_SPEC=1` / `_use_spec_render=True`) that, after prepare, builds a **provisional** `FigureSpec` from `prepared_data_info` + config (`n_rows` → empty/`PanelSpec` stubs, ranges into `AxisSpec` / `extras`) and calls `PlotlyBackend.render`.
   - Default **off** for the full render path — public `summary_plot` stays on today’s `px.line` + layout adapter until #638 supplies real specs. Document the flag in the status/design note.
   - Goal of the flag: prove the protocol exists and is callable without forcing a public flip.

5. **Exports / package**
   - `cellpy/plotting/backends/__init__.py` exporting `Backend`, `PlotlyBackend` (or `get_backend("plotly")` stub).
   - Do not re-export from `cellpy.utils.plotutils` beyond what the builder needs privately.

6. **Tests**
   - Keep `tests/test_figure_specs.py` plotly summary cases green (formation on by default for summary).
   - Add focused unit tests for the generic layout: N=1..4 produce the expected count of x/y axes + annotation slots; unknown N>4 still raises; fullcell post-step still applied for a 4-row fullcell family.
   - Mark new tests `essential` where they guard the oracle contract cheaply (axis-count / no-per-N-method smoke), heavier figure compares stay in the existing oracle.

7. **Design note** — update or add under `.issueflows/04-designs-and-guides/` (formation layout lives in `backends/plotly.py`; builder is a thin adapter; full render gated until #638).

## Files to touch

| Path | Change |
|---|---|
| `cellpy/plotting/backends/__init__.py` | **new** — package exports |
| `cellpy/plotting/backends/base.py` | **new** — `Backend` protocol |
| `cellpy/plotting/backends/plotly.py` | **new** — generic formation layout + `PlotlyBackend` |
| `cellpy/utils/plotutils.py` | thin `_configure_formation_axes`; delete four `_configure_formation_*_rows`; optional flag branch |
| `cellpy/plotting/spec.py` | only if `extras` / fields need a documented key for formation (prefer no schema break) |
| `cellpy/plotting/__init__.py` | optional light re-export |
| `tests/test_plotly_backend_layout.py` (name flexible) | **new** — N-row layout unit tests |
| `tests/test_figure_specs.py` | run only; regen snapshots only if proven intentional |
| `.issueflows/04-designs-and-guides/plotting-registry.md` or sibling | note backend layout ownership |

## Test strategy

```bash
MPLBACKEND=Agg uv run pytest tests/test_plotly_backend_layout.py tests/test_figure_specs.py -q
MPLBACKEND=Agg uv run pytest -m essential --ignore=tests/test_arbin_variants_two_stage.py
```

Focus oracle cases: summary families with `show_formation=True` (default) across 1–4 row shapes (voltages / CE / CV-split / fullcell).

## Open questions

1. **Scope of `_configure_no_formation_axes`** — **Recommend:** leave in `PlotlyPlotBuilder` this PR; only formation N-row collapse is acceptance-critical. Move no-formation in #638 when `render` owns the whole path.
2. **Full `render(frame, spec)` default** — **Recommend:** layout engine always on; full spec-render path behind internal flag default **off** until #638. Alternative: no flag at all — only extract layout + protocol stub `render` that raises `NotImplementedError` until #638 (weaker vs issue text asking for a thin adapter).
3. **Where fullcell domain titles live** — **Recommend:** keep `configure_fullcell_standard_domains` as a named helper next to the generic engine (called when family/mode says fullcell), not inlined into the N-loop.

## Scope check

One Stage-1 slice: backend package + formation layout collapse + thin builder wire-up. Fits a single PR. Follow-ups already published: #638 (prepare flip), #639 (mpl backend).
