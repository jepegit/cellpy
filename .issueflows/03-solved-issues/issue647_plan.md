# Issue #647 — Plan: port `raw_plot` and `cycle_info_plot` to prepare→spec→render

## Goal

Route public `raw_plot` and `cycle_info_plot` through **context → registry → prepare → backend.render**: add `prepare/raw.py` and `prepare/steps.py`, register two families, move private plotly/matplotlib layout into shared backends (`kind` branches), and replace hand-composed unit f-strings with `units_label()` helpers via `plotting.labels`. Oracle green for both functions × both backends. Keep `cycle_info_plot` matplotlib single-cycle asymmetry.

## Constraints

- Plan of record: [`architecture-plan/cellpy2-plotting-redesign-plan.md`](../../../architecture-plan/cellpy2-plotting-redesign-plan.md) Phase 3; epic [`.issueflows/05-epics/epic567_plan.md`](../05-epics/epic567_plan.md) Stage 2 issue 2 (Published: #647).
- Depends on #646 (merged): `prepare/curves.py`, `spec.extras["kind"]` dispatch, `backend=` / `interactive=` warn_once pattern.
- Design notes: [`plotting-prepare.md`](../04-designs-and-guides/plotting-prepare.md), [`plotting-backends.md`](../04-designs-and-guides/plotting-backends.md), [`plotting-registry.md`](../04-designs-and-guides/plotting-registry.md).
- Epic already decided: **do not** expand matplotlib `cycle_info_plot` to multi-cycle unless trivial + oracle-covered (default: keep asymmetry).
- Oracle gate: `tests/test_figure_specs.py` cases `raw_plot[*]` and `cycle_info_plot[*]` green; prefer **no** intentional `figure_specs.json` regen.
- Scope: these two entry points only — not ICA/DVA (#648), not collectors.
- Acceptance: no new hard-coded legacy header names; no hand-composed unit f-strings in these two code paths.

### Prior art

- `raw_plot` — `cellpy/utils/plotutils.py` (~1445–1712): copy `cell.data.raw`, resolve columns via `_LiveHeaders(cell, "raw")`, build y-lists from `plot_type` / explicit `y`, optional time-unit x column via pint `Q`, then **inline** plotly (`px.line` / `make_subplots`) or matplotlib (single / twin / nrows). Labels today: `f"Voltage ({cell.data.raw_units.voltage})"` etc. Public switch still `interactive=` (bool), not `backend=`.
- `cycle_info_plot` + `_cycle_info_plot_plotly` / `_cycle_info_plot_matplotlib` / `_get_info` / `_plot_step` — same module (~1715–2055). Merge scaled raw + step-table deltas; plotly multi-cycle hover; matplotlib single-cycle twin + step spans. Headers already `_LiveHeaders` (Phase 0); matplotlib still warns on multi-cycle.
- `#646` mirror — `prepare/curves.py` + `registry` family `"cycles"` + `extras["kind"]=="cycles"` in `PlotlyBackend` / `MatplotlibBackend` + thin public orchestrator in `plotutils`. **Mirror this shape twice** (raw + cycle_info).
- `_LiveHeaders` — `plotutils.py` (~551+): schema-backed per-cell header resolution. Required for both prepares; do not reintroduce module-level `get_headers_*()` singletons.
- `units_label` — `cellpy/units.py`; already used in summary/curves prepare. Issue asks extension of `cellpy/plotting/labels.py` beyond legend/marker helpers.
- `CellContext` — `cellpy/plotting/context.py`: summary-oriented today; prepares can reach `ctx.cell` (same as curves) rather than expanding context in this issue.
- Oracle: `tests/figure_spec_support.py` `_other_family_cases()` — both functions × both backends (still `interactive=`).
- Smoke: `tests/test_plotutils_headers.py` (`test_raw_plot_*`, `test_cycle_info_plot_*`).
- Toolbox: scanners unrelated. Graphify present but no need to query beyond known plotting communities — prior art from #646 + plotutils is sufficient.

## Approach

1. **Register two families** in `cellpy/plotting/registry.py`  
   - `"raw"` — `extras={"entry_point": "raw_plot", "kind": "raw"}`.  
   - `"cycle_info"` — `extras={"entry_point": "cycle_info_plot", "kind": "cycle_info"}`.  
   - `column_builder` can list the columns the prepare actually uses (raw: voltage/current/… stems; cycle_info: time/voltage/current + step stats). Keep them out of the summary oracle menu (same pattern as `"cycles"` / `families(entry_point=...)`).

2. **`cellpy/plotting/prepare/raw.py`**  
   - `RawPrepareConfig` mirrors public `raw_plot` args (`y`, `y_label`, `x`, `x_label`, `title`, `plot_type`, `double_y`, size knobs, backend, `additional_kwargs`).  
   - `prepare(ctx, family, config) -> (frame, FigureSpec)`:  
     - Resolve headers via `_LiveHeaders` (import from plotutils **or** move helper into `cellpy.plotting.headers` if the import cycle is ugly — prefer move only if needed).  
     - Build the plotting frame (including synthetic `test_time_hrs` / days / years columns).  
     - Emit `FigureSpec` with panels/axes describing the subplot layout (1 row, twin-y, or N rows); put render knobs in `extras` (`kind="raw"`, `y` column list, labels, `double_y`, height heuristics, `backend`, kwargs).  
   - Axis labels: go through new helpers in `plotting.labels` (see step 4) — no `f"... ({raw_units...})"` in prepare or backends.

3. **`cellpy/plotting/prepare/steps.py`** (cycle-info family)  
   - `CycleInfoPrepareConfig`: `cycle`, `t_unit` / `v_unit` / `i_unit`, `get_axes`, title/size knobs, backend, kwargs.  
   - Prepare: compute scalers (`unit_scaler_from_raw`), filter/merge raw+steps (same columns as today), attach scaled series on the returned frame; stash step-annotation inputs / hover customdata columns in `extras` as needed so backends do not re-query the cell.  
   - Matplotlib single-cycle clamp stays in prepare **or** the mpl branch (warn + take first) — behaviour unchanged.  
   - `FigureSpec.extras["kind"] = "cycle_info"`.

4. **`plotting.labels` axis helpers**  
   - Add small formatters, e.g. `quantity_label(name, unit)` → `"Voltage (V)"`, and/or thin wrappers that call `units_label(physical_property, ..., units=...)` then compose the display name.  
   - **Raw path:** prefer labelling from the cell’s **raw** unit spec when that is what the series still carries (today’s behaviour); if `units_label` only accepts `CellpyUnits`, pass `cell.raw_units` when compatible, else format via the helper using the same unit strings the frame was scaled with (cycle_info already has explicit `t_unit`/`v_unit`/`i_unit`).  
   - Goal: zero hand-rolled `f"{name} ({unit})"` left in the two public paths / their private helpers.

5. **Backend branches**  
   - In `PlotlyBackend.render` / `MatplotlibBackend.render`:  
     - `kind == "raw"` → port current inline raw layout.  
     - `kind == "cycle_info"` → port `_cycle_info_plot_*` (plus keep `_get_info` / `_plot_step` as private backend or prepare helpers).  
     - else existing summary / cycles paths.  
   - Mechanical port first (oracle parity). Delete the live private forks from `plotutils` once unused.

6. **Thin public entry points** in `cellpy/utils/plotutils.py`  
   - Same orchestration as `cycles_plot`: resolve `backend=` vs deprecated `interactive=` (`warn_once`, removal 2.1) → `from_source` → `registry.get(...)` → prepare → `get_backend(...).render`.  
   - Preserve `raw_plot` return figure; preserve `cycle_info_plot` `get_axes` / `fig.show()` / matplotlib axes semantics (including plotly default show + `None` return that the oracle already documents).  
   - Register deprecations in `_deprecation` seed + regen `DEPRECATIONS.md`.

7. **Tests / oracle harness**  
   - Point `raw_plot[*]` / `cycle_info_plot[*]` cases at `backend=` (drop `interactive=` noise).  
   - New focused tests (names flexible): prepare returns `(frame, FigureSpec)` with correct `kind`; `interactive=` warns+maps; no private `_cycle_info_plot_*` left on the public path; header smoke tests still pass.  
   - Prefer no snapshot regen; if axis-title text changes solely because of `units_label` wording, regenerate in the same commit and note it in the PR.

8. **Design notes**  
   - Update `plotting-prepare.md` (raw + steps) and `plotting-backends.md` (`kind` raw / cycle_info). Brief registry note for the two families.

## Files to touch

| Path | Change |
|---|---|
| `cellpy/plotting/prepare/raw.py` | **new** — raw frame + `FigureSpec` |
| `cellpy/plotting/prepare/steps.py` | **new** — cycle-info merge/scale + `FigureSpec` |
| `cellpy/plotting/prepare/__init__.py` | export / note |
| `cellpy/plotting/registry.py` | register `"raw"` and `"cycle_info"` |
| `cellpy/plotting/labels.py` | axis/quantity label helpers via `units_label` |
| `cellpy/plotting/backends/plotly.py` | `kind` branches for raw + cycle_info |
| `cellpy/plotting/backends/mpl.py` | same |
| `cellpy/utils/plotutils.py` | thin `raw_plot` / `cycle_info_plot`; delete private layout helpers |
| `cellpy/plotting/headers.py` (optional) | move `_LiveHeaders` only if import cycle forces it |
| `cellpy/_deprecation.py` + `DEPRECATIONS.md` | `interactive=` for both entry points |
| `tests/figure_spec_support.py` | cases → `backend=` |
| `tests/test_raw_prepare.py` / `tests/test_cycle_info_prepare.py` (flexible) | **new** — prepare / deprecations / no private fork |
| `tests/test_plotutils_headers.py` | keep green; adjust kwargs if needed |
| `tests/test_figure_specs.py` | run; regen snapshot only if titles intentionally change |
| `.issueflows/04-designs-and-guides/plotting-*.md` | document the two prepares + kinds |

## Test strategy

```bash
uv sync --extra batch
MPLBACKEND=Agg uv run pytest tests/test_raw_prepare.py tests/test_cycle_info_prepare.py tests/test_plotutils_headers.py tests/test_figure_specs.py -q
MPLBACKEND=Agg uv run pytest -m essential --ignore=tests/test_arbin_variants_two_stage.py
```

Parity focus: default oracle cell × both backends for both functions; `plot_type` smoke for raw; cycle=3 for cycle_info; matplotlib multi-cycle warn + single-cycle behaviour unchanged.

## Open questions

1. **`kind` / registry names** — **Recommend:** `"raw"` / `"cycle_info"` (matches entry points; issue’s `prepare/steps.py` is the module name, not the kind string). Alternative: `"steps"` as kind — slightly clearer file↔kind link, worse API symmetry.
2. **Flip `backend=` / deprecate `interactive=` on both?** — **Recommend:** yes (global epic policy; matches #639/#646; oracle harness update is cheap).
3. **Where `_LiveHeaders` lives** — **Recommend:** keep in `plotutils` and import into prepare unless that creates a cycle; then move to `cellpy/plotting/headers.py`. Do not duplicate.
4. **Raw axis units source** — **Recommend:** label with the unit string that matches the plotted series (today: `raw_units` via a labels helper). Do not silently switch to `cellpy_units` if that changes oracle axis titles. Alternative: always `cellpy_units` — only if we accept snapshot churn.
5. **Matplotlib multi-cycle for `cycle_info_plot`?** — **Recommend:** keep single-cycle asymmetry (epic default). Expanding is a follow-up.

## Scope check

One Stage-2 slice: two prepares + two registry families + two backend kinds + thin public APIs + label helpers + deprecations. Fits a single PR. Follow-up already published: #648 (ICA/DVA).
