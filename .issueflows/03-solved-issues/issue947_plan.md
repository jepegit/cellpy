# Issue #947 — plan

## Goal

Put units on collected-summary y-axis titles, make `custom_group_labels=` the legend text on the issue's plot path, and document that facet rows follow `columns=` (top → bottom).

## Constraints

- Back-compat: pretty names stay (`Charge Capacity`), units go in parentheses (`Charge Capacity (mAh/g)`). Explicit `y_label_mapper=` still wins and is left untouched.
- Session / cell `CellpyUnits` via `cellpy.units.units_label` / `with_cellpy_unit` — no new hand-rolled `f"{charge}/{specific}"` strings. Unknown variables stay unit-less (do not raise).
- One PR; no collector redesign.
- Tests: `conda activate cellpy_dev_313` then `pytest -m essential` (plotting extras needed for figure assertions).

### Prior art

- `_pretty_variable_label` / `_default_summary_y_label_mapper` in [`cellpy/plotting/collected.py`](../../../cellpy/plotting/collected.py) — already title-cases and *can* append units, but only when `units={"cellpy_units": …}` is passed. [`Collection.plot`](../../../cellpy/collect/collection.py) never forwards units, so defaults are `"Charge Capacity"` with no parenthesis ([`test_collected_app_hooks.py`](../../../tests/test_collected_app_hooks.py)).
- `cellpy.units.units_label` / `with_cellpy_unit` — canonical label helper (single-cell plots already use it).
- Grouped legend + facet order (#923): [`plotting-collected.md`](../04-designs-and-guides/plotting-collected.md), `summary_plotter` + [`test_collected_summary_groups.py`](../../../tests/test_collected_summary_groups.py). Line path colours by `group_label` when present. `spread_plot` still keys series by `"group"` / `"cell"` and uses `variable.unique()` (unordered) — likely leftover if the screenshot used `spread=True`.
- Toolbox: none relevant.

## Approach

1. **Reproduce** the issue snippet (`summary_collector` + `group_it=True` + `custom_group_labels=` + `.plot()`) on this branch. Note whether the default (line) path already shows group labels; if only `spread=True` shows numbers, fix that path.
2. **Y-axis units.** Default mapper always resolves units:
   - Prefer `units=` when the caller / `FrameContext` / first batch cell supplies `CellpyUnits`.
   - Else `get_cellpy_units()` (session default).
   - Capacity + mode suffix → `with_cellpy_unit("Charge Capacity", "charge", "gravimetric")` (and areal / volumetric). CE → `Coulombic Efficiency (%)`. Other known quantities if cheap; else pretty name only.
   - Keep accepting the old `{"cellpy_units": …}` dict so any leftover caller still works.
3. **Group labels.** If line-path reproduction already matches #923 tests, add one end-to-end test through `summary_collector` with the issue's column names. If `spread_plot` still legends by group id, colour / name by `group_label` when that column is present (same fallback as `summary_plotter`).
4. **Facet order.** Already deliberate on the line path (`order_variables` from collected `columns=`; Plotly first row on top). Document in `summary_collector` docstring + [`docs/examples/batch_utility/cellpy_batch_processing.md`](../../../docs/examples/batch_utility/cellpy_batch_processing.md) (and `agents.md` if that section lists collected knobs). If `spread_plot` ignores categorical order, sort variables by `order_variables` there too.
5. Update [`plotting-collected.md`](../04-designs-and-guides/plotting-collected.md) one bullet: default y-titles include units.

## Files to touch

- `cellpy/plotting/collected.py` — default unit-aware labels; `spread_plot` group_label + facet order if still broken.
- `cellpy/collect/collection.py` — optional: forward `units=` from kwargs / meta; docstring.
- `cellpy/collect/collector.py` — `summary_collector` docstring: `columns=` sets top→bottom facet order.
- `tests/test_collected_app_hooks.py` — expect `"Charge Capacity (mAh/g)"` (or session-unit equivalent).
- `tests/test_collected_summary_groups.py` (or a small new test) — issue-shaped `summary_collector` → legend labels; spread if needed.
- `docs/examples/batch_utility/cellpy_batch_processing.md` (+ `docs/getting_started/agents.md` if that list is the agent contract).
- `.issueflows/04-designs-and-guides/plotting-collected.md` — units-on-default-titles note.

## Test strategy

- New / updated essential tests: default mapper includes units; CE gets `%`; explicit `y_label_mapper` still wins; `summary_collector(..., custom_group_labels=…)` legend names; facet order for the issue's three columns (and spread if we touch it).
- `conda activate cellpy_dev_313 && pytest -m essential` (or the collected-summary files if the full essential set is heavy locally).

## Open questions

- None that block coding. Units come from session `CellpyUnits` when the collection has no cell (reload-from-disk). Override remains `units=` / `y_label_mapper=`.
