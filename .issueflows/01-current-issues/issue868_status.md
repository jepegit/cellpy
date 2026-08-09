# Issue #868 — status

- [x] Done

## What was done

Option 1 from the issue: the registry is now self-describing for the collect
path.

- `PlotFamily.summary_options(hdr, *, norm_factor=None)` returns a ready
  `SummaryOptions`, derived generically from the family's declared columns — no
  per-family builder. It requests base columns (stripping `_cv` / `_non_cv`),
  sets `partition_by_cv` when the family declares a CV column or sets
  `supports_cv_split`, and turns each declared `mod_01_*` marker into a real
  `frame -> frame` transform that writes that column from its prefix-stripped
  source.
- `cellpy.collect.normalize_column_on_max` added beside `normalize_column`,
  because the plotting default normalises against the column's own maximum and
  `normalize_column` only divides by a scalar known up front.
- `PlotFamily.transforms()` now documents that its nested mapping is the
  `summary_plot` normalization spec consumed by `prepare/summary.py`, not a
  collect transform. That mismatch was the `TypeError` in the issue: the two
  concepts share a name but are not interchangeable, which is why no adapter
  existed.

## Measured effect (demo cell, 20 registered summary families)

| options | families whose declared columns are all present |
|---|---|
| `SummaryOptions()` | 8 |
| `SummaryOptions(partition_by_cv=True)` | 12 |
| `family.summary_options(hdr)` | **15** |

The remaining 5 are the `*_absolute` families: this cell's summary has no
`*_absolute` columns at all, so "data missing" is the honest answer for them
rather than an API gap.

## Tests

Six new `essential` tests in `tests/test_collect.py`. The load-bearing one is an
oracle over *every* summary family: a family's own options must satisfy the
family's own declared columns, and the only columns permitted to stay missing
are those whose source is absent from the cell's summary — asserted as exact set
equality, so a regression cannot hide behind a loose check. Full
`uv run pytest -m essential` gate green.

## Remaining work

None for this issue. The `*_absolute` gap is a data-availability question about
the demo cell, not the registry.
