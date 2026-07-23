# Issue #639: Matplotlib backend; retire SeabornPlotBuilder; unify backend=

Source: https://github.com/jepegit/cellpy/issues/639

## Original issue text

## Context

Part of epic #567 (Stage 1 — Spec pipeline for `summary_plot`). Plan of record: `architecture-plan/cellpy2-plotting-redesign-plan.md`.

## Scope

Add `cellpy/plotting/backends/mpl.py` that renders the same `FigureSpec` (seaborn used only for palette/style helpers, not as a separate backend). Delete `SeabornPlotBuilder`. Public API: `backend="plotly"|"matplotlib"` on `summary_plot`; keep `interactive=` as a `warn_once` alias registered in `DEPRECATIONS.md` (removal 2.1).

## Acceptance

- Matplotlib summary oracle cases green and describe to the same structural shape family-for-family as plotly where the snapshot already compares them.
- No `SeabornPlotBuilder` class remains.
- Calling `interactive=True/False` warns once and maps to the right backend.

## Depends on

#638

Part of epic #567.
