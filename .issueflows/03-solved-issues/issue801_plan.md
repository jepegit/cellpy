# Issue #801 — Plan: App-friendly collected figures (theme / label / height)

Status: **confirmed** (2026-07-31) — open questions resolved as recommended:
pretty labels default; no `spec=` this PR; include `layout_updates`.

## Goal

Give apps first-class, documented knobs on `collected_plot` / `Collection.plot` so faceted Plotly figures can be dropped into an app shell without a private restyle pass — covering **template/theme**, **facet labels**, and **height**.

## Constraints

- Patch release (`v.2.1.2`); stay on the **collected** Plotly path (`Collection.plot` → `collected_plot` → `summary_plotter` / `_cycles_plotter`). Do not rework single-cell prepare→render.
- Collected path still builds a thin `FigureSpec` (extras only; panels unused) — same as #804. Do **not** force a full PanelSpec migration.
- Prefer additive kwargs + clearer defaults over a new theming framework.
- Companion context: [cellpy/cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui) pain-point §11 (restyles every figure today); #804 already landed `share_y` / `y_ranges`.
- Design docs: [plotting-collected.md](../04-designs-and-guides/plotting-collected.md), [plotting-backends.md](../04-designs-and-guides/plotting-backends.md).

### Prior art

| Hit | Where | Relation |
| --- | --- | --- |
| Hardcoded `template = f"{PLOTLY_BASE_TEMPLATE}+{method}"` | [`collected.py`](../../cellpy/plotting/collected.py) `_cycles_plotter` | Theme seam — no public override today |
| `make_collector_templates` / `make_plotly_template` | [`theme.py`](../../cellpy/plotting/theme.py) | Axis chrome only; apps still restyle paper/legend/facet strip |
| `y_label_mapper` + `_plotly_y_label_cleaner` | `sequence_plotter` / `summary_plotter` | Label seam exists; only populated when `units=` is passed (Batch path). Plain `Collection.plot` keeps `variable=…` facet titles |
| `height` / `sub_fig_min_height` / `figure_border_height` | `_cycles_plotter` | Height seam exists but names are obscure; summary forces `sub_fig_min_height=300` |
| `plotly_template` on single-cell prepare configs | `prepare/{summary,curves,ica}.py` | Naming to mirror for collected override |
| Thin `FigureSpec(extras=…)` in `collected_plot` | [`collected.py`](../../cellpy/plotting/collected.py) | Escape hatch possible via merging `render_opts`; panels still ignored |
| Toolbox / graphify | `.issueflows/00-tools/`, `graphify-out/` | No plotting-theme helper |

## Approach

Ship **three public knobs** (kwargs through `Collection.plot` / `collected_plot` → `render_opts`), document them, and improve the default label path so apps are not forced to pass `units=` just to drop `variable=`.

### 1. Theme / template

- Accept `plotly_template=` (string; Plotly template name or `"+"`-combined). When set, use it in `_cycles_plotter`'s `fig.update_layout(template=…)` instead of hardcoding `simple_white+{method}`.
- Accept optional `layout_updates: Mapping[str, Any]` applied after the collector layout (paper/plot bgcolor, margin, legend dict patches). Keep this a shallow `update_layout(**layout_updates)` — not a second theme system.
- Out of scope: new light/dark token packs, discrete colorway registry (existing `palette=` / `palette_*` stay as-is).

### 2. Labels (facet strip / y titles)

- When `y_label_mapper` is omitted, build a **default pretty mapper** from the frame's `variable` values (title-case / split `_`, optional unit suffix only if `units=` present — reuse the existing units branch). Always strip Plotly's `variable=` annotation text (move facet label onto the y-axis title and clear the side strip), matching today's `y_label_mapper` behaviour.
- Keep explicit `y_label_mapper=` as override (wins over the default).
- Gate the new default behind `pretty_labels=True` **if** Open question 1 chooses opt-in; otherwise make it the summary default (recommended).

### 3. Height

- Document and prefer public names:
  - `height=` — absolute figure height (already works).
  - `height_per_panel=` — alias of `sub_fig_min_height` (clearer for apps).
  - keep `figure_border_height=` / `sub_fig_min_height=` as synonyms.
- Ensure summary's internal default (`300` per panel) still applies when neither absolute `height` nor `height_per_panel` is given.
- No change to the experimental `height_fractions` path.

### 4. Optional `spec=` (thin)

- Allow `collected_plot(..., spec=FigureSpec)` / `spec=` on `Collection.plot`: merge `spec.extras["render_opts"]` into opts, honour `spec.title`, and if `spec.extras` carries `plotly_template` / `layout_updates`, treat them like the kwargs above. Still ignore `panels` (same as #804).
- If Open question 2 says kwargs-only, skip this bullet.

### 5. Docs

- Update `plotting-collected.md` with the three knobs + a short app example.
- Docstrings on `collected_plot` / `Collection.plot` / `summary_plotter`.
- Tiny example in existing plotting/collect docs if a natural home exists (no new guide).

## Files to touch

| Path | Change |
| --- | --- |
| [`cellpy/plotting/collected.py`](../../cellpy/plotting/collected.py) | `plotly_template`, `layout_updates`, default/`pretty_labels` mapper, `height_per_panel` alias; optional `spec=` merge; docstrings |
| [`cellpy/collect/collection.py`](../../cellpy/collect/collection.py) | Docstring mention of the new knobs |
| [`.issueflows/04-designs-and-guides/plotting-collected.md`](../04-designs-and-guides/plotting-collected.md) | Decision bullets + example |
| `tests/test_collected_summary_axes.py` or new `tests/test_collected_app_hooks.py` | Assert template override, pretty labels (no `variable=`), height math |

## Test strategy

```bash
uv run pytest tests/test_collected_summary_axes.py tests/test_collected_app_hooks.py -q
MPLBACKEND=Agg uv run pytest -m essential
```

- Synthetic long summary frame (reuse #804 helper pattern).
- Assert: with `plotly_template="plotly_white"`, layout template reflects it; with default/pretty labels, annotations empty or lack `variable=`; with `height_per_panel=180` and 2 variables, `layout.height == figure_border_height + 2*180` (or documented formula).
- Mark essential only if cheap (same bar as #804).

## Open questions

1. **Pretty labels default?**  
   - **Recommended: yes** — summary collected path always builds a pretty mapper when `y_label_mapper` is omitted (visual change: side `variable=…` strip goes away; y-axis titles become humanized).  
   - Alternative: opt-in `pretty_labels=True`.

2. **`spec=` escape hatch this PR?**  
   - **Recommended: no** — kwargs cover the issue text; thin `FigureSpec` merge can wait.  
   - Alternative: accept `spec=` merge as above.

3. **`layout_updates=` this PR?**  
   - **Recommended: yes** (small; unblocks paper/plot colors without a template factory).  
   - Alternative: template string only.
