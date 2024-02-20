# Stuff that you might want to do with `cellpy`

:::{note}
This chapter would benefit from some more love and care. Any help
on that would be highly appreciated.
:::

A more or less random collection of things that you might want to do with
`cellpy`. This is not a tutorial, but rather a collection of examples.

## Extract current-voltage graphs

If you have loaded your data into a CellpyCell-object,
let's now consider how to extract current-voltage graphs
from your data. We assume that the name of your
CellpyCell-object is `cell_data`:

```python
cycle_number = 5
charge_capacity, charge_voltage = cell_data.get_ccap(cycle_number)
discharge_capacity, discharge_voltage = cell_data.get_dcap(cycle_number)
```

You can also get the capacity-voltage curves with both charge and discharge:

```python
capacity, charge_voltage = cell_data.get_cap(cycle_number)
# the second capacity (charge (delithiation) for typical anode half-cell experiments)
# will be given "in reverse".
```

The `CellpyCell` object has several get-methods, including getting current,
timestamps, etc.

## Extract summaries of runs

Summaries of runs includes data pr. cycle for your data set. Examples of
summary data is charge- and
discharge-values, coulombic efficiencies and internal resistances.
These are calculated by the
`make_summary` method.

Remark that note all the possible summary statistics are calculated as
default. This means that you might have to re-run the `make_summary` method
with appropriate parameters as input (e.g. `normalization_cycle`,
to give the appropriate cycle numbers to use for finding nominal capacity).

Another method is responsible for investigating the individual steps in the
data (`make_step_table`). It is typically run automatically before creating
the summaries (since the summary creation depends on the step_table). This
table is interesting in itself since it contains delta, minimum, maximum and
average values for the measured values pr. step. This is used to find out
what type of step it is, *e.g.* a charge-step or maybe a ocv-step. It is
possible to provide information to this function if you already knows what
kind of step each step is. This saves `cellpy` for a lot of work.

Remark that the default is to calculate values for each unique (step-number -
cycle-number) pair. For some experiments, a step can be repeated many times
pr. cycle. And if you need for example average values of the voltage for each
step (for example if you are doing GITT experiments), you would need to
tell `make_step_table` that it should calculate for all the steps
(`all_steps=True`).

## Create dQ/dV plots

The methods for creating incremental capacity curves is located in
the `cellpy.utils.ica` module ({ref}`utils-ica`).

## Do some plotting

The plotting methods are located in the `cellpy.utils.plotting` module
({ref}`utils-plotting`).

## What else?

There are many things you can do with `cellpy`. The idea is that you
should be able to use `cellpy` as a tool to do your own analysis. This
means that you need to know a little bit about python and how to use
the different modules. It is not difficult, but it requires some
playing around and maybe reading some of the source code. Let's keep our
fingers crossed and hope that the documentation will be improved in the
future.

Why not just try out the highly popular (?) `cellpy.utils.batch`
utility. You will need to make (or copy from a friend) the "database" (an excel-file
with appropriate headers in the first row) and make sure that all the paths
are set up correctly in you `cellpy` configuration file. Then you can
process many cells in one go. And compare them.

Or, for example: If you would like to do some interactive plotting of your
data, try to install `plotly` and use `Jupyter Lab` to make some fancy plots
and dash-boards.

And why not: make a script that goes through all your thousands of measured
cells, extracts the life-time (e.g. number of cycles until the capacity
has dropped below 80% of the average of the three first cycles), and plot
this versus time the cell was put. And maybe color the data-points based
on who was doing the experiment?
