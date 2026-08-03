# Issue #820 — Plan

## Goal

Pretty-print Plotly facet strips for collected **cycles** (and other non-summary)
layouts so apps see `Cycle 1` / cell label instead of `cycle_num=1` / `cell=demo`,
matching the polish #801 gave summary plots — without changing summary behaviour.

## Constraints

- Plotly primary; seaborn/matplotlib best-effort (same as #801 — no new seaborn work).
- Summary path (`method="summary"` / `y_label_mapper` clear-strip + y-title) **unchanged**.
- Facet strip stays visible for cycles (unlike summary): panel identity lives on the
  strip; y-axis is already capacity/voltage.
- Cycle column may be `cycle_num` (capacity curves) or `cycle` (ICA) — never hardcode
  one name (#679 / `plotting-collected.md`).
- Prefer `layout=` over legacy `method="fig_pr_*"` in docs; keep legacy knobs working.
- Small, single-PR scope; no new deps.

### Prior art

| Hit | Module | Role |
| --- | --- | --- |
| `_pretty_variable_label` / `_default_summary_y_label_mapper` | [`collected.py`](../../cellpy/plotting/collected.py) | Summary-only humanize of `variable` names (#801) |
| Summary annotation cleanup (`variable=` → y-title, then `update_annotations("")`) | `sequence_plotter` plotly `summary` branch | Pattern to **mirror, not reuse** — cycles rewrite strip text instead of clearing |
| `_yaxis_key_for_facet_label` | same | Summary y-range mapping; leave alone |
| `tests/test_collected_app_hooks.py` | tests | Essential chrome tests for #801 — extend or sibling for cycles |
| `plotting-collected.md` | designs | Decision home for collected `layout=` / app chrome |

Toolbox: no helper applies. Graph: `graphify-out/` absent this session — grep-only.

## Approach

### 1. Pretty facet annotation helper

Add a small helper (e.g. `_pretty_facet_annotation(text: str) -> str`) next to the
summary label helpers in `collected.py`:

| Raw Plotly strip | Pretty default |
| --- | --- |
| `cycle_num=1` / `cycle=1` | `Cycle 1` |
| `cell=demo` | `demo` (cell label only) |
| anything else / no `=` | leave unchanged |

No opt-out knob in this PR (same default-on stance as #801 for summary). Explicit
override later if someone needs raw `key=value`.

### 2. Apply after `px.line` for non-summary faceted methods

In `sequence_plotter`'s plotly branch, after creating the figure for
`fig_pr_cell` / `fig_pr_cycle` (and `film` if it emits the same `cell=` strips),
walk `fig.layout.annotations` and rewrite `.text` via the helper.

Do **not** clear strips and do **not** touch y-axis titles. Keep strip rewrite
out of the `summary` branch so #801 stays bit-identical.

Public entry points already funnel here:

- `cycles_plotter` / `collected_plot(..., family_kind="cycles", layout=…)`
- `ica_plotter` / `family_kind="ica"` (same `_cycles_plotter`, `z="cycle"`)

### 3. Docs

- Bullet + short example in [`plotting-collected.md`](../04-designs-and-guides/plotting-collected.md).
- `cycles_plotter` / `collected_plot` docstrings: note default pretty facet chrome;
  prefer `layout="per_cell"|"per_cycle"` over `method="fig_pr_*"`.

## Files to touch

| Path | Change |
| --- | --- |
| [`cellpy/plotting/collected.py`](../../cellpy/plotting/collected.py) | Helper + apply on `fig_pr_cell` / `fig_pr_cycle` (/`film`); docstring notes |
| [`.issueflows/04-designs-and-guides/plotting-collected.md`](../04-designs-and-guides/plotting-collected.md) | Decision + example |
| [`tests/test_collected_app_hooks.py`](../../tests/test_collected_app_hooks.py) (or sibling) | Cycles facet strip assertions; keep existing summary tests |

## Test strategy

```bash
uv run pytest tests/test_collected_app_hooks.py -q
MPLBACKEND=Agg uv run pytest -m essential
```

- Synthetic multi-cell / multi-cycle long frame (same shape as the probe in planning).
- `layout="per_cell"` / `method="fig_pr_cell"`: no `cell=` in annotation texts; cell
  labels present; still unambiguous with ≥2 cells.
- `layout="per_cycle"` / `method="fig_pr_cycle"`: no `cycle_num=` (or `cycle=`);
  texts look like `Cycle N`.
- Existing `test_summary_pretty_labels_clear_variable_facet_strip` still green.
- Mark essential if cheap (same bar as #801).

## Open questions

None blocking — issue text already picks strip form (`Cycle N` / cell label only)
and default-on. Reply **Accept** / **Revise** / **Abort**.
