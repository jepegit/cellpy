# Issue #638 — Status

- [ ] Done

## What's done

- Plan accepted (2026-07-23).
- Branch `cursor/638-summary-prepare-render-4efd`; draft PR #644.

## Remaining work

- Add `context.py` + `prepare/summary.py` (port preparer, emit `FigureSpec`).
- Complete `PlotlyBackend.render`; delete `PlotlyPlotBuilder` + provisional env flag.
- Flip `summary_plot`; keep `SeabornPlotBuilder` on the same prepared frame.
- Tests (prepare + oracle + summary_plot) and design-note update.
