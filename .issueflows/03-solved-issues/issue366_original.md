# Issue #366: bug-plotutils-summary-plot

Source: https://github.com/jepegit/cellpy/issues/366

## Original issue text

I get an error when trying to use plotutils.summary_plot on the pec example data when chosing not to show formation cycles.

### Code

```python

p = example_data.pec_file_path()
c = cellpy.get(p, instrument="pec_csv", cycle_mode="full_cell")
plotutils.summary_plot(
    c,
    y="capacities",
    width=800,
    height=400,
    formation_cycles=False,  # breaks if False, works if True
)
```

### Error message

```bash
TypeError                                 Traceback (most recent call last)
Cell In[10], line 1
----> 1 plotutils.summary_plot(
      2     c,
      3     y="capacities",
      4     width=800,

File /opt/tljh/user/lib/python3.12/site-packages/cellpy/utils/plotutils.py:94, in notebook_docstring_printer.<locals>.wrapper(*args, **kwargs)
     91         pass
     93 # Call the original function
---> 94 return func(*args, **kwargs)

File /opt/tljh/user/lib/python3.12/site-packages/cellpy/utils/plotutils.py:4885, in summary_plot(c, x, y, height, width, markers, title, x_range, y_range, ce_range, norm_range, cv_share_range, split, hover_columns, auto_convert_legend_labels, interactive, share_y, rangeslider, return_data, verbose, plotly_template, seaborn_palette, seaborn_style, formation_cycles, show_formation, show_legend, x_axis_domain_formation_fraction, column_separator, reset_losses, link_capacity_scales, fullcell_standard_normalization_type, fullcell_standard_normalization_factor, fullcell_standard_normalization_scaler, fullcell_standard_normalization_cycle_numbers, seaborn_line_hooks, filters, nominal_capacity, rate_filter_columns, **kwargs)
   4877 prepared_data_info = preparer.prepare_data(
   4878     c,
   4879     config,
   4880     plot_info,
   4881 )
   4883 builder = PlotlyPlotBuilder() if config.interactive else SeabornPlotBuilder()
-> 4885 fig = builder.build_plot(
   4886     prepared_data_info["data"],
   4887     prepared_data_info,
   4888     config,
   4889     config.additional_kwargs,
   4890     c,
   4891 )
   4893 if config.return_data:
   4894     return fig, prepared_data_info["data"]

File /opt/tljh/user/lib/python3.12/site-packages/cellpy/utils/plotutils.py:1665, in PlotlyPlotBuilder.build_plot(self, data, prepared_data_info, config, additional_kwargs, c)
   1663 # Configure formation cycles and subplot layouts
   1664 if config.show_formation:
-> 1665     self._configure_formation_axes(
   1666         fig,
   1667         data,
   1668         x,
   1669         config,
   1670         number_of_rows,
   1671         max_cycle,
   1672         min_cycle,
   1673         formation_cycle_selector,
   1674         show_y_labels_on_right_pane,
   1675         y,
   1676         max_val_normalized_col,
   1677         plotly_row_ratios,
   1678         plotly_row_space,
   1679         c,
   1680     )
   1681 else:
   1682     # Configure without formation cycles
   1683     self._configure_no_formation_axes(
   1684         fig,
   1685         config,
   (...)   1691         c,
   1692     )

File /opt/tljh/user/lib/python3.12/site-packages/cellpy/utils/plotutils.py:1783, in PlotlyPlotBuilder._configure_formation_axes(self, fig, data, x, config, number_of_rows, max_cycle, min_cycle, formation_cycle_selector, show_y_labels_on_right_pane, y, max_val_normalized_col, plotly_row_ratios, plotly_row_space, c)
   1778 x_axis_domain_rest = [
   1779     config.x_axis_domain_formation_fraction + config.column_separator / 2,
   1780     0.95,
   1781 ]
   1782 max_cycle_formation = data.loc[formation_cycle_selector, x].max()
-> 1783 min_cycle_rest = data.loc[~formation_cycle_selector, x].min()
   1785 if x == _hdr_summary.normalized_cycle_index:
   1786     dd = 0.1

TypeError: bad operand type for unary ~: 'slice'
```

Please fix the bug.
