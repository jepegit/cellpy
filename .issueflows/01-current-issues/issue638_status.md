# Issue #638 — Status

- [ ] Done

## What's done

- Plan accepted (2026-07-23).
- Branch `cursor/638-summary-prepare-render-4efd`; draft PR #644.
- Added `cellpy/plotting/context.py` (`CellContext` / `from_source`).
- Ported preparer to `cellpy/plotting/prepare/summary.py`; `prepare()` returns `(frame, FigureSpec)` with formation/no-formation knobs in `extras['render']`.
- Completed `PlotlyBackend.render`; deleted `PlotlyPlotBuilder` + `CELLPY_SUMMARY_PLOTLY_SPEC` dual-path.
- Flipped public `summary_plot` to context → registry → prepare → render; `SeabornPlotBuilder` kept on the same frame until #639.
- Design notes: `plotting-prepare.md`; updated backends/registry docs.
- Tests: `tests/test_summary_prepare.py`; layout test asserts builders gone.
- Verified green:
  - `tests/test_summary_prepare.py` + layout + registry
  - `tests/test_plotutils_summary_plot.py` + `tests/test_figure_specs.py` (103)
  - `pytest -m essential --ignore=tests/test_arbin_variants_two_stage.py` (551)

## Remaining work

- `/iflow-close` — HISTORY, archive issue docs, push, mark Done.
