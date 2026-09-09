# Plot one cell

Four ready-made plots cover most of what you want to look at straight after
loading a cell. This page shows what each one is for, how to get the figure
object back, and how to save it.

For plotting a whole *batch* of cells on one set of axes, see
[Batch processing](../examples/batch_utility/cellpy_batch_processing.md). For
dQ/dV and dV/dQ, see [Compute ICA / DVA](ica.md).

## What you need installed

Plotting is optional, so a bare `pip install cellpy` cannot draw anything:

```console
python -m pip install "cellpy[batch]"          # plotly, seaborn, kaleido
python -m pip install "cellpy[plotting-mpl]"   # matplotlib
```

`cellpy[batch]` is the one you normally want — plotly is the default backend.
If plotly is missing, cellpy warns and falls back to matplotlib; if that is
missing too you get an `OptionalDependencyError` naming the extra.

## The four plots

```python
from cellpy.utils import example_data
from cellpy.utils.plotutils import (
    summary_plot,
    cycles_plot,
    raw_plot,
    cycle_info_plot,
)

c = example_data.raw_file()
```

| Function | Answers | Typical use |
| --- | --- | --- |
| `summary_plot` | how does the cell behave over its life? | capacity fade, coulombic efficiency, C-rates |
| `cycles_plot` | what do the voltage curves look like? | potential vs capacity, cycle by cycle |
| `raw_plot` | what did the tester actually record? | voltage / current vs time |
| `cycle_info_plot` | what happened inside one cycle? | raw traces annotated with step types |

### Careful: two of them return a figure, two of them show it

This trips people up. `summary_plot` and `raw_plot` hand you the figure and do
nothing else. `cycles_plot` and `cycle_info_plot` display the figure themselves
and return `None`.

```python
fig = summary_plot(c)          # returns a figure
fig.show()                     # you display it

cycles_plot(c)                 # displays it itself, returns None
fig = cycles_plot(c, return_figure=True)          # ask for the figure instead
fig = cycle_info_plot(c, cycle=3, get_axes=True)  # same idea, different keyword
```

In a Jupyter notebook the returned plotly figure also renders on its own if it
is the last expression in the cell — which is why the difference is easy to
miss until you move your code into a script.

## Capacity over cycle life — `summary_plot`

```python
fig = summary_plot(c, y="capacities_gravimetric_coulombic_efficiency")
fig.show()
```

The `y` argument names a **family** — a pre-composed set of panels — rather
than a single column. To see what is available:

```python
from cellpy.plotting import families

for name, description in families():
    print(f"{name:50s} {description}")
```

```text
capacities                                         Raw charge/discharge capacity vs cycle
capacities_absolute                                Absolute charge/discharge capacity vs cycle
capacities_areal                                   Areal charge/discharge capacity vs cycle
capacities_gravimetric                             Gravimetric charge/discharge capacity vs cycle
capacities_gravimetric_coulombic_efficiency        Gravimetric capacity with coulombic efficiency
capacities_gravimetric_split_constant_voltage      Gravimetric capacity split into CV / non-CV parts
capacities_gravimetric_with_rate                   Gravimetric capacity with C-rate panels
fullcell_standard_gravimetric                      Full-cell standard: CE, capacity, retention, CV (gravimetric)
voltages                                           End-of-charge and end-of-discharge voltages vs cycle
...
```

The list also includes families used by the other plot functions (`cycles`,
`raw`, `cycle_info`, `ica`, `dva`) — those are not valid `summary_plot` values.

Reading the names: everything comes in `_gravimetric` / `_areal` /
`_absolute` flavours, matching the summary columns described in
[Units, mass, area and C-rates](units.md). Pick the one your normalisation
supports — an areal plot of a cell with no `area=` is just the absolute plot
with a misleading axis label.

Common adjustments:

```python
fig = summary_plot(
    c,
    y="capacities_gravimetric",
    x_range=[0, 50],           # cycles to show
    title="Si anode, 0.1C",
    markers=False,             # lines only
    show_formation=False,      # do not split out the first cycles
    formation_cycles=3,        # how many count as formation
)
```

`summary_plot` draws formation cycles in their own narrow panel by default, so
that a large first-cycle capacity does not squash the rest of the curve.

## Voltage curves — `cycles_plot`

```python
cycles_plot(c, cycles=[1, 5, 10, 15])
```

Potential against capacity, one coloured curve per cycle. Useful options:

```python
fig = cycles_plot(
    c,
    cycles=[5, 10, 15],
    mode="gravimetric",              # or "areal" / "absolute"
    method="forth-and-forth",        # how charge and discharge are laid out
    interpolated=True,
    number_of_points=200,            # points per curve after interpolation
    return_figure=True,
)
```

This one is meant for a quick look rather than a publication figure — for full
control, pull the numbers out (see below) and draw them yourself.

!!! warning "Formation-only selections crash the matplotlib backend"
    `cycles_plot(c, cycles=[1, 2, 3], backend="matplotlib")` raises
    `ValueError: arange: cannot compute length` when every selected cycle is a
    formation cycle (the first three, by default). The plotly backend is fine.
    Tracked as [issue #1026](https://github.com/jepegit/cellpy/issues/1026).

## Raw traces — `raw_plot`

```python
fig = raw_plot(c, plot_type="voltage-current")
fig.show()
```

`plot_type` picks what goes on the axes:

| `plot_type` | Shows |
| --- | --- |
| `"voltage-current"` (default) | potential and current vs time |
| `"raw"` | the raw time-series traces |
| `"capacity"` | capacity vs time |
| `"capacity-current"` | capacity and current vs time |
| `"full"` | everything, stacked |

Raw frames can be large. `max_points` thins the data while keeping the minimum
and maximum inside each bucket, so spikes survive:

```python
fig = raw_plot(c, plot_type="full", max_points=5000)
```

You can also restrict it to a few cycles: `raw_plot(c, cycles=[3, 4])`.

## Inside one cycle — `cycle_info_plot`

```python
cycle_info_plot(c, cycle=3)
```

Raw traces for a single cycle, annotated with the step numbers and step types
that `make_step_table` assigned. This is the plot to reach for when you suspect
cellpy has mislabelled a step — a CV tail read as a rest, say.

```python
cycle_info_plot(c, cycle=3, t_unit="hours", v_unit="V", i_unit="mA")
```

## Getting the numbers behind a plot

Every plot can hand back the frame it drew, which is usually what you want if
you are going to redraw it in your own style or paste it into a spreadsheet:

```python
fig, data = summary_plot(c, y="capacities_gravimetric", return_data=True)

print(list(data.columns))
# ['cycle_num', 'variable', 'value', 'row', 'cycle_type']
```

The frame is in long form: one row per point, with `variable` naming the
quantity. `cycles_plot(..., return_data=True)` works the same way.

## Choosing a backend

```python
fig = summary_plot(c, backend="matplotlib")
```

| Backend | Good for | Notes |
| --- | --- | --- |
| `"plotly"` (default) | exploring — zoom, hover, toggle traces | needs `cellpy[batch]` |
| `"matplotlib"` | static figures for a paper or report | needs `cellpy[plotting-mpl]` |

The matplotlib backend styles itself through seaborn; `seaborn_palette` and
`seaborn_style` are accepted by `summary_plot` and `cycles_plot`.

## Saving a figure

**Plotly, as an image file** (needs kaleido, which comes with
`cellpy[batch]`):

```python
from cellpy.plotting import write_image

fig = summary_plot(c, y="capacities_gravimetric")
open("capacity.png", "wb").write(write_image(fig, "png"))
```

`write_image` returns the encoded bytes. Supported formats are `png`, `svg`,
`pdf`, `jpg` / `jpeg` and `webp`; `scale=2` doubles the pixel density, and
`width=` / `height=` are passed straight through.

**Plotly, as an interactive HTML file** — no kaleido needed, and the reader can
still zoom:

```python
fig.write_html("capacity.html")
```

**Matplotlib:**

```python
fig = summary_plot(c, y="capacities_gravimetric", backend="matplotlib")
fig.savefig("capacity.png", dpi=300, bbox_inches="tight")
```

## Labelling axes yourself

If you redraw the data, use the unit helpers rather than typing the unit in by
hand — see
[Units, mass, area and C-rates](units.md#writing-the-unit-on-a-plot-label).

## See also

- [Compute ICA / DVA](ica.md) — dQ/dV and dV/dQ, and their `ica_plot` /
  `dva_plot` companions
- [Batch processing](../examples/batch_utility/cellpy_batch_processing.md) —
  `b.plot()` across many cells
- [Capacity vs voltage](../examples/03_capacity_vs_voltage.md) — a worked
  notebook
- [Troubleshooting](../troubleshooting.md) — `OptionalDependencyError` and
  other plotting stumbles
