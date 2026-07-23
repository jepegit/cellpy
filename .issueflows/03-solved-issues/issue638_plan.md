# Issue #638 — Plan: port summary prepare path; flip `summary_plot` to prepare→spec→render

## Goal

Make public `summary_plot` run **context → registry → prepare → backend.render** for the interactive (plotly) path: extract prepare into `cellpy/plotting/prepare/summary.py` (emitting a tidy frame + real `FigureSpec`), absorb `PlotlyPlotBuilder` into `PlotlyBackend.render`, and leave no third parallel summary prepare/render path. Preserve signature, defaults, and `return_data` frame shape.

## Constraints

- Plan of record: [`architecture-plan/cellpy2-plotting-redesign-plan.md`](../../../architecture-plan/cellpy2-plotting-redesign-plan.md) §3.1 / Phase 2 items 2–3; epic [`.issueflows/05-epics/epic567_plan.md`](../05-epics/epic567_plan.md) Stage 1 issue 3.
- Depends on #636/#637 (merged): registry + `FigureSpec` exist; formation layout lives in `backends/plotly.py`; `PlotlyBackend.render` is provisional/incomplete; public path still uses `SummaryPlotDataPreparer` + `PlotlyPlotBuilder` / `SeabornPlotBuilder`.
- Oracle gate: `tests/test_figure_specs.py` green for all summary families × both backends currently covered (**no** intentional `figure_specs.json` regen unless a proven intentional visual change).
- Do **not** add `backends/mpl.py` or delete `SeabornPlotBuilder` (that is #639). Do **not** port collectors / batch faceting.
- User-facing `summary_plot` signature and defaults stay verbatim (including named `y=` and `return_data=True`).
- Not yolo — flag-day for the main plot entry; needs careful parity.

### Prior art

- `SummaryPlotDataPreparer` — `cellpy/utils/plotutils.py` (~1008–1420). Filters, rate rescale, normalization, formation marking, CV / fullcell / standard melts → tidy frame + metadata dict (`data`, `number_of_rows`, labels, cycle bounds, `formation_cycle_selector`).
- `PlotlyPlotBuilder.build_plot` — same module (~1429–1853). Owns `px.line` construction, hover/facet kwargs, formation adapter → `configure_formation_layout`, **no-formation** layout (`_configure_no_formation_axes`), legend prettify, rangeslider / share_y. This is what must land inside `PlotlyBackend.render` (or helpers it calls).
- `SeabornPlotBuilder` — same module (~1856+). Stays until #639; must consume the **same** prepared frame from the new prepare module.
- `PlotlyBackend.render` — `cellpy/plotting/backends/plotly.py`. Minimal `px.line` + formation via `extras`; missing no-formation, legend convert, height defaults, hover, fullcell post-steps wiring from config, etc. `CELLPY_SUMMARY_PLOTLY_SPEC` / `use_spec_render()` exist but are **not** wired into `summary_plot` today.
- `SummaryPlotInfo` + registry — column sets / labels already registry-backed (#636); prepare keeps using them (or equivalent) rather than reinventing column tables.
- Architecture sketch: `context.from_source` → `registry.get` → `prepare.summary.prepare` → `backends.get(backend).render` — no `context.py` yet.
- Toolbox / graphify: nothing relevant.

## Approach

1. **Minimal context adapter** — add `cellpy/plotting/context.py` with a thin `CellContext` (or `from_source(c)`) that exposes what prepare/render need from a `CellpyCell` (`data.summary`, headers/schema, `make_summary`, `cell_name`, units helpers). BatchContext is out of scope. `summary_plot` builds context once and passes it into prepare (and into plotly render only where cell-bound labels still need it, e.g. capacity units / title).

2. **`cellpy/plotting/prepare/summary.py`**
   - Move `SummaryPlotDataPreparer` here ( mechanistically; keep private helpers). Public function shape aligned with the plan of record:

     ```python
     def prepare(ctx, family, config) -> tuple[pd.DataFrame, FigureSpec]:
         ...
     ```

   - Still produce today’s tidy long frame (same columns / dtypes / row marks for formation and panel `row`).
   - Build a **real** `FigureSpec`: panels from family/row count; `x_axis` / per-panel `y_axis.range` from config (`y_range`, `ce_range`, `norm_range`, `cv_share_range`); `supports_formation` from family + `config.show_formation`; put render knobs that are not yet first-class fields into `spec.extras` (x column name, `y_header`, plotly facet keys, formation domains/ranges once computed, fullcell domain kwargs, height/markers/template flags, etc.). Prefer computing formation domain/range numbers in prepare (or a small shared helper) so `render` stays declarative.
   - Delete the class from `plotutils` (or leave a thin re-export alias only if something external imports it — prefer delete; nothing in tests should import the class name).

3. **Complete `PlotlyBackend.render(frame, spec)`**
   - Port the body of `PlotlyPlotBuilder.build_plot` (including **no-formation** path and legend conversion) to operate from `(frame, FigureSpec)` + whatever tiny cell-bound bits remain on context/extras.
   - Formation continues to call `configure_formation_layout` / `configure_fullcell_standard_domains`.
   - Delete `PlotlyPlotBuilder` from the live path (class removed or reduced to a one-liner deprecated shim that calls the backend — prefer remove).
   - Remove the provisional `CELLPY_SUMMARY_PLOTLY_SPEC` dual-path concept (flag unused today): interactive path **always** uses `PlotlyBackend.render`. No third path.

4. **Flip `summary_plot`**
   ```text
   config → resolve columns → CellContext
        → registry.get(y) / SummaryPlotInfo as needed
        → prepare.summary.prepare(ctx, family, config) → frame, spec
        → if interactive: PlotlyBackend().render(frame, spec)
          else: SeabornPlotBuilder().build_plot(frame, prepared_meta_or_spec, …)
        → return_data ? (fig, frame) : fig
   ```
   - `interactive=False` keeps `SeabornPlotBuilder` until #639, but it must use the **same** `frame` from `prepare/summary.py` (adapt its `prepared_data_info` needs from `FigureSpec` / a small metadata side-channel if required — do not re-run preparer logic).
   - Keep the public function in `cellpy.utils.plotutils` for this PR (permanent re-export home already decided); no API move to `cellpy.plotting.summary_plot` required here.

5. **Package exports**
   - `cellpy/plotting/prepare/__init__.py` (+ optional `summary` re-export).
   - Light updates to `cellpy/plotting/__init__.py` / `backends` docs; update [`.issueflows/04-designs-and-guides/plotting-backends.md`](../04-designs-and-guides/plotting-backends.md) and add a short prepare note (or extend registry/backends docs) recording the flip.

6. **Parity / tests**
   - Oracle: all summary families × plotly + seaborn paths green.
   - Add focused tests: prepare returns `(frame, FigureSpec)` with expected panel count / extras keys for 1–2 representative families; `return_data` columns match pre-flip shape on the oracle cell; asserting `PlotlyPlotBuilder` is gone (or not imported by `summary_plot`).
   - Existing `tests/test_plotutils_summary_plot.py` stays green.

## Files to touch

| Path | Change |
|---|---|
| `cellpy/plotting/context.py` | **new** — minimal `CellContext` / `from_source` |
| `cellpy/plotting/prepare/__init__.py` | **new** |
| `cellpy/plotting/prepare/summary.py` | **new** — port of `SummaryPlotDataPreparer` + `FigureSpec` emission |
| `cellpy/plotting/backends/plotly.py` | complete `render`; drop unused spec-render env gate; own no-formation layout |
| `cellpy/plotting/backends/__init__.py` | drop/adjust `use_spec_render` exports if removed |
| `cellpy/plotting/spec.py` | only if documented `extras` keys or small field tweaks needed |
| `cellpy/utils/plotutils.py` | thin `summary_plot` orchestration; delete preparer + `PlotlyPlotBuilder`; keep `SeabornPlotBuilder` + helpers still shared |
| `cellpy/plotting/__init__.py` | optional exports |
| `tests/test_summary_prepare.py` (name flexible) | **new** — prepare + return_data / spec shape |
| `tests/test_figure_specs.py` / `test_plotutils_summary_plot.py` / `test_plotly_backend_layout.py` | run; adjust imports if builders move |
| `.issueflows/04-designs-and-guides/plotting-backends.md` (+ prepare note) | document the flip |

## Test strategy

```bash
uv sync --extra batch
MPLBACKEND=Agg uv run pytest tests/test_summary_prepare.py tests/test_plotly_backend_layout.py tests/test_plotutils_summary_plot.py tests/test_figure_specs.py -q
MPLBACKEND=Agg uv run pytest -m essential --ignore=tests/test_arbin_variants_two_stage.py
```

Parity focus: formation on/off, CE / with_rate / CV-split / fullcell families, `return_data` columns/dtypes on the oracle cell, both `interactive=True/False`.

## Open questions

1. **How thin is `context.py`?** — **Recommend:** minimal `CellContext` wrapping one `CellpyCell` (attributes/methods prepare already needs). No BatchContext. Alternative: skip new module and pass `c` into prepare until collectors stage — weaker vs issue text (“context adapter”).
2. **`SeabornPlotBuilder` this PR?** — **Recommend:** keep as the only `interactive=False` renderer, fed by the new prepare output; delete only `PlotlyPlotBuilder` + old preparer. Meets “no third path” (one prepare, plotly via backend, seaborn temporary). Alternative: also stub mpl backend early — rejected (belongs to #639).
3. **Escape-hatch env flag?** — **Recommend:** no dual path after flip (remove `CELLPY_SUMMARY_PLOTLY_SPEC`). Oracle + existing unit tests are the safety net; a legacy flag would reintroduce the third path the issue forbids. Alternative: keep `CELLPY_LEGACY_SUMMARY_PLOTLY=1` for one release — only if Accept asks for it.
4. **Where formation domain/range math lives** — **Recommend:** compute in prepare (or a shared helper used by prepare) and stash on `FigureSpec.extras`, so `render` applies layout without re-reading the frame for cycle bounds. Alternative: keep that math inside `PlotlyBackend` (closer to today’s builder) — acceptable if it unblocks parity faster; still one path.

## Scope check

Single Stage-1 flag-day PR: prepare module + context stub + complete plotly render + `summary_plot` flip + delete preparer/`PlotlyPlotBuilder`. Fits one PR. Follow-up already published: #639 (mpl backend; retire seaborn builder).
