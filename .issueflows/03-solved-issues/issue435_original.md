# Issue #435: Stage 0.8: Extend consumer scans to filters/, exporters/, internals/

Source: https://github.com/jepegit/cellpy/issues/435

## Original issue text

> Part of **Stage 0 â€” foundations for cellpy 2** (see the tracking issue). Plan documents live in the shared workspace: `cellpy-workspace/architecture-plan/` (the [architecture-plan repo](https://github.com/cellpy/architecture-plan); formerly `architecture-plan/`) (alongside the `cellpy` and `cellpy-core` repos).

## Goal

Re-run the two inventory scans over the packages the original reports skipped â€”
`cellpy/filters/`, `cellpy/exporters/`, `cellpy/internals/` (consumers only) â€” and append
the findings to the existing reports:

- Data/CellpyCell member usage (which parts of the core API these packages touch),
- hard-coded column-header literals.

## Why

Gap item G5: `filters/` shows up in the polars index findings but is in no migration
inventory; `exporters/` has been scanned by nobody. Every later wave plans work from these
reports â€” a blind spot here surfaces as surprise breakage in utils wave 1. Half a day,
pure prevention.

## Links

- `architecture-plan/cellpy2-plans-gap-analysis.md` (G5)
- `architecture-plan/data-and-cellpycell-usage-in-cellpy-utils.md` (append here)
- `architecture-plan/hardcoded-column-headers-report.md` (append here)
- `architecture-plan/cellpy2-utils-migration-plan.md` (wave 0 â€” this issue is that wave)

## Acceptance

- Both reports carry a dated addendum section covering the three packages.
- The utils-migration triage table gains rows for anything discovered in `exporters/`.

