# Issue #647: Port raw_plot and cycle_info_plot

Source: https://github.com/jepegit/cellpy/issues/647

## Original issue text

## Context

Part of epic #567 (Stage 2 â€” Other plot families on the same skeleton). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md`.

## Scope

Add `prepare/raw.py` and `prepare/steps.py`; route both public functions through the shared backends. Keep `cycle_info_plot`'s matplotlib single-cycle limitation unless expanding it is trivial and oracle-covered. Axis/legend text goes through `units_label()` via `plotting.labels` (extend `labels.py` beyond legend/marker helpers as needed).

## Acceptance

- Oracle cases for both functions Ã— both backends green.
- No hand-composed unit f-strings remain in these two code paths.
- Header lookups use the public schema/header helpers (no new hard-coded legacy names).

## Depends on

#646

Part of epic #567.
