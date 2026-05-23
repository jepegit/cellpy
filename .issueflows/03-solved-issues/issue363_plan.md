# Plan for issue #363: Add filtering possibility to plotters in plotutils

## Goal

Make it easy to skip "characterisation" cycles (typically slow C-rate) when
plotting summaries by adding (a) a generic, extendable row-filtering layer
inside `cellpy/filters/` that operates on plain DataFrames, (b) a thin
`CellpyCell.filter_summary(...)` wrapper so users can call it directly, and
(c) a `filters=...` parameter on `summary_plot` so the same filter applies to
the data the plot consumes. Also add a new predefined y set that includes a
C-rate subplot, with an optional `nominal_capacity` override that rescales
the existing `charge_c_rate` / `discharge_c_rate` columns.

## Constraints

- KISS: filter package keeps the same shape as today
  ([`cellpy/filters/cycles.py`](../../cellpy/filters/cycles.py)) — small,
  stdlib + pandas, no new dependencies.
- Filters operate on **plain DataFrames** so they stay testable and reusable
  outside the plotter (this matches the design decision implied by the
  existing `filters/__init__.py` docstring).
- Backwards compatibility: existing `summary_plot` callers must keep working
  unchanged. New args default to "no filtering" / "use object's nominal
  capacity". No new predefined `y` set replaces an old one.
- Rescaling rule from the issue: when `nominal_capacity` is passed to
  `summary_plot`, it must **replace** the rate scaling implied by
  `c.nom_cap`, not multiply on top of it.
- No churn in `plotutils.py` outside the data-prep path and the
  `SummaryPlotInfo` column registry. The 5987-line file is already large; we
  add a small, isolated entry point and avoid touching the Plotly/Seaborn
  rendering classes beyond passing the new row through.
- Tests: extend `tests/test_filters_cycles.py` style (small, dataframe-only
  unit tests) and add a focused test for the `summary_plot` filter/rate
  wiring using a minimal fake `c` object (the file already exercises
  `summary_plot` — see [`tests/test_plotutils_summary_plot.py`](../../tests/test_plotutils_summary_plot.py)).

### Prior art (from the graphify report + a confirmation grep)

`graphify-out/GRAPH_REPORT.md` surfaced an existing ecosystem of
summary-row-filtering helpers that this work needs to be **consistent
with**, not duplicate. The new `cellpy.filters.filter_summary` must coexist
sensibly with these. A quick grep before `/issue-start` will pin down their
exact module(s) and signatures:

- **Community 238 / 239** — `yank_before()`, `yank_after()`,
  `remove_first_cycles_from_summary()`, `remove_last_cycles_from_summary()`.
  Existing "trim by cycle index" helpers. `filter_cycles` already overlaps
  partially; the new `filter_summary` should follow the same naming /
  param-shape conventions (e.g. operate on a DataFrame, accept a column
  name) so users see one coherent filter API.
- **Community 125** — `remove_outliers_from_summary*`,
  `remove_outliers_from_summary_on_index()`, plus a `remove_outliers_from_*`
  variant for batch objects. Outlier removal is a sibling of rate-filtering
  and a likely future addition to the `cellpy.filters.summary` registry —
  the registry shape must leave room for them.
- **Community 76** — `add_c_rate()`, `create_rate_column()`. These build
  the `charge_c_rate` / `discharge_c_rate` columns the new filter consumes;
  the rescaling helper for `nominal_capacity` needs to respect whatever
  convention they use (units, sign, NaN handling).

Design intent: **do not migrate** these helpers as part of this issue. Add
`filter_summary` next to them with a consistent API and record the
convergence intent (registry-based, DataFrame-first, header-resolved
defaults) in the design note at
[`.issueflows/04-designs-and-guides/filters-and-plot-filtering.md`](../04-designs-and-guides/filters-and-plot-filtering.md).
A follow-up issue can collapse the older helpers into the registry once the
shape has settled.

Implementation note for `/issue-start`: before writing
`cellpy/filters/summary.py`, run a targeted grep for the function names
above to confirm their current locations, signatures, and any column-name /
unit conventions worth mirroring. (Follow-up process
improvement tracked upstream at
<https://github.com/jepegit/issue-flow/issues/57>.)

## Approach

### 1. Filter package: `cellpy/filters/`

Add a new module `cellpy/filters/summary.py` with a generic `filter_summary`
function. Keep it dataframe-first like
[`filter_cycles`](../../cellpy/filters/cycles.py):

```python
def filter_summary(
    df: pd.DataFrame,
    *,
    rate: RangeArg = None,           # (low, high) or {"value": v, "delta": d}
    rate_columns: Union[str, Sequence[str]] = (
        "charge_c_rate", "discharge_c_rate",
    ),
    # placeholder slots for future filters (capacity, temperature, ...) -
    # accept **filters and dispatch through a small registry.
    **extra_filters,
) -> pd.DataFrame: ...
```

`rate_columns` is intentionally flexible:

- **Default** (`("charge_c_rate", "discharge_c_rate")`) — filter on both
  rates AND-ed: a row is kept only when **every** listed rate column falls
  in range. This is the usual "drop characterisation cycles" case.
- **Single string** (e.g. `rate_columns="discharge_c_rate"`) — coerced to a
  one-element tuple internally so callers don't have to remember the
  `("foo",)` trailing-comma syntax. Use this when only the discharge (or
  only the charge) side defines a characterisation cycle.
- **Explicit tuple/list** (e.g. `rate_columns=("charge_c_rate",)`) — same as
  the string form; useful when programmatically building the argument.

Missing rate columns (e.g. a summary that doesn't have `charge_c_rate`)
raise a clear `KeyError` so the failure mode is obvious. The
`CellpyCell.filter_summary` wrapper resolves the defaults from
`self.headers_summary` and forwards `rate_columns` straight through, so the
same flexibility is available from the cell API.

Range semantics (from the issue):

- `(low, high)` → keep rows where `low < value <= high`.
- `{"value": v, "delta": d}` → keep rows where `v - d < value <= v + d`
  (exclusive lower bound, inclusive upper — same convention as the range
  form, so both forms behave consistently).
- `None` → no filter.

Internals: a tiny `_RANGE_FILTERS` registry mapping a filter name (e.g.
`"rate"`) to `(column_resolver, range_predicate)`. New filters slot in by
registering an entry — that's the "extendable" part the issue asks for, kept
to a single small file.

Export `filter_summary` from `cellpy/filters/__init__.py` alongside
`filter_cycles`.

### 2. `CellpyCell` method

Add a thin method on `CellpyCell` (in
[`cellpy/readers/cellreader.py`](../../cellpy/readers/cellreader.py)) that
forwards to the filter module and resolves header names from
`self.headers_summary`:

```python
def filter_summary(self, *, rate=None, **kwargs):
    from cellpy.filters import filter_summary as _fs
    h = self.headers_summary
    return _fs(
        self.data.summary.reset_index(),
        rate=rate,
        rate_columns=(h.charge_c_rate, h.discharge_c_rate),
        **kwargs,
    )
```

Keep it tiny — no business logic beyond resolving defaults; all real work
stays in `cellpy/filters/`.

### 3. `summary_plot` integration

In [`cellpy/utils/plotutils.py`](../../cellpy/utils/plotutils.py):

1. Add three new fields to `SummaryPlotConfig` (≈ line 620):
   - `filters: Optional[dict] = None` — passed straight to `filter_summary`.
   - `nominal_capacity: Optional[float] = None` — rate-rescaling override
     (plain float, in `c.cellpy_units.nominal_capacity` units; pint-style
     string support can be added later if asked).
   - `rate_filter_columns: Union[str, tuple[str, ...]] = ("charge_c_rate",
     "discharge_c_rate")` — which rate columns the `rate` filter applies to
     (AND-ed). Default keeps both rates in sync; callers can pass a single
     column name (`"charge_c_rate"` or `"discharge_c_rate"`) to filter on
     just one side.

2. In `SummaryPlotDataPreparer._prepare_standard_data` (≈ line 1245) and the
   fullcell variant (`_prepare_fullcell_standard_data`, ≈ line 1160), after
   `summary = c.data.summary.copy()` / `.reset_index()`:
   - If `config.nominal_capacity is not None`, rescale
     `charge_c_rate` and `discharge_c_rate` in-place: multiply by the
     object's current `nom_cap` (undo old scale) then divide by the new
     `nominal_capacity` (apply new scale). Centralise this as a small helper
     in `plotutils.py` so both prep paths share it.
   - If `config.filters` is truthy, call `filter_summary(summary,
     **config.filters)` before the `.melt(...)` step.
   - Both steps are guarded by `if ...` and default to no-op, so existing
     behaviour is unchanged.

3. Add new predefined y set entries in
   `SummaryPlotInfo._create_col_info` (≈ line 900) and matching label
   entries in `_create_label_dict` (≈ line 764):
   - `"capacities_gravimetric_with_rate"`,
     `"capacities_areal_with_rate"`,
     `"capacities_absolute_with_rate"`
     — same columns as the existing `capacities_*` sets, with
     `charge_c_rate` and `discharge_c_rate` added on an extra row (row 1).
   - Wire the extra row in the standard-data prep path (use the same `row`
     trick already in use for `fullcell_standard_*`; see the
     `s[self.row] = ...` assignments around line 1185).
   - Add a y-axis label entry like `"C-rate (1/h)"` for the new row in
     `y_axis_label`.

4. Expose the new arguments on the public `summary_plot` and
   `summary_plot_legacy` signatures (≈ lines 4462 and 3021): add
   `filters=None`, `nominal_capacity=None`, `rate_filter_columns=
   ("charge_c_rate", "discharge_c_rate")` as optional parameters, document
   them in the docstring (mention C-rate rescaling semantics explicitly, and
   that `nominal_capacity` is currently a plain float in the object's
   nominal-capacity units), and thread them through
   `SummaryPlotConfig.from_kwargs`.

### 4. Tests

- New file `tests/test_filters_summary.py` covering:
  - `(low, high)` semantics (exclusive low, inclusive high).
  - `{"value", "delta"}` semantics (exclusive lower, inclusive upper).
  - `None` → returns the dataframe unchanged (copy semantics).
  - Default `rate_columns` ANDs across both rate columns.
  - `rate_columns="discharge_c_rate"` (single string) and
    `rate_columns=("charge_c_rate",)` filter on just that column.
  - Missing rate column → clear `KeyError`.
  - Unknown filter key → clear `ValueError` (extension point sanity).
- Extend
  [`tests/test_plotutils_summary_plot.py`](../../tests/test_plotutils_summary_plot.py)
  with two small tests (reuse existing fixture style):
  - `summary_plot(..., filters={"rate": (0, 0.5)})` drops the slow-rate
    rows before plotting (assert via `return_data=True`).
  - `summary_plot(..., nominal_capacity=...)` rescales the C-rate columns
    in the returned data.

`uv run pytest tests/test_filters_cycles.py tests/test_filters_summary.py
tests/test_plotutils_summary_plot.py` is the focused check; full suite still
runs at `/issue-close`.

## Files to touch

- [`cellpy/filters/summary.py`](../../cellpy/filters/summary.py) — **new**:
  `filter_summary` + tiny range-filter registry.
- [`cellpy/filters/__init__.py`](../../cellpy/filters/__init__.py) — export
  `filter_summary`.
- [`cellpy/readers/cellreader.py`](../../cellpy/readers/cellreader.py) — add
  `CellpyCell.filter_summary` wrapper (near `inspect_nominal_capacity`,
  ≈ line 6783).
- [`cellpy/utils/plotutils.py`](../../cellpy/utils/plotutils.py) —
  `SummaryPlotConfig` fields, prep-path hooks, new predefined y-sets and
  labels, `summary_plot` / `summary_plot_legacy` signature.
- `tests/test_filters_summary.py` — **new** unit tests.
- [`tests/test_plotutils_summary_plot.py`](../../tests/test_plotutils_summary_plot.py)
  — two small integration tests.
- [`.issueflows/04-designs-and-guides/filters-and-plot-filtering.md`](../04-designs-and-guides/filters-and-plot-filtering.md)
  — **new**: short design note recording the
  "filters live in `cellpy/filters/`, plotters consume them via `filters=`,
  ranges are `(low, high]` or `{value, delta}`" decision so future filters
  follow the same shape.

## Test strategy

- `uv run pytest tests/test_filters_cycles.py tests/test_filters_summary.py`
  — fast, dataframe-only.
- `uv run pytest tests/test_plotutils_summary_plot.py` — covers the
  plot-integration path.
- Full suite at `/issue-close`: `uv run pytest`.
- Manual sanity (optional): run the existing
  `_check_summary_plotter_seaborn()` block at the bottom of `plotutils.py`
  with the new `y="capacities_gravimetric_with_rate"` set and
  `filters={"rate": (0.0, 0.5)}` to eyeball the figure.

## Open questions

All resolved (locked in above):

1. **Rate filter default columns** — default AND across both `charge_c_rate`
   and `discharge_c_rate`; `rate_columns` accepts a single string
   (`"charge_c_rate"` / `"discharge_c_rate"`) or a tuple to override and
   filter on just one side.
2. **`nominal_capacity` type** — plain float for now (units = the object's
   `cellpy_units.nominal_capacity`); pint-style string accepted as a future
   extension only.
3. **Delta-range semantics** — exclusive lower, inclusive upper:
   `v - d < value <= v + d`. Same convention as the `(low, high]` range form
   for consistency.

---

**Status**: ready for `/issue-start` pending user confirmation.
