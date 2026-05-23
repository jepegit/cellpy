# Issue #363 - Status

- [x] Done

## Summary

Filtering machinery for cellpy summary DataFrames is now in place, wired
into `summary_plot` and exposed as a `CellpyCell` method. A new family of
`*_with_rate` predefined y-sets adds a C-rate subplot to the standard
capacity plots, with an optional `nominal_capacity` override that
rescales the existing `charge_c_rate` / `discharge_c_rate` columns.

## What landed

- New module `cellpy/filters/summary.py`:
  - `filter_summary(df, *, rate=..., rate_columns=..., **extra)` with a
    small registry-based extension point (`register_range_filter`).
  - Range semantics: both `(low, high)` and `{"value": v, "delta": d}`
    use exclusive lower / inclusive upper.
  - `rate_columns` accepts a string or a sequence; default ANDs across
    `("charge_c_rate", "discharge_c_rate")`.
- Exported from `cellpy/filters/__init__.py` next to `filter_cycles`.
- `CellpyCell.filter_summary(...)` wrapper in
  `cellpy/readers/cellreader.py` that resolves rate-column defaults
  from `self.headers_summary` and forwards everything else to the
  filter module.
- `cellpy/utils/plotutils.py`:
  - New `SummaryPlotConfig` fields: `filters`, `nominal_capacity`,
    `rate_filter_columns`.
  - New `SummaryPlotDataPreparer._preprocess_summary(c, summary,
    config)` helper that rescales rate columns and applies
    `filter_summary` before melting.
  - Called from `_prepare_standard_data` and
    `_prepare_fullcell_standard_data`.
  - New predefined y-sets:
    `capacities_gravimetric_with_rate`,
    `capacities_areal_with_rate`,
    `capacities_absolute_with_rate`, plus matching labels.
    The new sets route the rate columns to row 0 (`number_of_rows = 2`).
  - New public kwargs on `summary_plot`: `filters`,
    `nominal_capacity`, `rate_filter_columns` (threaded into
    `SummaryPlotConfig.from_kwargs`).
- Tests:
  - `tests/test_filters_summary.py` - DataFrame-only unit tests for
    range semantics, default-AND, single-column override, missing-column
    errors, registry extension, orphan `_columns` kwargs.
  - `tests/test_plotutils_summary_plot.py::TestSummaryPlotFiltersAndRate`
    - filter drops rows, `filters=None` passthrough,
    `nominal_capacity` doubling halves rate columns,
    `*_with_rate` y-sets emit the rate variables.
- Design doc:
  `.issueflows/04-designs-and-guides/filters-and-plot-filtering.md`
  records the registry shape, range convention, and the coexistence
  plan with the prior-art helpers in `cellpy/utils/helpers.py`.

## Local test runs

User ran the focused pytest subset locally; all relevant tests passed
(`tests/test_filters_summary.py`, `tests/test_filters_cycles.py`,
`tests/test_plotutils_summary_plot.py`). Wider suite was run before
`/issue-close`.

## Follow-up (out of scope for this issue)

- Plotly row-0 y-axis label on the new `*_with_rate` sets currently
  inherits the capacity label rather than reading "C-rate". The plot
  is functionally correct; refining the label is a small cosmetic
  follow-up.
- The existing helpers in `cellpy/utils/helpers.py`
  (`remove_first/last_cycles_from_summary`, `yank_before/after`,
  `remove_outliers_from_summary_*`) should eventually fold into the
  `cellpy.filters` registry. Tracked in the design note at
  [`.issueflows/04-designs-and-guides/filters-and-plot-filtering.md`](../04-designs-and-guides/filters-and-plot-filtering.md).

## Files touched

- `cellpy/filters/summary.py` (new)
- `cellpy/filters/__init__.py`
- `cellpy/readers/cellreader.py`
- `cellpy/utils/plotutils.py`
- `tests/test_filters_summary.py` (new)
- `tests/test_plotutils_summary_plot.py`
- `.issueflows/04-designs-and-guides/filters-and-plot-filtering.md` (new)
