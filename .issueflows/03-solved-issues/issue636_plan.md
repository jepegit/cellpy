# Issue #636 — Plan: FigureSpec dataclasses + PlotFamily registry

## Goal

Move named `summary_plot` y-set selection behind a declarative
`PlotFamily` registry in `cellpy.plotting`, and land the `FigureSpec` /
`PanelSpec` / `AxisSpec` dataclasses the later Stage-1 issues will render.
Drawing still goes through today's builders; only column-set selection
moves.

## Constraints

- Plan of record: [`architecture-plan/cellpy2-plotting-redesign-plan.md`](../../../architecture-plan/cellpy2-plotting-redesign-plan.md) §3.1–3.2 / Phase 1; epic [`.issueflows/05-epics/epic567_plan.md`](../05-epics/epic567_plan.md) Stage 1 issue 1.
- Package home is already `cellpy.plotting` (#595); extend it — do not invent a second home.
- `summary_plot` public signature / figure look stay unchanged. Do **not** flip to prepare→spec→render (that is #637–#639).
- Figure-spec oracle (`tests/test_figure_specs.py` + `tests/data/figure_specs.json`) must stay green **without** regenerating snapshots unless an intentional visual change is proven necessary (it should not be).
- `_register_family` stays provisional (leading underscore) for 2.0 — epic decision.
- Filters stay in `cellpy/filters/` ([`filters-and-plot-filtering.md`](../04-designs-and-guides/filters-and-plot-filtering.md)); this issue does not touch them.
- Today's `_create_col_info` is a big `dict` of y-keys → column lists (+ a parallel `y_transformations` dict), not a literal if/elif. "Mechanical translation" means that table becomes `PlotFamily` records; the preparer's `y_cols.get(y, y)` fallthrough is the selection path to retire.

### Prior art

- `SummaryPlotInfo._create_col_info` / `_create_label_dict` — `cellpy/utils/plotutils.py` (~961–1136, ~822–872). Source of truth for the 20 named y-sets; target of the thin adapter.
- `SummaryPlotDataPreparer.prepare_data` — same module (~1175–1208). Routes by `y.startswith("fullcell_standard_")` / `endswith("_split_constant_voltage")` / else; column lookup via `y_cols.get(y, y)` (silent custom-column fallthrough).
- `SUMMARY_FAMILIES` — `tests/figure_spec_support.py` (~146–167). Duplicate menu of the same 20 names; should derive from the registry after this lands.
- `cellpy.filters.summary.register_range_filter` + unknown-name `ValueError` listing known keys — mirror for `get` / `_register_family` error shape.
- `cellpy/plotting/{figures,labels,theme}.py` + `__init__.py` — existing package pattern (single home, re-exports). Coexist; add `spec` / `registry` beside them.
- Toolbox (`00-tools/`): no helper for this. Graphify: not present. No existing `PlotFamily` / `FigureSpec` types in-tree.

## Approach

1. **`cellpy/plotting/spec.py`** — add frozen dataclasses (scaffolding for #637+; unused by builders in this PR):
   - `AxisSpec` — label, range, unit/mode hooks as optional fields (keep small).
   - `PanelSpec` — columns / kind / y-axis (`AxisSpec`) / optional extras.
   - `FigureSpec` — ordered `panels`, shared x-axis, title, formation/facet flags as needed by later issues.
   - Do **not** invent a parallel render path here.

2. **`cellpy/plotting/registry.py`** — declarative menu:
   - `PlotFamily` frozen dataclass: at least `name`, `description`, `mode` (`gravimetric` / `areal` / `absolute` / `raw` / `None`), `supports_formation`, `supports_cv_split`, plus a **header-bound column resolver** (callable or small strategy) that reproduces today's `y_cols[name]` lists from `c.headers_summary`, and optional transform metadata matching today's `y_transformations` entries.
   - `panels` on `PlotFamily` may stay empty / minimal in this PR (full panel layout is #638); column selection is the acceptance bar.
   - Module-level registry dict populated at import with all 20 current families (same set as `SUMMARY_FAMILIES` / `_create_col_info` keys).
   - API: `get(name) -> PlotFamily` (unknown → `ValueError` listing known names), `families() -> list[tuple[str, str]]` (name + description), `_register_family(family)` (overwrite-with-warning like `register_range_filter`).

3. **Thin adapter in `SummaryPlotInfo`** — `_create_col_info` rebuilds `self.y_cols` / `self.y_trans` (and keeps `x_cols` as today) by resolving every registered family against `c.headers_summary`. Delete the inline column table (or leave a one-line comment pointing at the registry). `_create_label_dict` stays for this PR unless a family description already covers it — labels can migrate later without blocking.

4. **Selection path** — early in `SummaryPlotDataPreparer.prepare_data` (or immediately before column lookup), call `registry.get(y)` so unknown named y-sets fail with the new error. Replace `y_cols.get(y, y)` fallthroughs used for **named** families with registry-backed lookup. Custom raw column strings (today's silent fallthrough) are **dropped** in favour of the issue acceptance criterion; escape hatch is `_register_family` (recommended default — see Open questions).

5. **Exports** — re-export `families`, `_register_family`, and the spec dataclasses from `cellpy.plotting` (`__all__` updated). `cellpy.utils.plotutils` keeps working; no new public names required there.

6. **Tests** — add a focused essential unit test module for registry (known set == `SUMMARY_FAMILIES` or `families()`; unknown raises with names; `_register_family` round-trip). Point `tests/figure_spec_support.SUMMARY_FAMILIES` at `tuple(name for name, _ in plotting.families())` (or import the registry's canonical tuple) so the oracle menu cannot drift. Run figure-spec + essential plotutils tests; no snapshot regen expected.

## Files to touch

| Path | Change |
|---|---|
| `cellpy/plotting/spec.py` | **new** — `AxisSpec` / `PanelSpec` / `FigureSpec` |
| `cellpy/plotting/registry.py` | **new** — `PlotFamily`, built-in families, `get` / `families` / `_register_family` |
| `cellpy/plotting/__init__.py` | export new public/provisional API |
| `cellpy/utils/plotutils.py` | thin `_create_col_info` adapter; `registry.get(y)` on the selection path |
| `tests/figure_spec_support.py` | derive `SUMMARY_FAMILIES` from registry |
| `tests/test_plotting_registry.py` (name flexible) | **new** — essential unit tests for registry behaviour |
| `.issueflows/01-current-issues/issue636_status.md` | created at `/iflow-start` |

## Test strategy

```bash
uv run pytest -m essential
uv run pytest tests/test_figure_specs.py tests/test_plotutils_headers.py
# plus the new registry tests (marked essential)
```

Plotting under `MPLBACKEND=Agg`. Expect figure-spec oracle unchanged (no `figure_specs.json` rewrite).

## Open questions

1. **Custom `y=` column fallthrough** — Today `y_cols.get(y, y)` lets a raw summary column name through. Issue acceptance wants unknown y → clear error. **Recommend:** enforce registry lookup (breaking for undocumented custom strings); users extend via `_register_family`. Alternative: keep fallthrough only when `y` is present as a column on `c.data.summary`.
2. **`PlotFamily.panels` richness this PR** — **Recommend:** leave `panels` empty/minimal; store column/transform resolvers only. Full `PanelSpec` trees land when prepare builds a real `FigureSpec` (#638).
3. **`SUMMARY_FAMILIES` source of truth** — **Recommend:** derive from `plotting.families()` in the same PR so the oracle cannot list a family the registry lacks (and vice versa).

## Scope check

One cohesive Stage-1 slice (registry + spec scaffold + thin adapter). Fits a single PR. Not splitting further. Follow-ups already published: #637 (plotly layout), #638 (prepare flip), #639 (mpl backend).
