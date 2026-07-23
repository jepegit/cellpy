# Plotting

The shared plotting machinery. Figure loading and saving, legend and marker
post-processing, and the plotly templates all live here in **one** copy —
`cellpy.utils.plotutils` and `cellpy.utils.collectors` re-export from it, so
existing imports keep working. `Batch.plot` delegates to
`cellpy.plotting.batch_summary_plot` (#658); the old
`cellpy.utils.batch_tools.batch_plotters` module is gone.

The drawing functions themselves (`summary_plot`, `raw_plot`,
`cycle_info_plot`, `cycles_plot`) still live in
[Utils](utils.md#plotting) and move here in a later phase of the redesign.

::: cellpy.plotting.figures

::: cellpy.plotting.labels

::: cellpy.plotting.theme

::: cellpy.plotting.batch_summary
