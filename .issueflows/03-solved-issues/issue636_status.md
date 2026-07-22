# Issue #636 — Status

- [ ] Done

## What's done

- Plan accepted (recommended defaults for unknown-`y`, minimal panels, `SUMMARY_FAMILIES` from registry).
- Added `cellpy/plotting/spec.py` (`AxisSpec` / `PanelSpec` / `FigureSpec`).
- Added `cellpy/plotting/registry.py` with 20 builtin `PlotFamily` records, `get` / `families` / `_register_family`.
- `SummaryPlotInfo._create_col_info` is a thin header-bound adapter; `prepare_data` validates via `registry.get(y)`.
- Exported new API from `cellpy.plotting`; `tests/figure_spec_support.SUMMARY_FAMILIES` derives from `families()`.
- Essential registry unit tests in `tests/test_plotting_registry.py`.
- Verified: `tests/test_plotting_registry.py` + `tests/test_figure_specs.py` + `tests/test_plotutils_headers.py` green; `pytest -m essential` green (533 passed; ignored `test_arbin_variants_two_stage.py` collection ImportError for missing `libodbc` — pre-existing env gap).

## Remaining work

- `/iflow-close` (PR already open as draft #640).
