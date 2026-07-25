# Issue #679: bug in BatchICACollector

Source: https://github.com/jepegit/cellpy/issues/679

## Original issue text

Bug in v2.0.0rc1.

Running the following cell in batch loader notebook:

```python
cycles_collected = collectors.BatchICACollector(
    b,
    plot_type="fig_pr_cycle",
    cycles=[1, 2, 3],
    palette="Viridis",
    data_collector_arguments={"voltage_resolution": 0.01},
)
```

Error message:

```python
WARNING:py.warnings:[C:\Users\jepe\.pixi\envs\cellpy-v2\Lib\site-packages\cellpy\utils\collectors.py:1698](file:///C:/Users/jepe/.pixi/envs/cellpy-v2/Lib/site-packages/cellpy/utils/collectors.py#line=1697): RuntimeWarning: dqdv failed for 1 half-cycle(s): cycle 2 discharge
  curves = ica.dqdv(

---------------------------------------------------------------------------
KeyError                                  Traceback (most recent call last)
File [~\.pixi\envs\cellpy-v2\Lib\site-packages\pandas\core\indexes\base.py:3641](file:///C:/Users/jepe/.pixi/envs/cellpy-v2/Lib/site-packages/pandas/core/indexes/base.py#line=3640), in Index.get_loc(self, key)
   3640 try:
-> 3641     return self._engine.get_loc(casted_key)
   3642 except KeyError as err:

File pandas/_libs/index.pyx:168, in pandas._libs.index.IndexEngine.get_loc()
--> 168 'Could not get source, probably due dynamically evaluated source code.'

File pandas/_libs/index.pyx:197, in pandas._libs.index.IndexEngine.get_loc()
--> 197 'Could not get source, probably due dynamically evaluated source code.'

File pandas/_libs/hashtable_class_helper.pxi:7668, in pandas._libs.hashtable.PyObjectHashTable.get_item()
-> 7668 'Could not get source, probably due dynamically evaluated source code.'

File pandas/_libs/hashtable_class_helper.pxi:7676, in pandas._libs.hashtable.PyObjectHashTable.get_item()
-> 7676 'Could not get source, probably due dynamically evaluated source code.'

KeyError: 'cycle_num'

The above exception was the direct cause of the following exception:

KeyError                                  Traceback (most recent call last)
Cell In[10], line 1
----> 1 cycles_collected = collectors.BatchICACollector(
      2     b,
      3     plot_type="fig_pr_cycle",
      4     cycles=[1, 2, 3],

File [~\.pixi\envs\cellpy-v2\Lib\site-packages\cellpy\utils\collectors.py:1286](file:///C:/Users/jepe/.pixi/envs/cellpy-v2/Lib/site-packages/cellpy/utils/collectors.py#line=1285), in BatchICACollector.__init__(self, b, plot_type, cycles, max_cycle, rate, rate_on, rate_std, rate_agg, inverse, label_mapper, backend, cycles_to_plot, width, palette, show_legend, legend_position, fig_title, cols, group_legend_muting, only_selected, *args, **kwargs)
   1264 elevated_data_collector_arguments = dict(
   1265     cycles=cycles,
   1266     max_cycle=max_cycle,
   (...)   1273     only_selected=only_selected,
   1274 )
   1275 elevated_plotter_arguments = dict(
   1276     cycles_to_plot=cycles_to_plot,
   1277     width=width,
   (...)   1283     group_legend_muting=group_legend_muting,
   1284 )
-> 1286 super().__init__(
   1287     b,
   1288     family_kind="ica",
   1289     data_collector=ica_collector,
   1290     collector_name="ica",
   1291     backend=backend,
   1292     elevated_data_collector_arguments=elevated_data_collector_arguments,
   1293     elevated_plotter_arguments=elevated_plotter_arguments,
   1294     *args,
   1295     **kwargs,
   1296 )

File [~\.pixi\envs\cellpy-v2\Lib\site-packages\cellpy\utils\collectors.py:295](file:///C:/Users/jepe/.pixi/envs/cellpy-v2/Lib/site-packages/cellpy/utils/collectors.py#line=294), in BatchCollector.__init__(self, b, data_collector, plotter, collector_name, name, nick, autorun, backend, elevated_data_collector_arguments, elevated_plotter_arguments, data_collector_arguments, plotter_arguments, experimental, family_kind, **kwargs)
    292 self.parse_units()
    294 if autorun:
--> 295     self.update(update_name=False)

File [~\.pixi\envs\cellpy-v2\Lib\site-packages\cellpy\utils\collectors.py:609](file:///C:/Users/jepe/.pixi/envs/cellpy-v2/Lib/site-packages/cellpy/utils/collectors.py#line=608), in BatchCollector.update(self, data_collector_arguments, plotter_arguments, reset, update_data, update_name, update_plot)
    607 if update_plot:
    608     try:
--> 609         self.render()
    610     except TypeError as e:
    611         print("Type error:", e)

File [~\.pixi\envs\cellpy-v2\Lib\site-packages\cellpy\utils\collectors.py:451](file:///C:/Users/jepe/.pixi/envs/cellpy-v2/Lib/site-packages/cellpy/utils/collectors.py#line=450), in BatchCollector.render(self, **kwargs)
    443     self.figure = self.plotter(
    444         self.data,
    445         backend=self.backend,
   (...)    448         **kwargs,
    449     )
    450     return
--> 451 self.figure = collected_plot(
    452     self.data,
    453     family_kind=self.family_kind,
    454     backend=self.backend,
    455     journal=self.b.journal,
    456     units=self.units,
    457     **kwargs,
    458 )

File [~\.pixi\envs\cellpy-v2\Lib\site-packages\cellpy\plotting\collected.py:1474](file:///C:/Users/jepe/.pixi/envs/cellpy-v2/Lib/site-packages/cellpy/plotting/collected.py#line=1473), in collected_plot(frame, family_kind, layout, kind, backend, method, plot_type, spread, **opts)
   1469 if backend_key == "seaborn":
   1470     # Keep the historical seaborn branch without forcing get_backend("matplotlib")
   1471     # into the single-cell summary path.
   1472     return render_collected(frame, spec, backend_override="seaborn")
-> 1474 return get_backend(backend_key).render(frame, spec)

File [~\.pixi\envs\cellpy-v2\Lib\site-packages\cellpy\plotting\backends\plotly.py:303](file:///C:/Users/jepe/.pixi/envs/cellpy-v2/Lib/site-packages/cellpy/plotting/backends/plotly.py#line=302), in PlotlyBackend.render(self, frame, spec)
    300 if kind == "collected":
    301     from cellpy.plotting.collected import render_collected
--> 303     return render_collected(frame, spec, backend_override="plotly")
    304 if kind == "cycles":
    305     return self._render_cycles(frame, spec)

File [~\.pixi\envs\cellpy-v2\Lib\site-packages\cellpy\plotting\collected.py:1394](file:///C:/Users/jepe/.pixi/envs/cellpy-v2/Lib/site-packages/cellpy/plotting/collected.py#line=1393), in render_collected(frame, spec, backend_override)
   1392     return summary_plotter(frame, backend=backend, **opts)
   1393 if family_kind == "ica":
-> 1394     return ica_plotter(frame, backend=backend, method=method, **opts)
   1395 if family_kind == "cycles":
   1396     return cycles_plotter(frame, backend=backend, method=method, **opts)

File [~\.pixi\envs\cellpy-v2\Lib\site-packages\cellpy\plotting\collected.py:1273](file:///C:/Users/jepe/.pixi/envs/cellpy-v2/Lib/site-packages/cellpy/plotting/collected.py#line=1272), in ica_plotter(collected_curves, cycles_to_plot, backend, method, direction, **kwargs)
   1270 if method == "film":
   1271     kwargs["range_y"] = kwargs.pop("range_y", None) or (1, max_cycle)
-> 1273 return _cycles_plotter(
   1274     collected_curves,
   1275     x="voltage",
   1276     y="dqdv",
   1277     z="cycle",
   1278     g="cell",
   1279     x_label="Voltage",
   1280     x_unit="V",
   1281     y_label="dQ/dV",
   1282     y_unit="mAh/g/V.",
   1283     default_title=f"Incremental Analysis Plots",
   1284     direction=direction,
   1285     backend=backend,
   1286     method=method,
   1287     cycles=cycles_to_plot,
   1288     **kwargs,
   1289 )

File [~\.pixi\envs\cellpy-v2\Lib\site-packages\cellpy\plotting\collected.py:911](file:///C:/Users/jepe/.pixi/envs/cellpy-v2/Lib/site-packages/cellpy/plotting/collected.py#line=910), in _cycles_plotter(collected_curves, cycles, x, y, z, g, standard_deviation, default_title, backend, method, match_axes, **kwargs)
    909         number_of_figs = len(cycles)
    910     else:
--> 911         number_of_figs = len(collected_curves[_CCOLS.cycle_num].unique())
    912 elif method == "summary":
    913     number_of_figs = len(collected_curves["variable"].unique())

File [~\.pixi\envs\cellpy-v2\Lib\site-packages\pandas\core\frame.py:4378](file:///C:/Users/jepe/.pixi/envs/cellpy-v2/Lib/site-packages/pandas/core/frame.py#line=4377), in DataFrame.__getitem__(self, key)
   4374 
   4375         if is_single_key:
   4376             if self.columns.nlevels > 1:
   4377                 return self._getitem_multilevel(key)
-> 4378             indexer = self.columns.get_loc(key)
   4379             if is_integer(indexer):
   4380                 indexer = [indexer]
   4381         else:

File [~\.pixi\envs\cellpy-v2\Lib\site-packages\pandas\core\indexes\base.py:3648](file:///C:/Users/jepe/.pixi/envs/cellpy-v2/Lib/site-packages/pandas/core/indexes/base.py#line=3647), in Index.get_loc(self, key)
   3643     if isinstance(casted_key, slice) or (
   3644         isinstance(casted_key, abc.Iterable)
   3645         and any(isinstance(x, slice) for x in casted_key)
   3646     ):
   3647         raise InvalidIndexError(key) from err
-> 3648     raise KeyError(key) from err
   3649 except TypeError:
   3650     # If we have a listlike key, _check_indexing_error will raise
   3651     #  InvalidIndexError. Otherwise we fall through and re-raise
   3652     #  the TypeError.
   3653     self._check_indexing_error(key)

KeyError: 'cycle_num'
```

## Comments (curated summary)

- **Clarifications / constraints**:
  - Failure is specific to `plot_type="fig_pr_cycle"`; `plot_type="fig_pr_cell"` and `plot_type="film"` did not fail on the same batch.

_Note: this section is an interpretive summary of the comment thread, not a verbatim dump. Source comments: 1, last comment by @jepegit on 2026-07-24._
