# Issue #1158 — plan

Drafted 2026-10-23. Not confirmed yet.

## Goal

Say, in the `cycle_info_plot` docstring and the plotting guide, what is displayed and what is returned. A notebook can show a figure while the call still returns `None`.

## Constraints

- Do not change the return contract. Default plotly calls `fig.show()` and returns `None`. `get_axes=True` returns that figure and does not show it. Default matplotlib returns `None` (the figure stays on pyplot, so an inline notebook still draws it). `get_axes=True` returns the axes tuple from the matplotlib backend, not a `Figure`.
- `tests/data/figure_specs.json` already records both default calls as empty (`backend: null`). `test_cycle_info_plot_backend_matplotlib` already asserts the matplotlib default is `None`.
- No in-repo `loader.ipynb` tells the reader to pass `get_axes=True` to get a figure. The cookiecutter processing notebook only has a commented `cycle_info_plot` call, with no `get_axes`. Do not edit that notebook.
- Do not rename `get_axes`. Do not fix the matplotlib axes tuple (`ax1, ax2, ax2, ax4`) in this issue.
- Docs live on `master`.

### Prior art

- `cycle_info_plot` in `src/cellpy/utils/plotutils.py` (about line 1331): plotly `show()` then `None`, unless `get_axes`. Matplotlib returns the render result only when `get_axes` is true.
- `MatplotlibBackend._render_cycle_info` in `src/cellpy/plotting/backends/mpl.py`: `get_axes` returns `(ax1, ax2, ax2, ax4)`; otherwise it returns the `Figure`. The wrapper then drops that figure when `get_axes` is false.
- `docs/guides/plotting.md` already says `cycle_info_plot` displays the figure and returns `None`, then assigns `cycle_info_plot(..., get_axes=True)` to `fig`. That assignment is a plotly figure. For matplotlib it is the axes tuple.
- `cycles_plot` uses `return_figure`, not `get_axes`. Leave that name alone.
- Toolbox: none of the `00-tools/` scripts inspect plot return values.
- No `graphify-out/`.

## Approach

1. Rewrite the `get_axes` argument and the `Returns` section of `cycle_info_plot` so each backend is explicit: what is drawn, and what the call returns, with and without `get_axes`.
2. In `docs/guides/plotting.md`, keep the "two of them return a figure, two of them show it" warning. Split the `cycle_info_plot` example into plotly (the returned object is the figure) and matplotlib (the returned object is the axes tuple). Say that seeing a plot in a notebook does not mean the call returned that object.
3. Extend `test_cycle_info_plot_backend_matplotlib` so `get_axes=True` is a tuple, not a `Figure`. Add a plotly check, skipped when plotly is missing: default is `None`, `get_axes=True` has `show`. Mark it essential, next to the existing matplotlib test.

## Files to touch

- `src/cellpy/utils/plotutils.py` — docstring only.
- `docs/guides/plotting.md` — the return-value warning and the `get_axes` example.
- `tests/test_raw_cycle_info_prepare.py` — lock the return contract.
- `HISTORY.md` at close.

## Test strategy

- `uv run pytest -m essential tests/test_raw_cycle_info_prepare.py -q`
- `uv run pytest -m essential` before close. No golden regeneration. The figure-spec rows for `cycle_info_plot` stay empty because the default return stays `None`.

## Open questions

1. **Leave the return values as they are, and only correct the docstring and the plotting guide?** Recommended yes. The figure the reporter sees is `fig.show()` (plotly) or the pyplot figure (matplotlib). The call still returns `None`.
2. **Skip `loader.ipynb` because it is not in this repo?** Recommended yes.
