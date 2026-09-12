# Issue #1026 — plan (yolo)

## Goal

`cycles_plot(c, backend="matplotlib", cycles=[1, 2, 3])` (every selected cycle
is a formation cycle) draws the formation cycles instead of raising
`ValueError: arange: cannot compute length`.

## Approach

`cellpy/plotting/backends/mpl.py::_render_cycles` builds the non-formation
colour normalisation, `np.arange` sequence, and colourbar unconditionally from
`rest_cycles`. When `rest_cycles` is empty, `min()` / `max()` are `NaN` and
`np.arange(NaN, NaN + 1, 1)` fails. Guard the whole non-formation block with
`if not rest_cycles.empty:` so only the formation block runs. Warn via
`logging` when nothing is left to draw (`show_formation=False` and no
non-formation cycles) rather than silently returning an empty axes.

## Files to touch

- `cellpy/plotting/backends/mpl.py` — guard in `_render_cycles`.
- `tests/test_cycles_prepare.py` — regression test (`cycles=[1, 2, 3]` and
  `show_formation=False` variants).
- `HISTORY.md` — bullet under `[Unreleased]`.

## Test strategy

- `uv run pytest tests/test_cycles_prepare.py tests/test_mpl_backend.py`
- `uv run pytest -m essential` (merge gate).
- Script repro from the issue against `example_data.raw_file()` on the branch.
