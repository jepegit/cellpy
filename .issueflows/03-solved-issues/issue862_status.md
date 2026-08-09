# Status — Issue #862

- [x] Done

## What's done

- Investigated and confirmed `ica_plot` and `dva_plot` share the same `_render_ica_dva`
  renderer (plotly + mpl) and both currently lacked dash distinction for `direction="both"`
  (the issue's "ica_plotter already does this" comparison was to the separate
  `cellpy.plotting.collected.ica_plotter`, fixed in #821 — a different code path).
- Plan written (`issue862_plan.md`), accepted.
- `PlotlyBackend._render_ica_dva` (`cellpy/plotting/backends/plotly.py`): dash keyed by
  direction (`charge` solid, `discharge` dotted) whenever both directions are overlaid in the
  frame; single-direction plots stay solid.
- `MatplotlibBackend._render_ica_dva` (`cellpy/plotting/backends/mpl.py`): same behaviour via
  `linestyle` (`"-"` / `":"`).
- Docstrings updated on both renderers.
- New tests in `tests/test_ica_plot_prepare.py`: dash/linestyle differ for `direction="both"`
  (both `ica_plot` and `dva_plot`, both backends), and stays solid for a single direction.
- `uv run pytest tests/test_ica_plot_prepare.py`, related plotting tests (49 passed), and the
  full `uv run pytest -m essential` merge gate (698 passed, 1 skipped, 2 xfailed, 1 xpassed, no
  regressions) all green with `MPLBACKEND=Agg`.
- `black --diff` / `flake8` on touched files: only pre-existing, unrelated findings (line-length
  config mismatch); no new issues from this change.

## Remaining work

None.
