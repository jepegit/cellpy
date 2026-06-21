# Status for issue #366: bug-plotutils-summary-plot

- [x] Done

## What was done

- Identified the root cause: `plotutils.summary_plot(c, ..., formation_cycles=False)` (or `formation_cycles=0`) crashed with `TypeError: bad operand type for unary ~: 'slice'`. The `SummaryPlotConfig` left `show_formation=True` while `_mark_formation_cycles` returned the `slice(None, None)` sentinel, so `_configure_formation_axes` evaluated `~slice(None, None)` and failed.
- Fix: added `SummaryPlotConfig.__post_init__` in [cellpy/utils/plotutils.py](../../cellpy/utils/plotutils.py) that coerces `formation_cycles` to `int` and forces `show_formation = False` when `formation_cycles < 1`, mirroring the long-standing normalisation in `summary_plot_legacy` (line ~3354).
- Tests: added `TestSummaryPlotFormationCyclesNormalisation` in [tests/test_plotutils_summary_plot.py](../../tests/test_plotutils_summary_plot.py) covering:
  - `SummaryPlotConfig.from_kwargs(formation_cycles=0/False/3)` normalisation,
  - end-to-end `summary_plot(...)` calls (the exact reproduction from the issue) on both the plotly and seaborn backends, parametrised over `formation_cycles in (False, 0)`.
- HISTORY.md: appended a bullet under `## 1.0.3 (pre-release)`.

## Tests

- `uv run pytest tests/test_plotutils_summary_plot.py -x` — all green (confirmed by user).

## Remaining work

None. The bug is fixed and covered by regression tests. Closes #366.
