# Issue #1009 — plan (rev 2)

## Diagnosis

`summary_collector(b, family="fullcell_standard_gravimetric").plot()` draws 10
facets instead of the 4 the family declares, and even the declared layout is
one facet *per variable* where the user wants charge and discharge of the same
quantity in **one** panel.

Root causes:

1. `PlotFamily.summary_options` (`cellpy/plotting/registry.py`) strips the
   `_cv` / `_non_cv` suffix off declared columns and requests the *base*
   column with `partition_by_cv=True` — "only the CV part" is lost.
2. `collect_summaries` (`cellpy/collect/summary.py`) then keeps
   `col`, `col_non_cv`, `col_cv` for **every** requested column, including
   `coulombic_efficiency`.
3. `summary_plotter` (`cellpy/plotting/collected.py`) facets on `variable`,
   so `charge_x` and `discharge_x` always land in separate rows.

Audit over all 20 `summary_plot` families (two `.res` cells, in-memory
batch): the 13 `capacities*` / `voltages` families collect exactly their
declared columns; all 7 `fullcell_standard*` families collect 10–12.
Single-cell `summary_plot(y=...)` is unaffected by 1–2 (selects `y_cols`
explicitly) and is out of scope for 3.

## Approach

### A. Collect exactly the declared columns

1. `summary_options`: keep declared names literally in `columns` (no suffix
   stripping); still set `partition_by_cv` when a `_cv` / `_non_cv` name (or
   `supports_cv_split`) is present. `mod_01_*` handling unchanged.
2. `collect_summaries`: expand `col → (col, col_non_cv, col_cv)` only when the
   requested list names no CV variant itself; a list that spells out
   `*_cv` / `*_non_cv` is taken literally. Existing
   `columns=("charge_capacity",), partition_by_cv=True` still expands.

### B. Combine charge/discharge into one panel (`summary_plotter`, Plotly)

3. Panel key: split `variable` on `_`, drop the first token equal to
   `charge` / `discharge` → panel; that token is the `direction`. Works for
   prefix (`charge_capacity_gravimetric_cv`), suffix
   (`potential_end_charge`) and mid-name
   (`test_cumulated_discharge_capacity_loss_gravimetric`,
   `mod_01_discharge_capacity_gravimetric`). No token → panel = variable,
   direction none.
4. Before the backend call, rewrite `variable` to the panel key and add a
   `direction` column. Everything keyed on `variable` (facets, `y_ranges`,
   `order_variables`, label mapper, `spread_plot`) keeps working on panel
   keys; `y_ranges` / `order_variables` given as original variable names are
   translated the same way.
5. `px.line(..., line_dash="direction", line_dash_map={charge: solid,
   discharge: dash})` when any direction is present. Trace names reduced to
   the series (cell / group) with one legend entry per series; a second
   Plotly legend (`legend2`, title "Direction") carries two style-only
   entries: Charge (solid) / Discharge (dashed). `spread_plot` (grouped
   mean/std) gets the same dash per direction.
6. Panel labels: `_pretty_variable_label` must recognise `capacity_gravimetric`
   (no direction prefix) so units still appear → "Capacity (mAh/g)".
7. Opt-out: `combine_directions=False` on `summary_plotter` /
   `Collection.plot` restores one facet per variable. Default **on** (this is
   the requested layout; noted in HISTORY).
8. Seaborn backend: facets follow the panel rewrite; `style="direction"` only
   when style is free (not `group_cells`). Matplotlib/bokeh summary paths
   untouched.

Resulting facet counts: `fullcell_standard_*` 4 (CE, capacity, retention,
CV part); `capacities_*` 1; `*_coulombic_efficiency` 2; `*_with_rate` 2;
`*_split_constant_voltage` 3; `voltages` 1.

### C. Tests (essential)

- Registry/collect: tighten the family oracle in `tests/test_collect.py` to
  reject *extra* columns; literal-list case for `collect_summaries`.
- Plot: unit tests for the panel/direction split; Plotly facet count and
  dash mapping on a synthetic frame; `legend2` present with two entries;
  `combine_directions=False` gives per-variable facets; `y_ranges` keyed by
  original variable still applies.
- Update `tests/test_collected_summary_groups.py` fixtures that used
  `cap_charge` / `cap_discharge` as separate facets (they now merge).

### D. Docs

`HISTORY.md` `[Unreleased]`, `AGENTS.md` / `docs/getting_started/agents.md`
batch bullet (combined panels + `combine_directions`), `test-registry.md`.

## Constraints

- No new `SummaryOptions` fields; family declarations unchanged.
- Legacy `plot_cycle_life_summary_plotly` (Batch `b.plot()`) untouched.
