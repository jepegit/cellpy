# Issue #646 — Status

- [x] Done

## What's done

- Plan accepted (`issue646_plan.md`).
- Registered `"cycles"` family with `entry_point="cycles_plot"`; summary oracle filters via `families(entry_point="summary_plot")`.
- Added `cellpy/plotting/prepare/curves.py` (`CyclesPrepareConfig` + `prepare` → frame/`FigureSpec`, `kind="cycles"`).
- Ported cycles render into `PlotlyBackend` / `MatplotlibBackend` (`_render_cycles`).
- Thinned `cycles_plot`: `backend=`, `warn_once` for `interactive=` / `xlim`/`ylim`; deleted `CyclesPlotterConfig` + private plotters.
- Tests: `tests/test_cycles_prepare.py`; oracle harness on `backend=`; design notes updated; `DEPRECATIONS.md` regenerated.
- `MPLBACKEND=Agg uv run pytest tests/test_cycles_prepare.py tests/test_plotting_registry.py tests/test_figure_specs.py tests/test_mpl_backend.py` — 72 passed.
- `MPLBACKEND=Agg uv run pytest -m essential --ignore=tests/test_arbin_variants_two_stage.py` — 562 passed, 1 skipped.
- `HISTORY.md` Unreleased bullet added; issue group archived to `03-solved-issues/`.

## Remaining work

- None (merge + `/iflow-cleanup` after PR lands).
