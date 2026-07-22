# Issue #636: Add FigureSpec dataclasses and a PlotFamily registry

Source: https://github.com/jepegit/cellpy/issues/636

## Original issue text

## Context

Part of epic #567 (Stage 1 — Spec pipeline for `summary_plot`). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md`. Phase 0–2a already landed (#593–#596).

## Scope

Create `cellpy/plotting/spec.py` (`FigureSpec` / `PanelSpec` / `AxisSpec`) and `cellpy/plotting/registry.py` by mechanically translating today's `SummaryPlotInfo._create_col_info` if/elif chain into `PlotFamily` records for every current named y-set. Expose `plotting.families()` (list + descriptions) and provisional `_register_family(...)`. `summary_plot` still draws via the existing builders in this issue — only the column-set selection moves behind the registry (old path calls `registry.get(y)`).

## Acceptance

- Every y-set currently accepted by `summary_plot` resolves to a family.
- Unknown y raises a clear error listing known families.
- Figure-spec oracle unchanged (`tests/test_figure_specs.py` green without regenerating snapshots unless intentional).
- `_create_col_info` if/elif chain deleted or reduced to a thin adapter over the registry.

## Depends on

none

Part of epic #567.
