# Deprecations

Auto-generated table of registered deprecations. Regenerate with:

```shell
uv run python -m cellpy._deprecation
```

| Name | Replacement | Introduced | Removal |
| --- | --- | --- | --- |
| `cycle_info_plot(interactive=...)` | `backend="plotly"|"matplotlib"` | 2.0 | 2.1 |
| `cycles_plot(interactive=...)` | `backend="plotly"|"matplotlib"` | 2.0 | 2.1 |
| `cycles_plot(xlim=...)` | `cycles_plot(x_range=...)` | 2.0 | 2.1 |
| `cycles_plot(ylim=...)` | `cycles_plot(y_range=...)` | 2.0 | 2.1 |
| `dva_plot(interactive=...)` | `backend="plotly"|"matplotlib"` | 2.0 | 2.1 |
| `ica.Converter` | `cellpy.ica.transform_half_cycle with IcaOptions` | 2.0 | 2.1 |
| `ica.dqdv(cycle=...)` | `cellpy.ica.dqdv(cycles=...)` | 2.0 | 2.1 |
| `ica.dqdv(label_direction=...)` | `the direction column, which the specced frame always carries` | 2.0 | 2.1 |
| `ica.dqdv(split=... / tidy=...)` | `cellpy.ica.dqdv(direction=...) and cellpy.ica.to_wide()` | 2.0 | 2.1 |
| `ica.dqdv_cycle` | `cellpy.ica.dqdv (returns the specced long frame)` | 2.0 | 2.1 |
| `ica.dqdv_cycles` | `cellpy.ica.dqdv (returns the specced long frame)` | 2.0 | 2.1 |
| `ica.dqdv_np` | `cellpy.ica.transform_half_cycle with IcaOptions` | 2.0 | 2.1 |
| `ica_plot(interactive=...)` | `backend="plotly"|"matplotlib"` | 2.0 | 2.1 |
| `legacy header attribute access (headers_normal / _summary / _step_table)` | `c.schema.raw / c.schema.steps / c.schema.summary` | 2.0 | 2.1 |
| `make_new_cell` | `CellpyCell.vacant` | 2.0 | 2.1 |
| `plotutils.summary_plot_legacy` | `cellpy.utils.plotutils.summary_plot (same figures, same options)` | 2.0 | 2.1 |
| `raw_plot(interactive=...)` | `backend="plotly"|"matplotlib"` | 2.0 | 2.1 |
| `summary_plot(interactive=...)` | `backend="plotly"|"matplotlib"` | 2.0 | 2.1 |
| `the 'dq' column of the ica output frame` | `the 'dqdv' column of the same frame` | 2.0 | 2.1 |
