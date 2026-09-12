# Issue #1026 — status

- [x] Done

## What's done

- `cellpy/plotting/backends/mpl.py::_render_cycles`: non-formation colour
  norm / `np.arange` / plotting / colourbar now run only when `rest_cycles`
  is non-empty. A `logging.warning` explains an empty axes when formation
  cycles are hidden and no non-formation cycle was selected.
- Regression tests in `tests/test_cycles_prepare.py`:
  `test_cycles_plot_matplotlib_only_formation_cycles` (3 lines drawn) and
  `..._hidden` (0 lines, warning logged).
- HISTORY bullet under `[Unreleased]`.

## Verification

- Repro script from the issue (Arbin `.res` test file): `cycles=[1, 2, 3]`
  failed with `ValueError: arange: cannot compute length` before, draws 3
  lines after; `[5, 6, 7]` and all-cycles unchanged.
- `uv run pytest tests/test_cycles_prepare.py tests/test_mpl_backend.py`
  green; `uv run pytest -m essential` green.

## Remaining work

- None.
