# Filters and plot filtering

Where the row-filtering helpers live and how new filters should be shaped.

## Context

Cellpy already had several "drop rows from a summary" helpers scattered
across `cellpy/utils/helpers.py` (see `remove_first_cycles_from_summary`,
`remove_last_cycles_from_summary`, `remove_outliers_from_summary_*`,
`yank_before`, `yank_after`). They evolved organically and use slightly
different parameter shapes.

Issue #363 added a need for **value-range filtering** of the summary
(starting with C-rate, to drop characterisation cycles), reachable
directly from `summary_plot` and as a method on `CellpyCell`. We chose to
introduce a small, registry-based filter module rather than extend
`helpers.py`, but the two ecosystems must converge over time.

## Decision

1. **Value-range filters live in `cellpy/filters/`.** The package is
   intentionally narrow: each module exports DataFrame-first functions
   that take a `pd.DataFrame` and return a filtered copy. No
   `CellpyCell` coupling, no batch-object coupling.
2. **`filter_summary` is registry-based.** New range filters (capacity,
   temperature, ...) register themselves via
   `cellpy.filters.summary.register_range_filter(name, fn)` and are then
   reachable through `filter_summary(df, name=range_arg,
   name_columns=...)`. The default `rate` filter is registered at module
   import.
3. **Ranges have one convention.** Both
   `(low, high)` and `{"value": v, "delta": d}` are interpreted as
   **exclusive lower / inclusive upper** so the two forms behave
   consistently. The same convention is used downstream by
   `summary_plot(filters=...)` and `CellpyCell.filtered_summary(...)`.
4. **Columns are configurable per filter.** Each filter accepts a
   `<name>_columns` kwarg (string -> single column, sequence ->
   AND-across-columns). The cellpy wrapper resolves the defaults from
   `headers_summary` so the public API is `rate=(low, high)` without
   needing to know column names.
4b. **`CellpyCell` method naming.** The DataFrame-returning accessor is
   `CellpyCell.filtered_summary(...)` (reads as "give me a filtered
   summary"). The slot `CellpyCell.filter_summary(...)` is reserved
   for a future implementation that returns a full `CellpyCell` with
   `summary`, `raw`, and `steps` filtered together. Don't rebind that
   name to the DataFrame helper.
5. **C-rate rescaling lives next to the filter call.** `summary_plot`'s
   `nominal_capacity=` rescales the existing `charge_c_rate` /
   `discharge_c_rate` columns by `c.data.nom_cap / nominal_capacity`
   (since `rate = current / nom_cap`). Rescale runs *before* filtering
   so the filter range is interpreted in the new nominal-capacity
   units.

## Coexistence with prior art

The new module **does not migrate** the existing helpers (see issue
#363 plan). It coexists with them and follows a consistent shape so
they can be consolidated in a follow-up:

- `remove_first/last_cycles_from_summary` -> trim by cycle index.
  Conceptually fits as a future registered filter
  (`cycle=(first, last)`).
- `remove_outliers_from_summary_*` -> statistical outlier removal.
  Different shape (uses windowing / z-scores), but should eventually
  expose a registered entry point.
- `yank_before` / `yank_after` -> batch-level wrappers.
  Equivalent helpers can be added on top of the `cellpy.filters`
  primitives without changing the primitives themselves.
- `add_c_rate` / `create_rate_column` -> rate-column *production*.
  Treated as upstream of filtering. The `nominal_capacity` rescale in
  `summary_plot` assumes these columns are present in the summary and
  scaled by `c.data.nom_cap`.

## Alternatives considered

- **Extend `helpers.py` directly.** Faster to land, but bakes the
  divergent parameter shapes deeper into the codebase and gives no
  obvious extension point for non-cycle-index filters.
- **Inline filtering inside `summary_plot`.** Fastest of all, but
  duplicates logic for any other code path that needs filtering
  (exporters, batch tools, `CellpyCell` helpers).
- **Class-based filter chain.** Over-engineered for the current scope;
  the registry pattern in `filters/summary.py` is the smallest thing
  that solves the issue and stays extendable.

## Links

- Issue: [#363](https://github.com/jepegit/cellpy/issues/363)
- Code: [`cellpy/filters/summary.py`](../../cellpy/filters/summary.py),
  [`cellpy/filters/cycles.py`](../../cellpy/filters/cycles.py),
  [`cellpy/utils/plotutils.py`](../../cellpy/utils/plotutils.py)
  (`SummaryPlotDataPreparer._preprocess_summary`),
  [`cellpy/readers/cellreader.py`](../../cellpy/readers/cellreader.py)
  (`CellpyCell.filtered_summary`).
- Tests:
  [`tests/test_filters_summary.py`](../../tests/test_filters_summary.py),
  [`tests/test_plotutils_summary_plot.py`](../../tests/test_plotutils_summary_plot.py)
  (`TestSummaryPlotFiltersAndRate`).
- Related upstream process improvement (`/issue-plan` should mine prior
  art automatically): [jepegit/issue-flow#57](https://github.com/jepegit/issue-flow/issues/57).
