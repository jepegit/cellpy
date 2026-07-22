# Issue #637: Generic plotly panel/formation layout backend

Source: https://github.com/jepegit/cellpy/issues/637

## Original issue text

## Context

Part of epic #567 (Stage 1 — Spec pipeline for `summary_plot`). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md`.

## Scope

Add `cellpy/plotting/backends/base.py` (render protocol) and `backends/plotly.py` with **one** generic panel/formation/facet layout engine that replaces the four `PlotlyPlotBuilder._configure_formation_{1,2,3,4}_rows` methods. Wire a thin adapter so `PlotlyPlotBuilder` (or a parallel path behind a feature flag / internal switch) can render from `(tidy_frame, FigureSpec)`. Do not flip the public `summary_plot` default yet if parity is incomplete — ship behind an internal switch or keep dual-path until the next issue's gate.

## Acceptance

- Formation figures with 1–4 rows match the oracle structurally.
- No per-row-count method remains in the hot path once the switch is on.
- `tests/test_figure_specs.py` green for plotly summary cases.

## Depends on

#636

Part of epic #567.
