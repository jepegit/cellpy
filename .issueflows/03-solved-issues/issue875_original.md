# Issue #875: spread_plot traces carry no hovertemplate — turning on spread loses all hover detail

Source: https://github.com/jepegit/cellpy/issues/875

## Original issue text

Found while wiring group-averaged summary plots in [cellpy-simple-gui](https://github.com/cellpy/cellpy-simple-gui) (against **cellpy 2.1.2**).

## What happens

On the collected summary path, hover is informative — until `spread=True`, at which point **every trace has `hovertemplate = None`**.

Same collection, same columns, three renderings:

| mode | `hovertemplate` on the first trace |
|---|---|
| per-cell | `cellpy<br>group=1<br>sub_group=1<br>variable=coulombic_efficiency<br>Cycle (n.)=%{x}<br>value=%{y}` |
| `group_it=True` | `group=1<br>variable=coulombic_efficiency<br>Cycle (n.)=%{x}<br>mean=%{y}` |
| `group_it=True, spread=True` | **`None`** — on all 18 traces, mean lines included |

## Why

`summary_plotter` goes through plotly.express, which attaches hover from the frame. `spread_plot` builds traces directly with `go.Scatter` (`make_subplots` + add_trace) and never sets `hovertemplate` or `hoverinfo`, so the figure ships with Plotly's bare default.

The docstring already flags the function as experimental — this looks like one of the gaps that implies, rather than a deliberate choice.

## Why it matters for an app

Spread is the mode where hover is *most* useful: the band hides the individual cells, so the tooltip is the only way to read a value. Losing group, variable, cycle and value at exactly that moment is a visible regression to a user toggling one checkbox.

There is also a smaller issue underneath: the **Upper Bound / Lower Bound** traces are hoverable. They are construction artefacts (mean ± std), so a tooltip on them reads like a measurement that was never taken.

## Suggestions

1. Set `hovertemplate` on the mean traces in `spread_plot`, matching the `group_it` path's fields (group, variable, x, y) — ideally with the spread itself, since `mean` and `std` are both in hand at that point.
2. Set `hoverinfo="skip"` on the band edges so only the mean is hoverable.
3. Longer term, the docstring says plotly.express is to be replaced by this path for all summary plots — worth making hover parity part of that, since it is currently the main functional difference.

## Workaround (app)

cellpy-simple-gui reconstructs hover after the fact: it groups traces by subplot, takes the variable from the y-axis title and the group from the mean trace's name, derives `std` from the upper-bound trace, and skips hover on the bounds. It works, but it depends on trace naming (`"Upper Bound <group>"`) and on emission order (mean, upper, lower) — both internal details that would be better not to rely on.

## Environment

cellpy 2.1.2, Python 3.13, Windows.
