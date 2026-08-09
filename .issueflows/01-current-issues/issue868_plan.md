# Issue #868 — plan

Direction confirmed up front in the cycle confirm: **Option 1** — the family
tells the collector what it needs.

## What the investigation showed

The two "transforms" are different concepts that happen to share a name, which
is why no adapter exists:

- `SummaryOptions.transforms` are `frame -> frame` callables applied at the end
  of `collect_summaries`.
- `PlotFamily.transforms_builder` yields `{col: {(row, new_col): fn}}`, consumed
  only by `prepare/summary.py::_apply_normalization` on the melted single-cell
  frame — `row` is the subplot row, `new_col` the variable to create, and `fn`
  is `SummaryPlotInfo.normalize_col`, not `collect.normalize_column`.

So the nested mapping should not be fed to the collector at all. What the
collect path actually needs is: the real source columns, `partition_by_cv` where
the family declares `*_cv` columns, and a callable that materialises each
synthetic `mod_01_*` column the family declares. `mod_01_*` is a marker, not a
summary column — `prepare/summary.py` strips the prefix to find its source.

Measured on the demo cell (20 summary families): 8 satisfied with defaults, 12
with `partition_by_cv=True`. Of the 8 still unsatisfied, 3 need `mod_01_*`
(`fullcell_standard_gravimetric`, `_areal`, `_dev`) and 5 are `*_absolute`
families whose source columns are simply absent from this cell's summary — a
genuine data-availability limit, not an API gap, so those stay honestly
"data missing".

## Approach

`cellpy/collect/collector.py`

- Add `normalize_column_on_max(column, out=None, scaler=100.0)` beside
  `normalize_column`, same wide / grouped-long handling. Needed because the
  plotting default is `normalization_type="max"` and `normalize_column` only
  divides by a scalar known up front.

`cellpy/collect/__init__.py`

- Export it next to `normalize_column`.

`cellpy/plotting/registry.py`

- Add `PlotFamily.summary_options(hdr, *, norm_factor=None) -> SummaryOptions`,
  derived generically from the declared columns (no per-family builder):
  - strip `_non_cv` / `_cv` suffixes to get the base column to request;
  - `partition_by_cv=True` when the family declares a `*_cv` column or sets
    `supports_cv_split` — this is the "family declares the options it needs"
    half of the issue;
  - each declared `mod_01_*` becomes a transform writing exactly that column
    from its prefix-stripped source: `normalize_column` when `norm_factor` is
    given, else `normalize_column_on_max`.
- Import the collect symbols lazily inside the method to keep
  `plotting -> collect` from becoming an import cycle.

## Files to touch

- `cellpy/collect/collector.py`
- `cellpy/collect/__init__.py`
- `cellpy/plotting/registry.py`
- `tests/test_collect.py`
- `HISTORY.md` (changelog bullet at close)

## Test strategy

In `tests/test_collect.py`, against the real demo-cell batch fixture:

- the oracle: for **every** summary family, `collect_summaries(batch,
  options=family.summary_options(hdr))` satisfies `family.columns(hdr)` except
  for columns whose source is genuinely absent from the cell's own summary —
  asserted as an exact set equality, so a regression cannot hide;
- `fullcell_standard_gravimetric` specifically gains its `mod_01_*` column and
  the values are the normalised discharge capacity;
- `summary_options` sets `partition_by_cv` for the split and full-cell families
  and leaves it off elsewhere;
- `normalize_column_on_max` on wide and grouped-long frames.

Then the full `uv run pytest -m essential` gate.
