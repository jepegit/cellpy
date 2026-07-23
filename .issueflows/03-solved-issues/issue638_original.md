# Issue #638: Port summary prepare path and flip summary_plot to prepare→spec→render

Source: https://github.com/jepegit/cellpy/issues/638

## Original issue text

## Context

Part of epic #567 (Stage 1 — Spec pipeline for `summary_plot`). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md`.

## Scope

Add `cellpy/plotting/prepare/summary.py` by extracting/reusing `SummaryPlotDataPreparer` (filters, rate rescaling, normalization, formation marking, CV partitioning → tidy long frame + `FigureSpec`). Point public `summary_plot` at context adapter → registry → prepare → backend.render. Preserve the user-facing signature and defaults (including named `y=` strings and `return_data=True` frame shape).

## Acceptance

- Figure-spec oracle green for all summary families × both backends currently covered.
- `return_data` frame columns/dtypes match today's builder output on the oracle cell.
- `SummaryPlotDataPreparer` / `PlotlyPlotBuilder` live code either becomes the prepare/backend implementation or is deleted in this PR — no third parallel summary path left.

## Depends on

#637

Part of epic #567.
