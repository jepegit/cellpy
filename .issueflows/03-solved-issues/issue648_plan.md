# Issue #648 — Plan: `ica_plot` / `dva_plot` on prepare→spec→render

## Goal

Register ICA/DVA figure families that consume the specced long frames from [`cellpy.ica`](cellpy/ica.py) (`dqdv` / `dvdq`), add prepare + backend `kind` branches, and expose public `ica_plot` / `dva_plot` (plotutils + re-exports). New figure-spec oracle cases green. Honour cell-centric `direction`. No use of deprecated `Converter` / wide-frame helpers.

## Constraints

- Plan of record: [`architecture-plan/cellpy2-plotting-redesign-plan.md`](../architecture-plan/cellpy2-plotting-redesign-plan.md) Phase 3; epic [`.issueflows/05-epics/epic567_plan.md`](.issueflows/05-epics/epic567_plan.md) Stage 2 (Published: #648). ICA data contract: [`cellpy2-ica-redesign-plan.md`](../architecture-plan/cellpy2-ica-redesign-plan.md) + migration notes (#566 / #591).
- Depends on #647 (merged): prepare/`kind` dispatch pattern.
- Design notes: [`plotting-prepare.md`](.issueflows/04-designs-and-guides/plotting-prepare.md), [`plotting-backends.md`](.issueflows/04-designs-and-guides/plotting-backends.md), [`plotting-registry.md`](.issueflows/04-designs-and-guides/plotting-registry.md).
- **Direction display (locked):** when `direction="both"`, plot **both halves in one figure**. Same line/marker style for charge and discharge (no dash/solid split). Plotly hover includes `direction` (and cycle). Matplotlib: identical props; reader infers half from curve shape.
- **Trace identity:** one series per `(cycle, direction)` so half-cycles are **not** connected end-to-end; color scale still keyed by `cycle` (both halves of a cycle share color).
- Math stays in `cellpy.ica` — prepare only calls `dqdv` / `dvdq` and builds `FigureSpec`.
- Collectors’ `ica_plotter` / film layouts stay out of scope (Stage 3).
- Oracle: add cases and **commit** updated `tests/data/figure_specs.json` in the same PR.

### Prior art

- Mirror `#647` / `#646`: [`prepare/raw.py`](cellpy/plotting/prepare/raw.py), [`prepare/curves.py`](cellpy/plotting/prepare/curves.py), registry families with `extras={"entry_point", "kind"}`, backend `kind` branches in [`plotly.py`](cellpy/plotting/backends/plotly.py) / [`mpl.py`](cellpy/plotting/backends/mpl.py), thin orchestrators in [`plotutils.py`](cellpy/utils/plotutils.py).
- Data: [`cellpy.ica.dqdv`](cellpy/ica.py) / `dvdq` → columns via `ICA_COLS` (`cycle`, `direction`, `voltage`, `capacity`, `dqdv` / `dvdq`). Defaults: `direction="both"`, DVA uses `DVA_DEFAULTS` (normalize=False).
- Collectors [`ica_plotter`](cellpy/utils/collectors.py) (~2858): single-direction default, x=voltage y=dqdv — **do not** copy its direction clamp; new public API matches `ica.dqdv` defaults.
- Oracle menu: [`tests/figure_spec_support.py`](tests/figure_spec_support.py) `_other_family_cases()`.
- Toolbox: none relevant. Graphify: plotting/ICA migration communities only.

## Approach

```mermaid
flowchart LR
  entry["ica_plot / dva_plot"] --> ctx["from_source"]
  ctx --> reg["registry.get ica|dva"]
  reg --> prep["prepare/ica.py"]
  prep --> ica["ica.dqdv / dvdq"]
  ica --> spec["frame + FigureSpec kind=ica|dva"]
  spec --> be["get_backend.render"]
```

1. **Register families** in [`registry.py`](cellpy/plotting/registry.py)
   - `"ica"` — `extras={"entry_point": "ica_plot", "kind": "ica"}`; columns voltage/dqdv (+ cycle, direction).
   - `"dva"` — `extras={"entry_point": "dva_plot", "kind": "dva"}`; columns capacity/dvdq (+ cycle, direction).
   - Excluded from summary oracle via `entry_point` filter (same as cycles/raw).

2. **One prepare module** [`cellpy/plotting/prepare/ica.py`](cellpy/plotting/prepare/ica.py)
   - Shared `IcaPrepareConfig`: `cycles`, `direction` (default `"both"`), `options` / IcaOptions field overrides, title/size/colormap knobs, `backend`, `additional_kwargs`, plus `derivative: "dqdv" | "dvdq"`.
   - `prepare(ctx, family, config) -> (frame, FigureSpec)`:
     - Call `ica.dqdv(cell, ...)` or `ica.dvdq(cell, ...)` only (never `Converter`, `to_wide`, or legacy `split`/`tidy` paths).
     - Drop deprecated duplicate `dq` column from the plotting frame if present (avoid accidental y-column confusion).
     - Build `FigureSpec` with one panel; axis labels via `plotting.labels` / `units_label` where units are known; stash render knobs in `extras` (`kind`, x/y columns, color=`cycle`, hover fields including `direction`, colormap, ranges, title).
   - Export from [`prepare/__init__.py`](cellpy/plotting/prepare/__init__.py).

3. **Backend branches** (`kind == "ica"` | `"dva"`)
   - Plotly: multi-trace lines colored by cycle; hovertemplate / `hover_data` includes `direction` (and cycle). Do **not** vary dash by direction. Prefer grouping that yields one trace per `(cycle, direction)` with color mapped from cycle.
   - Matplotlib: same; legend by cycle; no direction linestyle. Accept visual overlap of styles.
   - Keep branches small; share a private helper if ica/dva differ only by x/y column names from extras.

4. **Public entry points** in [`plotutils.py`](cellpy/utils/plotutils.py)
   - `ica_plot(cell, cycles=None, direction="both", backend=None, interactive=None, **kwargs)` and `dva_plot(...)` — same `backend=` / deprecated `interactive=` `warn_once` pattern as `raw_plot`.
   - Orchestrate: resolve backend → `from_source` → `registry.get` → prepare → `get_backend(...).render`.
   - Re-export from [`cellpy.plotting`](cellpy/plotting/__init__.py) and keep plotutils as the permanent import path (existing convention).
   - Seed `interactive=` deprecations in [`_deprecation.py`](cellpy/_deprecation.py) + `DEPRECATIONS.md` if that pattern is registered for peer entry points.

5. **Oracle + tests**
   - Add to `_other_family_cases()`: `ica_plot` × both backends, `dva_plot` × both backends (defaults enough for structural snapshot; golden cell already used by figure specs / ICA goldens).
   - Focused unit tests: prepare returns correct `kind` + frame columns; `direction="both"` keeps both labels; no `Converter` import in prepare; `interactive=` warns+maps.
   - Regenerate `tests/data/figure_specs.json` in the same commit.

6. **Design notes** — update `plotting-prepare.md`, `plotting-backends.md`, `plotting-registry.md` for ica/dva.

## Files to touch

| Path | Change |
|---|---|
| `cellpy/plotting/prepare/ica.py` | **new** — dqdv/dvdq prepare + FigureSpec |
| `cellpy/plotting/prepare/__init__.py` | export prepare_ica (and alias if useful) |
| `cellpy/plotting/registry.py` | register `"ica"`, `"dva"` |
| `cellpy/plotting/backends/plotly.py` | `kind` ica/dva render |
| `cellpy/plotting/backends/mpl.py` | same |
| `cellpy/utils/plotutils.py` | `ica_plot` / `dva_plot` orchestrators |
| `cellpy/plotting/__init__.py` | re-export entry points if peers are exported |
| `cellpy/_deprecation.py` + `DEPRECATIONS.md` | `interactive=` for new entry points |
| `tests/figure_spec_support.py` | four new FigureCases |
| `tests/data/figure_specs.json` | regenerate |
| `tests/test_ica_plot_prepare.py` (name flexible) | prepare / direction / deprecation |
| `.issueflows/04-designs-and-guides/plotting-*.md` | document |
| `.issueflows/01-current-issues/issue648_plan.md` | persist this plan (on Accept) |
| `.issueflows/01-current-issues/issue648_status.md` | start status on build |

## Test strategy

```bash
uv sync --extra batch
MPLBACKEND=Agg uv run pytest tests/test_ica_plot_prepare.py tests/test_figure_specs.py -q
MPLBACKEND=Agg uv run pytest -m essential --ignore=tests/test_arbin_variants_two_stage.py
```

(Conda `cellpy_dev_313` acceptable per project rules if preferred locally.)

## Open questions

None remaining for coding — direction overlay + shared styling + plotly hover decided.

## Scope check

Single coherent deliverable (two entry points, one prepare module, two registry families). Fits one PR. Collectors rebase stays Stage 3.
