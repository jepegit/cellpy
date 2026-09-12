# Issue #1026: cycles_plot with matplotlib backend crashes when all selected cycles are formation cycles

Source: https://github.com/jepegit/cellpy/issues/1026

## Original issue text

## Symptom

`cycles_plot(..., backend="matplotlib")` raises `ValueError: arange: cannot
compute length` when every selected cycle is a formation cycle.

## Repro

```python
import matplotlib
matplotlib.use("Agg")

from cellpy.utils import example_data
from cellpy.utils.plotutils import cycles_plot

c = example_data.raw_file()          # 18 cycles
cycles_plot(c, backend="matplotlib", cycles=[1, 2, 3])   # boom
cycles_plot(c, backend="matplotlib", cycles=[5, 6, 7])   # fine
cycles_plot(c, backend="matplotlib")                     # fine (all cycles)
```

```text
File "cellpy/plotting/backends/mpl.py", line 1059, in _render_cycles
    cycle_sequence = np.arange(
        rest_cycles[ccols.cycle_num].min(),
        rest_cycles[ccols.cycle_num].max() + 1,
        1,
    )
ValueError: arange: cannot compute length
```

## Cause

`formation_cycles` defaults to `3`, so cycles 1–3 are all classified as
formation. `rest_cycles` is then empty, `.min()` / `.max()` return `NaN`, and
`np.arange(NaN, NaN + 1, 1)` fails.

`show_formation=False` does not help — the same `arange` still runs.

The plotly backend does not have this problem, so it is specific to
`cellpy/plotting/backends/mpl.py::_render_cycles`.

## Expected

Plotting only the formation cycles should work and draw those cycles, the same
way the plotly backend does.

## Suggested fix

Guard the `np.arange` on `rest_cycles` being non-empty in
`_render_cycles`, and skip the non-formation colour sequence when there are no
non-formation cycles to colour.

## Notes

Found while writing a plotting how-to guide for #1023 — "plot the first three
cycles" is a very natural first thing to try.
