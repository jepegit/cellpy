# Issue #637 — Status

- [ ] Done

## What's done

- Plan accepted (no-formation stays in builder; layout engine always on; full `render` flag default off; fullcell domains as named helper).
- Added `cellpy/plotting/backends/{base,plotly,__init__}.py` with `Backend` protocol, `configure_formation_layout`, `configure_fullcell_standard_domains`, `PlotlyBackend`.
- `PlotlyPlotBuilder._configure_formation_axes` is a thin adapter; `_configure_formation_{1,2,3,4}_rows` deleted.
- Design note: `.issueflows/04-designs-and-guides/plotting-backends.md`.
- Tests: `tests/test_plotly_backend_layout.py`; figure-spec oracle green (63 passed with plotly/seaborn); `pytest -m essential` 547 passed.

## Remaining work

- `/iflow-close`.
