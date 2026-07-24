# Issue #668: bugs in batch

Source: https://github.com/jepegit/cellpy/issues/668

## Original issue text

Running the loader notebook (using standard template), several bugs were found:

**Bug in `b.plot`**

```python
# Plot the charge capacity and the C.E. (and resistance and rate) vs. cycle number (standard plot)
b.plot(rate=True, ir=True,  direction="discharge")
```

Get this error report:

```python
WARNING:py.warnings:[C:\Users\jepe\.pixi\envs\cellpy-v1\Lib\site-packages\cellpy\utils\batch_tools\batch_plotters.py:811](file:///C:/Users/jepe/.pixi/envs/cellpy-v1/Lib/site-packages/cellpy/utils/batch_tools/batch_plotters.py#line=810): PerformanceWarning: DataFrame is highly fragmented.  This is usually the result of calling `frame.insert` many times, which has poor performance.  Consider joining all columns at once using pd.concat(axis=1) instead. To get a de-fragmented frame, use `newframe = frame.copy()`
  summaries = summaries.reset_index()

CRITICAL:root:could not get the required summaries (<class 'KeyError'>: "['cycle_index'] not in index")
---------------------------------------------------------------------------
AttributeError                            Traceback (most recent call last)
Cell In[5], line 2
      1 # Plot the charge capacity and the C.E. (and resistance and rate) vs. cycle number (standard plot)
----> 2 b.plot(rate=True, ir=True,  direction="discharge")

File [~\.pixi\envs\cellpy-v1\Lib\site-packages\cellpy\utils\batch.py:1443](file:///C:/Users/jepe/.pixi/envs/cellpy-v1/Lib/site-packages/cellpy/utils/batch.py#line=1442), in Batch.plot(self, backend, reload_data, **kwargs)
   1437     # 1: summary_plotting_engine
   1438     # 2:   _preparing_data_and_plotting_legacy
   1439     # 3:   _plotting_data_legacy
   1440     # 4:   plot_cycle_life_summary_[backend]
   1442 elif backend == "plotly":
-> 1443     self.plotter.do(**kwargs)
   1445 elif backend == "seaborn":
   1446     self.plotter.do(**kwargs)

File [~\.pixi\envs\cellpy-v1\Lib\site-packages\cellpy\utils\batch_tools\batch_core.py:136](file:///C:/Users/jepe/.pixi/envs/cellpy-v1/Lib/site-packages/cellpy/utils/batch_tools/batch_core.py#line=135), in Doer.do(self, **kwargs)
    134 self.empty_the_farms()
    135 logging.debug(f"running - {str(engine)}")
--> 136 self.run_engine(engine, **kwargs)
    138 for dumper in self.dumpers:
    139     logging.debug(f"exporting - {str(dumper)}")

File [~\.pixi\envs\cellpy-v1\Lib\site-packages\cellpy\utils\batch_tools\batch_plotters.py:1505](file:///C:/Users/jepe/.pixi/envs/cellpy-v1/Lib/site-packages/cellpy/utils/batch_tools/batch_plotters.py#line=1504), in CyclingSummaryPlotter.run_engine(self, engine, **kwargs)
   1503 if self.reset_farms:
   1504     self.farms = []
-> 1505 self.farms, self.barn = engine(
   1506     experiments=self.experiments, farms=self.farms, **kwargs
   1507 )
   1509 logging.debug("::engine ended")

File [~\.pixi\envs\cellpy-v1\Lib\site-packages\cellpy\utils\batch_tools\batch_plotters.py:757](file:///C:/Users/jepe/.pixi/envs/cellpy-v1/Lib/site-packages/cellpy/utils/batch_tools/batch_plotters.py#line=756), in summary_plotting_engine(**kwargs)
    755         if backend == "plotly":
    756             if kwargs.pop("plotly_show", True):
--> 757                 canvas.show()
    759 return farms, barn

AttributeError: 'NoneType' object has no attribute 'show'
```
**Running custom `update_cell function`**

```python
def update_cell(c):
    raw = c.data.raw
    steps = c.data.steps
    discharge = steps.query("type=='discharge'")
    un = set(discharge["step"].unique())
    for i, g in raw.groupby("cycle_index"):
        sts = set(g.step_index.unique()) & un
        dc_max = g.discharge_capacity.max()
        if sts:
            lp = g.loc[g.step_index == max(sts), "data_point"].max()
            raw.loc[(raw.data_point > lp) & (raw.cycle_index == i), "discharge_capacity"] = dc_max
    c.make_step_table()
    c.make_summary()

    return c
```

Running in a loop, getting this error message:

```python
WARNING:cellpycore.summarizers:found 1:730 non-categorized steps (please, check your raw-limits)


---------------------------------------------------------------------------
AttributeError                            Traceback (most recent call last)
Cell In[8], line 5
      1 for label in b.cell_names:
      2     print(f"processing {label}")
      3     c = b.experiment.data[label]
      4     cellpyfilename = b.pages.loc[label, "cellpy_file_name"]
----> 5     c = update_cell(c)
      6     c.save(cellpyfilename)

Cell In[7], line 13, in update_cell(c)
      9         if sts:
     10             lp = g.loc[g.step_index == max(sts), "data_point"].max()
     11             raw.loc[(raw.data_point > lp) & (raw.cycle_index == i), "discharge_capacity"] = dc_max
     12     c.make_step_table()
---> 13     c.make_summary()
     14 
     15     return c

File [~\.pixi\envs\cellpy-v1\Lib\site-packages\cellpy\readers\cellreader.py:4653](file:///C:/Users/jepe/.pixi/envs/cellpy-v1/Lib/site-packages/cellpy/readers/cellreader.py#line=4652), in CellpyCell.make_summary(self, find_ir, find_end_voltage, use_cellpy_stat_file, ensure_step_table, remove_duplicates, normalization_cycles, nom_cap, nom_cap_specifics, old, create_copy, exclude_types, exclude_steps, selector_type, selector, **kwargs)
   4640     self._make_summar_legacy(
   4641         # find_ocv=find_ocv,
   4642         find_ir=find_ir,
   (...)   4649         nom_cap_specifics=nom_cap_specifics,
   4650     )
   4651     return self
-> 4653 data = self._make_summary(
   4654     find_ir=find_ir,
   4655     find_end_voltage=find_end_voltage,
   4656     use_cellpy_stat_file=use_cellpy_stat_file,
   4657     ensure_step_table=ensure_step_table,
   4658     remove_duplicates=remove_duplicates,
   4659     normalization_cycles=normalization_cycles,
   4660     nom_cap=nom_cap,
   4661     nom_cap_specifics=nom_cap_specifics,
   4662     create_copy=create_copy,
   4663     **kwargs,
   4664 )
   4665 if create_copy:
   4666     other = copy.deepcopy(self)

File [~\.pixi\envs\cellpy-v1\Lib\site-packages\cellpy\readers\cellreader.py:4822](file:///C:/Users/jepe/.pixi/envs/cellpy-v1/Lib/site-packages/cellpy/readers/cellreader.py#line=4821), in CellpyCell._make_summary(self, mass, nom_cap, nom_cap_specifics, update_mass, select_columns, find_ir, find_end_voltage, ensure_step_table, remove_duplicates, sort_my_columns, use_cellpy_stat_file, normalization_cycles, create_copy, **kwargs)
   4813 current_conversion_factor = core_units.calculate_current_conversion_factor(
   4814     data.raw_units["current"], to_units=self.cellpy_units
   4815 )
   4816 specific_conversion_factors = {
   4817     mode: self.get_converter_to_specific(
   4818         dataset=data, mode=mode, to_units=self.cellpy_units
   4819     )
   4820     for mode in specifics
   4821 }
-> 4822 data = self.core.make_core_summary(
   4823     data,
   4824     find_ir=find_ir,
   4825     find_end_voltage=find_end_voltage,
   4826     select_columns=select_columns,
   4827     current_conversion_factor=current_conversion_factor,
   4828 )
   4829 data = self.core.add_scaled_summary_columns(
   4830     data,
   4831     nom_cap_abs=nom_cap_abs,
   (...)   4834     specific_conversion_factors=specific_conversion_factors,
   4835 )
   4837 if sort_my_columns:

File [~\.pixi\envs\cellpy-v1\Lib\site-packages\cellpycore\cell_core.py:1020](file:///C:/Users/jepe/.pixi/envs/cellpy-v1/Lib/site-packages/cellpycore/cell_core.py#line=1019), in OldCellpyCellCore.make_core_summary(self, data, find_ir, find_end_voltage, select_columns, final_data_points, current_conversion_factor, ir_extractor, exclude_step_types)
   1015 nd.steps = native_steps
   1016 # Honor cycle_mode on the bridge exactly as the native path does (issue
   1017 # #129): without this the bridge summary always ran NORMAL, so anode
   1018 # half-cells silently got the wrong-direction coulombic_efficiency /
   1019 # coulombic_difference.
-> 1020 test_mode = _cycle_mode_to_test_mode(self.cycle_mode)
   1021 summarizers.make_summary(
   1022     nd,
   1023     native_schema,
   (...)   1026     exclude_step_types=exclude_step_types,
   1027 )
   1029 # C-rate / IR are now native-schema columns (issue #21): compute them on the
   1030 # native polars frame before the single native->legacy rename. Their native
   1031 # names match the legacy names, so they survive the rename untouched.

File [~\.pixi\envs\cellpy-v1\Lib\site-packages\cellpycore\cell_core.py:48](file:///C:/Users/jepe/.pixi/envs/cellpy-v1/Lib/site-packages/cellpycore/cell_core.py#line=47), in _cycle_mode_to_test_mode(cycle_mode)
     46 if cycle_mode is None:
     47     return config.TestMode.NORMAL
---> 48 key = cycle_mode.strip().lower()
     49 if key in _INVERTED_CYCLE_MODES:
     50     return config.TestMode.INVERTED

AttributeError: 'list' object has no attribute 'strip'
```
