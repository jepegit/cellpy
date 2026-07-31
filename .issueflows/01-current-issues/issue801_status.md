# Issue #801 — Status

- [ ] Done

## What's done

- Plan accepted (pretty labels default; no `spec=`; include `layout_updates`).
- Implemented on collected Plotly path:
  - `plotly_template=` override
  - `layout_updates=` after collector layout
  - default pretty `y_label_mapper` (clears `variable=…` facet strip)
  - `height_per_panel=` alias of `sub_fig_min_height`
  - `y_ranges` applied before label cleanup (keeps #804 working with pretty labels)
- Docs: `plotting-collected.md`, docstrings on `collected_plot` / `Collection.plot` / `summary_plotter`.
- Tests: `tests/test_collected_app_hooks.py` + updated `tests/test_collected_summary_axes.py` (14 passed).
- Draft PR: https://github.com/jepegit/cellpy/pull/808 (#808, draft)

## Remaining work

- `/iflow-close` (HISTORY, finalize PR, mark Done).
