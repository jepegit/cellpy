# Issue #646 — Plan: port `cycles_plot` to prepare→spec→render

## Goal

Route public `cycles_plot` through **context → registry → prepare → backend.render**: add `cellpy/plotting/prepare/curves.py` (voltage–capacity frame + `FigureSpec`), register a cycles family, move the private plotly/matplotlib layout forks into the shared backends, and collapse dual range kwargs to one spelling with `warn_once` aliases. Oracle green both backends; no private layout left inside `cycles_plot`.

## Constraints

- Plan of record: [`architecture-plan/cellpy2-plotting-redesign-plan.md`](../../../architecture-plan/cellpy2-plotting-redesign-plan.md) Phase 3 / §1.3 (`x_range`/`y_range` vs `xlim`/`ylim`); epic [`.issueflows/05-epics/epic567_plan.md`](../05-epics/epic567_plan.md) Stage 2 issue 1.
- Depends on #639 (merged): `get_backend("plotly"|"matplotlib")`, `Backend.render(frame, spec)`, `warn_once` + `DEPRECATIONS.md` pattern for `interactive=`.
- Design notes: [`plotting-prepare.md`](../04-designs-and-guides/plotting-prepare.md), [`plotting-backends.md`](../04-designs-and-guides/plotting-backends.md), [`plotting-registry.md`](../04-designs-and-guides/plotting-registry.md).
- Oracle gate: `tests/test_figure_specs.py` `cycles_plot[plotly|matplotlib]` green **without** intentional `figure_specs.json` regen unless a proven structural change is required.
- Scope is **`cycles_plot` only** — do not port `raw_plot` / `cycle_info_plot` (#647) or ICA/DVA (#648).
- Preserve user-facing defaults where possible (`return_data`, `return_figure` / `fig.show()` behaviour, formation split, capacity mode / interpolation knobs).
- Not yolo — dual kwargs + curves adapter + second family in backends.

### Prior art

- `cycles_plot` + `CyclesPlotterConfig` + `_cycles_plotter_plotly` / `_cycles_plotter_matplotlib` — `cellpy/utils/plotutils.py` (~2070–2550). Today: `c.get_cap(...)` → sort → formation/rest split → private layout forks; `x_range`/`y_range` overwrite `xlim`/`ylim`; `interactive=` bool (not `backend=` yet).
- `summary_plot` orchestration (#638/#639) — `cellpy/utils/plotutils.py`: resolve `backend=` / deprecated `interactive=` → `from_source` → `prepare.summary.prepare` → `get_backend(...).render`. **Mirror this shape.**
- `prepare/summary.py` — contract `prepare(ctx, family, config) -> (frame, FigureSpec)`; render knobs in `spec.extras`.
- `PlotlyBackend` / `MatplotlibBackend` — currently **summary-only** `render` (formation facet / `sns.relplot`). Cycles need a **second render branch**, not the summary formation engine.
- Registry (`PlotFamily`) — summary `y=` names today; cycles is a single fixed family (no `y=` selector). Still register for `families()` / prepare routing / Stage-3 collectors reuse.
- Curve source: public `CellpyCell.get_cap` → `cellpy.readers.capacity_curves.get_cap` (native `CurveCols` names). `cellpycore.curves.get_cap_curve` exists on the pinned core; issue text prefers it with `c.get_cap` fallback (architecture risk table).
- Labels: `_get_capacity_unit` + `with_cellpy_unit("Voltage", ...)` in plotutils; prefer `units_label` / plotting.labels where already used by summary prepare.
- Deprecations: `cellpy._deprecation.warn_once` + `DEPRECATIONS.md` (summary already registered `summary_plot(interactive=...)`).
- Oracle: `tests/figure_spec_support.py` still passes `interactive=True/False` for cycles cases.
- Toolbox / graphify: nothing relevant (`00-tools/` scanners unrelated; no `graphify-out/`).

## Approach

1. **Register a cycles family** in `cellpy/plotting/registry.py`  
   - Name: `"cycles"` (description: voltage vs capacity by cycle).  
   - `column_builder` can return the curve column ids used in the tidy frame (`capacity`, CurveCols `potential` / `cycle_num`) or a no-op list — cycles is not selected via `y=`.  
   - `supports_formation=True`.  
   - Do not break summary `families()` consumers: oracle summary menu stays derived from summary names only (or filter by a small `extras["menu"]` / keep cycles out of `SUMMARY_FAMILIES` — today menu is hardcoded in `figure_spec_support`, so registering `"cycles"` is fine).

2. **`cellpy/plotting/prepare/curves.py`**
   - Public: `prepare(ctx, family, config) -> tuple[pd.DataFrame, FigureSpec]`.
   - **Curve load (one seam):** `_load_curve_frame(ctx, cycles, **get_cap_kwargs)`  
     - Prefer `cellpycore.curves.get_cap_curve` when the cell exposes core-ready data/schema **and** the resulting pandas frame matches today's column contract (`capacity`, `potential`, `cycle_num`, `direction`, …).  
     - Else fall back to `ctx.cell.get_cap(...)` (current path — oracle-stable).  
     - Keep the same kwargs currently passed (`method`, `interpolated`, `label_cycle_number`, `categorical_column`, `number_of_points`, `insert_nan`, `mode`, `cycle_mode`, `inter_cycle_shift`).
   - Sort by cycle/direction; split formation vs rest; compute capacity unit + title strings.
   - Emit `FigureSpec`: single panel, `x_axis`/`y_axis` labels + ranges from resolved `x_range`/`y_range`, `supports_formation` from config, title; stash cycles-specific render knobs in `extras` (`kind="cycles"`, form/rest frames or markers, colormap / colorbar flags, figsize/width/height, seaborn style knobs, plotly template, `n_form_cycles` / `n_rest_cycles`, etc.). Prefer one tidy `frame` (full `df`) plus selectors/extras rather than forcing backends to re-fetch.

3. **Backend cycles branch**
   - In `PlotlyBackend.render` / `MatplotlibBackend.render`: if `spec.extras.get("kind") == "cycles"` (or equivalent), run the ported `_cycles_plotter_*` logic; else keep today's summary path.
   - Delete `_cycles_plotter_plotly` / `_cycles_plotter_matplotlib` (and ideally `CyclesPlotterConfig` if fully absorbed into prepare config/`FigureSpec`) from the live `cycles_plot` path — **no private layout fork left in `cycles_plot`**.
   - Mechanical port first (oracle parity); do not redesign colorbar / px.line vs scatter heuristics in this issue.

4. **Thin public `cycles_plot`**
   - Keep the function in `cellpy.utils.plotutils` (permanent re-export home).
   - Add `backend: Optional[str] = None`; change `interactive` default to `None` (same resolution order as `summary_plot`: warn on explicit `interactive=`, honour `backend=` if set, default `"plotly"`).
   - **Range kwargs:** canonical spelling = `x_range` / `y_range` (align with `summary_plot` + architecture deprecation table). `xlim` / `ylim` become `warn_once` aliases → map into `x_range`/`y_range` when the canonical args are unset; if both set, prefer canonical after warning. Register in `_deprecation` seed + regen `DEPRECATIONS.md` (removal 2.1).
   - Orchestration: build config → resolve backend + ranges → `from_source(c)` → `registry.get("cycles")` → `prepare.curves.prepare` → attach live cell/config on extras if mpl still needs them → `get_backend(...).render` → preserve `return_data` / `return_figure` / `fig.show()` semantics.

5. **Tests / oracle harness**
   - Point `cycles_plot[*]` cases at `backend=` (drop `interactive=` to avoid warning noise).
   - Focused tests: prepare returns `(frame, FigureSpec)` with `kind=cycles`; `xlim`/`ylim` warn once and match `x_range`/`y_range`; `interactive=` warn+map; private plotter helpers gone / not imported by `cycles_plot`; oracle green.
   - Prefer **no** `figure_specs.json` regen.

6. **Design notes**
   - Extend [`plotting-prepare.md`](../04-designs-and-guides/plotting-prepare.md) (curves prepare) and [`plotting-backends.md`](../04-designs-and-guides/plotting-backends.md) (cycles branch / `kind`). Brief registry note that non-summary families exist.

## Files to touch

| Path | Change |
|---|---|
| `cellpy/plotting/prepare/curves.py` | **new** — curve load + formation split + `FigureSpec` |
| `cellpy/plotting/prepare/__init__.py` | export / note |
| `cellpy/plotting/registry.py` | register `"cycles"` family |
| `cellpy/plotting/backends/plotly.py` | cycles branch in `render` (port plotly plotter) |
| `cellpy/plotting/backends/mpl.py` | cycles branch in `render` (port matplotlib plotter) |
| `cellpy/utils/plotutils.py` | thin `cycles_plot`; delete private plotters / absorb config |
| `cellpy/_deprecation.py` | seed `cycles_plot(xlim/ylim=...)` (+ `interactive=` if added) |
| `DEPRECATIONS.md` | regen |
| `tests/figure_spec_support.py` | cycles cases → `backend=` |
| `tests/test_cycles_prepare.py` (name flexible) | **new** — prepare / deprecations / no private fork |
| `tests/test_figure_specs.py` | run; adjust only if describe asymmetry notes need wording |
| `.issueflows/04-designs-and-guides/plotting-*.md` | document curves prepare + backend kind |

## Test strategy

```bash
uv sync --extra batch
MPLBACKEND=Agg uv run pytest tests/test_cycles_prepare.py tests/test_figure_specs.py -q
MPLBACKEND=Agg uv run pytest -m essential --ignore=tests/test_arbin_variants_two_stage.py
```

Parity focus: default oracle cell × both backends; formation on/off; range aliases; `return_data` frame columns match pre-port `get_cap` shape on the oracle cell.

## Open questions

1. **Canonical range spelling** — **Recommend:** keep `x_range`/`y_range`; deprecate `xlim`/`ylim` (matches `summary_plot` + architecture plan). Alternative: keep `xlim`/`ylim` because docstring/examples emphasize them — rejected (inconsistent API).
2. **Also flip `backend=` / deprecate `interactive=` on `cycles_plot` in this PR?** — **Recommend:** yes (same pattern as #639; oracle harness already needs updating; epic backend policy is global). Alternative: leave `interactive=` only until a later cleanup — leaves Stage-2 API half-migrated.
3. **`cellpycore.curves` vs `c.get_cap` for this PR** — **Recommend:** implement the load seam; use `c.get_cap` as the default working path so the oracle does not drift; attempt core `get_cap_curve` only when it can be proven column-/row-equivalent (or behind a small internal helper that falls back immediately on mismatch/ImportError). Alternative: hard-require core first — higher risk of snapshot churn with little user benefit.
4. **How backends dispatch** — **Recommend:** `spec.extras["kind"] == "cycles"` branch inside existing `render` methods (mechanical port). Alternative: separate `CyclesPlotlyBackend` class — rejected (breaks `get_backend` two-name API).

## Scope check

One Stage-2 slice: prepare/curves + registry family + backend cycles branch + thin public API + deprecations. Fits a single PR. Follow-ups already published: #647 (`raw_plot` / `cycle_info_plot`), #648 (ICA/DVA).
