# Issue #940: update example notebooks

Source: https://github.com/jepegit/cellpy/issues/940

## Original issue text

notebooks in examples folder.

for instance names of columns have changed from what function examples uses, some files/functions have been removed from source files, removed arguments in functions.

specifics: 
- notebooks I've seen impacted now: 02_initial_data_inspection, 03_capacity_vs_voltage, 05_GITT, 06_loading_different_formats, 08_batmo_bdf
- from cellpy.readers import core doesnt exist
- "20210210_FC.h5" file is not in "data"/"out", but just "data"
- plotutils.summary_plot(y="shifted_discharge_capacity_gravimetric") doesnt exist
- voltage instead of potential in get_cap function -> change in notebook to potential
- some cycles in plotutils.cycle_info_plot doesnt show up(missing in example file?)
- no column named "type" in data.steps -> rename to "step_type" ?
   - also other columns missing/renamed ('cycle', 'step', 'type', 'point_min', 'point_max', 'voltage_first',\n       'voltage_last'],\n      dtype='str')
- cell is not defined in cell.schema.raw -> change to just c
- raw_data plot of batmo_bdf.csv doesnt work -> change voltage to potential
- change to cycle_nm and potential for plotting batmo voltage-capacity curves
- 09_loading_pec_data is written in a different format than the others. commented information instead of in markdown cells

also change example usage of get function in cellreader.py.
