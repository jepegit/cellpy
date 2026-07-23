# Issue #658 — Status

- [x] Done

## What's done

- Added `cellpy.plotting.batch_summary` with relocated cycle-life frame prep +
  plotly/matplotlib renderers and public `batch_summary_plot`.
- Wired `Batch.plot` / `plot_summaries` through plotting; thin `_BatchPlotterHolder`
  keeps `b.plotter.figure` / `.farms`.
- Backend triage: plotly / matplotlib; `seaborn` → `warn_once` → matplotlib;
  `bokeh` → `ValueError`.
- Deleted `cellpy/utils/batch_tools/batch_plotters.py`; cleaned imports/docs/tests.
- Snapshot `tests/data/batch_figure_specs.json` + tests; DEPRECATIONS + migration
  note.
- Frame-prep fix: unnamed summary index named `cycle_index` before `reset_index`
  (latent break after index name became `None`).

## Remaining work

- None for this issue.

## Tests

- `MPLBACKEND=Agg uv run pytest tests/test_batch.py::test_batch_plot_* tests/test_batch.py::test_batch_figure_* tests/test_plotting_package.py tests/test_collectors.py tests/test_figure_specs.py` → 85 passed, 1 skipped.
