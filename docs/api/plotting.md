# Plotting

The shared plotting machinery. Figure loading and saving, legend and marker
post-processing, and the plotly templates all live here in **one** copy —
`cellpy.utils.plotutils`, `cellpy.utils.collectors` and
`cellpy.utils.batch_tools.batch_plotters` re-export from it, so existing
imports keep working.

The drawing functions themselves (`summary_plot`, `raw_plot`,
`cycle_info_plot`, `cycles_plot`) still live in
[Utils](utils.md#plotting) and move here in a later phase of the redesign.

::: cellpy.plotting.figures

::: cellpy.plotting.labels

::: cellpy.plotting.theme
